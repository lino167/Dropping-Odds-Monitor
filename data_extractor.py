from bs4 import BeautifulSoup
import pandas as pd
import logging

def extract_table_data(page_source, game_id, match_url, table_type="total"):
    soup = BeautifulSoup(page_source, 'html.parser')
    tables = soup.find_all('table')
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

def unify_tables(data_total, data_1x2):
    """
    Unifica os dados de 'total' e '1x2' em um único DataFrame.
    Agora com tratamento de erros para sempre retornar uma tupla.
    """
    try:
        if not data_total or not data_1x2:
            logging.warning("Dados de uma das tabelas estão faltando, não é possível unificar.")
            return pd.DataFrame(), pd.DataFrame()

        df_total = pd.DataFrame(data_total)
        df_1x2 = pd.DataFrame(data_1x2)

        # Remove colunas duplicadas antes do merge para evitar conflitos
        cols_to_drop_total = [col for col in ['league', 'home_team', 'away_team'] if col in df_total.columns]
        df_total = df_total.drop(columns=cols_to_drop_total)

        cols_to_drop_1x2 = [col for col in ['league', 'home_team', 'away_team', 'score'] if col in df_1x2.columns]
        df_1x2 = df_1x2.drop(columns=cols_to_drop_1x2)
        
        # Garante que a coluna 'time' exista para o merge
        if 'time' not in df_total.columns or 'time' not in df_1x2.columns:
            logging.error("A coluna 'time' é essencial para o merge e não foi encontrada em ambas as tabelas.")
            return pd.DataFrame(), pd.DataFrame()

        unified_df = pd.merge(df_total, df_1x2, on='time', how='outer')

        unified_df['league'] = data_total[0]['league']
        unified_df['home_team'] = data_total[0]['home_team']
        unified_df['away_team'] = data_total[0]['away_team']

        # Limpeza e ordenação
        odds_cols = ['over', 'under', 'home', 'draw', 'away']
        def odds_invalid(row):
            for col in odds_cols:
                val = row.get(col, None)
                # Verifica se o valor pode ser convertido para número e é uma odd válida
                if val is not None and pd.to_numeric(val, errors='coerce') > 1.01:
                    return False
            return True

        unified_df = unified_df[~unified_df.apply(odds_invalid, axis=1)].reset_index(drop=True)
        unified_df = unified_df.sort_values(by='time', ascending=False).reset_index(drop=True)

        return unified_df, df_total

    except Exception as e:
        logging.error(f"Erro crítico ao unificar tabelas: {e}", exc_info=True)
        return pd.DataFrame(), pd.DataFrame()