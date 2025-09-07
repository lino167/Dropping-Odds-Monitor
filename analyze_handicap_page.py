#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para analisar a estrutura da página de handicap asiático.
Este script examina o layout e estrutura das tabelas de apostas de handicap.
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

def analyze_handicap_page():
    """Analisa a estrutura da página de handicap asiático."""
    
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
        # URL da página de handicap
        url = "https://dropping-odds.com/event.php?id=10519888&t=handicap"
        print(f"🔍 Analisando página de handicap: {url}")
        
        driver.get(url)
        
        # Aguarda a página carregar
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        time.sleep(3)
        
        # Obtém o HTML da página
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Análise das tabelas
        tables = soup.find_all('table')
        print(f"📊 Encontradas {len(tables)} tabela(s)")
        
        analysis_data = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'total_tables': len(tables),
            'tables_analysis': []
        }
        
        for i, table in enumerate(tables):
            print(f"\n📋 Analisando tabela {i+1}:")
            
            # Análise dos cabeçalhos
            headers = []
            header_row = table.find('tr')
            if header_row:
                for th in header_row.find_all(['th', 'td']):
                    header_text = th.get_text(strip=True)
                    headers.append(header_text)
                    
            print(f"   📝 Cabeçalhos ({len(headers)}): {headers}")
            
            # Análise das linhas de dados
            rows = table.find_all('tr')
            total_rows = len(rows) - 1  # Exclui cabeçalho
            print(f"   📊 Total de linhas: {total_rows}")
            
            # Amostra das primeiras linhas
            sample_rows = []
            for j, row in enumerate(rows[1:6]):  # Primeiras 5 linhas após cabeçalho
                cells = row.find_all(['td', 'th'])
                row_data = {
                    'row_index': j + 1,
                    'cells': [cell.get_text(strip=True) for cell in cells],
                    'cell_count': len(cells)
                }
                sample_rows.append(row_data)
                print(f"   📄 Linha {j+1}: {len(cells)} células - {[cell.get_text(strip=True) for cell in cells[:5]]}")
            
            # Análise de classes CSS e IDs
            css_classes = table.get('class', [])
            table_id = table.get('id', '')
            
            table_analysis = {
                'table_index': i + 1,
                'total_rows': total_rows,
                'headers': headers,
                'header_count': len(headers),
                'sample_rows': sample_rows,
                'css_classes': css_classes,
                'table_id': table_id
            }
            
            analysis_data['tables_analysis'].append(table_analysis)
        
        # Análise de elementos de tempo/data
        time_elements = []
        for element in soup.find_all(text=True):
            text = element.strip()
            if any(char.isdigit() for char in text) and ('.' in text or ':' in text):
                if len(text) < 100:  # Evita textos muito longos
                    time_elements.append(text)
        
        analysis_data['time_elements'] = time_elements[:20]  # Primeiros 20 elementos
        
        # Salva a análise
        filename = 'handicap_page_analysis.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Análise concluída e salva em: {filename}")
        
        return analysis_data
        
    except TimeoutException:
        print("⏰ Timeout ao carregar a página")
        return None
    except Exception as e:
        print(f"❌ Erro durante análise: {str(e)}")
        return None
    finally:
        driver.quit()

if __name__ == "__main__":
    analyze_handicap_page()