import logging
from supabase_utils import alerta_ja_existente

def check_and_create_alert(unified_data, game_id, match_url):
    """
    Verifica as condições do jogo com base nas regras do usuário. Se forem atendidas e o 
    alerta não existir no Supabase, retorna um dicionário com todos os dados do alerta. 
    Caso contrário, retorna None.
    """
    if unified_data.empty:
        logging.info(f"Dados unificados vazios para o jogo {game_id}.")
        return None

    if alerta_ja_existente(game_id):
        return None

    # --- Início da Lógica de Negócio do Usuário ---

    # 1. Pega informações gerais da partida
    league = unified_data["league"].iloc[0] if "league" in unified_data.columns else "N/A"
    home_team = unified_data["home_team"].iloc[0] if "home_team" in unified_data.columns else "N/A"
    away_team = unified_data["away_team"].iloc[0] if "away_team" in unified_data.columns else "N/A"

    # 2. Identifica o favorito e sua odd inicial
    favorite_team_code = None
    favorite_initial_odd = 0.0
    favorite_name = "N/A"
    
    for _, row in unified_data.iterrows():
        try:
            home_odd = float(row.get("home", 0))
            away_odd = float(row.get("away", 0))
            if home_odd > 1.01 and away_odd > 1.01:
                if home_odd < away_odd:
                    favorite_team_code = "home"
                    favorite_initial_odd = home_odd
                    favorite_name = home_team
                else:
                    favorite_team_code = "away"
                    favorite_initial_odd = away_odd
                    favorite_name = away_team
                break
        except (ValueError, TypeError):
            continue

    if not favorite_team_code:
        logging.info(f"Favorito não pôde ser determinado para o jogo {game_id}.")
        return None

    # 3. Pega dados iniciais da linha de gols
    initial_row = unified_data.iloc[0]
    handicap_inicial = initial_row.get("handicap", "N/A")
    over_inicial = initial_row.get("over", "N/A")

    # 4. Itera em cada registro de tempo para encontrar uma oportunidade de alerta
    for _, current_row in unified_data.iterrows():
        
        # ... (As condições 1 a 4 permanecem as mesmas) ...
        try:
            drop_gols_float = float(current_row.get("drop", 0))
            if drop_gols_float < 0.60: continue
        except (ValueError, TypeError): continue

        if current_row.get("red_card", "0-0") != "0-0" or current_row.get("penalty", "0-0") != "0-0": continue

        try:
            score = current_row.get("score", "")
            gols_home, gols_away = map(int, str(score).split("-"))
            if (favorite_team_code == "home" and gols_home > gols_away) or \
               (favorite_team_code == "away" and gols_away > gols_home): continue
        except (ValueError, TypeError): continue

        try:
            current_odd = float(current_row.get(favorite_team_code, 0))
            if current_odd <= 1.01: continue
        except (ValueError, TypeError): continue
            
        # CONDIÇÃO 5: Tempo de jogo
        try:
            time_min_int = int(current_row.get("time", 99))
            if time_min_int >= 80: continue
        except (ValueError, TypeError): continue

        # Se todas as condições passaram, calcula a variação e monta o alerta
        if current_odd < favorite_initial_odd:
            variacao = round(((favorite_initial_odd - current_odd) / favorite_initial_odd) * 100, 2)
        elif current_odd > favorite_initial_odd:
            variacao = round(((current_odd - favorite_initial_odd) / current_odd) * 100, 2)
        else:
            continue
        
        # Monta o dicionário de alerta com o tipo de dado correto para cada coluna
        alerta_data = {
            "game_id": game_id,
            "liga": league,
            "times": f"{home_team} vs {away_team}",
            "favorito": favorite_name,
            "odd_inicial_favorito": favorite_initial_odd,
            "odd_atual_favorito": current_odd,
            "queda_odd_favorito": variacao,
            "linha_gols_inicial": handicap_inicial,
            "odd_linha_gols_inicial": over_inicial,
            "linha_gols_atual": current_row.get("handicap", "N/A"),
            "odd_linha_gols_atual": current_row.get("over", "N/A"),
            "drop_total": drop_gols_float,
            "placar": score,
            "tempo_jogo": time_min_int,  # <<< CORREÇÃO APLICADA AQUI
            "url": match_url,
        }

        # Formata a mensagem HTML para o Telegram (aqui sim usamos o texto formatado)
        info_drop_total = f"{drop_gols_float * 100:.0f}%"
        tipo_variacao = 'queda' if current_odd < favorite_initial_odd else 'subida'
        tempo_formatado = f"{time_min_int}'"

        alerta_data["mensagem_html"] = (
            f"🤖 <b>Alerta Automático: {home_team} x {away_team} ({league})</b>\n\n"
            f"📉 Drop significativo na linha de gols: <b>{info_drop_total}</b>\n"
            f"📊 Linha inicial: {handicap_inicial} (Odd: {over_inicial})\n"
            f"⚡ Linha atual: {current_row.get('handicap', 'N/A')} (Odd: {current_row.get('over', 'N/A')})\n\n"
            f"⭐ O favorito <b>{favorite_name}</b> está com <b>{tipo_variacao}</b> na odd de: "
            f"<b>{abs(variacao):.2f}%</b> ({favorite_initial_odd} → {current_odd}).\n\n"
            f"🔢 Placar: <b>{score}</b>\n"
            f"⏱️ Minuto: <b>{tempo_formatado}</b>\n\n"
            f'<a href="{match_url}">Ver detalhes da partida</a>\n\n'
            f"<i>⚠️ Lembre-se: analise o jogo antes de investir.</i>"
        )
        
        return alerta_data

    return None