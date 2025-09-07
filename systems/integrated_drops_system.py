#!/usr/bin/env python3
"""
Sistema Integrado de Detecção de Drops

Este sistema combina:
1. Extração de dados ao vivo do dropping-odds.com
2. Algoritmos avançados de detecção de drops
3. Dashboard unificado que mostra apenas jogos com drops reais
4. Persistência de dados para análise histórica
5. Sistema de alertas em tempo real
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import statistics

@dataclass
class GameData:
    """Dados de um jogo extraído do dropping-odds.com"""
    game_id: str
    home_team: str
    away_team: str
    league: str
    score: str
    game_time: str
    status: str
    odds_1x2: Dict[str, float]
    timestamp: str
    url: str = ""

@dataclass
class DropAlert:
    """Alerta de drop detectado"""
    game_id: str
    bet_type: str
    market_type: str
    old_value: float
    new_value: float
    percentage_change: float
    severity: str
    timestamp: str
    game_info: GameData

class IntegratedDropsSystem:
    """Sistema integrado de detecção de drops"""
    
    def __init__(self):
        self.base_url = "https://dropping-odds.com"
        self.live_url = f"{self.base_url}/index.php?view=live"
        self.driver = None
        self.historical_data = {}
        self.current_games = {}
        self.detected_drops = []
        self.data_file = "integrated_drops_data.json"
        self.html_file = "integrated_drops_dashboard.html"
        
        # Configurações de detecção de drops
        self.drop_config = {
            'thresholds': {
                'low': 5.0,      # 5% de mudança
                'medium': 10.0,   # 10% de mudança
                'high': 20.0,     # 20% de mudança
                'critical': 30.0  # 30% de mudança
            },
            'min_odds_value': 1.01,
            'max_odds_value': 50.0,
            'min_time_between_checks': 60  # segundos
        }
        
    def setup_driver(self):
        """Configura o driver do Selenium"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            print("✅ Driver configurado com sucesso")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao configurar driver: {e}")
            return False
    
    def extract_live_games(self) -> List[GameData]:
        """Extrai jogos ao vivo do dropping-odds.com"""
        if not self.driver:
            if not self.setup_driver():
                return []
        
        try:
            print(f"🌐 Acessando {self.live_url}...")
            self.driver.get(self.live_url)
            time.sleep(3)
            
            games = []
            timestamp = datetime.now().isoformat()
            
            # Procura pela tabela principal de jogos
            try:
                table = self.driver.find_element(By.CSS_SELECTOR, "table")
                rows = table.find_elements(By.TAG_NAME, "tr")
                
                for i, row in enumerate(rows[1:], 1):  # Pula cabeçalho
                    try:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 6:
                            # Extrai dados básicos
                            country = cells[0].text.strip()
                            league = cells[1].text.strip()
                            home_team = cells[2].text.strip()
                            score = cells[3].text.strip()
                            away_team = cells[4].text.strip()
                            game_time = cells[5].text.strip()
                            
                            if home_team and away_team:
                                game_id = f"{country}_{league}_{home_team}_{away_team}".replace(" ", "_")
                                
                                # Tenta extrair odds se disponíveis
                                odds_1x2 = self._extract_odds_from_row(row)
                                
                                game_data = GameData(
                                    game_id=game_id,
                                    home_team=home_team,
                                    away_team=away_team,
                                    league=f"{country} - {league}",
                                    score=score,
                                    game_time=game_time,
                                    status="live" if ":" in game_time else "finished",
                                    odds_1x2=odds_1x2,
                                    timestamp=timestamp
                                )
                                
                                games.append(game_data)
                                print(f"Jogo extraído: {home_team} vs {away_team} ({league}) - {score} - {game_time}")
                                
                    except Exception as e:
                        print(f"⚠️ Erro ao processar linha {i}: {e}")
                        continue
                        
            except Exception as e:
                print(f"❌ Erro ao encontrar tabela: {e}")
                return []
            
            print(f"✅ Total de jogos extraídos: {len(games)}")
            return games
            
        except Exception as e:
            print(f"❌ Erro ao extrair jogos: {e}")
            return []
    
    def _extract_odds_from_row(self, row) -> Dict[str, float]:
        """Extrai odds de uma linha da tabela (se disponíveis)"""
        odds = {'1': 0.0, 'X': 0.0, '2': 0.0}
        
        try:
            # Procura por elementos com odds na linha
            odds_elements = row.find_elements(By.CSS_SELECTOR, "[data-odd], .odd, .odds")
            
            for i, element in enumerate(odds_elements[:3]):
                try:
                    odd_text = element.text.strip()
                    if odd_text and odd_text.replace('.', '').replace(',', '').isdigit():
                        odd_value = float(odd_text.replace(',', '.'))
                        if 1.01 <= odd_value <= 50.0:
                            if i == 0:
                                odds['1'] = odd_value
                            elif i == 1:
                                odds['X'] = odd_value
                            elif i == 2:
                                odds['2'] = odd_value
                except:
                    continue
                    
        except Exception as e:
            print(f"⚠️ Erro ao extrair odds: {e}")
            
        return odds
    
    def detect_drops(self, current_games: List[GameData]) -> List[DropAlert]:
        """Detecta drops comparando com dados históricos"""
        drops_detected = []
        
        for current_game in current_games:
            game_id = current_game.game_id
            
            # Verifica se temos dados históricos para este jogo
            if game_id in self.historical_data:
                previous_data = self.historical_data[game_id]
                
                # Analisa mudanças nas odds 1x2
                for bet_type in ['1', 'X', '2']:
                    if (bet_type in current_game.odds_1x2 and 
                        bet_type in previous_data.odds_1x2 and
                        current_game.odds_1x2[bet_type] > 0 and
                        previous_data.odds_1x2[bet_type] > 0):
                        
                        current_odd = current_game.odds_1x2[bet_type]
                        previous_odd = previous_data.odds_1x2[bet_type]
                        
                        # Calcula percentual de mudança
                        percentage_change = ((previous_odd - current_odd) / previous_odd) * 100
                        
                        # Verifica se é um drop significativo
                        if abs(percentage_change) >= self.drop_config['thresholds']['low']:
                            severity = self._calculate_severity(abs(percentage_change))
                            
                            drop_alert = DropAlert(
                                game_id=game_id,
                                bet_type=bet_type,
                                market_type='1x2',
                                old_value=previous_odd,
                                new_value=current_odd,
                                percentage_change=percentage_change,
                                severity=severity,
                                timestamp=current_game.timestamp,
                                game_info=current_game
                            )
                            
                            drops_detected.append(drop_alert)
                            print(f"🚨 Drop detectado: {current_game.home_team} vs {current_game.away_team} - {bet_type}: {previous_odd:.2f} → {current_odd:.2f} ({percentage_change:+.1f}%)")
            
            # Atualiza dados históricos
            self.historical_data[game_id] = current_game
        
        return drops_detected
    
    def _calculate_severity(self, percentage: float) -> str:
        """Calcula severidade do drop baseado no percentual"""
        thresholds = self.drop_config['thresholds']
        
        if percentage >= thresholds['critical']:
            return 'critical'
        elif percentage >= thresholds['high']:
            return 'high'
        elif percentage >= thresholds['medium']:
            return 'medium'
        else:
            return 'low'
    
    def save_data(self, games: List[GameData], drops: List[DropAlert]):
        """Salva dados em arquivo JSON"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'games_count': len(games),
            'drops_count': len(drops),
            'games': [asdict(game) for game in games],
            'drops': [asdict(drop) for drop in drops],
            'summary': {
                'total_games': len(games),
                'games_with_drops': len(set(drop.game_id for drop in drops)),
                'total_drops': len(drops),
                'drops_by_severity': {
                    'critical': len([d for d in drops if d.severity == 'critical']),
                    'high': len([d for d in drops if d.severity == 'high']),
                    'medium': len([d for d in drops if d.severity == 'medium']),
                    'low': len([d for d in drops if d.severity == 'low'])
                }
            }
        }
        
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"💾 Dados salvos: {self.data_file}")
        except Exception as e:
            print(f"❌ Erro ao salvar dados: {e}")
    
    def generate_dashboard(self, games: List[GameData], drops: List[DropAlert]):
        """Gera dashboard HTML mostrando apenas jogos com drops"""
        
        # Agrupa drops por jogo
        drops_by_game = {}
        for drop in drops:
            if drop.game_id not in drops_by_game:
                drops_by_game[drop.game_id] = []
            drops_by_game[drop.game_id].append(drop)
        
        # Filtra apenas jogos com drops
        games_with_drops = [game for game in games if game.game_id in drops_by_game]
        
        html_content = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Integrado - Jogos com Drops Detectados</title>
    <meta http-equiv="refresh" content="300">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1600px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            text-align: center;
        }}
        
        .header h1 {{
            color: #2c3e50;
            font-size: 2.8em;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }}
        
        .stat-card:hover {{ transform: translateY(-5px); }}
        
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        .games-count {{ color: #3498db; }}
        .drops-count {{ color: #e74c3c; }}
        .critical-count {{ color: #c0392b; }}
        .high-count {{ color: #e67e22; }}
        
        .stat-label {{
            color: #7f8c8d;
            font-size: 1.1em;
            font-weight: 500;
        }}
        
        .games-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }}
        
        .game-card {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
            border-left: 5px solid #e74c3c;
        }}
        
        .game-card:hover {{ transform: translateY(-5px); }}
        
        .game-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        
        .game-title {{
            font-size: 1.3em;
            font-weight: bold;
            color: #2c3e50;
        }}
        
        .game-status {{
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
        }}
        
        .status-live {{
            background: #e74c3c;
            color: white;
        }}
        
        .status-finished {{
            background: #95a5a6;
            color: white;
        }}
        
        .game-info {{
            margin-bottom: 15px;
        }}
        
        .game-info div {{
            margin-bottom: 5px;
            color: #7f8c8d;
        }}
        
        .drops-section {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            margin-top: 15px;
        }}
        
        .drops-title {{
            font-weight: bold;
            color: #e74c3c;
            margin-bottom: 10px;
            font-size: 1.1em;
        }}
        
        .drop-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 12px;
            background: white;
            border-radius: 8px;
            margin-bottom: 8px;
            border-left: 4px solid #e74c3c;
        }}
        
        .drop-percentage {{
            font-weight: bold;
            padding: 4px 8px;
            border-radius: 15px;
            color: white;
        }}
        
        .severity-critical {{ background: #c0392b; }}
        .severity-high {{ background: #e67e22; }}
        .severity-medium {{ background: #f39c12; }}
        .severity-low {{ background: #3498db; }}
        
        .last-update {{
            text-align: center;
            color: rgba(255, 255, 255, 0.8);
            margin-top: 30px;
            font-size: 1.1em;
        }}
        
        .no-drops {{
            text-align: center;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 40px;
            color: #7f8c8d;
            font-size: 1.2em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Dashboard Integrado - Drops Detectados</h1>
            <p>Sistema de monitoramento em tempo real do dropping-odds.com com detecção avançada de drops</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number games-count">{len(games_with_drops)}</div>
                <div class="stat-label">Jogos com Drops</div>
            </div>
            <div class="stat-card">
                <div class="stat-number drops-count">{len(drops)}</div>
                <div class="stat-label">Total de Drops</div>
            </div>
            <div class="stat-card">
                <div class="stat-number critical-count">{len([d for d in drops if d.severity == 'critical'])}</div>
                <div class="stat-label">Drops Críticos</div>
            </div>
            <div class="stat-card">
                <div class="stat-number high-count">{len([d for d in drops if d.severity == 'high'])}</div>
                <div class="stat-label">Drops Altos</div>
            </div>
        </div>
"""
        
        if games_with_drops:
            html_content += '<div class="games-grid">'
            
            for game in games_with_drops:
                game_drops = drops_by_game.get(game.game_id, [])
                
                html_content += f"""
                <div class="game-card">
                    <div class="game-header">
                        <div class="game-title">{game.home_team} vs {game.away_team}</div>
                        <div class="game-status status-{game.status}">{game.status.upper()}</div>
                    </div>
                    
                    <div class="game-info">
                        <div><strong>Liga:</strong> {game.league}</div>
                        <div><strong>Placar:</strong> {game.score}</div>
                        <div><strong>Tempo:</strong> {game.game_time}</div>
                    </div>
                    
                    <div class="drops-section">
                        <div class="drops-title">🚨 Drops Detectados ({len(game_drops)})</div>
"""
                
                for drop in game_drops:
                    html_content += f"""
                        <div class="drop-item">
                            <span><strong>{drop.bet_type}</strong>: {drop.old_value:.2f} → {drop.new_value:.2f}</span>
                            <span class="drop-percentage severity-{drop.severity}">{drop.percentage_change:+.1f}%</span>
                        </div>
"""
                
                html_content += """
                    </div>
                </div>
"""
            
            html_content += '</div>'
        else:
            html_content += """
            <div class="no-drops">
                <h2>🔍 Nenhum drop detectado no momento</h2>
                <p>O sistema está monitorando continuamente. Drops serão exibidos aqui quando detectados.</p>
            </div>
"""
        
        html_content += f"""
        <div class="last-update">
            Última atualização: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}
        </div>
    </div>
</body>
</html>
"""
        
        try:
            with open(self.html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"📊 Dashboard gerado: {self.html_file}")
        except Exception as e:
            print(f"❌ Erro ao gerar dashboard: {e}")
    
    def run_monitoring_cycle(self):
        """Executa um ciclo de monitoramento"""
        print(f"\n🔄 Iniciando ciclo de monitoramento - {datetime.now().strftime('%H:%M:%S')}")
        
        # Extrai jogos atuais
        current_games = self.extract_live_games()
        
        if not current_games:
            print("❌ Nenhum jogo extraído")
            return
        
        # Detecta drops
        detected_drops = self.detect_drops(current_games)
        
        # Salva dados
        self.save_data(current_games, detected_drops)
        
        # Gera dashboard
        self.generate_dashboard(current_games, detected_drops)
        
        print(f"✅ Ciclo concluído: {len(current_games)} jogos, {len(detected_drops)} drops detectados")
        
        return len(current_games), len(detected_drops)
    
    def start_monitoring(self, interval_minutes: int = 5):
        """Inicia monitoramento contínuo"""
        print(f"🚀 Iniciando sistema integrado de detecção de drops")
        print(f"⏰ Intervalo de monitoramento: {interval_minutes} minutos")
        print(f"🌐 Fonte: {self.live_url}")
        
        if not self.setup_driver():
            print("❌ Falha ao configurar driver")
            return
        
        try:
            cycle_count = 0
            while True:
                cycle_count += 1
                print(f"\n📊 Ciclo #{cycle_count}")
                
                games_count, drops_count = self.run_monitoring_cycle()
                
                print(f"⏳ Aguardando {interval_minutes} minutos para próximo ciclo...")
                time.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            print("\n⏹️ Monitoramento interrompido pelo usuário")
        except Exception as e:
            print(f"❌ Erro no monitoramento: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                print("🔒 Driver fechado")

if __name__ == "__main__":
    system = IntegratedDropsSystem()
    system.start_monitoring(interval_minutes=5)