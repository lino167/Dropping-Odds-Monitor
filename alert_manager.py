import logging
import os
from openpyxl import load_workbook
from excel_utils import registrar_alerta_excel  # Certifique-se de importar corretamente

# Variáveis globais para rastrear alertas
sent_alerts = set()

def check_alerts(unified_data, game_id, match_url, df_total):
    """
    Verifica condições para alertas e retorna mensagens formatadas.
    Só envia se o game_id não estiver na memória e nem registrado na planilha.
    """
    global sent_alerts
    alerts = []

    if unified_data.empty:
        logging.info(f"Nenhum dado unificado disponível para verificar alertas no jogo {game_id}.")
        return alerts

    # Verifica se o alerta já foi enviado (na memória)
    if game_id in sent_alerts:
        logging.info(f"Alerta já enviado para game_id {game_id}. Ignorando.")
        return alerts

    # Verifica se o alerta já está registrado na planilha
    nome_arquivo = "alertas.xlsx"
    if os.path.exists(nome_arquivo):
        workbook = load_workbook(nome_arquivo)
        sheet = workbook.active
        game_ids_registrados = [str(row[0].value) for row in sheet.iter_rows(min_row=2, max_col=1)]
        if str(game_id) in game_ids_registrados:
            logging.info(f"Alerta para game_id {game_id} já registrado na planilha. Ignorando.")
            return alerts

    league = df_total['league'].iloc[0] if 'league' in df_total.columns else 'N/A'
    home_team = df_total['home_team'].iloc[0] if 'home_team' in df_total.columns else 'N/A'
    away_team = df_total['away_team'].iloc[0] if 'away_team' in df_total.columns else 'N/A'
    initial_row = unified_data.iloc[0]
    home_initial = initial_row.get("home", None)
    away_initial = initial_row.get("away", None)
    line_initial = df_total['handicap'].iloc[0] if 'handicap' in df_total.columns else 'N/A'
    line_initial_odd = df_total['over'].iloc[0] if 'over' in df_total.columns else 'N/A'

    if home_initial is None or away_initial is None:
        logging.info(f"Odds iniciais ausentes no jogo {game_id}. Não é possível determinar favorito.")
        return alerts

    favorite = "home" if float(home_initial) < float(away_initial) else "away"

    for index, row in unified_data.iterrows():
        # Ignora pré-live
        if str(row.get("time", "")).strip() == "":
            continue
        # Ignora mercados suspensos
        if (
            row.get("over", "-") == "-" and
            row.get("under", "-") == "-" and
            row.get("home", "-") == "-" and
            row.get("draw", "-") == "-" and
            row.get("away", "-") == "-"
        ):
            continue

        drop = row.get("drop", 0)
        penalty = row.get("penalty", "")
        red_card = row.get("red_card", "")
        score = row.get("score", "")
        time_min = row.get("time", 0)

        # Condição de alerta
        if (
            penalty == "0-0" and red_card == "0-0" and drop >= 0.50
        ):
            line_current = row.get('handicap', 'N/A')
            line_current_odd = row.get('over', 'N/A')
            drop_percentage = round(((float(home_initial) - float(row[favorite])) / float(home_initial)) * 100, 2) if home_initial else 0

            alerta = [
                game_id, league, f"{home_team} - {away_team}", favorite.capitalize(),
                home_initial if favorite == "home" else away_initial, row[favorite], drop_percentage,
                line_initial, line_initial_odd, line_current, line_current_odd, row.get('drop', 'N/A'),
                score, time_min, match_url
            ]

            # Registrar o alerta na planilha
            if registrar_alerta_excel(game_id, alerta):
                sent_alerts.add(game_id)
                message = (
                    f"⚽ <b>Alerta de Queda de Odd</b>\n"
                    f"🏆 <b>Liga:</b> {league}\n"
                    f"🆚 <b>Times:</b> {home_team} - {away_team}\n"
                    f"⭐ <b>Favorito (F):</b> {favorite.capitalize()}\n"
                    f"📊 <b>Odd inicial do favorito:</b> {home_initial if favorite == 'home' else away_initial}\n"
                    f"📉 <b>Odd atual do favorito:</b> {row[favorite]}\n"
                    f"📉 <b>Queda:</b> {drop_percentage}%\n"
                    f"⚽ <b>Linha de gols inicial:</b> {line_initial}\n"
                    f"📊 <b>Odd inicial da linha de gols:</b> {line_initial_odd}\n"
                    f"⚽ <b>Linha de gols atual:</b> {line_current}\n"
                    f"📉 <b>Odd atual da linha de gols:</b> {line_current_odd}\n"
                    f"📉 <b>Queda:</b> {row.get('drop', 'N/A')}\n"
                    f"🔢 <b>Placar:</b> {score}\n"
                    f"⏱️ <b>Tempo:</b> {time_min} minutos\n"
                    f"🔗 <b>Link:</b> <a href='{match_url}'>Detalhes</a>"
                )
                alerts.append(message)
    return alerts