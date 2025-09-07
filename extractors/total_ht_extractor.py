#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extrator de dados de totals do primeiro tempo para páginas de eventos específicos.
Este módulo extrai dados de apostas Over/Under do primeiro tempo de páginas individuais de jogos.
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

class TotalHTExtractor:
    """Extrator para dados de totals do primeiro tempo de jogos específicos."""
    
    def __init__(self):
        """Inicializa o extrator de totals HT."""
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
        
    def extract_total_ht_data(self, game_id):
        """Extrai dados de totals do primeiro tempo para um jogo específico.
        
        Args:
            game_id (str): ID do jogo
            
        Returns:
            dict: Dados extraídos ou None se houver erro
        """
        if not self.driver:
            self.setup_driver()
            
        url = f"https://dropping-odds.com/event.php?id={game_id}&t=total_ht"
        
        try:
            print(f"🎯 Acessando página de totals HT: {url}")
            self.driver.get(url)
            
            # Aguarda a tabela carregar
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
            time.sleep(2)
            
            # Obtém o HTML da página
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Encontra a tabela principal
            table = soup.find('table')
            if not table:
                print("❌ Tabela não encontrada")
                return None
                
            # Extrai cabeçalhos
            headers = []
            header_row = table.find('tr')
            if header_row:
                for th in header_row.find_all(['th', 'td']):
                    headers.append(th.get_text(strip=True))
            
            print(f"📋 Cabeçalhos encontrados: {headers}")
            
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
                        'drop_percentage': cells[6].get_text(strip=True) if len(cells) > 6 else '',
                        'penalty': cells[7].get_text(strip=True) if len(cells) > 7 else '',
                        'red_card': cells[8].get_text(strip=True) if len(cells) > 8 else '',
                        'extracted_at': datetime.now().isoformat()
                    }
                    
                    # Filtra linhas com dados válidos
                    if (row_data['over_odds'] and row_data['under_odds'] and row_data['handicap'] and
                        row_data['over_odds'] not in ['', '-'] and row_data['under_odds'] not in ['', '-'] and
                        row_data['handicap'] not in ['', '-']):
                        rows_data.append(row_data)
            
            result = {
                'game_id': game_id,
                'url': url,
                'bet_type': 'total_ht',
                'extraction_time': datetime.now().isoformat(),
                'headers': headers,
                'total_rows': len(rows_data),
                'data': rows_data
            }
            
            print(f"✅ Extraídos {len(rows_data)} registros de totals HT")
            return result
            
        except TimeoutException:
            print(f"⏰ Timeout ao carregar página: {url}")
            return None
        except Exception as e:
            print(f"❌ Erro ao extrair dados de totals HT: {str(e)}")
            return None
            
    def close(self):
        """Fecha o driver."""
        if self.driver:
            self.driver.quit()
            self.driver = None

def main():
    """Função principal para testar o extrator."""
    extractor = TotalHTExtractor()
    
    try:
        # Testa com o mesmo jogo da análise
        game_id = "10519888"
        result = extractor.extract_total_ht_data(game_id)
        
        if result:
            # Salva os dados extraídos
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"total_ht_extraction_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"\n🎯 Resumo da extração de totals HT:")
            print(f"   🎮 Jogo ID: {result['game_id']}")
            print(f"   📈 Tipo de aposta: {result['bet_type']}")
            print(f"   📋 Total de registros: {result['total_rows']}")
            print(f"   💾 Dados salvos em: {filename}")
            
            # Mostra alguns exemplos
            if result['data']:
                print(f"\n📝 Primeiros registros:")
                for i, record in enumerate(result['data'][:3]):
                    print(f"   {i+1}. {record['date_time']} - Over: {record['over_odds']} ({record['handicap']}) Under: {record['under_odds']}")
        else:
            print("❌ Falha na extração de dados")
            
    except Exception as e:
        print(f"❌ Erro na execução: {str(e)}")
    finally:
        extractor.close()

if __name__ == "__main__":
    main()