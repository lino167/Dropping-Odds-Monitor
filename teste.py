import os
import pandas as pd
import logging
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from dotenv import load_dotenv
import requests
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Carregar variáveis do arquivo .env
load_dotenv()

# Configurar credenciais do Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    logging.error("As variáveis TELEGRAM_TOKEN ou TELEGRAM_CHAT_ID não estão configuradas no .env.")
    exit()

# Configuração do Selenium WebDriver
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(options=chrome_options)

logging.basicConfig(level=logging.INFO)

# Função para enviar mensagens no Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"  # Para suportar formatação HTML na mensagem
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        logging.info("Mensagem enviada com sucesso para o Telegram.")
        return response
    else:
        logging.error(f"Erro ao enviar mensagem para o Telegram: {response.text}")
        return None

# Função para editar mensagens no Telegram
def edit_telegram_message(message_id, new_message):
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

# Função para verificar o resultado do jogo e editar a mensagem no Telegram
def check_game_result_and_edit_message(game_id, match_url_total, message_id, initial_score, line_current):
    try:
        # Acessar o link da aba "total"
        driver.get(match_url_total)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'table'))
        )

        # Extrair a última linha da tabela
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        table = soup.find('table')
        rows = table.find_all('tr')
        last_row = rows[-1] if rows else None

        if last_row:
            cells = last_row.find_all('td')
            time = int(cells[1].text.strip()) if cells[1].text.strip().isdigit() else 0

            # Verificar se o jogo terminou (tempo = 90)
            if time == 90:
                # Extrair o placar final
                matchinfo = soup.select_one("body > div.matchinfo")
                score_matchinfo = matchinfo.find('h2').text.strip() if matchinfo and matchinfo.find('h2') else "0-0"

                # Avaliar o resultado da aposta
                resultado = avaliar_resultado_aposta(score_matchinfo, line_current)

                # Editar a mensagem no Telegram
                new_message = (
                    f"⚽ <b>Alerta de queda de odd!</b>\n"
                    f"🏆 <b>Resultado final:</b>\n"
                    f"🔢 <b>Placar final:</b> {score_matchinfo}\n"
                    f"⚽ <b>Linha de gols:</b> {line_current}\n"
                    f"✅ <b>Resultado:</b> {resultado}"
                )
                edit_telegram_message(message_id, new_message)
    except Exception as e:
        logging.error(f"Erro ao verificar o resultado do jogo {game_id}: {e}")

# Função para avaliar o resultado da aposta
def avaliar_resultado_aposta(score_matchinfo: str, linha: str) -> str:
    # Extrai os gols do placar final
    gols = list(map(int, score_matchinfo.strip().split("-")))
    total_gols = sum(gols)

    # Trata a linha (pode ser tipo '2.5' ou '2.0,2.5')
    if "," in linha:
        partes = list(map(float, linha.split(",")))
    else:
        partes = [float(linha)]

    # Caso linha simples
    if len(partes) == 1:
        linha_valor = partes[0]
        if total_gols > linha_valor:
            return "🟢 GREEN"
        elif total_gols == linha_valor:
            return "⚪️ PUSH"
        else:
            return "🔴 RED"

    # Caso linha asiática
    else:
        metade1, metade2 = partes

        resultado1 = (
            1 if total_gols > metade1 else
            0.5 if total_gols == metade1 else
            0
        )
        resultado2 = (
            1 if total_gols > metade2 else
            0.5 if total_gols == metade2 else
            0
        )

        media = (resultado1 + resultado2) / 2

        if media == 1:
            return "🟢 GREEN"
        elif media == 0.5:
            return "🟡 MEIO GREEN"
        elif media == 0:
            return "🔴 RED"
        else:
            return "🟠 MEIO RED"  # Isso só ocorre se media for 0.25 ou 0.75 (raro)

