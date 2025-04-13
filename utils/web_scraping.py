import logging
from bs4 import BeautifulSoup
from utils.file_operations import save_to_json, load_from_json, delete_json, add_game_to_excel
from utils.telegram import send_telegram_message

alerted_games = set()

def detect_alerts(data):
    alerts = []
    for entry in data:
        # Primeiro conjunto de condições (1° Tempo)
        if (entry.get("score") in "0-0" and
            5 <= entry.get("time", 0) <= 30 and  
            entry.get("drop", 0) >= 0.70 and
            entry.get("penalty") == "0-0" and
            entry.get("red_card") == "0-0"):
            alerts.append(entry)
            print(f"Alerta detectado (Conjunto 1 - Alerta de gols no 1° Tempo): {entry}")

        # Segundo conjunto de condições (Jogo todo)
        elif (entry.get("score") in "0-0" and
              31 <= entry.get("time", 0) <= 75 and  
              entry.get("drop", 0) >= 0.70 and
              entry.get("penalty") == "0-0" and
              entry.get("red_card") == "0-0"):
            alerts.append(entry)
            print(f"Alerta detectado (Conjunto 2 - Alerta de gols no jogo todo): {entry}")

        # Terceiro conjunto de condições (Nova condição)
        elif (entry.get("score") in ["0-0", "0-1", "1-0", "1-1"] and
              10 <= entry.get("time", 0) <= 80 and  
              entry.get("drop", 0) >= 1 and
              entry.get("penalty") == "0-0" and
              entry.get("red_card") == "0-0"):
            alerts.append(entry)
            print(f"Alerta detectado (Conjunto 3 - Nova condição): {entry}")

    return alerts

def extract_table_data(page_source, game_id, match_url):
    global alerted_games
    soup = BeautifulSoup(page_source, 'html.parser')           
    tables = soup.find_all('table')

    matchinfo = soup.find('div', class_='matchinfo')
    league = matchinfo.find('h3').text.strip() if matchinfo and matchinfo.find('h3') else 'N/A'
    teams = matchinfo.find('h1').text.strip() if matchinfo and matchinfo.find('h1') else 'N/A'
    score = matchinfo.find('h2').text.strip() if matchinfo and matchinfo.find('h2') else 'N/A'

    data = []
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) > 9:
                try:
                    over = cells[3].text.strip()
                    under = cells[5].text.strip()

                    row_data = {
                        'league': league,
                        'teams': teams,
                        'match_score': score,
                        'time': int(cells[1].text.strip()) if len(cells) > 1 and cells[1].text.strip().isdigit() else 0,
                        'score': cells[2].text.strip() if len(cells) > 2 else 'N/A',
                        'over': float(over) if over.replace('-', '').replace('.', '').isdigit() else 0.0,
                        'handicap': cells[4].text.strip() if len(cells) > 4 else 'N/A',
                        'under': float(under) if under.replace('-', '').replace('.', '').isdigit() else 0.0,
                        'drop': float(cells[6].text.strip()) if len(cells) > 6 and cells[6].text.strip().replace('-', '').replace('.', '').isdigit() else 0.0,
                        'sharp': float(cells[7].text.strip()) if len(cells) > 7 and cells[7].text.strip().replace('-', '').replace('.', '').isdigit() else 0.0,
                        'penalty': cells[8].text.strip() if len(cells) > 8 else 'N/A',
                        'red_card': cells[9].text.strip() if len(cells) > 9 else 'N/A'
                    }
                    data.append(row_data)
                except ValueError as e:
                    logging.warning(f"Erro ao converter valores: {e}. Linha ignorada: {row}")
            else:
                logging.warning(f"Linha com células insuficientes encontrada e processada como 'N/A': {row}")

    alerts = detect_alerts(data)

    for alert in alerts:
        if game_id not in alerted_games:
            # Mensagem específica para cada conjunto
            if 5 <= alert.get("time", 0) <= 30:
                alert_type = "Alerta de gols no 1° Tempo"
            elif 31 <= alert.get("time", 0) <= 75:
                alert_type = "Alerta de gols no jogo todo"
            elif 10 <= alert.get("time", 0) <= 50:
                alert_type = "Nova condição"
            else:
                alert_type = "Alerta desconhecido"

            message = (
                f"{alert_type}!\n"
                f"Liga: {alert['league']}\n"
                f"Times: {alert['teams']}\n"
                f"Placar: {alert['score']}\n"
                f"Tempo: {alert['time']}\n"
                f"Odd: {alert['over']}\n"
                f"Linha de gol over: {alert['handicap']}\n"
                f"Drop: {alert['drop']}\n"
                f"Link: {match_url}"
            )

            send_telegram_message(message)
            logging.info(f"Mensagem enviada: {message}")

            alerted_games.add(game_id)

            alert['game_id'] = game_id
            alert['alert_type'] = alert_type 
            add_game_to_excel(alert, match_url)

            break

    temp_filename = f"temp_data_{game_id}.json"
    delete_json(temp_filename)