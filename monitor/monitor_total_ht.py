import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options

# Configurações de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configura o webdriver (certifique-se de ter o ChromeDriver instalado e no PATH)
chrome_options = Options()
chrome_options.add_argument("--headless")  # Executa o navegador em modo headless
chrome_options.add_argument("--disable-gpu")  # Necessário para o modo headless no Windows
chrome_options.add_argument("--no-sandbox")  # Necessário para o modo headless em algumas distribuições Linux
chrome_options.add_argument("--disable-dev-shm-usage")  # Necessário para o modo headless em algumas distribuições Linux

driver = webdriver.Chrome(options=chrome_options)

def monitor_total_ht():
    url = 'https://dropping-odds.com/'
    try:
        driver.get(url)
        logging.info('Acessou o site de futebol')

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

                        # URL da aba de mercado 'total_ht'
                        match_url = f'https://dropping-odds.com/event.php?id={game_id}&t=total_ht'

                        # Abre a página do jogo em uma nova aba
                        driver.execute_script(f"window.open('{match_url}', '_blank');")
                        driver.switch_to.window(driver.window_handles[1])

                        # Aguarda 3 segundos para garantir que a página carregue
                        time.sleep(3)

                        # Espera até que a aba especificada esteja presente
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.smenu a'))
                        )

                        # Extrai dados da aba 'total_ht'
                        extract_total_ht_data(driver.page_source, game_id, match_url)

                    except Exception as e:
                        logging.error(f"Erro ao processar a partida com game_id {game_id}: {e}")
                    finally:
                        # Fecha a aba do jogo e volta para a página principal
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])

                        # Aguarda 3 segundos antes de continuar
                        time.sleep(3)

                # Atualiza a página principal de partidas
                driver.refresh()
                logging.info('Página principal atualizada')

                # Aguarda 60 segundos antes de verificar novamente
                time.sleep(60)
            except Exception as e:
                logging.error(f"Erro encontrado no loop principal: {e}")
                logging.info("Tentando reconectar...")
                time.sleep(10)
                driver.get(url)
    except Exception as e:
        logging.error(f"Erro crítico no monitoramento: {e}")
    finally:
        # Fecha o navegador
        driver.quit()
        logging.info('Navegador fechado')

def extract_total_ht_data(page_source, game_id, match_url):
    soup = BeautifulSoup(page_source, 'html.parser')
    tables = soup.find_all('table')

    logging.info(f"Extraindo dados da aba 'total_ht' para game_id {game_id}")

    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) > 1:
                logging.info(f"Dados extraídos: {[cell.text.strip() for cell in cells]}")

if __name__ == "__main__":
    monitor_total_ht()