#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Análise da Página Live do Dropping Odds - Sistema 2.0
Analisa a estrutura da página https://dropping-odds.com/index.php?view=live
para entender como extrair informações dos jogos ao vivo
"""

import logging
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('live_page_analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class LivePageAnalyzer:
    """
    Analisador da página de jogos ao vivo do dropping-odds.com
    """
    
    def __init__(self):
        self.url = "https://dropping-odds.com/index.php?view=live"
        self.driver = None
        self.analysis_results = {
            'timestamp': datetime.now().isoformat(),
            'url': self.url,
            'page_structure': {},
            'games_found': [],
            'table_structure': {},
            'navigation_elements': {},
            'recommendations': []
        }
    
    def setup_driver(self):
        """Configura o driver do Selenium"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            logging.info("✅ Driver configurado com sucesso")
            return True
        except Exception as e:
            logging.error(f"❌ Erro ao configurar driver: {e}")
            return False
    
    def analyze_page_structure(self):
        """Analisa a estrutura geral da página"""
        logging.info("🔍 Analisando estrutura da página...")
        
        try:
            # Navegar para a página
            self.driver.get(self.url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            
            # Aguardar carregamento completo
            time.sleep(3)
            
            # Analisar elementos principais
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Estrutura da página
            self.analysis_results['page_structure'] = {
                'title': soup.title.text if soup.title else 'N/A',
                'main_containers': self._find_main_containers(soup),
                'tables_found': len(soup.find_all('table')),
                'forms_found': len(soup.find_all('form')),
                'scripts_found': len(soup.find_all('script')),
                'css_files': len(soup.find_all('link', {'rel': 'stylesheet'}))
            }
            
            logging.info(f"📊 Estrutura básica identificada: {self.analysis_results['page_structure']['tables_found']} tabelas encontradas")
            
        except Exception as e:
            logging.error(f"❌ Erro ao analisar estrutura da página: {e}")
    
    def analyze_games_table(self):
        """Analisa a tabela de jogos ao vivo"""
        logging.info("🏆 Analisando tabela de jogos...")
        
        try:
            # Procurar pela tabela principal de jogos
            tables = self.driver.find_elements(By.TAG_NAME, 'table')
            
            for i, table in enumerate(tables):
                logging.info(f"📋 Analisando tabela {i+1}/{len(tables)}")
                
                # Verificar se é a tabela de jogos (procurar por cabeçalhos típicos)
                headers = table.find_elements(By.TAG_NAME, 'th')
                header_texts = [h.text.strip() for h in headers]
                
                logging.info(f"📝 Cabeçalhos encontrados: {header_texts}")
                
                # Se encontrar cabeçalhos relacionados a jogos
                if any(keyword in ' '.join(header_texts).lower() for keyword in ['country', 'league', 'home', 'away', 'score', 'time']):
                    logging.info("✅ Tabela de jogos identificada!")
                    self._analyze_games_in_table(table, i)
                    break
            
        except Exception as e:
            logging.error(f"❌ Erro ao analisar tabela de jogos: {e}")
    
    def _analyze_games_in_table(self, table, table_index):
        """Analisa os jogos dentro da tabela identificada"""
        try:
            rows = table.find_elements(By.TAG_NAME, 'tr')
            logging.info(f"📊 Encontradas {len(rows)} linhas na tabela")
            
            games_found = []
            
            for i, row in enumerate(rows):
                try:
                    cells = row.find_elements(By.TAG_NAME, 'td')
                    if len(cells) >= 4:  # Assumindo pelo menos 4 colunas para um jogo válido
                        game_data = {
                            'row_index': i,
                            'cells_count': len(cells),
                            'cell_contents': [cell.text.strip() for cell in cells[:8]],  # Primeiras 8 colunas
                            'links_found': len(row.find_elements(By.TAG_NAME, 'a')),
                            'css_classes': row.get_attribute('class'),
                            'has_score': self._check_for_score_pattern(row.text)
                        }
                        
                        # Procurar por links para páginas de detalhes do jogo
                        links = row.find_elements(By.TAG_NAME, 'a')
                        if links:
                            game_data['game_links'] = []
                            for link in links:
                                href = link.get_attribute('href')
                                if href and 'event.php' in href:
                                    game_data['game_links'].append({
                                        'href': href,
                                        'text': link.text.strip(),
                                        'game_id': self._extract_game_id(href)
                                    })
                        
                        games_found.append(game_data)
                        
                        if i <= 5:  # Log apenas os primeiros 5 jogos para não poluir
                            logging.info(f"🎮 Jogo {i}: {game_data['cell_contents'][:4]}")
                
                except Exception as e:
                    logging.warning(f"⚠️ Erro ao processar linha {i}: {e}")
            
            self.analysis_results['games_found'] = games_found
            self.analysis_results['table_structure'] = {
                'table_index': table_index,
                'total_rows': len(rows),
                'games_identified': len(games_found),
                'avg_cells_per_row': sum(g['cells_count'] for g in games_found) / len(games_found) if games_found else 0
            }
            
            logging.info(f"✅ Análise concluída: {len(games_found)} jogos identificados")
            
        except Exception as e:
            logging.error(f"❌ Erro ao analisar jogos na tabela: {e}")
    
    def analyze_navigation_elements(self):
        """Analisa elementos de navegação e filtros"""
        logging.info("🧭 Analisando elementos de navegação...")
        
        try:
            # Procurar por filtros, botões, dropdowns
            selects = self.driver.find_elements(By.TAG_NAME, 'select')
            buttons = self.driver.find_elements(By.TAG_NAME, 'button')
            inputs = self.driver.find_elements(By.TAG_NAME, 'input')
            
            navigation_info = {
                'select_elements': len(selects),
                'button_elements': len(buttons),
                'input_elements': len(inputs),
                'filters_found': [],
                'refresh_mechanisms': []
            }
            
            # Analisar selects (provavelmente filtros)
            for select in selects:
                try:
                    options = select.find_elements(By.TAG_NAME, 'option')
                    select_info = {
                        'id': select.get_attribute('id'),
                        'name': select.get_attribute('name'),
                        'options_count': len(options),
                        'options_sample': [opt.text.strip() for opt in options[:5]]  # Primeiras 5 opções
                    }
                    navigation_info['filters_found'].append(select_info)
                except Exception as e:
                    logging.warning(f"⚠️ Erro ao analisar select: {e}")
            
            # Procurar por mecanismos de refresh/atualização
            refresh_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'refresh') or contains(text(), 'update') or contains(text(), 'reload')]")
            for elem in refresh_elements:
                navigation_info['refresh_mechanisms'].append({
                    'tag': elem.tag_name,
                    'text': elem.text.strip(),
                    'class': elem.get_attribute('class')
                })
            
            self.analysis_results['navigation_elements'] = navigation_info
            logging.info(f"🧭 Navegação analisada: {len(selects)} filtros, {len(buttons)} botões")
            
        except Exception as e:
            logging.error(f"❌ Erro ao analisar navegação: {e}")
    
    def generate_recommendations(self):
        """Gera recomendações para o sistema 2.0"""
        logging.info("💡 Gerando recomendações...")
        
        recommendations = []
        
        # Baseado na análise dos jogos
        games_count = len(self.analysis_results.get('games_found', []))
        if games_count > 0:
            recommendations.append({
                'category': 'data_extraction',
                'priority': 'high',
                'title': 'Implementar extrator de jogos ao vivo',
                'description': f'Foram identificados {games_count} jogos na página. Criar módulo para extrair dados em tempo real.',
                'implementation': 'Criar classe LiveGamesExtractor com método get_live_games()'
            })
        
        # Baseado na estrutura da tabela
        if self.analysis_results.get('table_structure', {}).get('avg_cells_per_row', 0) > 5:
            recommendations.append({
                'category': 'data_parsing',
                'priority': 'high',
                'title': 'Parser estruturado para dados de jogos',
                'description': 'Tabela com múltiplas colunas requer parser robusto para extrair informações específicas.',
                'implementation': 'Criar GameDataParser com mapeamento de colunas configurável'
            })
        
        # Baseado nos elementos de navegação
        filters_count = len(self.analysis_results.get('navigation_elements', {}).get('filters_found', []))
        if filters_count > 0:
            recommendations.append({
                'category': 'filtering',
                'priority': 'medium',
                'title': 'Sistema de filtros dinâmicos',
                'description': f'Encontrados {filters_count} filtros na página. Implementar sistema para aplicar filtros automaticamente.',
                'implementation': 'Criar FilterManager para gerenciar filtros de país, liga, etc.'
            })
        
        # Recomendações arquiteturais
        recommendations.extend([
            {
                'category': 'architecture',
                'priority': 'high',
                'title': 'Arquitetura modular baseada em eventos',
                'description': 'Implementar sistema baseado em eventos para monitoramento contínuo.',
                'implementation': 'Padrão Observer com EventBus para comunicação entre módulos'
            },
            {
                'category': 'performance',
                'priority': 'medium',
                'title': 'Cache inteligente de dados',
                'description': 'Implementar cache para evitar requisições desnecessárias.',
                'implementation': 'Redis ou cache em memória com TTL configurável'
            },
            {
                'category': 'monitoring',
                'priority': 'high',
                'title': 'Sistema de monitoramento em tempo real',
                'description': 'Monitorar mudanças na página e detectar novos jogos automaticamente.',
                'implementation': 'WebSocket ou polling inteligente com detecção de mudanças'
            }
        ])
        
        self.analysis_results['recommendations'] = recommendations
        logging.info(f"💡 {len(recommendations)} recomendações geradas")
    
    def _find_main_containers(self, soup):
        """Identifica os principais containers da página"""
        containers = []
        
        # Procurar por divs com IDs ou classes relevantes
        main_divs = soup.find_all('div', {'id': True}) + soup.find_all('div', {'class': True})
        
        for div in main_divs[:10]:  # Limitar a 10 para não poluir
            container_info = {
                'tag': div.name,
                'id': div.get('id'),
                'class': div.get('class'),
                'children_count': len(div.find_all())
            }
            containers.append(container_info)
        
        return containers
    
    def _check_for_score_pattern(self, text):
        """Verifica se o texto contém padrão de placar (ex: 1:0, 2-1)"""
        import re
        score_patterns = [r'\d+:\d+', r'\d+-\d+', r'\d+ - \d+']
        return any(re.search(pattern, text) for pattern in score_patterns)
    
    def _extract_game_id(self, href):
        """Extrai ID do jogo da URL"""
        import re
        match = re.search(r'id=(\d+)', href)
        return match.group(1) if match else None
    
    def save_analysis_results(self):
        """Salva os resultados da análise em arquivo JSON"""
        filename = f"live_page_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.analysis_results, f, indent=2, ensure_ascii=False)
            logging.info(f"💾 Análise salva em: {filename}")
            return filename
        except Exception as e:
            logging.error(f"❌ Erro ao salvar análise: {e}")
            return None
    
    def run_complete_analysis(self):
        """Executa análise completa da página"""
        logging.info("🚀 Iniciando análise completa da página live")
        
        try:
            if not self.setup_driver():
                return None
            
            # Executar todas as análises
            self.analyze_page_structure()
            self.analyze_games_table()
            self.analyze_navigation_elements()
            self.generate_recommendations()
            
            # Salvar resultados
            filename = self.save_analysis_results()
            
            # Exibir resumo
            self.display_summary()
            
            return self.analysis_results
            
        except Exception as e:
            logging.error(f"❌ Erro durante análise: {e}")
            return None
        
        finally:
            if self.driver:
                self.driver.quit()
                logging.info("🔒 Driver fechado")
    
    def display_summary(self):
        """Exibe resumo da análise"""
        print("\n" + "="*80)
        print("📋 RESUMO DA ANÁLISE - PÁGINA LIVE")
        print("="*80)
        
        # Informações básicas
        print(f"\n🌐 URL analisada: {self.url}")
        print(f"⏰ Timestamp: {self.analysis_results['timestamp']}")
        
        # Estrutura da página
        structure = self.analysis_results.get('page_structure', {})
        print(f"\n📊 ESTRUTURA DA PÁGINA:")
        print(f"   • Título: {structure.get('title', 'N/A')}")
        print(f"   • Tabelas encontradas: {structure.get('tables_found', 0)}")
        print(f"   • Formulários: {structure.get('forms_found', 0)}")
        print(f"   • Scripts: {structure.get('scripts_found', 0)}")
        
        # Jogos encontrados
        games_count = len(self.analysis_results.get('games_found', []))
        table_info = self.analysis_results.get('table_structure', {})
        print(f"\n🏆 JOGOS IDENTIFICADOS:")
        print(f"   • Total de jogos: {games_count}")
        print(f"   • Linhas na tabela: {table_info.get('total_rows', 0)}")
        print(f"   • Média de colunas por linha: {table_info.get('avg_cells_per_row', 0):.1f}")
        
        # Elementos de navegação
        nav_info = self.analysis_results.get('navigation_elements', {})
        print(f"\n🧭 NAVEGAÇÃO:")
        print(f"   • Filtros (selects): {nav_info.get('select_elements', 0)}")
        print(f"   • Botões: {nav_info.get('button_elements', 0)}")
        print(f"   • Inputs: {nav_info.get('input_elements', 0)}")
        
        # Recomendações principais
        recommendations = self.analysis_results.get('recommendations', [])
        high_priority = [r for r in recommendations if r.get('priority') == 'high']
        print(f"\n💡 RECOMENDAÇÕES PRINCIPAIS ({len(high_priority)} de alta prioridade):")
        for i, rec in enumerate(high_priority[:5], 1):
            print(f"   {i}. {rec.get('title', 'N/A')} [{rec.get('category', 'N/A')}]")
        
        print("\n" + "="*80)

def main():
    """Função principal"""
    print("🔍 Analisador da Página Live - Sistema 2.0")
    print("Analisando: https://dropping-odds.com/index.php?view=live")
    print("="*60)
    
    analyzer = LivePageAnalyzer()
    results = analyzer.run_complete_analysis()
    
    if results:
        print("\n✅ Análise concluída com sucesso!")
        print("\n📋 Próximos passos recomendados:")
        print("   1. Revisar arquivo JSON gerado com análise detalhada")
        print("   2. Implementar módulos baseados nas recomendações")
        print("   3. Criar testes para validar extração de dados")
        print("   4. Desenvolver sistema de monitoramento contínuo")
    else:
        print("❌ Análise falhou. Verifique os logs para mais detalhes.")

if __name__ == "__main__":
    main()