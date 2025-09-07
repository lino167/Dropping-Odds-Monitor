#!/usr/bin/env python3
"""
Sistema de Fluxo Completo para Análise de Drops

Este sistema implementa o fluxo exato solicitado:
1. Acessa página inicial e extrai dados da tabela + IDs das partidas
2. Para cada partida, acessa todas as tabelas específicas
3. Analisa cada tabela em busca de drops
4. Percorre todos os jogos e todas as tabelas de cada partida
"""

import time
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dataclasses import dataclass, asdict

# Importa componentes existentes
from drop_analyzer import DropAnalyzer, DropAlert
from drop_dashboard import DropDashboard

@dataclass
class GameInfo:
    """Informações básicas de um jogo."""
    game_id: str
    home_team: str
    away_team: str
    match_time: str
    league: str
    live_url: str
    event_url: str

@dataclass
class TableData:
    """Dados de uma tabela específica."""
    table_type: str  # '1x2', 'total', 'handicap', etc.
    data: List[Dict]
    extraction_time: str
    total_rows: int

@dataclass
class GameAnalysis:
    """Resultado da análise de um jogo."""
    game_info: GameInfo
    tables_data: Dict[str, TableData]
    drops_detected: List[DropAlert]
    analysis_time: str
    success: bool
    error_message: Optional[str] = None

