#!/usr/bin/env python3
"""
Extrator Automatizado de Dados

Este script utiliza sessões gravadas pelo interactive_click_recorder.py
para automatizar a extração contínua de dados do site.
"""

import time
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dataclasses import dataclass, asdict
import pandas as pd
from interactive_click_recorder import InteractiveClickRecorder, RecordingSession, ClickAction

@dataclass
class ExtractedData:
    """Dados extraídos de uma execução."""
    extraction_id: str
    timestamp: str
    session_used: str
    url: str
    data: Dict[str, Any]
    success: bool
    error_message: str

class AutomatedDataExtractor:
    """Sistema automatizado de extração baseado em sessões gravadas."""
    
    def __init__(self, session_file: str = None):
        self.recorder = InteractiveClickRecorder()
        self.session_file = session_file
        self.extracted_data: List[ExtractedData] = []
        self.extraction_rules = {
            'tables': {
                'selector': 'table',
                'extract_headers': True,
                'extract_rows': True
            },
            'odds': {
                'selector': '.odds, [class*="odd"], [class*="coef"]',
                'extract_text': True,
                'extract_attributes': ['data-odd', 'data-value']
            },
            'games': {
                'selector': '.game, .match, [class*="game"], [class*="match"]',
                'extract_text': True,
                'extract_links': True
            }
        }
    
    def setup_driver(self):
        """Configura o driver para extração."""
        self.recorder.setup_driver()
        print("🚀 Driver configurado para extração automatizada")
    
    def load_session(self, session_file: str):
        """Carrega sessão de gravação."""
        self.recorder.load_session(session_file)
        self.session_file = session_file
        print(f"📂 Sessão carregada: {os.path.basename(session_file)}")
    
    def execute_extraction_flow(self) -> ExtractedData:
        """Executa o fluxo de extração baseado na sessão gravada."""
        if not self.recorder.current_session:
            raise ValueError("Nenhuma sessão carregada")
        
        extraction_id = f"extract_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            print(f"🔄 Iniciando extração: {extraction_id}")
            
            # Executa fluxo da sessão gravada
            success = self.recorder.replay_session()
            
            if not success:
                raise Exception("Falha na reprodução da sessão")
            
            # Aguarda carregamento da página final
            time.sleep(3)
            
            # Extrai dados da página atual
            extracted_data = self.extract_page_data()
            
            # Cria registro de extração
            extraction = ExtractedData(
                extraction_id=extraction_id,
                timestamp=datetime.now().isoformat(),
                session_used=os.path.basename(self.session_file) if self.session_file else "unknown",
                url=self.recorder.driver.current_url,
                data=extracted_data,
                success=True,
                error_message=""
            )
            
            self.extracted_data.append(extraction)
            print(f"✅ Extração concluída: {len(extracted_data)} elementos encontrados")
            
            return extraction
            
        except Exception as e:
            error_extraction = ExtractedData(
                extraction_id=extraction_id,
                timestamp=datetime.now().isoformat(),
                session_used=os.path.basename(self.session_file) if self.session_file else "unknown",
                url=self.recorder.driver.current_url if self.recorder.driver else "unknown",
                data={},
                success=False,
                error_message=str(e)
            )
            
            self.extracted_data.append(error_extraction)
            print(f"❌ Erro na extração: {str(e)}")
            
            return error_extraction
    
    def extract_page_data(self) -> Dict[str, Any]:
        """Extrai dados da página atual baseado nas regras definidas."""
        page_data = {
            'url': self.recorder.driver.current_url,
            'title': self.recorder.driver.title,
            'timestamp': datetime.now().isoformat(),
            'tables': [],
            'odds': [],
            'games': [],
            'raw_text': ''
        }
        
        try:
            # Extrai tabelas
            page_data['tables'] = self.extract_tables()
            
            # Extrai odds
            page_data['odds'] = self.extract_odds()
            
            # Extrai informações de jogos
            page_data['games'] = self.extract_games()
            
            # Extrai texto bruto da página
            page_data['raw_text'] = self.recorder.driver.find_element(By.TAG_NAME, 'body').text[:5000]
            
        except Exception as e:
            print(f"⚠️ Erro na extração de dados: {str(e)}")
        
        return page_data
    
    def extract_tables(self) -> List[Dict[str, Any]]:
        """Extrai dados de todas as tabelas da página."""
        tables_data = []
        
        try:
            tables = self.recorder.driver.find_elements(By.TAG_NAME, 'table')
            
            for i, table in enumerate(tables):
                table_data = {
                    'table_index': i,
                    'headers': [],
                    'rows': [],
                    'cell_count': 0
                }
                
                # Extrai cabeçalhos
                try:
                    headers = table.find_elements(By.TAG_NAME, 'th')
                    table_data['headers'] = [header.text.strip() for header in headers]
                except:
                    pass
                
                # Extrai linhas
                try:
                    rows = table.find_elements(By.TAG_NAME, 'tr')
                    for row in rows:
                        cells = row.find_elements(By.TAG_NAME, 'td')
                        if cells:  # Só adiciona se tiver células
                            row_data = []
                            for cell in cells:
                                cell_text = cell.text.strip()
                                cell_data = {
                                    'text': cell_text,
                                    'attributes': {}
                                }
                                
                                # Extrai atributos importantes
                                for attr in ['class', 'id', 'data-value', 'data-odd']:
                                    value = cell.get_attribute(attr)
                                    if value:
                                        cell_data['attributes'][attr] = value
                                
                                row_data.append(cell_data)
                            
                            table_data['rows'].append(row_data)
                            table_data['cell_count'] += len(row_data)
                except Exception as e:
                    print(f"   ⚠️ Erro ao extrair linhas da tabela {i}: {str(e)}")
                
                if table_data['cell_count'] > 0:  # Só adiciona tabelas com dados
                    tables_data.append(table_data)
        
        except Exception as e:
            print(f"⚠️ Erro ao extrair tabelas: {str(e)}")
        
        return tables_data
    
    def extract_odds(self) -> List[Dict[str, Any]]:
        """Extrai odds da página."""
        odds_data = []
        
        try:
            # Múltiplos seletores para odds
            selectors = [
                '.odds', '[class*="odd"]', '[class*="coef"]', 
                '[class*="price"]', '[data-odd]', '[data-value]'
            ]
            
            for selector in selectors:
                try:
                    elements = self.recorder.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        odd_text = element.text.strip()
                        if odd_text and self.is_valid_odd(odd_text):
                            odd_data = {
                                'text': odd_text,
                                'selector': selector,
                                'attributes': {},
                                'parent_text': ''
                            }
                            
                            # Extrai atributos
                            for attr in ['class', 'id', 'data-odd', 'data-value', 'title']:
                                value = element.get_attribute(attr)
                                if value:
                                    odd_data['attributes'][attr] = value
                            
                            # Extrai contexto do elemento pai
                            try:
                                parent = element.find_element(By.XPATH, '..')
                                odd_data['parent_text'] = parent.text.strip()[:100]
                            except:
                                pass
                            
                            odds_data.append(odd_data)
                
                except Exception as e:
                    continue
        
        except Exception as e:
            print(f"⚠️ Erro ao extrair odds: {str(e)}")
        
        return odds_data
    
    def extract_games(self) -> List[Dict[str, Any]]:
        """Extrai informações de jogos/partidas."""
        games_data = []
        
        try:
            # Múltiplos seletores para jogos
            selectors = [
                '.game', '.match', '[class*="game"]', '[class*="match"]',
                '[class*="event"]', 'tr', '.row'
            ]
            
            for selector in selectors:
                try:
                    elements = self.recorder.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        game_text = element.text.strip()
                        if game_text and len(game_text) > 10:  # Filtro básico
                            game_data = {
                                'text': game_text[:200],  # Limita tamanho
                                'selector': selector,
                                'links': [],
                                'attributes': {}
                            }
                            
                            # Extrai links dentro do elemento
                            try:
                                links = element.find_elements(By.TAG_NAME, 'a')
                                for link in links:
                                    href = link.get_attribute('href')
                                    if href:
                                        game_data['links'].append({
                                            'url': href,
                                            'text': link.text.strip()
                                        })
                            except:
                                pass
                            
                            # Extrai atributos importantes
                            for attr in ['class', 'id', 'data-id', 'data-game']:
                                value = element.get_attribute(attr)
                                if value:
                                    game_data['attributes'][attr] = value
                            
                            games_data.append(game_data)
                
                except Exception as e:
                    continue
        
        except Exception as e:
            print(f"⚠️ Erro ao extrair jogos: {str(e)}")
        
        return games_data
    
    def is_valid_odd(self, text: str) -> bool:
        """Verifica se um texto é uma odd válida."""
        try:
            # Remove espaços e caracteres especiais
            clean_text = text.replace(',', '.').strip()
            
            # Tenta converter para float
            value = float(clean_text)
            
            # Odds geralmente estão entre 1.01 e 100
            return 1.0 <= value <= 100.0
        
        except:
            return False
    
    def run_continuous_extraction(self, interval_minutes: int = 5, max_extractions: int = 100):
        """Executa extração contínua em intervalos."""
        print(f"🔄 Iniciando extração contínua (intervalo: {interval_minutes}min, máx: {max_extractions})")
        
        extraction_count = 0
        
        try:
            while extraction_count < max_extractions:
                print(f"\n--- Extração {extraction_count + 1}/{max_extractions} ---")
                
                # Executa extração
                extraction = self.execute_extraction_flow()
                
                if extraction.success:
                    print(f"✅ Dados extraídos com sucesso")
                    
                    # Salva dados incrementalmente
                    self.save_extraction_data(extraction)
                else:
                    print(f"❌ Falha na extração: {extraction.error_message}")
                
                extraction_count += 1
                
                # Aguarda próxima extração
                if extraction_count < max_extractions:
                    print(f"⏳ Aguardando {interval_minutes} minutos para próxima extração...")
                    time.sleep(interval_minutes * 60)
        
        except KeyboardInterrupt:
            print("\n⏹️ Extração interrompida pelo usuário")
        except Exception as e:
            print(f"\n❌ Erro na extração contínua: {str(e)}")
        
        print(f"\n📊 Extração finalizada: {extraction_count} execuções realizadas")
    
    def save_extraction_data(self, extraction: ExtractedData):
        """Salva dados de uma extração."""
        try:
            # Salva JSON individual
            filename = f"extraction_{extraction.extraction_id}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(asdict(extraction), f, indent=2, ensure_ascii=False)
            
            # Salva CSV consolidado de tabelas
            if extraction.data.get('tables'):
                self.save_tables_to_csv(extraction)
            
            print(f"💾 Dados salvos: {filename}")
            
        except Exception as e:
            print(f"⚠️ Erro ao salvar dados: {str(e)}")
    
    def save_tables_to_csv(self, extraction: ExtractedData):
        """Salva dados de tabelas em formato CSV."""
        try:
            for i, table in enumerate(extraction.data['tables']):
                if table['rows']:
                    # Converte dados da tabela para DataFrame
                    rows_data = []
                    for row in table['rows']:
                        row_dict = {}
                        for j, cell in enumerate(row):
                            col_name = table['headers'][j] if j < len(table['headers']) else f'col_{j}'
                            row_dict[col_name] = cell['text']
                        rows_data.append(row_dict)
                    
                    if rows_data:
                        df = pd.DataFrame(rows_data)
                        csv_filename = f"table_{extraction.extraction_id}_t{i}.csv"
                        df.to_csv(csv_filename, index=False, encoding='utf-8')
                        print(f"   📊 Tabela {i} salva: {csv_filename}")
        
        except Exception as e:
            print(f"⚠️ Erro ao salvar CSV: {str(e)}")
    
    def generate_summary_report(self):
        """Gera relatório resumo das extrações."""
        if not self.extracted_data:
            print("📊 Nenhum dado extraído para relatório")
            return
        
        successful = [e for e in self.extracted_data if e.success]
        failed = [e for e in self.extracted_data if not e.success]
        
        report = {
            'summary': {
                'total_extractions': len(self.extracted_data),
                'successful': len(successful),
                'failed': len(failed),
                'success_rate': len(successful) / len(self.extracted_data) * 100,
                'first_extraction': self.extracted_data[0].timestamp if self.extracted_data else None,
                'last_extraction': self.extracted_data[-1].timestamp if self.extracted_data else None
            },
            'data_stats': {
                'total_tables': sum(len(e.data.get('tables', [])) for e in successful),
                'total_odds': sum(len(e.data.get('odds', [])) for e in successful),
                'total_games': sum(len(e.data.get('games', [])) for e in successful)
            },
            'errors': [{'extraction_id': e.extraction_id, 'error': e.error_message} for e in failed]
        }
        
        # Salva relatório
        report_filename = f"extraction_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 RELATÓRIO DE EXTRAÇÃO")
        print(f"Total de extrações: {report['summary']['total_extractions']}")
        print(f"Sucessos: {report['summary']['successful']} ({report['summary']['success_rate']:.1f}%)")
        print(f"Falhas: {report['summary']['failed']}")
        print(f"Tabelas extraídas: {report['data_stats']['total_tables']}")
        print(f"Odds extraídas: {report['data_stats']['total_odds']}")
        print(f"Jogos extraídos: {report['data_stats']['total_games']}")
        print(f"Relatório salvo: {report_filename}")
    
    def close(self):
        """Fecha o extrator e gera relatório final."""
        self.generate_summary_report()
        self.recorder.close_driver()
        print("🔒 Extrator finalizado")

