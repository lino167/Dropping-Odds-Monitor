#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Análise da estrutura de página individual de jogo
URL: https://dropping-odds.com/event.php?id=10519888&t=1x2
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import json
from datetime import datetime

def analyze_event_page(game_id="10519888", bet_type="1x2"):
    """
    Analisa a estrutura da página individual de um jogo
    """
    url = f"https://dropping-odds.com/event.php?id={game_id}&t={bet_type}"
    
    print(f"🔍 Analisando página: {url}")
    print("=" * 60)
    
    # Configurar Selenium
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # Carregar página
        driver.get(url)
        time.sleep(5)  # Aguardar carregamento completo
        
        # Parse com BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Análise geral da página
        print(f"📄 Título da página: {soup.title.string if soup.title else 'N/A'}")
        
        # Encontrar todas as tabelas
        tables = soup.find_all('table')
        print(f"📊 Total de tabelas encontradas: {len(tables)}")
        print()
        
        analysis_results = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'total_tables': len(tables),
            'tables_analysis': []
        }
        
        # Analisar cada tabela
        for i, table in enumerate(tables):
            print(f"🔍 TABELA {i+1}:")
            print("-" * 40)
            
            rows = table.find_all('tr')
            print(f"   📏 Linhas: {len(rows)}")
            
            table_analysis = {
                'table_index': i+1,
                'total_rows': len(rows),
                'headers': [],
                'sample_rows': [],
                'css_classes': table.get('class', []),
                'table_id': table.get('id', '')
            }
            
            if rows:
                # Analisar cabeçalho
                header_row = rows[0]
                headers = []
                for cell in header_row.find_all(['th', 'td']):
                    text = cell.get_text(strip=True)
                    headers.append(text)
                
                table_analysis['headers'] = headers
                print(f"   📋 Cabeçalhos ({len(headers)}): {headers[:8]}")
                
                # Analisar algumas linhas de dados
                data_rows = rows[1:6]  # Primeiras 5 linhas de dados
                for j, row in enumerate(data_rows, 1):
                    cells = row.find_all('td')
                    row_data = [cell.get_text(strip=True) for cell in cells]
                    table_analysis['sample_rows'].append(row_data)
                    print(f"   📝 Linha {j} ({len(cells)} colunas): {row_data[:6]}")
                
                # Verificar se há links nas células
                links_found = 0
                for row in rows[1:6]:
                    links_found += len(row.find_all('a'))
                
                if links_found > 0:
                    print(f"   🔗 Links encontrados: {links_found}")
                
                # Verificar classes CSS da tabela
                if table_analysis['css_classes']:
                    print(f"   🎨 Classes CSS: {table_analysis['css_classes']}")
                
                if table_analysis['table_id']:
                    print(f"   🆔 ID da tabela: {table_analysis['table_id']}")
            
            analysis_results['tables_analysis'].append(table_analysis)
            print()
        
        # Procurar por elementos específicos de odds
        odds_elements = soup.find_all(class_=lambda x: x and ('odd' in x.lower() or 'bet' in x.lower()))
        print(f"🎯 Elementos com classes relacionadas a odds: {len(odds_elements)}")
        
        # Procurar por timestamps ou informações de tempo
        time_elements = soup.find_all(text=lambda text: text and (':' in text and any(char.isdigit() for char in text)))
        print(f"⏰ Elementos com informações de tempo: {len(time_elements[:5])}")
        
        # Salvar análise em arquivo JSON
        with open('event_page_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Análise salva em: event_page_analysis.json")
        
        return analysis_results
        
    except Exception as e:
        print(f"❌ Erro durante análise: {e}")
        return None
        
    finally:
        driver.quit()

if __name__ == "__main__":
    # Analisar página de exemplo
    results = analyze_event_page()
    
    if results:
        print("\n✅ Análise concluída com sucesso!")
        print(f"📊 {results['total_tables']} tabelas analisadas")
    else:
        print("\n❌ Falha na análise")