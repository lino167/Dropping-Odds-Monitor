import time
import logging
import signal
import sys
import os  # Adicione esta importação para manipular caminhos
import tempfile  # Adicione esta importação
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.web_scraping import extract_table_data
from utils.file_operations import initialize_excel_file
from config.settings import SENT_GAMES_FILE
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from pandas import DataFrame
initialize_excel_file()

# Configurar o Chrome para rodar em modo headless
chrome_options = Options()
chrome_options.add_argument("--headless")  # Executa o navegador sem interface gráfica
chrome_options.add_argument("--disable-gpu")  # Necessário para sistemas Windows em alguns casos
chrome_options.add_argument("--no-sandbox")  # Desativa o sandboxing
chrome_options.add_argument("--disable-dev-shm-usage")  # Evita problemas de memória compartilhada
chrome_options.add_argument("--window-size=1920,1080")  # Define um tamanho de janela padrão
chrome_options.add_argument("--log-level=3")  # Reduz os logs do navegador
chrome_options.add_argument("--silent")  # Minimiza a saída de logs

# Inicializar o WebDriver com as opções configuradas
driver = webdriver.Chrome(options=chrome_options)

# Initialize sent_games_df as an empty DataFrame
sent_games_df = DataFrame(columns=["game_id", "match_url", "data"])

def signal_handler(sig, frame):
    print('Saving sent games and exiting...')
    sent_games_df.to_excel(SENT_GAMES_FILE, index=False)
    driver.quit()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def monitor_games():
    url = 'https://dropping-odds.com/'
    try:
        driver.get(url)
        logging.info('Acessou o site de futebol')

        # Loop para monitorar as partidas
        while True:
            try:
                # Espera até que a tabela de partidas esteja presente
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div.tablediv.pointer table tbody tr'))
                )
                logging.info('Tabela de partidas encontrada')

                # Extrai a lista de partidas
                matches = driver.find_elements(By.CSS_SELECTOR, 'div.tablediv.pointer table tbody tr')

                # Itera sobre cada partida
                for match in matches:
                    try:
                        game_id = match.get_attribute('game_id')
                        if not game_id:
                            logging.warning("game_id não encontrado para uma partida. Ignorando.")
                            continue

                        logging.info(f"Processando partida com game_id: {game_id}")

                        # URLs para cada aba
                        match_url = f'https://dropping-odds.com/event.php?id={game_id}&t=total'

                        # Abre a página do jogo em uma nova aba
                        driver.execute_script(f"window.open('{match_url}', '_blank');")
                        driver.switch_to.window(driver.window_handles[1])

                        # Aguarda 2 segundos para garantir que a página carregue
                        time.sleep(2)

                        # Espera até que a aba especificada esteja presente
                        WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.smenu a'))
                        )

                        # Extrai dados das tabelas em cada aba
                        extract_table_data(driver.page_source, game_id, match_url)

                    except Exception as e:
                        logging.error(f"Erro ao processar a partida com game_id {game_id}: {e}")
                    finally:
                        # Fecha a aba do jogo e volta para a página principal
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])

                        # Aguarda 3 segundos antes de continuar
                        time.sleep(2)

                # Atualiza a página principal de partidas
                driver.refresh()
                logging.info('Página principal atualizada')

                # Aguarda 30 segundos antes de verificar novamente
                time.sleep(30)
            except Exception as e:
                logging.error(f"Erro encontrado no loop principal: {e}")
                logging.info("Tentando reconectar...")
                time.sleep(10)
                driver.get(url)
    except Exception as e:
        logging.error(f"Erro crítico no monitoramento: {e}")
    finally:
        # Salva os jogos enviados antes de fechar
        try:
            sent_games_df.to_excel(SENT_GAMES_FILE, index=False)
            logging.info('Jogos enviados salvos')
        except Exception as e:
            logging.error(f"Erro ao salvar a planilha: {e}")

        # Fecha o navegador
        driver.quit()
        logging.info('Navegador fechado')

if __name__ == "__main__":
    try:
        monitor_games()
    except KeyboardInterrupt:
        logging.info("Execução interrompida pelo usuário.")
        sent_games_df.to_excel(SENT_GAMES_FILE, index=False)
        logging.info('Jogos enviados salvos antes de sair.')
        driver.quit()
        logging.info('Navegador fechado.')