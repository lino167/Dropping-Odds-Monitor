#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extrator unificado para todos os tipos de apostas de um jogo específico.
Este módulo combina a extração de dados 1x2 e totais (Over/Under) em uma única operação.
"""

import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

class UnifiedExtractor:
    """Extrator unificado para todos os tipos de apostas de um jogo."""
    
    def __init__(self):
        """Inicializa o extrator unificado."""
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        """Configura o driver do Chrome."""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 30)
        
    def extract_1x2_data(self, game_id):
        """Extrai dados de apostas 1x2.
        
        Args:
            game_id (str): ID do jogo
            
        Returns:
            dict: Dados extraídos ou None se houver erro
        """
        url = f"https://dropping-odds.com/event.php?id={game_id}"
        
        try:
            print(f"🎯 Extraindo dados 1x2: {url}")
            self.driver.get(url)
            
            # Aguarda a tabela carregar
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
            time.sleep(2)
            
            # Obtém o HTML da página
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Encontra a tabela principal
            table = soup.find('table')
            if not table:
                print("❌ Tabela 1x2 não encontrada")
                return None
                
            # Extrai cabeçalhos
            headers = []
            header_row = table.find('tr')
            if header_row:
                for th in header_row.find_all(['th', 'td']):
                    headers.append(th.get_text(strip=True))
            
            # Extrai dados das linhas
            rows_data = []
            rows = table.find_all('tr')[1:]  # Pula o cabeçalho
            
            for i, row in enumerate(rows):
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 6:  # Verifica se tem dados suficientes
                    row_data = {
                        'row_index': i + 1,
                        'date_time': cells[0].get_text(strip=True) if len(cells) > 0 else '',
                        'time': cells[1].get_text(strip=True) if len(cells) > 1 else '',
                        'score': cells[2].get_text(strip=True) if len(cells) > 2 else '',
                        'home_odds': cells[3].get_text(strip=True) if len(cells) > 3 else '',
                        'draw_odds': cells[4].get_text(strip=True) if len(cells) > 4 else '',
                        'away_odds': cells[5].get_text(strip=True) if len(cells) > 5 else '',
                        'home_percentage': cells[6].get_text(strip=True) if len(cells) > 6 else '',
                        'penalty': cells[7].get_text(strip=True) if len(cells) > 7 else '',
                        'red_card': cells[8].get_text(strip=True) if len(cells) > 8 else '',
                        'bookmaker': cells[9].get_text(strip=True) if len(cells) > 9 else '',
                        'extracted_at': datetime.now().isoformat()
                    }
                    
                    # Filtra linhas com dados válidos
                    if (row_data['home_odds'] and row_data['away_odds'] and 
                        row_data['home_odds'] not in ['', '-'] and row_data['away_odds'] not in ['', '-']):
                        rows_data.append(row_data)
            
            result = {
                'bet_type': '1x2',
                'headers': headers,
                'total_rows': len(rows_data),
                'data': rows_data
            }
            
            print(f"✅ Extraídos {len(rows_data)} registros 1x2")
            return result
            
        except Exception as e:
            print(f"❌ Erro ao extrair dados 1x2: {str(e)}")
            return None
            
    def extract_total_data(self, game_id):
        """Extrai dados de totais (Over/Under).
        
        Args:
            game_id (str): ID do jogo
            
        Returns:
            dict: Dados extraídos ou None se houver erro
        """
        url = f"https://dropping-odds.com/event.php?id={game_id}&t=total"
        
        try:
            print(f"📊 Extraindo dados de totais: {url}")
            self.driver.get(url)
            
            # Aguarda a tabela carregar
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
            time.sleep(2)
            
            # Obtém o HTML da página
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Encontra a tabela principal
            table = soup.find('table')
            if not table:
                print("❌ Tabela de totais não encontrada")
                return None
                
            # Extrai cabeçalhos
            headers = []
            header_row = table.find('tr')
            if header_row:
                for th in header_row.find_all(['th', 'td']):
                    headers.append(th.get_text(strip=True))
            
            # Extrai dados das linhas
            rows_data = []
            rows = table.find_all('tr')[1:]  # Pula o cabeçalho
            
            for i, row in enumerate(rows):
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 6:  # Verifica se tem dados suficientes
                    row_data = {
                        'row_index': i + 1,
                        'date_time': cells[0].get_text(strip=True) if len(cells) > 0 else '',
                        'time': cells[1].get_text(strip=True) if len(cells) > 1 else '',
                        'score': cells[2].get_text(strip=True) if len(cells) > 2 else '',
                        'over_odds': cells[3].get_text(strip=True) if len(cells) > 3 else '',
                        'handicap': cells[4].get_text(strip=True) if len(cells) > 4 else '',
                        'under_odds': cells[5].get_text(strip=True) if len(cells) > 5 else '',
                        'over_percentage': cells[6].get_text(strip=True) if len(cells) > 6 else '',
                        'drop_percentage': cells[7].get_text(strip=True) if len(cells) > 7 else '',
                        'under_percentage': cells[8].get_text(strip=True) if len(cells) > 8 else '',
                        'bookmaker': cells[9].get_text(strip=True) if len(cells) > 9 else '',
                        'extracted_at': datetime.now().isoformat()
                    }
                    
                    # Filtra linhas com dados válidos
                    if (row_data['over_odds'] and row_data['under_odds'] and 
                        row_data['over_odds'] not in ['', '-'] and row_data['under_odds'] not in ['', '-']):
                        rows_data.append(row_data)
            
            result = {
                'bet_type': 'total',
                'headers': headers,
                'total_rows': len(rows_data),
                'data': rows_data
            }
            
            print(f"✅ Extraídos {len(rows_data)} registros de totais")
            return result
            
        except Exception as e:
            print(f"❌ Erro ao extrair dados de totais: {str(e)}")
            return None
            
    def extract_all_data(self, game_id):
        """Extrai todos os tipos de dados para um jogo.
        
        Args:
            game_id (str): ID do jogo
            
        Returns:
            dict: Dados completos extraídos
        """
        if not self.driver:
            self.setup_driver()
            
        start_time = time.time()
        
        print(f"🚀 Iniciando extração completa para jogo ID: {game_id}")
        
        # Extrai dados 1x2
        data_1x2 = self.extract_1x2_data(game_id)
        
        # Extrai dados de totais
        data_total = self.extract_total_data(game_id)
        
        # Compila resultado final
        result = {
            'game_id': game_id,
            'extraction_time': datetime.now().isoformat(),
            'processing_time_seconds': round(time.time() - start_time, 2),
            'bet_types': {
                '1x2': data_1x2,
                'total': data_total
            },
            'summary': {
                'total_1x2_records': data_1x2['total_rows'] if data_1x2 else 0,
                'total_total_records': data_total['total_rows'] if data_total else 0,
                'total_records': (data_1x2['total_rows'] if data_1x2 else 0) + (data_total['total_rows'] if data_total else 0),
                'success_1x2': data_1x2 is not None,
                'success_total': data_total is not None
            }
        }
        
        processing_time = time.time() - start_time
        
        print(f"\n🎯 Extração completa finalizada em {processing_time:.2f}s")
        print(f"   📊 Registros 1x2: {result['summary']['total_1x2_records']}")
        print(f"   📈 Registros totais: {result['summary']['total_total_records']}")
        print(f"   📋 Total geral: {result['summary']['total_records']}")
        
        return result
        
    def close(self):
        """Fecha o driver."""
        if self.driver:
            self.driver.quit()
            self.driver = None

def main():
    """Função principal para testar o extrator unificado."""
    extractor = UnifiedExtractor()
    
    try:
        # Testa com o mesmo jogo
        game_id = "10519888"
        result = extractor.extract_all_data(game_id)
        
        if result:
            # Salva os dados extraídos
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"unified_extraction_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"\n📊 Resumo da extração unificada:")
            print(f"   🎯 Jogo ID: {result['game_id']}")
            print(f"   ⏱️ Tempo de processamento: {result['processing_time_seconds']}s")
            print(f"   📋 Total de registros: {result['summary']['total_records']}")
            print(f"   💾 Dados salvos em: {filename}")
            
            # Mostra estatísticas por tipo
            for bet_type, data in result['bet_types'].items():
                if data:
                    print(f"\n📈 {bet_type.upper()}:")
                    print(f"   📊 Registros: {data['total_rows']}")
                    if data['data']:
                        first_record = data['data'][0]
                        if bet_type == '1x2':
                            print(f"   📝 Exemplo: {first_record['date_time']} - Casa: {first_record['home_odds']} Empate: {first_record['draw_odds']} Fora: {first_record['away_odds']}")
                        elif bet_type == 'total':
                            print(f"   📝 Exemplo: {first_record['date_time']} - Over: {first_record['over_odds']} ({first_record['handicap']}) Under: {first_record['under_odds']}")
        else:
            print("❌ Falha na extração de dados")
            
    except Exception as e:
        print(f"❌ Erro na execução: {str(e)}")
    finally:
        extractor.close()

if __name__ == "__main__":
    main()