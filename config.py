import os
from dotenv import load_dotenv
import logging

# Carrega as variáveis de ambiente do ficheiro .env
load_dotenv()

# --- Configurações do Telegram ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    logging.error("As variáveis TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID não estão configuradas no .env.")
    exit()

# --- Configurações do Supabase ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logging.error("As variáveis SUPABASE_URL ou SUPABASE_KEY não estão configuradas no .env.")
    exit()
    
# --- Configurações do Selenium ---
SELENIUM_OPTIONS = {
    'headless': True,               # Executa o Chrome em modo invisível (sem interface gráfica)
    'disable_gpu': True,            # Desativa a aceleração por hardware da GPU
    'no_sandbox': True,             # Desativa o modo sandbox (necessário em alguns ambientes de servidor)
    'disable_dev_shm_usage': True,  # Resolve problemas de recursos em ambientes Docker
    'window_size': "1920,1080"      # Define um tamanho de janela para o navegador
}

# --- Configurações de Monitoramento ---
# Intervalo entre a verificação da página principal para encontrar novos jogos (em segundos)
MONITORING_INTERVAL = 90

# Pausa entre o processamento de cada jogo individual para não sobrecarregar o site (em segundos)
GAME_PROCESSING_DELAY = 2

# Número máximo de tentativas em caso de erro no loop principal
MAX_RETRIES = 3 
# Atraso entre as tentativas de reconexão (em segundos)
RETRY_DELAY = 30

# MODIFICAÇÃO: Nova configuração para o atualizador de resultados
# Intervalo em que o script irá verificar e atualizar os placares finais dos alertas (em minutos)
UPDATE_RESULT_INTERVAL_MINUTES = 60

# --- Configuração de Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
