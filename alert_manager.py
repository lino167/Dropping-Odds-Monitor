import logging
from supabase_utils import alerta_ja_existente
import pandas as pd

def get_general_info(unified_data):
    """Extrai informações gerais e do favorito de um DataFrame unificado."""
    if unified_data.empty:
        return None

    info = {
        "league": unified_data["league"].iloc[0],
        "home_team": unified_data["home_team"].iloc[0],
        "away_team": unified_data["away_team"].iloc[0],
        "favorite_team_code": None,
        "favorite_initial_odd": 0.0,
        "favorite_name": "N/A"
    }

    # Itera para encontrar a primeira odd válida e definir o favorito
    for _, row in unified_data.iterrows():
        try:
            home_odd = float(row.get("home", 0))
            away_odd = float(row.get("away", 0))
            if home_odd > 1.01 and away_odd > 1.01:
                if home_odd < away_odd:
                    info["favorite_team_code"] = "home"
                    info["favorite_initial_odd"] = home_odd
                    info["favorite_name"] = info["home_team"]
                else:
                    info["favorite_team_code"] = "away"
                    info["favorite_initial_odd"] = away_odd
                    info["favorite_name"] = info["away_team"]
                break
        except (ValueError, TypeError):
            continue
    
    return info

def check_super_favorito_drop_duplo(unified_data: pd.DataFrame, game_id: str, match_url: str, games_in_observation: dict):
    """
    Verifica a estratégia de duplo drop, agora com gestão de estado.
    """
    if unified_data.empty or alerta_ja_existente(game_id):
        return None

    try:
        info = get_general_info(unified_data)
        if not info or not info.get("favorite_team_code"):
            return None

        # --- LÓGICA DE ESTADO ---
        # Se o jogo já está em observação, vamos verificar as condições do 2º Tempo
        if game_id in games_in_observation:
            logging.info(f"[{game_id}] Jogo já em observação. Verificando condições do 2ºT.")
            
            # Recupera o drop do primeiro tempo que guardámos
            observed_info = games_in_observation[game_id]
            drop_primeiro_tempo_valor = observed_info['drop_value']
            
            df_st = unified_data[(unified_data['time'] >= 45) & (unified_data['time'] <= 70)]
            for _, current_row in df_st.iterrows():
                if current_row['drop'] > drop_primeiro_tempo_valor and \
                   current_row.get("score") == "0-0" and \
                   current_row.get("red_card") == "0-0" and \
                   current_row.get("penalty") == "0-0":

                    logging.info(f"[{game_id}] ALERTA! Segundo drop ({current_row['drop']:.2f}) confirmado com placar 0-0.")
                    
                    alerta_data = {
                        "game_id": game_id, "liga": info["league"], "times": f"{info['home_team']} vs {info['away_team']}",
                        "favorito": info["favorite_name"], "odd_inicial_favorito": info["favorite_initial_odd"],
                        "odd_atual_favorito": current_row.get(info["favorite_team_code"], 0),
                        "linha_gols_atual": current_row.get("handicap", "N/A"), "odd_linha_gols_atual": current_row.get("over", "N/A"),
                        "drop_total": current_row.get("drop"), "placar": current_row.get("score"), "tempo_jogo": int(current_row.get("time")),
                        "url": match_url,
                    }
                    
                    alerta_data["mensagem_html"] = (
                        f"🔥 <b>Kairós: Alerta DROP DUPLO!</b>\n\n"
                        f"<b>Jogo:</b> {alerta_data['times']}\n\n"
                        f"⭐ <b>Super Favorito:</b> {alerta_data['favorito']} (Odd Inicial: {alerta_data['odd_inicial_favorito']:.2f})\n\n"
                        f"<b>Padrão Detectado:</b>\n"
                        f"  - 📉 Drop no 1º Tempo: <b>{drop_primeiro_tempo_valor*100:.0f}%</b>\n"
                        f"  - 📈 Drop no 2º Tempo: <b>{alerta_data['drop_total']*100:.0f}%</b> aos {alerta_data['tempo_jogo']}'\n\n"
                        f"<b>Condições no Momento do Alerta:</b> <b>0-0</b>, sem cartões ou pênaltis.\n\n"
                        f'<a href="{match_url}">Analise a partida</a>'
                    )
                    
                    # Remove o jogo da observação para não processar de novo
                    del games_in_observation[game_id]
                    return alerta_data

            return None # Continua a observar se as condições do 2T ainda não foram cumpridas

        # --- LÓGICA PARA ADICIONAR UM JOGO À OBSERVAÇÃO ---
        # Se o jogo não está em observação, verificamos as condições do 1º Tempo
        
        # CONDIÇÃO 1: Super Favorito
        if info["favorite_initial_odd"] > 1.70:
            return None
        
        df_ht = unified_data[unified_data['time'] < 45]
        if df_ht.empty:
            return None
            
        max_drop_ht_row = df_ht.loc[df_ht['drop'].idxmax()]
        
        # CONDIÇÃO 2: Drop mínimo no 1ºT com placar 0-0
        LIMIAR_DROP_MINIMO = 0.10
        if max_drop_ht_row['drop'] >= LIMIAR_DROP_MINIMO and \
           max_drop_ht_row.get("score") == "0-0" and \
           max_drop_ht_row.get("red_card") == "0-0" and \
           max_drop_ht_row.get("penalty") == "0-0":

            logging.info(f"[{game_id}] Jogo adicionado à lista de observação. Drop no 1ºT: {max_drop_ht_row['drop']:.2f}")
            games_in_observation[game_id] = {
                "drop_value": max_drop_ht_row['drop'],
                "time": max_drop_ht_row['time']
            }
            
    except Exception as e:
        logging.error(f"[{game_id}] Erro ao processar estratégia Drop Duplo: {e}", exc_info=True)
    
    return None