# Função para acessar links e extrair dados das tabelas
def extract_table_data(page_source, game_id, match_url, table_type="total"):
    soup = BeautifulSoup(page_source, 'html.parser')
    tables = soup.find_all('table')

    # Selecionar o elemento que contém as informações do jogo
    matchinfo = soup.select_one("body > div.matchinfo")
    if matchinfo:
        league = matchinfo.find('h3').text.strip() if matchinfo.find('h3') else 'N/A'
        teams = matchinfo.find('h1').text.strip() if matchinfo.find('h1') else 'N/A'
        score_matchinfo = matchinfo.find('h2').text.strip() if matchinfo.find('h2') else 'N/A'

        # Separar os times em casa e fora
        if "-" in teams:
            home_team, away_team = [team.strip() for team in teams.split("-")]
        else:
            home_team, away_team = teams, "N/A"
    else:
        league = 'N/A'
        home_team = 'N/A'
        away_team = 'N/A'

    data = []
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')

            if table_type == "total" and len(cells) > 9:
                try:
                    row_data = {
                        'league': league,
                        'home_team': home_team,
                        'away_team': away_team,
                        'time': int(cells[1].text.strip()) if cells[1].text.strip().isdigit() else 0,
                        'score': cells[2].text.strip(),
                        'over': float(cells[3].text.strip()) if cells[3].text.strip().replace('.', '', 1).isdigit() else 0.0,
                        'handicap': cells[4].text.strip(),
                        'under': float(cells[5].text.strip()) if cells[5].text.strip().replace('.', '', 1).isdigit() else 0.0,
                        'drop': float(cells[6].text.strip()) if cells[6].text.strip().replace('.', '', 1).isdigit() else 0.0,
                        'sharp': float(cells[7].text.strip()) if cells[7].text.strip().replace('.', '', 1).isdigit() else 0.0,
                        'penalty': cells[8].text.strip() if cells[8].text.strip() else "0-0",
                        'red_card': cells[9].text.strip() if cells[9].text.strip() else "0-0"
                    }
                    data.append(row_data)
                except Exception as e:
                    logging.warning(f"Erro ao processar linha da tabela 'total': {e}")

            elif table_type == "1x2" and len(cells) > 4:
                try:
                    row_data = {
                        'league': league,
                        'home_team': home_team,
                        'away_team': away_team,
                        'time': int(cells[1].text.strip()) if cells[1].text.strip().isdigit() else 0,
                        'home': float(cells[3].text.strip()) if cells[3].text.strip().replace('.', '', 1).isdigit() else 0.0,
                        'draw': float(cells[4].text.strip()) if cells[4].text.strip().replace('.', '', 1).isdigit() else 0.0,
                        'away': float(cells[5].text.strip()) if cells[5].text.strip().replace('.', '', 1).isdigit() else 0.0,
                    }
                    data.append(row_data)
                except Exception as e:
                    logging.warning(f"Erro ao processar linha da tabela '1x2': {e}")

    return data

# Função para unificar tabelas "total" e "1x2" em um DataFrame
def unify_tables(data_total, data_1x2):
    if not data_total:
        logging.warning("Tabela 'total' está vazia.")
    else:
        logging.info(f"Tabela 'total' contém {len(data_total)} linhas.")

    if not data_1x2:
        logging.warning("Tabela '1x2' está vazia.")
    else:
        logging.info(f"Tabela '1x2' contém {len(data_1x2)} linhas.")

    # Cria DataFrames a partir dos dados extraídos
    df_total = pd.DataFrame(data_total)
    df_1x2 = pd.DataFrame(data_1x2)

    # Log para verificar os DataFrames criados
    logging.info(f"DataFrame 'total':\n{df_total.head()}")
    logging.info(f"DataFrame '1x2':\n{df_1x2.head()}")

    # Verifica se as colunas essenciais estão presentes
    for col in ['league', 'home_team', 'away_team']:
        if col not in df_total.columns:
            df_total[col] = 'N/A'
        if col not in df_1x2.columns:
            df_1x2[col] = 'N/A'

    # Unifica as tabelas com base na coluna 'time'
    unified_df = pd.merge(df_total, df_1x2, on='time', how='outer', suffixes=('_total', '_1x2'))

    # Log para verificar o DataFrame unificado
    logging.info(f"Tabela unificada:\n{unified_df.head()}")

    # Reorganiza as colunas para manter uma ordem consistente
    reordered_columns = [
        'league', 'home_team', 'away_team', 'time', 'score', 'over', 'handicap', 'under', 'drop', 'sharp', 
        'penalty', 'red_card', 'home', 'draw', 'away'
    ]
    unified_df = unified_df[[col for col in reordered_columns if col in unified_df.columns]]

    return unified_df, df_total

# Variável global para rastrear alertas enviados
sent_alerts = set()
# Variável global para rastrear zebras alertadas
sent_zebra_alerts = set()

