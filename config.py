import os
from dotenv import load_dotenv
import logging

# Carregar variáveis do arquivo .env
load_dotenv()

# Configurações do Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    logging.error("As variáveis TELEGRAM_TOKEN ou TELEGRAM_CHAT_ID não estão configuradas no .env.")
    exit()

# Configurações do Selenium
SELENIUM_OPTIONS = {
    'headless': True,
    'disable_gpu': True,
    'no_sandbox': True,
    'disable_dev_shm_usage': True,
    'window_size': "1920,1080"
}

# Configurações de Monitoramento
MONITORING_INTERVAL = 10  # segundos
MAX_RETRIES = 5
RETRY_DELAY = 10  # segundos

# Configuração de Logging
logging.basicConfig(level=logging.INFO)

# Colunas da planilha Excel
EXCEL_COLUMNS = [
    "game_id", 
    "Liga",
    "Times",
    "Favorito (F)",
    "Odd inicial do favorito",
    "Odd atual do favorito",
    "Queda (%)",
    "Linha de gols inicial",
    "Odd inicial da linha de gols",
    "Linha de gols atual",
    "Odd atual da linha de gols",
    "Drop",
    "Placar",
    "Tempo (minutos)",
    "Link"
]