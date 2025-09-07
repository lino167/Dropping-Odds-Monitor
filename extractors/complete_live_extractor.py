#!/usr/bin/env python3
"""
Extrator Completo de Dados Live - Dropping Odds
Extrai dados da página live e de todas as tabelas de cada jogo
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import re
from typing import Dict, List, Optional
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CompleteLiveExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.base_url = "https://dropping-odds.com"
        self.live_url = f"{self.base_url}/index.php?view=live"
        
        # Tipos de tabelas disponíveis
        self.table_types = ['1x2', 'total', 'handicap', 'total_ht', '1x2_ht']
        
    def extract_live_games(self) -> List[Dict]:
        """Extrai lista de jogos da página live"""
        try:
            response = self.session.get(self.live_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            games = []
            
            # Encontrar todas as linhas de jogos
            game_rows = soup.find_all('tr', class_='a_link')
            
            for row in game_rows:
                game_id = row.get('game_id')
                if not game_id:
                    continue
                    
                cells = row.find_all('td')
                if len(cells) >= 6:
                    # Extrair informações básicas do jogo
                    country_img = cells[0].find('img')
                    country = country_img.get('src', '').split('/')[-1].replace('.svg', '') if country_img else 'unknown'
                    
                    league = cells[1].get_text(strip=True) if len(cells) > 1 else ''
                    home_team = cells[2].get_text(strip=True) if len(cells) > 2 else ''
                    score = cells[3].get_text(strip=True) if len(cells) > 3 else ''
                    away_team = cells[4].get_text(strip=True) if len(cells) > 4 else ''
                    time_info = cells[5].get_text(strip=True) if len(cells) > 5 else ''
                    
                    game_info = {
                        'game_id': game_id,
                        'country': country,
                        'league': league,
                        'home_team': home_team,
                        'away_team': away_team,
                        'score': score,
                        'time': time_info,
                        'extracted_at': datetime.now().isoformat()
                    }
                    
                    games.append(game_info)
                    
            logger.info(f"Extraídos {len(games)} jogos da página live")
            return games
            
        except Exception as e:
            logger.error(f"Erro ao extrair jogos live: {e}")
            return []
    
    def extract_table_data(self, game_id: str, table_type: str) -> Dict:
        """Extrai dados de uma tabela específica de um jogo"""
        url = f"{self.base_url}/event.php?id={game_id}&t={table_type}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extrair informações do cabeçalho do jogo
            game_header = self._extract_game_header(soup)
            
            # Extrair dados da tabela baseado no tipo
            table_data = self._extract_table_by_type(soup, table_type)
            
            return {
                'game_id': game_id,
                'table_type': table_type,
                'url': url,
                'game_info': game_header,
                'table_data': table_data,
                'extracted_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao extrair tabela {table_type} do jogo {game_id}: {e}")
            return {
                'game_id': game_id,
                'table_type': table_type,
                'url': url,
                'error': str(e),
                'extracted_at': datetime.now().isoformat()
            }
    
    def _extract_game_header(self, soup: BeautifulSoup) -> Dict:
        """Extrai informações do cabeçalho do jogo"""
        try:
            # Procurar pelo título do jogo
            title_elements = soup.find_all(['h1', 'h2', 'h3'])
            game_title = ''
            for elem in title_elements:
                text = elem.get_text(strip=True)
                if ' - ' in text and any(word in text.lower() for word in ['serie', 'league', 'division', 'cup']):
                    game_title = text
                    break
            
            # Extrair score se disponível
            score_elem = soup.find('td', string=re.compile(r'\d+:\d+'))
            score = score_elem.get_text(strip=True) if score_elem else ''
            
            return {
                'title': game_title,
                'score': score
            }
        except Exception as e:
            logger.error(f"Erro ao extrair cabeçalho: {e}")
            return {}
    
    def _extract_table_by_type(self, soup: BeautifulSoup, table_type: str) -> List[Dict]:
        """Extrai dados da tabela baseado no tipo"""
        try:
            # Encontrar a tabela principal
            table = soup.find('table')
            if not table:
                return []
            
            rows = table.find_all('tr')
            if not rows:
                return []
            
            # Extrair cabeçalho
            header_row = rows[0] if rows else None
            headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])] if header_row else []
            
            # Extrair dados
            data_rows = []
            for row in rows[1:]:
                cells = row.find_all('td')
                if cells:
                    row_data = {}
                    for i, cell in enumerate(cells):
                        header = headers[i] if i < len(headers) else f'col_{i}'
                        
                        # Limpar e processar o texto da célula
                        cell_text = cell.get_text(strip=True)
                        
                        # Tentar converter números
                        if cell_text and cell_text.replace('.', '').replace('-', '').isdigit():
                            try:
                                row_data[header] = float(cell_text) if '.' in cell_text else int(cell_text)
                            except ValueError:
                                row_data[header] = cell_text
                        else:
                            row_data[header] = cell_text
                    
                    if row_data:  # Só adicionar se houver dados
                        data_rows.append(row_data)
            
            return data_rows
            
        except Exception as e:
            logger.error(f"Erro ao extrair tabela {table_type}: {e}")
            return []
    
    def extract_complete_game_data(self, game_id: str) -> Dict:
        """Extrai dados completos de todas as tabelas de um jogo"""
        logger.info(f"Extraindo dados completos do jogo {game_id}")
        
        game_data = {
            'game_id': game_id,
            'tables': {},
            'extracted_at': datetime.now().isoformat()
        }
        
        for table_type in self.table_types:
            logger.info(f"Extraindo tabela {table_type} do jogo {game_id}")
            table_data = self.extract_table_data(game_id, table_type)
            game_data['tables'][table_type] = table_data
            
            # Pequena pausa entre requisições
            time.sleep(0.5)
        
        return game_data
    
    def extract_all_live_data(self, max_games: Optional[int] = None) -> Dict:
        """Extrai dados completos de todos os jogos live"""
        logger.info("Iniciando extração completa de dados live")
        
        # Extrair lista de jogos
        live_games = self.extract_live_games()
        
        if max_games:
            live_games = live_games[:max_games]
            logger.info(f"Limitando extração a {max_games} jogos")
        
        complete_data = {
            'extraction_info': {
                'timestamp': datetime.now().isoformat(),
                'total_games': len(live_games),
                'table_types': self.table_types
            },
            'live_games_summary': live_games,
            'games_data': {}
        }
        
        # Extrair dados completos de cada jogo
        for i, game in enumerate(live_games, 1):
            game_id = game['game_id']
            logger.info(f"Processando jogo {i}/{len(live_games)}: {game_id}")
            
            game_data = self.extract_complete_game_data(game_id)
            complete_data['games_data'][game_id] = game_data
            
            # Pausa entre jogos
            time.sleep(1)
        
        return complete_data
    
    def save_data(self, data: Dict, filename: str = None):
        """Salva os dados extraídos em arquivo JSON"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'complete_live_data_{timestamp}.json'
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Dados salvos em: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Erro ao salvar dados: {e}")
            return None

