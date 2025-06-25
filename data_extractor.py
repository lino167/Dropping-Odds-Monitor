from bs4 import BeautifulSoup
import pandas as pd
import logging
from typing import Optional

def extract_table_data(page_source: str, game_id: str, match_url: str, table_type: str = "total") -> list:
    """
    Extrai os dados de uma tabela de odds (Total ou 1x2) do código-fonte de uma página.
    """
    try:
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Extrai informações gerais do cabeçalho da página
        matchinfo = soup.select_one("body > div.matchinfo")
        league = matchinfo.find('h3').text.strip() if matchinfo and matchinfo.find('h3') else 'N/A'
        teams_text = matchinfo.find('h1').text.strip() if matchinfo and matchinfo.find('h1') else 'N/A'
        
        if " - " in teams_text:
            home_team, away_team = [team.strip() for team in teams_text.split(" - ", 1)]    
        else:
            home_team, away_team = teams_text, "N/A"

        data = []
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                
                # Processamento para a tabela 'total' (Over/Under)
                if table_type == "total" and len(cells) > 9:
                    try:
                        row_data = {
                            'league': league, 'home_team': home_team, 'away_team': away_team,
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
                    except (ValueError, IndexError) as e:
                        logging.warning(f"[{game_id}] Erro ao processar linha da tabela 'total': {e}")
                
                # Processamento para a tabela '1x2' (Home/Draw/Away)
                elif table_type == "1x2" and len(cells) > 4:
                    try:
                        row_data = {
                            'time': int(cells[1].text.strip()) if cells[1].text.strip().isdigit() else 0,
                            'home': float(cells[3].text.strip()) if cells[3].text.strip().replace('.', '', 1).isdigit() else 0.0,
                            'draw': float(cells[4].text.strip()) if cells[4].text.strip().replace('.', '', 1).isdigit() else 0.0,
                            'away': float(cells[5].text.strip()) if cells[5].text.strip().replace('.', '', 1).isdigit() else 0.0,
                        }
                        data.append(row_data)
                    except (ValueError, IndexError) as e:
                        logging.warning(f"[{game_id}] Erro ao processar linha da tabela '1x2': {e}")
    except Exception as e:
        logging.error(f"[{game_id}] Falha crítica ao extrair dados da página: {e}", exc_info=True)

    return data

def unify_tables(data_total: list, data_1x2: list) -> tuple:
    """
    Unifica os dados extraídos das tabelas 'total' e '1x2' em um único DataFrame do Pandas.
    """
    try:
        if not data_total or not data_1x2:
            logging.warning("Dados de uma das tabelas estão faltando, não é possível unificar.")
            return pd.DataFrame(), pd.DataFrame()

        df_total = pd.DataFrame(data_total)
        df_1x2 = pd.DataFrame(data_1x2)

        # Une as duas tabelas com base na coluna 'time'
        unified_df = pd.merge(df_total, df_1x2, on='time', how='outer')
        
        # Ordena os dados pelo tempo de jogo, do mais recente para o mais antigo
        unified_df = unified_df.sort_values(by='time', ascending=False).reset_index(drop=True)

        return unified_df, df_total

    except Exception as e:
        logging.error(f"Erro crítico ao unificar tabelas: {e}", exc_info=True)
        return pd.DataFrame(), pd.DataFrame()




def extract_final_score(page_source: str) -> Optional[str]:
    """
    Extrai o placar final da última linha da tabela de um jogo concluído.
    """
    try:
        soup = BeautifulSoup(page_source, 'html.parser')
        # Procura pela última linha da tabela principal de dados
        last_row = soup.select_one('div.tablediv.pointer table tbody tr:last-child')
        
        if last_row:
            cells = last_row.find_all('td')
            # Verifica se a linha tem o formato esperado
            if len(cells) > 2:
                time_cell = cells[1].text.strip().upper()
                score_cell = cells[2].text.strip()
                
                # A condição de sucesso é que o tempo seja 'FT' (Full Time) e o placar seja válido
                if time_cell == 'FT' and '-' in score_cell:
                    return score_cell
                    
    except Exception as e:
        logging.error(f"Erro ao extrair placar final: {e}")
        
    return None