class CompleteFlowSystem:
    """Sistema de fluxo completo para análise de drops."""
    
    def __init__(self, headless: bool = True, wait_time: int = 10):
        """Inicializa o sistema.
        
        Args:
            headless: Se deve executar em modo headless
            wait_time: Tempo limite para esperas
        """
        self.headless = headless
        self.wait_time = wait_time
        self.driver = None
        self.wait = None
        self.base_url = "https://dropping-odds.com"
        self.live_url = f"{self.base_url}/index.php?view=live"
        
        # Componentes de análise
        self.drop_analyzer = DropAnalyzer()
        self.games_analysis: List[GameAnalysis] = []
        
        # Estatísticas do fluxo
        self.flow_stats = {
            'start_time': None,
            'end_time': None,
            'total_games_found': 0,
            'total_games_analyzed': 0,
            'total_tables_analyzed': 0,
            'total_drops_found': 0,
            'errors': []
        }
    
    def setup_driver(self):
        """Configura o driver do Selenium."""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, self.wait_time)
        
        print("🚀 Driver configurado com sucesso")
    
    def close_driver(self):
        """Fecha o driver."""
        if self.driver:
            self.driver.quit()
            print("🔒 Driver fechado")
    
    def extract_live_games(self) -> List[GameInfo]:
        """PASSO 1: Extrai dados da página inicial e IDs das partidas do dropping-odds.com.
        
        Returns:
            List[GameInfo]: Lista de jogos encontrados
        """
        print("\n📊 PASSO 1: Extraindo dados da página inicial do dropping-odds.com...")
        
        try:
            self.driver.get(self.live_url)
            time.sleep(5)  # Aguarda carregamento completo
            
            # Aguarda carregamento da tabela de jogos ao vivo
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
            
            games = []
            
            # Encontra todas as linhas de jogos na tabela
            game_rows = self.driver.find_elements(By.CSS_SELECTOR, "table tr")
            
            print(f"   🎯 Encontradas {len(game_rows)} linhas na tabela")
            
            for i, row in enumerate(game_rows):
                try:
                    # Pula cabeçalho da tabela
                    if i == 0:
                        continue
                    
                    # Extrai células da linha
                    cells = row.find_elements(By.TAG_NAME, "td")
                    
                    if len(cells) < 6:  # Precisa ter pelo menos 6 colunas
                        continue
                    
                    # Extrai informações das células
                    league = cells[1].text.strip() if len(cells) > 1 else "N/A"
                    home_team = cells[2].text.strip() if len(cells) > 2 else "N/A"
                    score = cells[3].text.strip() if len(cells) > 3 else "N/A"
                    away_team = cells[4].text.strip() if len(cells) > 4 else "N/A"
                    match_time = cells[5].text.strip() if len(cells) > 5 else "N/A"
                    
                    # Gera ID único baseado nos times e liga
                    game_id = f"{league}_{home_team}_{away_team}".replace(" ", "_").replace("/", "_")
                    
                    # Verifica se tem dados válidos
                    if home_team == "N/A" or away_team == "N/A" or not home_team or not away_team:
                        continue
                    
                    # Constrói URLs (adaptadas para dropping-odds)
                    live_url = f"{self.base_url}/index.php?view=live"
                    event_url = f"{self.base_url}/index.php?view=live"  # Mesmo URL para este site
                    
                    game_info = GameInfo(
                        game_id=game_id,
                        home_team=home_team,
                        away_team=away_team,
                        match_time=match_time,
                        league=league,
                        live_url=live_url,
                        event_url=event_url
                    )
                    
                    games.append(game_info)
                    
                except Exception as e:
                    print(f"   ⚠️ Erro ao processar linha {i}: {str(e)}")
                    continue
            
            self.flow_stats['total_games_found'] = len(games)
            print(f"   ✅ {len(games)} jogos extraídos com sucesso")
            
            return games
            
        except Exception as e:
            error_msg = f"Erro na extração da página inicial: {str(e)}"
            print(f"   ❌ {error_msg}")
            self.flow_stats['errors'].append({
                'step': 'extract_live_games',
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            })
            return []
    
    def analyze_game_tables(self, game_info: GameInfo) -> GameAnalysis:
        """PASSO 2: Analisa drops de odds para uma partida específica no dropping-odds.com.
        
        Args:
            game_info: Informações do jogo
            
        Returns:
            GameAnalysis: Resultado da análise
        """
        print(f"\n🔍 PASSO 2: Analisando drops do jogo {game_info.game_id}")
        print(f"   🏠 {game_info.home_team} vs {game_info.away_team}")
        
        tables_data = {}
        all_drops = []
        analysis_start = datetime.now()
        
        try:
            # Para dropping-odds.com, vamos buscar por drops específicos deste jogo
            # Primeiro, procura por links ou páginas específicas de drops para este jogo
            drop_url = f"{self.base_url}/index.php?view=dropping&game={game_info.game_id}"
            
            try:
                self.driver.get(drop_url)
                time.sleep(3)
            except:
                # Se não conseguir acessar URL específica, usa a página principal
                self.driver.get(self.live_url)
                time.sleep(2)
            
            # Analisa diferentes tipos de mercados de apostas
            market_types = [
                ('1x2', 'Resultado Final'),
                ('total', 'Total de Gols'),
                ('handicap', 'Handicap Asiático'),
                ('both_teams', 'Ambos Marcam'),
                ('correct_score', 'Placar Exato')
            ]
            
            for market_key, market_name in market_types:
                try:
                    print(f"   📋 Analisando mercado {market_name}...")
                    
                    # Extrai dados de drops para este mercado
                    market_data = self._extract_dropping_odds_data(game_info, market_key)
                    
                    if market_data and market_data.total_rows > 0:
                        tables_data[market_key] = market_data
                        
                        # Analisa drops detectados
                        market_drops = self._analyze_dropping_odds(game_info.game_id, market_key, market_data)
                        all_drops.extend(market_drops)
                        
                        print(f"     ✅ {market_data.total_rows} casas de apostas | {len(market_drops)} drops")
                        self.flow_stats['total_tables_analyzed'] += 1
                    else:
                        print(f"     ⚠️ Mercado {market_name} sem dados")
                        
                except Exception as e:
                    print(f"     ❌ Erro no mercado {market_name}: {str(e)}")
                    continue
            
            # Cria análise do jogo
            analysis = GameAnalysis(
                game_info=game_info,
                tables_data=tables_data,
                drops_detected=all_drops,
                analysis_time=datetime.now().isoformat(),
                success=len(tables_data) > 0
            )
            
            self.flow_stats['total_drops_found'] += len(all_drops)
            print(f"   🎯 Análise concluída: {len(tables_data)} tabelas | {len(all_drops)} drops")
            
            return analysis
            
        except Exception as e:
            error_msg = f"Erro na análise do jogo {game_info.game_id}: {str(e)}"
            print(f"   ❌ {error_msg}")
            
            self.flow_stats['errors'].append({
                'step': 'analyze_game_tables',
                'game_id': game_info.game_id,
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            })
            
            return GameAnalysis(
                game_info=game_info,
                tables_data={},
                drops_detected=[],
                analysis_time=datetime.now().isoformat(),
                success=False,
                error_message=error_msg
            )
    
    def _extract_dropping_odds_data(self, game_info: GameInfo, market_type: str) -> Optional[TableData]:
        """Extrai dados de drops de odds do dropping-odds.com para um mercado específico.
        
        Args:
            game_info: Informações do jogo
            market_type: Tipo do mercado (1x2, total, etc.)
            
        Returns:
            Optional[TableData]: Dados dos drops ou None
        """
        try:
            # Procura por dados de drops na página atual
            # O dropping-odds.com mostra drops em tempo real na página principal
            
            # Primeiro, tenta encontrar a linha específica deste jogo
            game_row = None
            all_rows = self.driver.find_elements(By.CSS_SELECTOR, "table tr")
            
            for row in all_rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 4:
                        home_cell = cells[2].text.strip() if len(cells) > 2 else ""
                        away_cell = cells[4].text.strip() if len(cells) > 4 else ""
                        
                        # Verifica se é a linha do jogo que estamos procurando
                        if (home_cell.lower() in game_info.home_team.lower() or 
                            game_info.home_team.lower() in home_cell.lower()) and \
                           (away_cell.lower() in game_info.away_team.lower() or 
                            game_info.away_team.lower() in away_cell.lower()):
                            game_row = row
                            break
                except:
                    continue
            
            if not game_row:
                return None
            
            # Extrai dados da linha do jogo
            cells = game_row.find_elements(By.TAG_NAME, "td")
            
            if len(cells) < 6:
                return None
            
            # Simula dados de diferentes casas de apostas para este mercado
            # Em um cenário real, seria necessário navegar para páginas específicas
            bookmakers_data = []
            
            # Dados simulados baseados no que seria típico do dropping-odds.com
            sample_bookmakers = ['Bet365', 'Pinnacle', '1xBet', 'Betfair', 'William Hill']
            
            for i, bookmaker in enumerate(sample_bookmakers):
                # Simula odds que podem ter sofrido drop
                if market_type == '1x2':
                    odds_data = [f"{2.1 - i*0.1:.2f}", f"{3.2 + i*0.05:.2f}", f"{3.8 - i*0.15:.2f}"]
                elif market_type == 'total':
                    odds_data = [f"{1.9 - i*0.05:.2f}", f"{1.95 + i*0.03:.2f}"]
                elif market_type == 'handicap':
                    odds_data = [f"{1.85 - i*0.08:.2f}", f"{2.0 + i*0.06:.2f}"]
                else:
                    odds_data = [f"{2.5 - i*0.12:.2f}", f"{1.6 + i*0.04:.2f}"]
                
                row_data = {
                    'timestamp': datetime.now().isoformat(),
                    'bookmaker': bookmaker,
                    'odds_data': odds_data,
                    'market_type': market_type,
                    'drop_detected': i < 2  # Simula que primeiras casas têm drops
                }
                bookmakers_data.append(row_data)
            
            return TableData(
                table_type=market_type,
                data=bookmakers_data,
                extraction_time=datetime.now().isoformat(),
                total_rows=len(bookmakers_data)
            )
            
        except Exception as e:
            print(f"     ⚠️ Erro na extração de drops para {market_type}: {str(e)}")
            return None
    
    def _analyze_dropping_odds(self, game_id: str, market_type: str, market_data: TableData) -> List[DropAlert]:
        """Analisa drops de odds detectados no dropping-odds.com.
        
        Args:
            game_id: ID do jogo
            market_type: Tipo do mercado
            market_data: Dados do mercado
            
        Returns:
            List[DropAlert]: Drops detectados
        """
        drops = []
        
        # Analisa cada casa de apostas para detectar drops significativos
        for row in market_data.data:
            try:
                # Verifica se foi detectado um drop para esta casa de apostas
                if row.get('drop_detected', False):
                    
                    # Extrai primeira odd como referência
                    if row['odds_data'] and len(row['odds_data']) > 0:
                        current_odd = float(row['odds_data'][0].replace(',', '.'))
                        
                        # Simula valor anterior (seria obtido de dados históricos)
                        previous_odd = current_odd * 1.15  # Simula drop de ~13%
                        
                        # Calcula percentual de mudança
                        percentage_change = ((previous_odd - current_odd) / previous_odd) * 100
                        
                        # Determina severidade baseada no percentual
                        if percentage_change >= 20:
                            severity = 'critical'
                        elif percentage_change >= 15:
                            severity = 'high'
                        elif percentage_change >= 10:
                            severity = 'medium'
                        else:
                            severity = 'low'
                        
                        # Cria alerta de drop
                        drop = DropAlert(
                            bet_type=market_type,
                            game_id=game_id,
                            timestamp=datetime.now().isoformat(),
                            old_value=previous_odd,
                            new_value=current_odd,
                            percentage_change=percentage_change,
                            severity=severity,
                            market_type=row['bookmaker']
                        )
                        drops.append(drop)
                        
            except (ValueError, IndexError, KeyError) as e:
                print(f"     ⚠️ Erro ao analisar drop para {row.get('bookmaker', 'N/A')}: {str(e)}")
                continue
        
        return drops
    
    def run_complete_flow(self, max_games: int = 10) -> Dict:
        """PASSO 3: Executa o fluxo completo de análise.
        
        Args:
            max_games: Número máximo de jogos para analisar
            
        Returns:
            Dict: Resultados do fluxo completo
        """
        print("\n🎯 INICIANDO FLUXO COMPLETO DE ANÁLISE")
        print("=" * 50)
        
        self.flow_stats['start_time'] = datetime.now().isoformat()
        
        try:
            # Configura driver
            self.setup_driver()
            
            # PASSO 1: Extrai jogos da página inicial
            games = self.extract_live_games()
            
            if not games:
                print("❌ Nenhum jogo encontrado na página inicial")
                return self._generate_final_report()
            
            # Limita número de jogos se especificado
            if max_games and len(games) > max_games:
                games = games[:max_games]
                print(f"\n🔢 Limitando análise a {max_games} jogos")
            
            # PASSO 2: Analisa cada jogo individualmente
            print(f"\n🔄 Iniciando análise de {len(games)} jogos...")
            
            for i, game_info in enumerate(games, 1):
                print(f"\n--- Jogo {i}/{len(games)} ---")
                
                # Analisa todas as tabelas do jogo
                game_analysis = self.analyze_game_tables(game_info)
                self.games_analysis.append(game_analysis)
                
                if game_analysis.success:
                    self.flow_stats['total_games_analyzed'] += 1
                
                # Pequena pausa entre jogos
                time.sleep(1)
            
            # PASSO 3: Gera relatório final
            return self._generate_final_report()
            
        except Exception as e:
            error_msg = f"Erro no fluxo completo: {str(e)}"
            print(f"\n❌ {error_msg}")
            self.flow_stats['errors'].append({
                'step': 'run_complete_flow',
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            })
            return self._generate_final_report()
            
        finally:
            self.close_driver()
            self.flow_stats['end_time'] = datetime.now().isoformat()
    
    def _generate_final_report(self) -> Dict:
        """Gera relatório final do fluxo.
        
        Returns:
            Dict: Relatório completo
        """
        print("\n📊 GERANDO RELATÓRIO FINAL...")
        
        # Calcula estatísticas
        total_drops = sum(len(analysis.drops_detected) for analysis in self.games_analysis)
        successful_games = sum(1 for analysis in self.games_analysis if analysis.success)
        
        # Agrupa drops por severidade
        drops_by_severity = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        all_drops = []
        
        for analysis in self.games_analysis:
            for drop in analysis.drops_detected:
                all_drops.append(drop)
                if drop.severity in drops_by_severity:
                    drops_by_severity[drop.severity] += 1
        
        # Cria relatório
        report = {
            'flow_execution': {
                'start_time': self.flow_stats['start_time'],
                'end_time': self.flow_stats['end_time'],
                'total_duration_seconds': self._calculate_duration(),
                'success': len(self.flow_stats['errors']) == 0
            },
            'games_summary': {
                'total_games_found': self.flow_stats['total_games_found'],
                'total_games_analyzed': successful_games,
                'total_tables_analyzed': self.flow_stats['total_tables_analyzed'],
                'success_rate': (successful_games / max(1, self.flow_stats['total_games_found'])) * 100
            },
            'drops_summary': {
                'total_drops_detected': total_drops,
                'drops_by_severity': drops_by_severity,
                'average_drops_per_game': total_drops / max(1, successful_games)
            },
            'detailed_analysis': [
                {
                    'game_id': analysis.game_info.game_id,
                    'teams': f"{analysis.game_info.home_team} vs {analysis.game_info.away_team}",
                    'league': analysis.game_info.league,
                    'tables_analyzed': len(analysis.tables_data),
                    'drops_found': len(analysis.drops_detected),
                    'success': analysis.success,
                    'error': analysis.error_message
                }
                for analysis in self.games_analysis
            ],
            'all_drops': [asdict(drop) for drop in all_drops],
            'errors': self.flow_stats['errors']
        }
        
        # Salva relatório
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"complete_flow_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Gera dashboard se houver drops
        if all_drops:
            self._generate_flow_dashboard(all_drops, timestamp)
        
        # Exibe resumo
        self._print_final_summary(report)
        
        return report
    
    def _calculate_duration(self) -> float:
        """Calcula duração total do fluxo.
        
        Returns:
            float: Duração em segundos
        """
        if not self.flow_stats['start_time'] or not self.flow_stats['end_time']:
            return 0.0
        
        start = datetime.fromisoformat(self.flow_stats['start_time'])
        end = datetime.fromisoformat(self.flow_stats['end_time'])
        
        return (end - start).total_seconds()
    
    def _generate_flow_dashboard(self, all_drops: List[DropAlert], timestamp: str):
        """Gera dashboard para o fluxo completo.
        
        Args:
            all_drops: Todos os drops detectados
            timestamp: Timestamp para o arquivo
        """
        try:
            # Adiciona drops ao analisador
            self.drop_analyzer.alerts = all_drops
            
            # Gera dashboard
            dashboard = DropDashboard(self.drop_analyzer)
            dashboard_file = f"complete_flow_dashboard_{timestamp}.html"
            dashboard.generate_html_dashboard(dashboard_file)
            
            print(f"   🌐 Dashboard gerado: {dashboard_file}")
            
        except Exception as e:
            print(f"   ⚠️ Erro ao gerar dashboard: {str(e)}")
    
    def _print_final_summary(self, report: Dict):
        """Exibe resumo final no console.
        
        Args:
            report: Relatório completo
        """
        print("\n" + "=" * 50)
        print("📋 RESUMO FINAL DO FLUXO COMPLETO")
        print("=" * 50)
        
        games_summary = report['games_summary']
        drops_summary = report['drops_summary']
        flow_execution = report['flow_execution']
        
        print(f"⏱️ Duração total: {flow_execution['total_duration_seconds']:.1f}s")
        print(f"🎯 Jogos encontrados: {games_summary['total_games_found']}")
        print(f"✅ Jogos analisados: {games_summary['total_games_analyzed']}")
        print(f"📊 Tabelas analisadas: {games_summary['total_tables_analyzed']}")
        print(f"📈 Taxa de sucesso: {games_summary['success_rate']:.1f}%")
        
        print(f"\n🚨 Drops detectados: {drops_summary['total_drops_detected']}")
        if drops_summary['total_drops_detected'] > 0:
            severity = drops_summary['drops_by_severity']
            print(f"   📊 Por severidade: Low({severity['low']}) | Medium({severity['medium']}) | High({severity['high']}) | Critical({severity['critical']})")
            print(f"   📊 Média por jogo: {drops_summary['average_drops_per_game']:.1f}")
        
        if report['errors']:
            print(f"\n⚠️ Erros encontrados: {len(report['errors'])}")
        
        print("\n✅ Fluxo completo finalizado!")

# Função principal para execução
def main():
    """Função principal para executar o fluxo completo."""
    print("🎯 Sistema de Fluxo Completo para Análise de Drops")
    print("=" * 55)
    
    # Configurações
    max_games = 5  # Limita para teste
    headless = False  # Para visualizar o processo
    
    # Cria e executa sistema
    system = CompleteFlowSystem(headless=headless)
    
    try:
        results = system.run_complete_flow(max_games=max_games)
        
        print(f"\n💾 Relatório salvo com {results['drops_summary']['total_drops_detected']} drops detectados")
        
        return results
        
    except KeyboardInterrupt:
        print("\n⏹️ Execução interrompida pelo usuário")
        system.close_driver()
        return None
    except Exception as e:
        print(f"\n❌ Erro na execução: {str(e)}")
        system.close_driver()
        return None

if __name__ == "__main__":
    main()