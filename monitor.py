from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging
from config import SELENIUM_OPTIONS, MONITORING_INTERVAL, RETRY_DELAY, GAME_PROCESSING_DELAY
from data_extractor import extract_table_data, unify_tables
from alert_manager import check_and_create_alert, check_super_favorito_drop_duplo
from telegram_utils import send_telegram_message
from supabase_utils import salvar_alerta_supabase

class GameMonitor:
    def __init__(self):
        self.driver = self._setup_driver()
        self.games_in_observation = {}

    def _setup_driver(self):
        chrome_options = Options()
        if SELENIUM_OPTIONS.get('headless'):
            chrome_options.add_argument("--headless")
        try:
            driver = webdriver.Chrome(options=chrome_options)
            logging.info("WebDriver iniciado com sucesso.")
            return driver
        except Exception as e:
            logging.error(f"Falha ao iniciar o WebDriver: {e}")
            exit()

    def monitor_games(self):
        url = 'https://dropping-odds.com/'
        try:
            while True:
                try:
                    self._process_games(url)
                    logging.info(f"Ciclo concluído. Aguardando {MONITORING_INTERVAL} segundos...")
                    time.sleep(MONITORING_INTERVAL)
                except Exception as e:
                    logging.error(f"Erro no loop principal: {e}")
                    time.sleep(RETRY_DELAY)
        except KeyboardInterrupt:
            logging.info("Execução interrompida pelo usuário.")
        finally:
            self.driver.quit()
            logging.info("Navegador fechado e recursos liberados.")

    def _process_games(self, url):
        self.driver.get(url)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.tablediv.pointer table tbody tr'))
        )
        matches = self.driver.find_elements(By.CSS_SELECTOR, 'div.tablediv.pointer table tbody tr')
        game_ids = [match.get_attribute('game_id') for match in matches if match.get_attribute('game_id')]

        logging.info(f"Jogos a serem processados: {len(game_ids)}")
        for game_id in game_ids:
            try:
                self._process_single_game(game_id)
            except Exception as e:
                logging.error(f"Erro ao processar a partida com game_id {game_id}: {e}")
            finally:
                time.sleep(GAME_PROCESSING_DELAY)

    def _process_single_game(self, game_id):
        try:
            match_url_total = f'https://dropping-odds.com/event.php?id={game_id}&t=total'
            match_url_1x2 = f'https://dropping-odds.com/event.php?id={game_id}&t=1x2'

            self.driver.get(match_url_total)
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'table')))
            data_total = extract_table_data(self.driver.page_source, game_id, match_url_total, table_type="total")

            self.driver.get(match_url_1x2)
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'table')))
            data_1x2 = extract_table_data(self.driver.page_source, game_id, match_url_1x2, table_type="1x2")

            if not data_total or not data_1x2:
                return

            unified_data, _ = unify_tables(data_total, data_1x2)
            if unified_data.empty:
                return

            # MODIFICAÇÃO: Verifica a nova estratégia primeiro, passando o dicionário de observação
            alerta_para_enviar = check_super_favorito_drop_duplo(unified_data, game_id, match_url_total, self.games_in_observation)
            
            if not alerta_para_enviar:
                # Se não houver alerta da nova estratégia, verifica a antiga
                alerta_para_enviar = check_and_create_alert(unified_data, game_id, match_url_total)

            if alerta_para_enviar:
                if salvar_alerta_supabase(alerta_para_enviar):
                    send_telegram_message(alerta_para_enviar['mensagem_html'])

        except Exception as e:
            logging.error(f"Erro inesperado ao processar o jogo {game_id}: {e}", exc_info=True)


def main():
    monitor = GameMonitor()
    monitor.monitor_games()

if __name__ == "__main__":
    main()
