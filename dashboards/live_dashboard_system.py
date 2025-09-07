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

class LiveDashboardSystem:
    def __init__(self):
        self.base_url = "https://www.betexplorer.com"
        self.live_url = f"{self.base_url}/live/"
        self.data_file = "live_dashboard_data.json"
        self.html_file = "live_dashboard.html"
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
        """Extrai jogos ao vivo com nomes reais dos times"""
        driver = self.setup_driver()
        if not driver:
            return []
        
        try:
            print(f"Acessando página live: {self.live_url}")
            driver.get(self.live_url)
            
            # Aguarda carregamento
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "table-main"))
            )
            
            games_data = []
            
            # Busca todas as linhas de jogos
            game_rows = driver.find_elements(By.CSS_SELECTOR, "tr[data-id]")
            
            for row in game_rows:
                try:
                    game_id = row.get_attribute("data-id")
                    if not game_id:
                        continue
                    
                    # Extrai nomes dos times
                    team_elements = row.find_elements(By.CSS_SELECTOR, ".h-text-left a, .team-name")
                    if len(team_elements) >= 2:
                        home_team = team_elements[0].text.strip()
                        away_team = team_elements[1].text.strip()
                    else:
                        # Fallback: busca por outros seletores
                        team_links = row.find_elements(By.CSS_SELECTOR, "a[href*='/football/']")
                        if len(team_links) >= 2:
                            home_team = team_links[0].text.strip()
                            away_team = team_links[1].text.strip()
                        else:
                            continue
                    
                    # Extrai placar
                    score_element = row.find_element(By.CSS_SELECTOR, ".table-score")
                    score = score_element.text.strip() if score_element else "0:0"
                    
                    # Extrai tempo de jogo
                    time_element = row.find_element(By.CSS_SELECTOR, ".table-time")
                    game_time = time_element.text.strip() if time_element else "0'"
                    
                    # Extrai liga
                    league_element = row.find_element(By.CSS_SELECTOR, ".table-main__tournament")
                    league = league_element.text.strip() if league_element else "Liga Desconhecida"
                    
                    # Extrai odds 1x2
                    odds_elements = row.find_elements(By.CSS_SELECTOR, ".table-odds .kx")
                    odds_1x2 = {}
                    if len(odds_elements) >= 3:
                        odds_1x2 = {
                            "1": odds_elements[0].text.strip(),
                            "X": odds_elements[1].text.strip(),
                            "2": odds_elements[2].text.strip()
                        }
                    
                    game_data = {
                        "game_id": game_id,
                        "home_team": home_team,
                        "away_team": away_team,
                        "match_name": f"{home_team} vs {away_team}",
                        "score": score,
                        "game_time": game_time,
                        "league": league,
                        "odds_1x2": odds_1x2,
                        "last_updated": datetime.now().isoformat(),
                        "drops_detected": 0,
                        "max_drop_percentage": 0.0
                    }
                    
                    games_data.append(game_data)
                    print(f"Jogo extraído: {home_team} vs {away_team} ({league})")
                    
                except Exception as e:
                    print(f"Erro ao extrair jogo: {e}")
                    continue
            
            print(f"Total de jogos extraídos: {len(games_data)}")
            return games_data
            
        except Exception as e:
            print(f"Erro na extração: {e}")
            return []
        finally:
            driver.quit()
    
    def detect_drops(self, current_games, previous_games):
        """Detecta drops comparando odds atuais com anteriores"""
        if not previous_games:
            return current_games
        
        # Cria dicionário para busca rápida
        prev_games_dict = {game['game_id']: game for game in previous_games}
        
        for current_game in current_games:
            game_id = current_game['game_id']
            if game_id in prev_games_dict:
                prev_game = prev_games_dict[game_id]
                
                # Compara odds 1x2
                drops_found = []
                for bet_type in ['1', 'X', '2']:
                    if (bet_type in current_game['odds_1x2'] and 
                        bet_type in prev_game['odds_1x2']):
                        
                        try:
                            current_odd = float(current_game['odds_1x2'][bet_type])
                            prev_odd = float(prev_game['odds_1x2'][bet_type])
                            
                            if prev_odd > 0:
                                drop_percentage = ((prev_odd - current_odd) / prev_odd) * 100
                                
                                # Considera drop significativo se >= 5%
                                if drop_percentage >= 5.0:
                                    drops_found.append({
                                        'bet_type': bet_type,
                                        'prev_odd': prev_odd,
                                        'current_odd': current_odd,
                                        'drop_percentage': drop_percentage
                                    })
                        except ValueError:
                            continue
                
                current_game['drops_detected'] = len(drops_found)
                current_game['max_drop_percentage'] = max([d['drop_percentage'] for d in drops_found], default=0.0)
                current_game['drops_details'] = drops_found
        
        return current_games
    
    def save_data(self, games_data):
        """Salva dados em arquivo JSON"""
        data = {
            'games': games_data,
            'total_games': len(games_data),
            'games_with_drops': len([g for g in games_data if g['drops_detected'] > 0]),
            'last_update': datetime.now().isoformat(),
            'update_interval': self.update_interval
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
        """Gera dashboard HTML dinâmico"""
        total_games = len(games_data)
        games_with_drops = len([g for g in games_data if g['drops_detected'] > 0])
        total_drops = sum(g['drops_detected'] for g in games_data)
        
        # Ordena jogos por drops detectados
        sorted_games = sorted(games_data, key=lambda x: (x['drops_detected'], x['max_drop_percentage']), reverse=True)
        
        html_content = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Live - Análise de Drops</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
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
        
        .auto-update {{
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
        
        .games-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(450px, 1fr));
            gap: 25px;
        }}
        
        .game-card {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}
        
        .game-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
        }}
        
        .game-card.has-drops {{
            border-left: 5px solid #e74c3c;
            background: linear-gradient(135deg, #fff 0%, #ffe6e6 100%);
        }}
        
        .match-title {{
            font-size: 1.4em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 15px;
            text-align: center;
        }}
        
        .match-info {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .info-item {{
            text-align: center;
            padding: 10px;
            border-radius: 8px;
            background: rgba(52, 152, 219, 0.1);
        }}
        
        .info-label {{
            font-size: 0.9em;
            color: #7f8c8d;
            margin-bottom: 5px;
        }}
        
        .info-value {{
            font-weight: bold;
            color: #2c3e50;
        }}
        
        .score {{
            background: rgba(39, 174, 96, 0.1) !important;
            color: #27ae60 !important;
        }}
        
        .time {{
            background: rgba(52, 152, 219, 0.1) !important;
            color: #3498db !important;
        }}
        
        .odds-section {{
            margin-top: 15px;
        }}
        
        .odds-title {{
            font-weight: bold;
            margin-bottom: 10px;
            color: #34495e;
        }}
        
        .odds-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 10px;
        }}
        
        .odd-item {{
            text-align: center;
            padding: 8px;
            border-radius: 5px;
            background: #f8f9fa;
            border: 1px solid #dee2e6;
        }}
        
        .drops-section {{
            margin-top: 20px;
            padding: 15px;
            background: rgba(231, 76, 60, 0.1);
            border-radius: 10px;
            border-left: 4px solid #e74c3c;
        }}
        
        .drops-title {{
            font-weight: bold;
            color: #e74c3c;
            margin-bottom: 10px;
        }}
        
        .drop-item {{
            background: white;
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .drop-percentage {{
            background: #e74c3c;
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            font-weight: bold;
        }}
        
        .no-games {{
            text-align: center;
            padding: 50px;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 15px;
            color: #7f8c8d;
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
            
            .match-info {{
                grid-template-columns: 1fr;
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
            <h1>🎯 Dashboard Live - Análise de Drops</h1>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{total_games}</div>
                    <div class="stat-label">Jogos Monitorados</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{games_with_drops}</div>
                    <div class="stat-label">Jogos com Drops</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{total_drops}</div>
                    <div class="stat-label">Total de Drops</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{datetime.now().strftime('%H:%M')}</div>
                    <div class="stat-label">Última Atualização</div>
                </div>
            </div>
            <div class="auto-update">
                🔄 <span id="countdown">Carregando...</span>
            </div>
        </div>
        
        <div class="games-grid">
"""
        
        if not sorted_games:
            html_content += """
            <div class="no-games">
                <h2>🔍 Nenhum jogo encontrado</h2>
                <p>Aguardando dados dos jogos ao vivo...</p>
            </div>
"""
        else:
            for game in sorted_games:
                has_drops_class = "has-drops" if game['drops_detected'] > 0 else ""
                
                html_content += f"""
            <div class="game-card {has_drops_class}">
                <div class="match-title">
                    ⚽ {game['match_name']}
                </div>
                
                <div class="match-info">
                    <div class="info-item">
                        <div class="info-label">Liga</div>
                        <div class="info-value">{game['league']}</div>
                    </div>
                    <div class="info-item score">
                        <div class="info-label">Placar</div>
                        <div class="info-value">{game['score']}</div>
                    </div>
                    <div class="info-item time">
                        <div class="info-label">Tempo</div>
                        <div class="info-value">{game['game_time']}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">ID</div>
                        <div class="info-value">{game['game_id']}</div>
                    </div>
                </div>
                
                <div class="odds-section">
                    <div class="odds-title">📊 Odds 1X2</div>
                    <div class="odds-grid">
                        <div class="odd-item">
                            <strong>1</strong><br>
                            {game['odds_1x2'].get('1', 'N/A')}
                        </div>
                        <div class="odd-item">
                            <strong>X</strong><br>
                            {game['odds_1x2'].get('X', 'N/A')}
                        </div>
                        <div class="odd-item">
                            <strong>2</strong><br>
                            {game['odds_1x2'].get('2', 'N/A')}
                        </div>
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
                        <span><strong>{drop['bet_type']}</strong>: {drop['prev_odd']:.2f} → {drop['current_odd']:.2f}</span>
                        <span class="drop-percentage">{drop['drop_percentage']:.1f}%</span>
                    </div>
"""
                    html_content += "</div>"
                
                html_content += "</div>"
        
        html_content += f"""
        </div>
        
        <div class="last-update">
            Última atualização: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}
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
        else:
            print("Nenhum jogo encontrado na atualização")
    
    def start_monitoring(self):
        """Inicia monitoramento contínuo"""
        self.running = True
        print("🚀 Iniciando sistema de monitoramento live...")
        print(f"📊 Atualizações a cada {self.update_interval//60} minutos")
        
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
    system = LiveDashboardSystem()
    
    try:
        system.start_monitoring()
    except KeyboardInterrupt:
        system.stop_monitoring()
        print("\n👋 Sistema finalizado pelo usuário")
    except Exception as e:
        print(f"❌ Erro no sistema: {e}")
        system.stop_monitoring()