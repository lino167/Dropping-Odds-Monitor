import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config import (
    SELENIUM_OPTIONS, 
    MONITORING_INTERVAL, 
    RETRY_DELAY, 
    GAME_PROCESSING_DELAY,
    UPDATE_RESULT_INTERVAL_MINUTES # Nova configuração importada
)
from data_extractor import extract_table_data, unify_tables
from alert_manager import check_and_create_alert, check_super_favorito_drop_duplo
from supabase_utils import salvar_alerta_supabase
from telegram_utils import send_telegram_message

# Importa a nova função de atualização de resultados
from result_updater import update_finished_games

class GameMonitor:
    def __init__(self):
        self.driver = self._setup_driver()
        # Contador para controlar quando executar a atualização de resultados
        self.update_cycle_counter = 0
        # Calcula a frequência em ciclos de monitoramento (ex: a cada 60 minutos)
        self.UPDATE_FREQUENCY_CYCLES = (UPDATE_RESULT_INTERVAL_MINUTES * 60) // MONITORING_INTERVAL

    def _setup_driver(self):
        """Configura e retorna uma instância do WebDriver."""
        chrome_options = Options()
        if SELENIUM_OPTIONS.get('headless'):
            chrome_options.add_argument("--headless")
        if SELENIUM_OPTIONS.get('disable_gpu'):
            chrome_options.add_argument("--disable-gpu")
        if SELENIUM_OPTIONS.get('no_sandbox'):
            chrome_options.add_argument("--no-sandbox")
        try:
            driver = webdriver.Chrome(options=chrome_options)
            logging.info("WebDriver iniciado com sucesso.")
            return driver
        except Exception as e:
            logging.error(f"Falha ao iniciar o WebDriver: {e}")
            exit()

    def monitor_games(self):
        """
        Loop principal que monitora jogos para novos alertas e 
        atualiza resultados de jogos finalizados periodicamente.
        """
        url = 'https://dropping-odds.com/'
        
        try:
            while True:
                try:
                    # 1. Tarefa Principal: Buscar por novos alertas potenciais
                    self._process_new_alerts(url)
                    
                    # 2. Tarefa Secundária: Atualizar placares finais periodicamente
                    self.update_cycle_counter += 1
                    if self.update_cycle_counter >= self.UPDATE_FREQUENCY_CYCLES:
                        # Passa a instância do driver para ser reutilizada
                        update_finished_games(self.driver)
                        self.update_cycle_counter = 0 # Reseta o contador
                    
                    logging.info(f"Ciclo concluído. Próxima verificação em {MONITORING_INTERVAL}s. Próxima atualização de placares em {self.UPDATE_FREQUENCY_CYCLES - self.update_cycle_counter} ciclos.")
                    time.sleep(MONITORING_INTERVAL)

                except Exception as e:
                    logging.error(f"Erro no loop principal: {e}")
                    time.sleep(RETRY_DELAY)
        except KeyboardInterrupt:
            logging.info("Execução interrompida pelo usuário.")
        finally:
            if self.driver:
                self.driver.quit()
            logging.info("Navegador fechado e recursos liberados.")

    def _process_new_alerts(self, url):
        """Busca e processa jogos na página principal para gerar novos alertas."""
        logging.info("--- Iniciando ciclo de busca por novos alertas ---")
        self.driver.get(url)
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.tablediv.pointer table tbody tr')))
        
        matches = self.driver.find_elements(By.CSS_SELECTOR, 'div.tablediv.pointer table tbody tr')
        game_ids = [match.get_attribute('game_id') for match in matches if match.get_attribute('game_id')]

        logging.info(f"Jogos a serem processados: {len(game_ids)}")
        for game_id in game_ids:
            try:
                 self._process_single_game_for_alert(game_id)
            except Exception as e:
                logging.error(f"Erro ao verificar jogo {game_id}: {e}")
            finally:
                time.sleep(GAME_PROCESSING_DELAY)

    def _process_single_game_for_alert(self, game_id):
        """Processa um jogo para verificar se um novo alerta deve ser gerado."""
        try:
            match_url_total = f'https://dropping-odds.com/event.php?id={game_id}&t=total'
            match_url_1x2 = f'https://dropping-odds.com/event.php?id={game_id}&t=1x2'

            self.driver.get(match_url_total)
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'table')))
            data_total = extract_table_data(self.driver.page_source, game_id, match_url_total, "total")

            self.driver.get(match_url_1x2)
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'table')))
            data_1x2 = extract_table_data(self.driver.page_source, game_id, match_url_1x2, "1x2")

            if not data_total or not data_1x2: return

            unified_data, _ = unify_tables(data_total, data_1x2)
            if unified_data.empty: return

            # Tenta gerar um alerta com a estratégia "Drop Duplo"
            alerta_para_enviar = check_super_favorito_drop_duplo(unified_data, game_id, match_url_total)
            
            # Se não houver alerta da estratégia acima, verifica a sua original
            if not alerta_para_enviar:
                alerta_para_enviar = check_and_create_alert(unified_data, game_id, match_url_total)

            # Se qualquer uma das estratégias gerou um alerta, salva e envia
            if alerta_para_enviar:
                if salvar_alerta_supabase(alerta_para_enviar):
                    send_telegram_message(alerta_para_enviar['mensagem_html'])

        except Exception as e:
            logging.error(f"Erro inesperado ao processar o jogo {game_id} para alerta: {e}", exc_info=True)


def main():
    monitor = GameMonitor()
    monitor.monitor_games()

if __name__ == "__main__":
    main()
