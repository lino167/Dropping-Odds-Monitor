import logging
from typing import List, Dict, Any

# Variáveis globais para rastrear alertas
sent_alerts = set()
sent_zebra_alerts = set()

class AlertManager:
    def __init__(self):
        self.sent_alerts = set()
        self.sent_zebra_alerts = set()

    def check_alerts(self, unified_data, game_id, match_url, df_total) -> List[str]:
        """Verifica condições para alertas e retorna mensagens formatadas."""
        alerts = []
        
        if unified_data.empty:
            logging.info(f"Nenhum dado unificado para verificar alertas no jogo {game_id}.")
            return alerts

        if game_id in self.sent_alerts:
            logging.info(f"Alerta já enviado para game_id {game_id}. Ignorando.")
            return alerts

        # Extrai informações básicas do jogo
        league = df_total['league'].iloc[0] if 'league' in df_total.columns else 'N/A'
        home_team = df_total['home_team'].iloc[0] if 'home_team' in df_total.columns else 'N/A'
        away_team = df_total['away_team'].iloc[0] if 'away_team' in df_total.columns else 'N/A'

        initial_row = unified_data.iloc[0]
        home_initial = initial_row.get("home", None)
        away_initial = initial_row.get("away", None)

        line_initial = df_total['handicap'].iloc[0] if 'handicap' in df_total.columns else 'N/A'
        line_initial_odd = df_total['over'].iloc[0] if 'over' in df_total.columns else 'N/A'

        if home_initial is None or away_initial is None:
            logging.info(f"Odds iniciais ausentes no jogo {game_id}.")
            return alerts

        favorite = "home" if float(home_initial) < float(away_initial) else "away"
        logging.info(f"Favorito identificado: {favorite}")

        for index, row in unified_data.iterrows():
            if self._should_skip_row(row):
                continue

            if self._check_alert_conditions(row, favorite, home_initial, away_initial):
                alert_data = self._prepare_alert_data(
                    game_id, league, home_team, away_team, favorite, 
                    home_initial, away_initial, row, line_initial, 
                    line_initial_odd, match_url
                )
                
                alerts.append(self._format_telegram_message(alert_data))
                self.sent_alerts.add(game_id)

        return alerts

    def _should_skip_row(self, row) -> bool:
        """Determina se uma linha deve ser ignorada para alertas."""
        # Verifica se está em pré-live
        if str(row.get("time", "")).strip() == "":
            logging.info("Jogo em pré-live. Ignorando.")
            return True
            
        # Verifica se o mercado está suspenso
        if (
            row.get("over", "-") == "-" and
            row.get("under", "-") == "-" and
            row.get("home", "-") == "-" and
            row.get("draw", "-") == "-" and
            row.get("away", "-") == "-"
        ):
            logging.info("Mercado suspenso. Ignorando.")
            return True
            
        return False

    def _check_alert_conditions(self, row, favorite, home_initial, away_initial) -> bool:
        """Verifica se as condições para um alerta são atendidas."""
        drop = row.get("drop", 0)
        penalty = row.get("penalty", "")
        red_card = row.get("red_card", "")
        score = row.get("score", "")
        time = row.get("time", 0)

        return (
            penalty == "0-0" and 
            red_card == "0-0" and 
            drop >= 0.70 and 
            score == "0-0" and 
            time <= 80 and
            ((favorite == "home" and (home_initial - row[favorite]) / home_initial >= 0.20) or
             (favorite == "away" and (away_initial - row[favorite]) / away_initial >= 0.20))
        )

    def _prepare_alert_data(self, game_id, league, home_team, away_team, favorite, 
                          home_initial, away_initial, row, line_initial, 
                          line_initial_odd, match_url) -> Dict[str, Any]:
        """Prepara os dados para o alerta."""
        line_current = row.get('handicap', 'N/A')
        line_current_odd = row.get('over', 'N/A')
        favorite_initial = home_initial if favorite == "home" else away_initial
        favorite_current = row[favorite]
        drop_percentage = round(((favorite_initial - favorite_current) / favorite_initial) * 100, 2)

        return {
            'game_id': game_id,
            'league': league,
            'teams': f"{home_team} - {away_team}",
            'favorite': favorite.capitalize(),
            'favorite_initial': favorite_initial,
            'favorite_current': favorite_current,
            'drop_percentage': drop_percentage,
            'line_initial': line_initial,
            'line_initial_odd': line_initial_odd,
            'line_current': line_current,
            'line_current_odd': line_current_odd,
            'drop': row.get('drop', 'N/A'),
            'score': row.get('score', 'N/A'),
            'time': row.get('time', 'N/A'),
            'url': match_url
        }

    def _format_telegram_message(self, alert_data) -> str:
        """Formata a mensagem para o Telegram."""
        return (
            f"⚽ <b>Alerta de Queda de Odd</b>\n"
            f"🏆 <b>Liga:</b> {alert_data['league']}\n"
            f"🆚 <b>Times:</b> {alert_data['teams']}\n"
            f"⭐ <b>Favorito (F):</b> {alert_data['favorite']}\n"
            f"📊 <b>Odd inicial do favorito:</b> {alert_data['favorite_initial']}\n"
            f"📉 <b>Odd atual do favorito:</b> {alert_data['favorite_current']}\n"
            f"📉 <b>Queda:</b> {alert_data['drop_percentage']}%\n"
            f"⚽ <b>Linha de gols inicial:</b> {alert_data['line_initial']}\n"
            f"📊 <b>Odd inicial da linha de gols:</b> {alert_data['line_initial_odd']}\n"
            f"⚽ <b>Linha de gols atual:</b> {alert_data['line_current']}\n"
            f"📉 <b>Odd atual da linha de gols:</b> {alert_data['line_current_odd']}\n"
            f"📉 <b>Queda:</b> {alert_data['drop']}\n"
            f"🔢 <b>Placar:</b> {alert_data['score']}\n"
            f"⏱️ <b>Tempo:</b> {alert_data['time']} minutos\n"
            f"🔗 <b>Link:</b> <a href='{alert_data['url']}'>Detalhes</a>"
        )