def main():
    """Função principal"""
    extractor = CompleteLiveExtractor()
    
    print("🎯 Extrator Completo de Dados Live - Dropping Odds")
    print("=" * 50)
    
    # Opções do usuário
    print("\nOpções:")
    print("1. Extrair dados de todos os jogos live")
    print("2. Extrair dados de um jogo específico")
    print("3. Extrair dados limitados (primeiros 5 jogos)")
    
    choice = input("\nEscolha uma opção (1-3): ").strip()
    
    if choice == '1':
        print("\n📊 Extraindo dados de todos os jogos live...")
        data = extractor.extract_all_live_data()
        filename = extractor.save_data(data)
        print(f"\n✅ Extração completa! Dados salvos em: {filename}")
        
    elif choice == '2':
        game_id = input("\nDigite o ID do jogo: ").strip()
        if game_id:
            print(f"\n📊 Extraindo dados do jogo {game_id}...")
            data = extractor.extract_complete_game_data(game_id)
            filename = extractor.save_data({'games_data': {game_id: data}}, f'game_{game_id}_data.json')
            print(f"\n✅ Extração completa! Dados salvos em: {filename}")
        else:
            print("❌ ID do jogo não fornecido")
            
    elif choice == '3':
        print("\n📊 Extraindo dados dos primeiros 5 jogos...")
        data = extractor.extract_all_live_data(max_games=5)
        filename = extractor.save_data(data)
        print(f"\n✅ Extração completa! Dados salvos em: {filename}")
        
    else:
        print("❌ Opção inválida")

if __name__ == "__main__":
    main()