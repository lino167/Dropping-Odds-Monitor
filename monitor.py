from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging
from config import SELENIUM_OPTIONS, MONITORING_INTERVAL, MAX_RETRIES, RETRY_DELAY
from config import (
    SELENIUM_OPTIONS, MONITORING_INTERVAL, MAX_RETRIES, 
    RETRY_DELAY, GAME_PROCESSING_DELAY
)
from data_extractor import extract_table_data, unify_tables
from alert_manager import check_and_create_alert
from telegram_utils import send_telegram_message
from supabase_utils import salvar_alerta_supabase

class GameMonitor:
    def __init__(self):
        self.driver = self._setup_driver()

    def _setup_driver(self):
        """Configura e retorna uma instância do WebDriver."""
        chrome_options = Options()
        
        if SELENIUM_OPTIONS['headless']:
            chrome_options.add_argument("--headless")
        if SELENIUM_OPTIONS['disable_gpu']:
            chrome_options.add_argument("--disable-gpu")
        if SELENIUM_OPTIONS['no_sandbox']:
            chrome_options.add_argument("--no-sandbox")
        if SELENIUM_OPTIONS['disable_dev_shm_usage']:
            chrome_options.add_argument("--disable-dev-shm-usage")
        if 'window_size' in SELENIUM_OPTIONS:
            chrome_options.add_argument(f"--window-size={SELENIUM_OPTIONS['window_size']}")

        try:
            driver = webdriver.Chrome(options=chrome_options)
            logging.info("WebDriver iniciado com sucesso.")
            return driver
        except Exception as e:
            logging.error(f"Falha ao iniciar o WebDriver: {e}")
            exit()

        
    def monitor_games(self):
        """Monitora continuamente os jogos e verifica alertas."""
        url = 'https://dropping-odds.com/'
        retry_count = 0

        try:
            while retry_count < MAX_RETRIES:
                try:
                    self._process_games(url)
                    retry_count = 0  # Reset retry count after successful processing
                    time.sleep(MONITORING_INTERVAL)
                except Exception as e:
                    logging.error(f"Erro no loop principal: {e}")
                    retry_count += 1
                    if retry_count >= MAX_RETRIES:
                        logging.error("Número máximo de tentativas atingido. Encerrando.")
                        break
                    time.sleep(RETRY_DELAY)
        except KeyboardInterrupt:
            logging.info("Execução interrompida pelo usuário.")
        except Exception as e:
            logging.error(f"Erro crítico no monitoramento: {e}")
        finally:
            self.driver.quit()
            logging.info("Navegador fechado e recursos liberados.")

    def _process_games(self, url):
        """Processa todos os jogos na página principal."""
        self.driver.get(url)
        logging.info('Acessou o site de futebol')

        # Espera até que a tabela de partidas esteja presente
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.tablediv.pointer table tbody tr'))
        )
        logging.info('Tabela de partidas encontrada')

        # Captura todos os IDs das partidas
        matches = self.driver.find_elements(By.CSS_SELECTOR, 'div.tablediv.pointer table tbody tr')
        game_ids = [match.get_attribute('game_id') for match in matches if match.get_attribute('game_id')]
        logging.info(f"IDs capturados: {game_ids}")

        # Itera sobre cada ID capturado
        for game_id in game_ids:
            try:
                logging.info(f"Processando partida com game_id: {game_id}")
                self._process_single_game(game_id)
            except Exception as e:
                logging.error(f"Erro ao processar a partida com game_id {game_id}: {e}")
            finally:
                time.sleep(2)  # Aguarda 2 segundos entre partidas

    def _process_single_game(self, game_id):
        """Processa uma única partida, verifica e envia alerta se necessário."""
        try:
            logging.info(f"Processando partida: {game_id}")
            match_url_total = f'https://dropping-odds.com/event.php?id={game_id}&t=total'
            match_url_1x2 = f'https://dropping-odds.com/event.php?id={game_id}&t=1x2'

            # 1. Extrai dados
            self.driver.get(match_url_total)
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'table')))
            data_total = extract_table_data(self.driver.page_source, game_id, match_url_total, table_type="total")

            self.driver.get(match_url_1x2)
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'table')))
            data_1x2 = extract_table_data(self.driver.page_source, game_id, match_url_1x2, table_type="1x2")

            if not data_total or not data_1x2:
                logging.warning(f"Não foi possível extrair dados de uma das abas para o jogo {game_id}.")
                return

            # 2. Unifica dados
            unified_data, _ = unify_tables(data_total, data_1x2)

            if unified_data is None or unified_data.empty:
                logging.warning(f"Dados unificados resultaram vazios ou nulos para o jogo {game_id}. Pulando.")
                return

            # 3. Verifica se um alerta deve ser gerado
            alerta_para_enviar = check_and_create_alert(unified_data, game_id, match_url_total)

            if alerta_para_enviar:
                logging.info(f"Condições de alerta atendidas para {game_id}. Tentando salvar...")
                if salvar_alerta_supabase(alerta_para_enviar):
                    logging.info(f"Alerta salvo. Enviando para o Telegram: {game_id}")
                    send_telegram_message(alerta_para_enviar['mensagem_html'])
                else:
                    logging.error(f"Falha ao salvar alerta no Supabase para {game_id}. Envio cancelado.")
        
        except Exception as e:
            logging.error(f"Erro inesperado ao processar o jogo {game_id}: {e}", exc_info=True)

def main():
    monitor = GameMonitor()
    monitor.monitor_games()

if __name__ == "__main__":
    main()