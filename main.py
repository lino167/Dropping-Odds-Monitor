import logging
from monitor.monitor_games import monitor_games
import pandas as pd
from selenium import webdriver
from monitor.monitor_games import driver

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

if __name__ == "__main__":
    try:
        monitor_games()
    except KeyboardInterrupt:
        logging.info("Execução interrompida pelo usuário.")
       
        sent_games_df = pd.DataFrame()  
        SENT_GAMES_FILE = "sent_games.xlsx"  
        sent_games_df.to_excel(SENT_GAMES_FILE, index=False)
        logging.info('Jogos enviados salvos antes de sair.')
        
        try:
            driver.quit()
            logging.info('Navegador fechado com sucesso.')
        except Exception as e:
            logging.warning(f'Erro ao tentar fechar o navegador: {e}')
            