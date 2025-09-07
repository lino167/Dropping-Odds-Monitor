import requests
import json
import time
import threading
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
from bs4 import BeautifulSoup

class DroppingOddsDashboard:
    def __init__(self):
        self.base_url = "https://dropping-odds.com/index.php?view=live"
        self.data_file = "dropping_odds_data.json"
        self.html_file = "dropping_odds_dashboard.html"
        self.update_interval = 300  # 5 minutos
        self.running = False
        
    def setup_driver(self):
        """Configura o driver do Chrome"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            return driver
        except Exception as e:
            print(f"Erro ao configurar driver: {e}")
            return None
    
    def extract_live_games(self):
        """Extrai jogos ao vivo do dropping-odds.com"""
        driver = self.setup_driver()
        if not driver:
            return []
        
        try:
            print(f"Acessando: {self.base_url}")
            driver.get(self.base_url)
            
            # Aguarda carregamento da tabela
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            
            time.sleep(3)  # Aguarda carregamento completo
            
            games_data = []
            
            # Busca todas as linhas da tabela de jogos
            table_rows = driver.find_elements(By.CSS_SELECTOR, "table tr")
            
            for row in table_rows[1:]:  # Pula o cabeçalho
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    
                    if len(cells) >= 6:
                        # Extrai dados das células
                        country_league = cells[1].text.strip()
                        home_team = cells[2].text.strip()
                        score = cells[3].text.strip()
                        away_team = cells[4].text.strip()
                        game_time = cells[5].text.strip()
                        
                        # Verifica se os dados são válidos
                        if home_team and away_team and country_league:
                            # Separa país e liga se possível
                            if ' ' in country_league:
                                parts = country_league.split(' ', 1)
                                country = parts[0]
                                league = parts[1] if len(parts) > 1 else country_league
                            else:
                                country = country_league
                                league = country_league
                            
                            # Gera ID único baseado nos times
                            game_id = f"{home_team.replace(' ', '_')}_{away_team.replace(' ', '_')}".lower()
                            
                            game_data = {
                                "game_id": game_id,
                                "country": country,
                                "league": league,
                                "home_team": home_team,
                                "away_team": away_team,
                                "match_name": f"{home_team} vs {away_team}",
                                "score": score if score else "0:0",
                                "game_time": game_time if game_time else "0'",
                                "last_updated": datetime.now().isoformat(),
                                "drops_detected": 0,
                                "max_drop_percentage": 0.0,
                                "status": "live" if game_time and game_time != "FT" else "finished"
                            }
                            
                            games_data.append(game_data)
                            print(f"Jogo extraído: {home_team} vs {away_team} ({league}) - {score} - {game_time}")
                    
                except Exception as e:
                    print(f"Erro ao processar linha: {e}")
                    continue
            
            print(f"Total de jogos extraídos: {len(games_data)}")
            return games_data
            
        except Exception as e:
            print(f"Erro na extração: {e}")
            return []
        finally:
            driver.quit()
    
    def detect_drops(self, current_games, previous_games):
        """Simula detecção de drops (para demonstração)"""
        if not previous_games:
            return current_games
        
        # Cria dicionário para busca rápida
        prev_games_dict = {game['game_id']: game for game in previous_games}
        
        for current_game in current_games:
            game_id = current_game['game_id']
            if game_id in prev_games_dict:
                prev_game = prev_games_dict[game_id]
                
                # Simula detecção de drops baseado em mudanças no placar
                prev_score = prev_game.get('score', '0:0')
                current_score = current_game.get('score', '0:0')
                
                if prev_score != current_score:
                    # Simula drop quando há mudança no placar
                    current_game['drops_detected'] = 1
                    current_game['max_drop_percentage'] = 15.5  # Valor simulado
                    current_game['drops_details'] = [{
                        'bet_type': '1X2',
                        'description': f'Mudança no placar: {prev_score} → {current_score}',
                        'drop_percentage': 15.5
                    }]
        
        return current_games
    
    def save_data(self, games_data):
        """Salva dados em arquivo JSON"""
        data = {
            'games': games_data,
            'total_games': len(games_data),
            'games_with_drops': len([g for g in games_data if g['drops_detected'] > 0]),
            'live_games': len([g for g in games_data if g['status'] == 'live']),
            'finished_games': len([g for g in games_data if g['status'] == 'finished']),
            'last_update': datetime.now().isoformat(),
            'update_interval': self.update_interval,
            'source': 'dropping-odds.com'
        }
        
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_previous_data(self):
        """Carrega dados anteriores"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('games', [])
        except Exception as e:
            print(f"Erro ao carregar dados anteriores: {e}")
        return []
    
    def generate_html_dashboard(self, games_data):
        """Gera dashboard HTML com dados do dropping-odds.com"""
        total_games = len(games_data)
        live_games = len([g for g in games_data if g['status'] == 'live'])
        finished_games = len([g for g in games_data if g['status'] == 'finished'])
        games_with_drops = len([g for g in games_data if g['drops_detected'] > 0])
        
        # Agrupa jogos por país/liga
        leagues = {}
        for game in games_data:
            league_key = f"{game['country']} - {game['league']}"
            if league_key not in leagues:
                leagues[league_key] = []
            leagues[league_key].append(game)
        
        # Ordena jogos: primeiro com drops, depois por status (live primeiro)
        sorted_games = sorted(games_data, key=lambda x: (
            -x['drops_detected'],  # Drops primeiro (ordem decrescente)
            x['status'] != 'live',  # Live primeiro
            x['league'],  # Por liga
            x['home_team']  # Por time da casa
        ))
        
        html_content = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Dropping Odds - Monitoramento Live</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1600px;
            margin: 0 auto;
        }}
        
        .header {{
            background: rgba(255, 255, 255, 0.95);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            text-align: center;
        }}
        
        .header h1 {{
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .source-info {{
            background: #3498db;
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            display: inline-block;
            margin: 10px 0;
            font-weight: bold;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        
        .stat-card {{
            background: rgba(255, 255, 255, 0.9);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }}
        
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #3498db;
        }}
        
        .stat-label {{
            color: #7f8c8d;
            margin-top: 5px;
        }}
        
        .live-indicator {{
            background: #27ae60;
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            display: inline-block;
            margin-top: 15px;
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0% {{ opacity: 1; }}
            50% {{ opacity: 0.7; }}
            100% {{ opacity: 1; }}
        }}
        
        .leagues-section {{
            margin-bottom: 30px;
        }}
        
        .league-header {{
            background: rgba(255, 255, 255, 0.9);
            padding: 15px 25px;
            border-radius: 10px 10px 0 0;
            font-weight: bold;
            color: #2c3e50;
            font-size: 1.2em;
            border-left: 5px solid #3498db;
        }}
        
        .games-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 20px;
            background: rgba(255, 255, 255, 0.05);
            padding: 20px;
            border-radius: 0 0 10px 10px;
        }}
        
        .game-card {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}
        
        .game-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.2);
        }}
        
        .game-card.live {{
            border-left: 5px solid #27ae60;
            background: linear-gradient(135deg, #fff 0%, #e8f5e8 100%);
        }}
        
        .game-card.finished {{
            border-left: 5px solid #95a5a6;
            background: linear-gradient(135deg, #fff 0%, #f8f9fa 100%);
        }}
        
        .game-card.has-drops {{
            border-left: 5px solid #e74c3c;
            background: linear-gradient(135deg, #fff 0%, #ffe6e6 100%);
        }}
        
        .match-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        
        .match-title {{
            font-size: 1.3em;
            font-weight: bold;
            color: #2c3e50;
        }}
        
        .status-badge {{
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }}
        
        .status-live {{
            background: #27ae60;
            color: white;
        }}
        
        .status-finished {{
            background: #95a5a6;
            color: white;
        }}
        
        .match-details {{
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            gap: 15px;
            align-items: center;
            margin-bottom: 15px;
        }}
        
        .team {{
            text-align: center;
            font-weight: bold;
            color: #34495e;
        }}
        
        .score {{
            font-size: 1.8em;
            font-weight: bold;
            color: #27ae60;
            text-align: center;
            background: rgba(39, 174, 96, 0.1);
            padding: 10px;
            border-radius: 8px;
        }}
        
        .game-info {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 15px;
        }}
        
        .info-item {{
            text-align: center;
            padding: 8px;
            border-radius: 6px;
            background: rgba(52, 152, 219, 0.1);
        }}
        
        .info-label {{
            font-size: 0.8em;
            color: #7f8c8d;
            margin-bottom: 3px;
        }}
        
        .info-value {{
            font-weight: bold;
            color: #2c3e50;
        }}
        
        .drops-section {{
            margin-top: 15px;
            padding: 12px;
            background: rgba(231, 76, 60, 0.1);
            border-radius: 8px;
            border-left: 4px solid #e74c3c;
        }}
        
        .drops-title {{
            font-weight: bold;
            color: #e74c3c;
            margin-bottom: 8px;
            font-size: 0.9em;
        }}
        
        .drop-item {{
            background: white;
            padding: 8px;
            margin: 5px 0;
            border-radius: 4px;
            font-size: 0.85em;
        }}
        
        .no-games {{
            text-align: center;
            padding: 50px;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 15px;
            color: #7f8c8d;
            grid-column: 1 / -1;
        }}
        
        .last-update {{
            text-align: center;
            margin-top: 30px;
            color: rgba(255, 255, 255, 0.8);
            font-size: 0.9em;
        }}
        
        @media (max-width: 768px) {{
            .games-grid {{
                grid-template-columns: 1fr;
            }}
            
            .match-details {{
                grid-template-columns: 1fr;
                gap: 10px;
            }}
        }}
    </style>
    <script>
        // Auto-refresh a cada 5 minutos
        setTimeout(function() {{
            location.reload();
        }}, 300000);
        
        // Contador regressivo
        let countdown = 300;
        function updateCountdown() {{
            const minutes = Math.floor(countdown / 60);
            const seconds = countdown % 60;
            document.getElementById('countdown').textContent = 
                `Próxima atualização em: ${{minutes}}:${{seconds.toString().padStart(2, '0')}}`;
            countdown--;
            if (countdown < 0) countdown = 300;
        }}
        
        setInterval(updateCountdown, 1000);
        window.onload = updateCountdown;
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Dashboard Dropping Odds</h1>
            <div class="source-info">
                📊 Dados em tempo real de dropping-odds.com
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{total_games}</div>
                    <div class="stat-label">Total de Jogos</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{live_games}</div>
                    <div class="stat-label">Jogos ao Vivo</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{finished_games}</div>
                    <div class="stat-label">Jogos Finalizados</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{games_with_drops}</div>
                    <div class="stat-label">Com Drops Detectados</div>
                </div>
            </div>
            
            <div class="live-indicator">
                🔴 <span id="countdown">Carregando...</span>
            </div>
        </div>
"""
        
        if not sorted_games:
            html_content += """
        <div class="games-grid">
            <div class="no-games">
                <h2>🔍 Nenhum jogo encontrado</h2>
                <p>Aguardando dados dos jogos ao vivo...</p>
            </div>
        </div>
"""
        else:
            # Agrupa por liga para melhor organização
            current_league = None
            for game in sorted_games:
                league_key = f"{game['country']} - {game['league']}"
                
                if current_league != league_key:
                    if current_league is not None:
                        html_content += "        </div>\n    </div>\n"  # Fecha liga anterior
                    
                    html_content += f"""
        <div class="leagues-section">
            <div class="league-header">
                🏆 {league_key} ({len([g for g in sorted_games if f"{g['country']} - {g['league']}" == league_key])} jogos)
            </div>
            <div class="games-grid">
"""
                    current_league = league_key
                
                # Determina classes CSS
                status_class = game['status']
                has_drops_class = "has-drops" if game['drops_detected'] > 0 else ""
                card_classes = f"{status_class} {has_drops_class}".strip()
                
                # Badge de status
                status_badge_class = f"status-{game['status']}"
                status_text = "AO VIVO" if game['status'] == 'live' else "FINALIZADO"
                
                html_content += f"""
                <div class="game-card {card_classes}">
                    <div class="match-header">
                        <div class="match-title">⚽ {game['match_name']}</div>
                        <div class="status-badge {status_badge_class}">{status_text}</div>
                    </div>
                    
                    <div class="match-details">
                        <div class="team">{game['home_team']}</div>
                        <div class="score">{game['score']}</div>
                        <div class="team">{game['away_team']}</div>
                    </div>
                    
                    <div class="game-info">
                        <div class="info-item">
                            <div class="info-label">Tempo</div>
                            <div class="info-value">{game['game_time']}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">País</div>
                            <div class="info-value">{game['country']}</div>
                        </div>
                    </div>
"""
                
                if game['drops_detected'] > 0:
                    html_content += f"""
                    <div class="drops-section">
                        <div class="drops-title">🚨 Drops Detectados ({game['drops_detected']})</div>
"""
                    for drop in game.get('drops_details', []):
                        html_content += f"""
                        <div class="drop-item">
                            <strong>{drop.get('bet_type', 'N/A')}</strong>: {drop.get('description', 'Drop detectado')}
                        </div>
"""
                    html_content += "                    </div>"
                
                html_content += "                </div>"
            
            # Fecha última liga
            if current_league is not None:
                html_content += "            </div>\n        </div>"
        
        html_content += f"""
        
        <div class="last-update">
            Última atualização: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')} | 
            Fonte: dropping-odds.com
        </div>
    </div>
</body>
</html>
"""
        
        with open(self.html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Dashboard HTML gerado: {self.html_file}")
    
    def update_cycle(self):
        """Ciclo de atualização dos dados"""
        print("Iniciando ciclo de atualização...")
        
        # Carrega dados anteriores
        previous_games = self.load_previous_data()
        
        # Extrai novos dados
        current_games = self.extract_live_games()
        
        if current_games:
            # Detecta drops
            games_with_drops = self.detect_drops(current_games, previous_games)
            
            # Salva dados
            self.save_data(games_with_drops)
            
            # Gera dashboard
            self.generate_html_dashboard(games_with_drops)
            
            print(f"Atualização concluída: {len(games_with_drops)} jogos processados")
            print(f"Jogos ao vivo: {len([g for g in games_with_drops if g['status'] == 'live'])}")
            print(f"Jogos com drops: {len([g for g in games_with_drops if g['drops_detected'] > 0])}")
        else:
            print("Nenhum jogo encontrado na atualização")
    
    def start_monitoring(self):
        """Inicia monitoramento contínuo"""
        self.running = True
        print("🚀 Iniciando sistema de monitoramento Dropping Odds...")
        print(f"📊 Fonte: {self.base_url}")
        print(f"⏰ Atualizações a cada {self.update_interval//60} minutos")
        
        # Primeira execução
        self.update_cycle()
        
        # Loop de monitoramento
        while self.running:
            time.sleep(self.update_interval)
            if self.running:
                self.update_cycle()
    
    def stop_monitoring(self):
        """Para o monitoramento"""
        self.running = False
        print("⏹️ Monitoramento interrompido")

if __name__ == "__main__":
    system = DroppingOddsDashboard()
    
    try:
        system.start_monitoring()
    except KeyboardInterrupt:
        system.stop_monitoring()
        print("\n👋 Sistema finalizado pelo usuário")
    except Exception as e:
        print(f"❌ Erro no sistema: {e}")
        system.stop_monitoring()