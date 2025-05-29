import requests
import logging
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

def send_telegram_message(message):
    """Envia mensagem para o Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        logging.info("Mensagem enviada com sucesso para o Telegram.")
        return response
    else:
        logging.error(f"Erro ao enviar mensagem para o Telegram: {response.text}")
        return None

def edit_telegram_message(message_id, new_message):
    """Edita mensagem existente no Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/editMessageText"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "message_id": message_id,
        "text": new_message,
        "parse_mode": "HTML"
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        logging.info("Mensagem editada com sucesso no Telegram.")
    else:
        logging.error(f"Erro ao editar mensagem no Telegram: {response.text}")