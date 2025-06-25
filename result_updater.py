import logging
import time
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from supabase_utils import get_alerts_to_update, update_alert_with_final_score
from data_extractor import extract_final_score
from config import GAME_PROCESSING_DELAY

def update_finished_games(driver: WebDriver):
    """
    Função principal para o processo de atualização de resultados.
    Recebe a instância do driver para reutilizá-la.
    """
    logging.info("--- Iniciando ciclo de atualização de placares finais ---")
    
    # 1. Busca por alertas que precisam de atualização (enviados nas últimas 3 horas)
    alerts_to_check = get_alerts_to_update(time_window_hours=3) 
    
    if not alerts_to_check:
        logging.info("Nenhum alerta para atualizar no momento.")
        return

    logging.info(f"Encontrados {len(alerts_to_check)} alertas para verificar o placar final.")

    for alert in alerts_to_check:
        game_id = alert['game_id']
        url = alert.get('url') # Usamos .get() para segurança
        
        if not url:
            logging.warning(f"URL não encontrada para o alerta do jogo {game_id}. Pulando.")
            continue
        
        try:
            logging.info(f"Verificando placar final para o jogo {game_id}...")
            
            # 2. Acessa a página do jogo
            driver.get(url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'table')))
            
            # 3. Extrai o placar final da última linha da tabela
            final_score = extract_final_score(driver.page_source)
            
            if final_score:
                logging.info(f"Placar final encontrado para {game_id}: {final_score}")
                # 4. Atualiza o placar no Supabase
                update_alert_with_final_score(game_id, final_score)
            else:
                logging.info(f"Placar final ainda não disponível para {game_id}.")

            time.sleep(GAME_PROCESSING_DELAY) # Reutiliza a configuração de delay

        except Exception as e:
            logging.error(f"Erro ao processar a atualização do jogo {game_id}: {e}")

    logging.info("--- Ciclo de atualização de placares finalizado ---")