def check_alerts(unified_data, game_id, match_url, df_total):
    global sent_alerts, sent_zebra_alerts
    alerts = []

    if unified_data.empty:
        logging.info(f"Nenhum dado unificado disponível para verificar alertas no jogo {game_id}.")
        return alerts

    if game_id in sent_alerts:
        logging.info(f"Alerta já enviado para game_id {game_id}. Ignorando.")
        return alerts

    league = df_total['league'].iloc[0] if 'league' in df_total.columns else 'N/A'
    home_team = df_total['home_team'].iloc[0] if 'home_team' in df_total.columns else 'N/A'
    away_team = df_total['away_team'].iloc[0] if 'away_team' in df_total.columns else 'N/A'

    initial_row = unified_data.iloc[0]
    home_initial = initial_row.get("home", None)
    away_initial = initial_row.get("away", None)

    line_initial = df_total['handicap'].iloc[0] if 'handicap' in df_total.columns else 'N/A'
    line_initial_odd = df_total['over'].iloc[0] if 'over' in df_total.columns else 'N/A'

    logging.info(f"Linha de gols inicial: {line_initial}, Odd inicial da linha de gols: {line_initial_odd}")

    if home_initial is None or away_initial is None:
        logging.info(f"Odds iniciais ausentes no jogo {game_id}. Não é possível determinar favorito.")
        return alerts

    favorite = "home" if home_initial < away_initial else "away" if away_initial < home_initial else "none"
    logging.info(f"Favorito identificado: {favorite}")

    zebra = "away" if favorite == "home" else "home" if favorite == "away" else None
    zebra_initial_odd = initial_row.get(zebra, None) if zebra else None

    alert_sent = False

    for _, row in unified_data.iterrows():
        if alert_sent:
            continue

        drop = row.get("drop", 0)
        penalty = row.get("penalty", "")
        red_card = row.get("red_card", "")
        score = row.get("score", "")

        # Condição 1: Alerta para Over Gol (mantida como está)
        if (
            drop >= 0.70
            and penalty == "0-0"
            and red_card == "0-0"
            and score in ["0-0", "1-0", "0-1", "1-1"]
        ):
            line_current = row.get('handicap', 'N/A')
            line_current_odd = row.get('over', 'N/A')

            if favorite == "home" and "home" in row and (home_initial - row["home"]) >= 0.05:
                alert_type = "Favorito Home com queda de odds"
            elif favorite == "away" and "away" in row and (away_initial - row["away"]) >= 0.05:
                alert_type = "Favorito Away com queda de odds"
            else:
                logging.info(f"Queda de odds detectada, mas não significativa para alerta no jogo {game_id}.")
                continue

            if alert_type:
                # Formatar a mensagem para o Telegram
                message = (
                    f"⚽ <b>Alerta Over gols</b>\n"
                    f"🏆 <b>Liga:</b> {league}\n"
                    f"🆚 <b>Times:</b> {home_team} - {away_team}\n"
                    f"⭐ <b>Favorito:</b> {favorite.capitalize()}\n"
                    f"⚽ <b>Linha de gols inicial:</b> {line_initial}\n"
                    f"📊 <b>Odd inicial da linha de gols:</b> {line_initial_odd}\n"
                    f"⚽ <b>Linha de gols atual:</b> {line_current}\n"
                    f"📉 <b>Odd atual da linha de gols:</b> {line_current_odd}\n"
                    f"🔢 <b>Placar:</b> {row.get('score', 'N/A')}\n"
                    f"⏱️ <b>Tempo:</b> {row.get('time', 'N/A')} minutos\n"
                    f"📉 <b>Drop:</b> {row.get('drop', 'N/A')}\n"
                    f"🔗 <b>Link:</b> <a href='{match_url}'>Detalhes</a>"
                )

                # Enviar mensagem formatada para o Telegram
                response = send_telegram_message(message)
                if response:
                    message_id = response.json().get("result", {}).get("message_id")
                    # Verificar o resultado do jogo e editar a mensagem
                    check_game_result_and_edit_message(game_id, match_url, message_id, row.get('score', '0-0'), line_current)

                alerts.append(message)
                sent_alerts.add(game_id)
                alert_sent = True

    # Identificar a zebra com base na maior odd inicial entre home e away
    zebra = None
    zebra_initial_odd = None
    if home_initial and away_initial:
        if home_initial > away_initial:
            zebra = "home"
            zebra_initial_odd = home_initial
        elif away_initial > home_initial:
            zebra = "away"
            zebra_initial_odd = away_initial

    if zebra:
        zebra_current_odd = row.get(zebra, None)
        zebra_identifier = f"{game_id}_{zebra}"  # Identificador único para a zebra

        if (
            zebra_current_odd is not None
            and zebra_initial_odd is not None
            and (zebra_initial_odd - zebra_current_odd) >= 0.90  # Queda de odd maior ou igual a 0.90
            and penalty == "0-0"  # Sem penalidades
            and red_card == "0-0"  # Sem cartões vermelhos
            and zebra_identifier not in sent_zebra_alerts  # Verifica se já foi alertada
        ):
            alert_type = f"Zebra {zebra.capitalize()} com queda de odds"

            # Formatar a mensagem para o Telegram
            message = (
                f"⚽ <b>Alerta de Zebra!</b>\n"
                f"🏆 <b>Liga:</b> {league}\n"
                f"🆚 <b>Times:</b> {home_team} - {away_team}\n"
                f"🦓 <b>Zebra:</b> {zebra.capitalize()}\n"
                f"📊 <b>Odd inicial:</b> {zebra_initial_odd}\n"
                f"📉 <b>Odd atual:</b> {zebra_current_odd}\n"
                f"🔢 <b>Placar:</b> {score}\n"
                f"⏱️ <b>Tempo:</b> {row.get('time', 'N/A')} minutos\n"
                f"🔗 <b>Link:</b> <a href='{match_url}'>Detalhes</a>"
            )

            # Enviar mensagem formatada para o Telegram
            response = send_telegram_message(message)
            if response:
                message_id = response.json().get("result", {}).get("message_id")
                logging.info(f"Mensagem de zebra enviada com sucesso para o Telegram. ID: {message_id}")

            # Adicionar a zebra ao conjunto de alertas enviados
            sent_zebra_alerts.add(zebra_identifier)
            alerts.append(message)
            alert_sent = True

    return alerts


