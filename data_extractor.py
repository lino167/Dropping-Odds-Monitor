from bs4 import BeautifulSoup
import pandas as pd
import logging

def extract_table_data(page_source, game_id, match_url, table_type="total"):
    """Extrai dados das tabelas da página."""
    try:
        soup = BeautifulSoup(page_source, 'html.parser')
        tables = soup.find_all('table')
    except Exception as e:
        logging.error(f"Erro ao processar o HTML da página: {e}")
        return []

    # Extrai informações básicas do jogo
    matchinfo = soup.select_one("body > div.matchinfo")
    league = matchinfo.find('h3').text.strip() if matchinfo and matchinfo.find('h3') else 'N/A'
    teams = matchinfo.find('h1').text.strip() if matchinfo and matchinfo.find('h1') else 'N/A'
    
    if "-" in teams:
        home_team, away_team = [team.strip() for team in teams.split("-")]
    else:
        home_team, away_team = teams, "N/A"

    data = []
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            
            if table_type == "total" and len(cells) > 9:
                try:
                    data.append(process_total_row(cells, league, home_team, away_team))
                except Exception as e:
                    logging.warning(f"Erro ao processar linha da tabela 'total': {e}")
            elif table_type == "1x2" and len(cells) > 4:
                try:
                    data.append(process_1x2_row(cells, league, home_team, away_team))
                except Exception as e:
                    logging.warning(f"Erro ao processar linha da tabela '1x2': {e}")

    return data

def process_total_row(cells, league, home_team, away_team):
    """Processa uma linha da tabela 'total'."""
    return {
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

def process_1x2_row(cells, league, home_team, away_team):
    """Processa uma linha da tabela '1x2'."""
    return {
        'league': league,
        'home_team': home_team,
        'away_team': away_team,
        'time': int(cells[1].text.strip()) if cells[1].text.strip().isdigit() else 0,
        'home': float(cells[3].text.strip()) if cells[3].text.strip().replace('.', '', 1).isdigit() else 0.0,
        'draw': float(cells[4].text.strip()) if cells[4].text.strip().replace('.', '', 1).isdigit() else 0.0,
        'away': float(cells[5].text.strip()) if cells[5].text.strip().replace('.', '', 1).isdigit() else 0.0,
    }

def unify_tables(data_total, data_1x2):
    """Unifica tabelas 'total' e '1x2' em um DataFrame."""
    if not data_total:
        logging.warning("Tabela 'total' está vazia.")
    else:
        logging.info(f"Tabela 'total' contém {len(data_total)} linhas.")

    if not data_1x2:
        logging.warning("Tabela '1x2' está vazia.")
    else:
        logging.info(f"Tabela '1x2' contém {len(data_1x2)} linhas.")

    df_total = pd.DataFrame(data_total)
    df_1x2 = pd.DataFrame(data_1x2)

    # Verifica colunas essenciais
    for col in ['league', 'home_team', 'away_team']:
        if col not in df_total.columns:
            df_total[col] = 'N/A'
        if col not in df_1x2.columns:
            df_1x2[col] = 'N/A'

    # Unifica as tabelas
    unified_df = pd.merge(df_total, df_1x2, on='time', how='outer', suffixes=('_total', '_1x2'))

    # Reorganiza as colunas
    reordered_columns = [
        'league', 'home_team', 'away_team', 'time', 'score', 'over', 'handicap', 'under', 'drop', 'sharp', 
        'penalty', 'red_card', 'home', 'draw', 'away'
    ]
    unified_df = unified_df[[col for col in reordered_columns if col in unified_df.columns]]

    return unified_df, df_total