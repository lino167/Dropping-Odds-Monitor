import os
from dotenv import load_dotenv
import logging

# Carregar variáveis do arquivo .env
load_dotenv()

# Configurações do Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    logging.error("As variáveis TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID não estão configuradas no .env.")
    exit()

# Configurações do Supabase (adicionado para clareza)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logging.error("As variáveis SUPABASE_URL ou SUPABASE_KEY não estão configuradas no .env.")
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
MONITORING_INTERVAL = 15  # segundos entre as verificações de novos jogos
GAME_PROCESSING_DELAY = 3 # segundos de espera entre o processamento de cada jogo
MAX_RETRIES = 3
RETRY_DELAY = 10  # segundos

# Configuração de Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)