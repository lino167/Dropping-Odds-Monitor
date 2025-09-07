#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para analisar a estrutura da página de apostas 1x2 do primeiro tempo.
Este script examina o layout e estrutura dos dados de apostas HT 1x2.
"""

import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup

def analyze_1x2_ht_page():
    """Analisa a estrutura da página de apostas 1x2 HT."""
    
    # URL da página de apostas 1x2 do primeiro tempo
    url = "https://dropping-odds.com/event.php?id=10519888&t=1x2_ht"
    
    # Configuração do Chrome
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 30)
    
    try:
        print(f"🔍 Analisando página de 1x2 HT: {url}")
        driver.get(url)
        
        # Aguarda a página carregar
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)
        
        # Obtém o HTML da página
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Encontra todas as tabelas
        tables = soup.find_all('table')
        print(f"📊 Encontradas {len(tables)} tabela(s)")
        
        analysis_data = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'total_tables': len(tables),
            'tables_analysis': []
        }
        
        for i, table in enumerate(tables, 1):
            print(f"\n📋 Analisando tabela {i}:")
            
            # Extrai cabeçalhos
            headers = []
            header_row = table.find('tr')
            if header_row:
                for th in header_row.find_all(['th', 'td']):
                    header_text = th.get_text(strip=True)
                    if header_text:
                        headers.append(header_text)
            
            print(f"   📝 Cabeçalhos ({len(headers)}): {headers}")
            
            # Extrai dados das linhas
            rows = table.find_all('tr')[1:]  # Pula o cabeçalho
            print(f"   📊 Total de linhas: {len(rows)}")
            
            # Analisa primeiras 5 linhas como exemplo
            sample_rows = []
            for j, row in enumerate(rows[:5], 1):
                cells = row.find_all(['td', 'th'])
                cell_data = [cell.get_text(strip=True) for cell in cells]
                sample_rows.append({
                    'row_index': j,
                    'cells': cell_data,
                    'cell_count': len(cell_data)
                })
                print(f"   📄 Linha {j}: {len(cell_data)} células - {cell_data[:5]}")
            
            table_analysis = {
                'table_index': i,
                'total_rows': len(rows),
                'headers': headers,
                'header_count': len(headers),
                'sample_rows': sample_rows
            }
            
            analysis_data['tables_analysis'].append(table_analysis)
        
        # Verifica se há informações sobre o jogo
        game_info = soup.find('title')
        if game_info:
            analysis_data['page_title'] = game_info.get_text(strip=True)
            print(f"\n🎮 Título da página: {analysis_data['page_title']}")
        
        # Procura por informações de score ou status do jogo
        score_elements = soup.find_all(text=True)
        time_elements = soup.find_all(text=True)
        
        # Salva a análise
        filename = "1x2_ht_page_analysis.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Análise concluída e salva em: {filename}")
        return analysis_data
        
    except TimeoutException:
        print(f"⏰ Timeout ao carregar página: {url}")
        return None
    except Exception as e:
        print(f"❌ Erro durante análise: {str(e)}")
        return None
    finally:
        driver.quit()

if __name__ == "__main__":
    analyze_1x2_ht_page()