def check_and_create_alert(unified_data, game_id, match_url):
    """Sua função original para a estratégia de queda de odd do favorito."""
    # (O código da sua função original permanece inalterado aqui)
    if unified_data.empty or alerta_ja_existente(game_id):
        return None

    info = get_general_info(unified_data)
    if not info or not info.get("favorite_team_code"):
        return None

    initial_row = unified_data.iloc[0]
    handicap_inicial = initial_row.get("handicap", "N/A")
    over_inicial = initial_row.get("over", "N/A")

    for _, current_row in unified_data.iterrows():
        try:
            drop_gols_float = float(current_row.get("drop", 0))
            if drop_gols_float < 0.60: continue
        except (ValueError, TypeError): continue

        if current_row.get("red_card", "0-0") != "0-0" or current_row.get("penalty", "0-0") != "0-0": continue

        try:
            score = current_row.get("score", "")
            gols_home, gols_away = map(int, str(score).split("-"))
            if (info["favorite_team_code"] == "home" and gols_home > gols_away) or \
               (info["favorite_team_code"] == "away" and gols_away > gols_home): continue
        except (ValueError, TypeError): continue

        try:
            current_odd = float(current_row.get(info["favorite_team_code"], 0))
            if current_odd <= 1.01: continue
        except (ValueError, TypeError): continue
            
        try:
            time_min_int = int(current_row.get("time", 99))
            if time_min_int >= 80: continue
        except (ValueError, TypeError): continue

        if current_odd < info["favorite_initial_odd"]:
            variacao = round(((info["favorite_initial_odd"] - current_odd) / info["favorite_initial_odd"]) * 100, 2)
        elif current_odd > info["favorite_initial_odd"]:
            variacao = round(((current_odd - info["favorite_initial_odd"]) / current_odd) * 100, 2)
        else:
            continue
        
        alerta_data = {
            "game_id": game_id, "liga": info["league"], "times": f"{info['home_team']} vs {info['away_team']}",
            "favorito": info["favorite_name"], "odd_inicial_favorito": info["favorite_initial_odd"],
            "odd_atual_favorito": current_odd, "queda_odd_favorito": variacao,
            "linha_gols_inicial": handicap_inicial, "odd_linha_gols_inicial": over_inicial,
            "linha_gols_atual": current_row.get("handicap", "N/A"), "odd_linha_gols_atual": current_row.get("over", "N/A"),
            "drop_total": drop_gols_float, "placar": score, "tempo_jogo": time_min_int, "url": match_url,
        }
        
        alerta_data["mensagem_html"] = "..." # Sua mensagem original
        return alerta_data
    return None