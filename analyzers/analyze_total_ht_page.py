#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para analisar a estrutura da página de totals do primeiro tempo (total_ht).
Este script examina o layout e estrutura das tabelas de odds de Over/Under do primeiro tempo.
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

def analyze_total_ht_page(game_id):
    """Analisa a estrutura da página de totals do primeiro tempo.
    
    Args:
        game_id (str): ID do jogo para análise
    """
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
    
    url = f"https://dropping-odds.com/event.php?id={game_id}&t=total_ht"
    
    try:
        print(f"🔍 Analisando página de totals HT: {url}")
        driver.get(url)
        
        # Aguarda a página carregar
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)
        
        # Parse do HTML
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
            
            # Conta linhas de dados
            rows = table.find_all('tr')[1:]  # Pula cabeçalho
            print(f"   📊 Total de linhas: {len(rows)}")
            
            # Analisa primeiras 5 linhas
            sample_rows = []
            for j, row in enumerate(rows[:5], 1):
                cells = row.find_all(['td', 'th'])
                cell_texts = [cell.get_text(strip=True) for cell in cells]
                sample_rows.append({
                    'row_index': j,
                    'cells': cell_texts,
                    'cell_count': len(cell_texts)
                })
                print(f"   📄 Linha {j}: {len(cell_texts)} células - {cell_texts[:5]}")
            
            # Analisa classes CSS
            table_classes = table.get('class', [])
            
            table_analysis = {
                'table_index': i,
                'total_rows': len(rows),
                'headers': headers,
                'header_count': len(headers),
                'sample_rows': sample_rows,
                'css_classes': table_classes
            }
            
            analysis_data['tables_analysis'].append(table_analysis)
        
        # Procura por elementos de tempo/data
        time_elements = soup.find_all(text=True)
        time_patterns = []
        for element in time_elements:
            text = element.strip()
            if text and (':' in text or '.' in text) and len(text) < 50:
                if any(char.isdigit() for char in text):
                    time_patterns.append(text)
        
        analysis_data['time_patterns'] = list(set(time_patterns[:20]))  # Primeiros 20 únicos
        
        # Salva análise
        filename = "total_ht_page_analysis.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Análise concluída e salva em: {filename}")
        
    except TimeoutException:
        print(f"⏰ Timeout ao carregar página: {url}")
    except Exception as e:
        print(f"❌ Erro durante análise: {str(e)}")
    finally:
        driver.quit()

def main():
    """Função principal."""
    # Usa o mesmo game_id dos testes anteriores
    game_id = "10519888"
    analyze_total_ht_page(game_id)

if __name__ == "__main__":
    main()