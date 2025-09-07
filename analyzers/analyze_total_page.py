#!/usr/bin/env python3
"""
Script para analisar a estrutura da página de totais (Over/Under) de um jogo específico
URL: https://dropping-odds.com/event.php?id=10519888&t=total
"""

import json
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def setup_driver(headless=True):
    """Configurar driver do Chrome"""
    options = Options()
    if headless:
        options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    return webdriver.Chrome(options=options)

def analyze_total_page(url):
    """Analisar estrutura da página de totais"""
    driver = setup_driver(headless=True)
    
    try:
        print(f"🔄 Acessando: {url}")
        driver.get(url)
        
        # Aguardar carregamento
        wait = WebDriverWait(driver, 30)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        
        # Obter HTML da página
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Encontrar todas as tabelas
        tables = soup.find_all('table')
        print(f"📊 Encontradas {len(tables)} tabelas")
        
        analysis = {
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "total_tables": len(tables),
            "tables_analysis": []
        }
        
        for i, table in enumerate(tables):
            print(f"\n🔍 Analisando tabela {i+1}...")
            
            # Encontrar cabeçalhos
            headers = []
            header_row = table.find('tr')
            if header_row:
                header_cells = header_row.find_all(['th', 'td'])
                headers = [cell.get_text(strip=True) for cell in header_cells]
            
            # Encontrar todas as linhas
            rows = table.find_all('tr')
            
            # Analisar algumas linhas de dados
            sample_rows = []
            for j, row in enumerate(rows[1:6]):  # Primeiras 5 linhas após cabeçalho
                cells = row.find_all(['td', 'th'])
                row_data = [cell.get_text(strip=True) for cell in cells]
                if row_data:  # Só adicionar se não estiver vazia
                    sample_rows.append({
                        "row_index": j + 1,
                        "cells": row_data,
                        "cell_count": len(row_data)
                    })
            
            table_analysis = {
                "table_index": i + 1,
                "total_rows": len(rows),
                "headers": headers,
                "header_count": len(headers),
                "sample_rows": sample_rows,
                "css_classes": table.get('class', []),
                "table_id": table.get('id', '')
            }
            
            analysis["tables_analysis"].append(table_analysis)
            
            print(f"   📋 {len(rows)} linhas, {len(headers)} colunas")
            print(f"   📝 Cabeçalhos: {headers[:5]}{'...' if len(headers) > 5 else ''}")
        
        # Procurar elementos de tempo/data específicos
        time_elements = soup.find_all(text=lambda text: text and any(char.isdigit() for char in text) and (':' in text or '.' in text))
        analysis["time_elements"] = [elem.strip() for elem in time_elements[:10] if elem.strip()]
        
        # Salvar análise
        filename = "total_page_analysis.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Análise salva em: {filename}")
        return analysis
        
    except Exception as e:
        print(f"❌ Erro na análise: {e}")
        return None
    finally:
        driver.quit()

def main():
    """Função principal"""
    print("🏆 ANÁLISE DA PÁGINA DE TOTAIS (OVER/UNDER)")
    print("=" * 60)
    print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    # URL da página de totais do mesmo jogo
    url = "https://dropping-odds.com/event.php?id=10519888&t=total"
    
    analysis = analyze_total_page(url)
    
    if analysis:
        print("\n📊 RESUMO DA ANÁLISE:")
        print("=" * 40)
        print(f"🌐 URL: {analysis['url']}")
        print(f"📊 Total de tabelas: {analysis['total_tables']}")
        
        for table in analysis['tables_analysis']:
            print(f"\n📋 Tabela {table['table_index']}:")
            print(f"   📏 Linhas: {table['total_rows']}")
            print(f"   📐 Colunas: {table['header_count']}")
            print(f"   📝 Cabeçalhos: {table['headers']}")
    
    print("\n✅ Análise concluída!")

if __name__ == "__main__":
    main()