# Função principal
def main():
    """Função principal para executar extração automatizada."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extrator Automatizado de Dados')
    parser.add_argument('--session', '-s', required=True, help='Arquivo de sessão gravada (.json)')
    parser.add_argument('--interval', '-i', type=int, default=5, help='Intervalo entre extrações (minutos)')
    parser.add_argument('--max-extractions', '-m', type=int, default=100, help='Número máximo de extrações')
    parser.add_argument('--single', action='store_true', help='Executa apenas uma extração')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.session):
        print(f"❌ Arquivo de sessão não encontrado: {args.session}")
        return
    
    print("🤖 Extrator Automatizado de Dados")
    print("=" * 40)
    
    extractor = AutomatedDataExtractor()
    
    try:
        # Configura driver e carrega sessão
        extractor.setup_driver()
        extractor.load_session(args.session)
        
        if args.single:
            # Execução única
            print("🎯 Executando extração única...")
            extraction = extractor.execute_extraction_flow()
            
            if extraction.success:
                print("✅ Extração concluída com sucesso")
                extractor.save_extraction_data(extraction)
            else:
                print(f"❌ Falha na extração: {extraction.error_message}")
        else:
            # Execução contínua
            extractor.run_continuous_extraction(args.interval, args.max_extractions)
        
    except KeyboardInterrupt:
        print("\n⏹️ Execução interrompida pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro na execução: {str(e)}")
    finally:
        extractor.close()

if __name__ == "__main__":
    main()