def monitor_games():
    url = 'https://dropping-odds.com/'
    max_retries = 5  # Número máximo de tentativas de reconexão
    retry_count = 0

    try:
        while True:
            try:
                # Acessa a página principal
                driver.get(url)
                logging.info('Acessou o site de futebol')
                retry_count = 0  # Reseta o contador de tentativas após sucesso

                # Espera até que a tabela de partidas esteja presente
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div.tablediv.pointer table tbody tr'))
                )
                logging.info('Tabela de partidas encontrada')

                # Captura todos os IDs das partidas
                matches = driver.find_elements(By.CSS_SELECTOR, 'div.tablediv.pointer table tbody tr')
                game_ids = []
                for match in matches:
                    game_id = match.get_attribute('game_id')
                    if game_id:
                        game_ids.append(game_id)
                    else:
                        logging.warning("game_id não encontrado para uma partida. Ignorando.")

                logging.info(f"IDs capturados: {game_ids}")

                # Itera sobre cada ID capturado
                for game_id in game_ids:
                    try:
                        logging.info(f"Processando partida com game_id: {game_id}")

                        # URLs para cada aba
                        match_url_total = f'https://dropping-odds.com/event.php?id={game_id}&t=total'
                        match_url_1x2 = f'https://dropping-odds.com/event.php?id={game_id}&t=1x2'

                        # Processa a aba "total"
                        driver.get(match_url_total)
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.smenu a'))
                        )
                        data_total = extract_table_data(driver.page_source, game_id, match_url_total, table_type="total")
                        logging.info(f"Dados extraídos da aba 'total' para game_id {game_id}:\n{data_total}")

                        # Processa a aba "1x2"
                        driver.get(match_url_1x2)
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.smenu a'))
                        )
                        data_1x2 = extract_table_data(driver.page_source, game_id, match_url_1x2, table_type="1x2")
                        logging.info(f"Dados extraídos da aba '1x2' para game_id {game_id}:\n{data_1x2}")

                        # Unifica os dados e verifica alertas
                        unified_data, df_total = unify_tables(data_total, data_1x2)

                        # Adiciona o print da tabela unificada
                        if not unified_data.empty:
                            print(f"Tabela unificada para game_id {game_id}:\n{unified_data}")
                            alerts = check_alerts(unified_data, game_id, match_url_total, df_total)
                            for alert in alerts:
                                send_telegram_message(alert)
                        else:
                            logging.info(f"Tabela unificada vazia para game_id {game_id}.")
                    except Exception as e:
                        logging.error(f"Erro ao processar a partida com game_id {game_id}: {e}")
                    finally:
                        # Aguarda 2 segundos antes de continuar
                        time.sleep(2)

                # Aguarda 10 segundos antes de atualizar a página principal
                logging.info('Aguardando 10 segundos antes de atualizar a página principal...')
                time.sleep(10)

            except Exception as e:
                logging.error(f"Erro encontrado no loop principal: {e}")
                logging.info("Tentando reconectar...")
                time.sleep(10)
                retry_count += 1
                if retry_count >= max_retries:
                    logging.error("Número máximo de tentativas de reconexão atingido. Encerrando.")
                    break

    except Exception as e:
        logging.error(f"Erro crítico no monitoramento: {e}")
    finally:
        # Fecha o navegador e limpa os recursos
        driver.quit()
        logging.info('Recursos limpos e navegador fechado')


if __name__ == "__main__":
    try:
        monitor_games()
    except KeyboardInterrupt:
        logging.info("Execução interrompida pelo usuário.")
    except Exception as e:
        logging.error(f"Erro crítico no monitoramento: {e}")
    finally:
        driver.quit()  # Garante que o WebDriver seja fechado
        logging.info("Navegador fechado e recursos liberados.")
