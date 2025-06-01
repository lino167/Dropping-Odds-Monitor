import requests
import logging
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def send_telegram_message(message):
    """Envia mensagem para o Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    response = requests.post(url, data=data)
    print(response.text)
    if response.status_code != 200:
        logging.error(f"Erro ao enviar mensagem para o Telegram: {response.text}")
    else:
        logging.info("Mensagem enviada com sucesso para o Telegram.")
    return response.ok
    
    