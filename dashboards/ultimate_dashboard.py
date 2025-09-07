import json
import os
from datetime import datetime
from typing import Dict, List, Any

class UltimateDashboard:
    def __init__(self):
        self.drops_data = None
        self.games_data = None
        
    def load_data(self):
        """Carrega todos os dados necessários"""
        # Carrega análise de drops
        drops_file = 'final_drop_analysis_20250907_182957.json'
        if os.path.exists(drops_file):
            with open(drops_file, 'r', encoding='utf-8') as f:
                self.drops_data = json.load(f)
            print(f"✅ Dados de drops carregados: {drops_file}")
        else:
            print(f"❌ Arquivo não encontrado: {drops_file}")
            return False
            
        # Carrega dados completos
        games_file = 'complete_live_data_20250907_172408.json'
        if os.path.exists(games_file):
            with open(games_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.games_data = data.get('games_data', {})
            print(f"✅ Dados dos jogos carregados: {games_file}")
        else:
            print(f"❌ Arquivo não encontrado: {games_file}")
            return False
            
        return True
    
    def find_drops_in_data(self):
        """Encontra drops em qualquer estrutura dos dados"""
        
        print("🔍 Procurando drops em todas as estruturas possíveis...")
        
        # Lista de possíveis chaves onde podem estar os drops
        possible_keys = [
            'all_drops_found',
            'drops_detected', 
            'significant_drops',
            'drops_list',
            'all_drops',
            'detected_drops'
        ]
        
        drops_found = None
        drops_key = None
        
        # Procura nas chaves diretas
        for key in possible_keys:
            if key in self.drops_data:
                data = self.drops_data[key]
                if isinstance(data, list) and len(data) > 0:
                    print(f"✅ Encontrados {len(data)} drops na chave '{key}'")
                    drops_found = data
                    drops_key = key
                    break
        
        # Se não encontrou, procura em estruturas aninhadas
        if not drops_found:
            print("🔍 Procurando em estruturas aninhadas...")
            for key, value in self.drops_data.items():
                if isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        if isinstance(subvalue, list) and len(subvalue) > 0:
                            # Verifica se parece com dados de drops
                            if len(subvalue) > 0 and isinstance(subvalue[0], dict):
                                first_item = subvalue[0]
                                if any(field in first_item for field in ['drop_magnitude', 'percentage_change', 'game_id']):
                                    print(f"✅ Encontrados {len(subvalue)} drops em '{key}.{subkey}'")
                                    drops_found = subvalue
                                    drops_key = f"{key}.{subkey}"
                                    break
                    if drops_found:
                        break
        
        # Se ainda não encontrou, procura por listas grandes
        if not drops_found:
            print("🔍 Procurando por listas grandes que podem conter drops...")
            for key, value in self.drops_data.items():
                if isinstance(value, list) and len(value) > 1000:  # Lista grande
                    if len(value) > 0 and isinstance(value[0], dict):
                        first_item = value[0]
                        print(f"📊 Lista grande encontrada em '{key}': {len(value)} itens")
                        print(f"   Primeiro item: {first_item}")
                        
                        # Se tem campos que parecem com drops, usa essa lista
                        if any(field in first_item for field in ['game_id', 'odds', 'change', 'drop', 'magnitude']):
                            print(f"✅ Usando lista '{key}' como fonte de drops")
                            drops_found = value
                            drops_key = key
                            break
        
        if not drops_found:
            print("❌ Nenhuma lista de drops encontrada")
            return None, None
            
        print(f"🎯 Usando drops da chave: {drops_key}")
        print(f"📊 Total de drops: {len(drops_found)}")
        
        if len(drops_found) > 0:
            print(f"📋 Exemplo do primeiro drop: {drops_found[0]}")
        
        return drops_found, drops_key
    
    def get_game_details(self, game_id: str) -> Dict:
        """Obtém detalhes completos do jogo"""
        game_data = self.games_data.get(game_id, {})
        
        # Extrai informações do jogo
        home_team = game_data.get('home_team', f'Time Casa {game_id[:4]}')
        away_team = game_data.get('away_team', f'Time Visitante {game_id[:4]}')
        league = game_data.get('league', 'Liga Desconhecida')
        score = game_data.get('score', '0-0')
        time_in_game = game_data.get('time_in_game', '0')
        status = game_data.get('status', 'Em andamento')
        
        # Se não tem dados específicos, tenta extrair de outras estruturas
        if home_team.startswith('Time Casa') and 'tables' in game_data:
            try:
                tables = game_data['tables']
                # Tenta diferentes tipos de tabela
                for table_type in ['1x2', '1x2_ht', 'total', 'handicap']:
                    if table_type in tables:
                        table_data = tables[table_type]
                        if isinstance(table_data, list) and len(table_data) > 0:
                            first_entry = table_data[0]
                            if isinstance(first_entry, dict) and 'teams' in first_entry:
                                teams = first_entry['teams']
                                if isinstance(teams, list) and len(teams) >= 2:
                                    home_team = teams[0]
                                    away_team = teams[1]
                                    break
                        elif isinstance(table_data, dict):
                            # Se table_data é um dict, pode ter estrutura diferente
                            for key, value in table_data.items():
                                if isinstance(value, list) and len(value) > 0:
                                    first_entry = value[0]
                                    if isinstance(first_entry, dict) and 'teams' in first_entry:
                                        teams = first_entry['teams']
                                        if isinstance(teams, list) and len(teams) >= 2:
                                            home_team = teams[0]
                                            away_team = teams[1]
                                            break
                            if not home_team.startswith('Time Casa'):
                                break
            except Exception as e:
                print(f"⚠️ Erro ao extrair dados do jogo {game_id}: {e}")
        
        return {
            'home_team': home_team,
            'away_team': away_team,
            'league': league,
            'score': score,
            'time_in_game': time_in_game,
            'status': status,
            'match_name': f"{home_team} vs {away_team}"
        }
    
    def process_drops_data(self, drops_list: List[Dict]):
        """Processa os dados de drops encontrados"""
        
        print(f"\n🔧 Processando {len(drops_list)} drops...")
        
        # Agrupa drops por jogo
        drops_by_game = {}
        processed_drops = 0
        
        for drop in drops_list:
            game_id = drop.get('game_id')
            if not game_id:
                continue
                
            if game_id not in drops_by_game:
                drops_by_game[game_id] = []
            
            drops_by_game[game_id].append(drop)
            processed_drops += 1
        
        print(f"✅ {processed_drops} drops processados")
        print(f"🎮 Drops agrupados por {len(drops_by_game)} jogos")
        
        # Cria lista de jogos para o dashboard
        games_list = []
        for game_id, game_drops in drops_by_game.items():
            if len(game_drops) > 0:
                # Obtém detalhes do jogo
                game_details = self.get_game_details(game_id)
                
                # Tenta diferentes campos para calcular o maior drop
                max_drop = 0
                for drop in game_drops:
                    drop_value = (
                        drop.get('drop_magnitude', 0) or
                        abs(drop.get('percentage_change', 0)) or
                        abs(drop.get('home_change', 0)) or
                        abs(drop.get('away_change', 0)) or
                        0
                    )
                    max_drop = max(max_drop, drop_value)
                
                tables_count = len(self.games_data.get(game_id, {}).get('tables', {}))
                
                games_list.append({
                    'game_id': game_id,
                    'drops_count': len(game_drops),
                    'max_drop': max_drop,
                    'tables_count': tables_count,
                    'drops': game_drops,
                    'details': game_details
                })
        
        # Ordena por número de drops
        games_list.sort(key=lambda x: x['drops_count'], reverse=True)
        
        print(f"📋 {len(games_list)} jogos processados para o dashboard")
        if len(games_list) > 0:
            print(f"🏆 Top 5 jogos com mais drops:")
            for i, game in enumerate(games_list[:5]):
                details = game['details']
                print(f"   {i+1}. {details['match_name']}: {game['drops_count']} drops (max: {game['max_drop']:.1f}%)")
        
        return games_list
    
    def create_main_dashboard_html(self, games_list: List[Dict], total_drops: int) -> str:
        """Cria HTML do dashboard principal"""
        
        total_games = len(games_list)
        avg_drops = total_drops / total_games if total_games > 0 else 0
        
        html_content = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Ultimate - Jogos com Drops</title>
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
        
        .stat-label {{
            color: #7f8c8d;
            font-size: 1em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .games-count {{ color: #3498db; }}
        .drops-count {{ color: #e74c3c; }}
        .avg-drops {{ color: #f39c12; }}
        .status {{ color: #27ae60; }}
        
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
            transition: all 0.3s ease;
            cursor: pointer;
            border: 2px solid transparent;
        }}
        
        .game-card:hover {{
            transform: translateY(-5px);
            border-color: #3498db;
            box-shadow: 0 12px 35px rgba(52, 152, 219, 0.2);
        }}
        
        .game-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 15px;
        }}
        
        .game-info {{
            flex: 1;
        }}
        
        .match-title {{
            font-size: 1.3em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
            line-height: 1.2;
        }}
        
        .league-info {{
            color: #7f8c8d;
            font-size: 0.9em;
            margin-bottom: 8px;
        }}
        
        .match-status {{
            display: flex;
            align-items: center;
            gap: 15px;
            font-size: 0.95em;
        }}
        
        .score {{
            background: #27ae60;
            color: white;
            padding: 4px 10px;
            border-radius: 12px;
            font-weight: bold;
        }}
        
        .time {{
            background: #3498db;
            color: white;
            padding: 4px 10px;
            border-radius: 12px;
            font-weight: bold;
        }}
        
        .drops-badge {{
            background: #e74c3c;
            color: white;
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
            white-space: nowrap;
        }}
        
        .game-stats {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-top: 15px;
        }}
        
        .game-stat {{
            text-align: center;
            padding: 12px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        
        .game-stat-number {{
            font-size: 1.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .game-stat-label {{
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        
        .max-drop {{ color: #8e44ad; }}
        .tables-count {{ color: #3498db; }}
        
        .click-hint {{
            text-align: center;
            color: #7f8c8d;
            font-style: italic;
            margin-top: 15px;
            font-size: 0.9em;
        }}
        
        .success-message {{
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
            font-weight: bold;
        }}
        
        .game-id {{
            color: #95a5a6;
            font-size: 0.8em;
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="success-message">
            🎉 Dashboard Ultimate funcionando! Todos os {total_games} jogos com drops estão sendo exibidos.
        </div>
        
        <div class="header">
            <h1>⚽ Dashboard Ultimate</h1>
            <p>Sistema Completo de Análise de Drops em Tempo Real</p>
            <p style="color: #7f8c8d; margin-top: 10px;">Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number games-count">{total_games}</div>
                <div class="stat-label">Jogos com Drops</div>
            </div>
            <div class="stat-card">
                <div class="stat-number drops-count">{total_drops:,}</div>
                <div class="stat-label">Total de Drops</div>
            </div>
            <div class="stat-card">
                <div class="stat-number avg-drops">{avg_drops:.1f}</div>
                <div class="stat-label">Drops por Jogo</div>
            </div>
            <div class="stat-card">
                <div class="stat-number status">✅</div>
                <div class="stat-label">Funcionando</div>
            </div>
        </div>
        
        <div class="games-grid">
        """
        
        for game in games_list:
            details = game['details']
            html_content += f"""
            <div class="game-card" onclick="openGamePage('{game['game_id']}')">
                <div class="game-header">
                    <div class="game-info">
                        <div class="match-title">⚽ {details['match_name']}</div>
                        <div class="league-info">🏆 {details['league']}</div>
                        <div class="match-status">
                            <span class="score">📊 {details['score']}</span>
                            <span class="time">⏱️ {details['time_in_game']}'</span>
                        </div>
                        <div class="game-id">ID: {game['game_id']}</div>
                    </div>
                    <div class="drops-badge">{game['drops_count']} drops</div>
                </div>
                
                <div class="game-stats">
                    <div class="game-stat">
                        <div class="game-stat-number max-drop">{game['max_drop']:.1f}%</div>
                        <div class="game-stat-label">Maior Drop</div>
                    </div>
                    <div class="game-stat">
                        <div class="game-stat-number tables-count">{game['tables_count']}</div>
                        <div class="game-stat-label">Tabelas</div>
                    </div>
                </div>
                
                <div class="click-hint">👆 Clique para ver análise completa e tabelas</div>
            </div>
            """
        
        html_content += """
        </div>
    </div>

    <script>
        function openGamePage(gameId) {
            window.open('game_' + gameId + '.html', '_blank');
        }

        // Animação de entrada
        window.addEventListener('load', () => {
            const elements = document.querySelectorAll('.stat-card, .game-card');
            elements.forEach((el, index) => {
                el.style.opacity = '0';
                el.style.transform = 'translateY(30px)';
                
                setTimeout(() => {
                    el.style.transition = 'all 0.8s ease';
                    el.style.opacity = '1';
                    el.style.transform = 'translateY(0)';
                }, index * 100);
            });
        });
    </script>
</body>
</html>
        """
        
        return html_content
    
    def create_game_page_html(self, game_id: str, game_drops: List[Dict], game_tables: Dict, game_details: Dict) -> str:
        """Cria HTML da página individual do jogo"""
        
        drops_count = len(game_drops)
        tables_count = len(game_tables)
        
        # Calcula maior drop
        max_drop = 0
        for drop in game_drops:
            drop_value = (
                drop.get('drop_magnitude', 0) or
                abs(drop.get('percentage_change', 0)) or
                abs(drop.get('home_change', 0)) or
                abs(drop.get('away_change', 0)) or
                0
            )
            max_drop = max(max_drop, drop_value)
        
        html_content = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{game_details['match_name']} - Análise Ultimate</title>
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
        
        .back-btn {{
            background: #3498db;
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 25px;
            font-size: 1em;
            cursor: pointer;
            margin-bottom: 20px;
            transition: all 0.3s ease;
            font-weight: 600;
        }}
        
        .back-btn:hover {{
            background: #2980b9;
            transform: translateY(-2px);
        }}
        
        .match-info {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        }}
        
        .match-title {{
            font-size: 2.2em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        
        .match-details {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}
        
        .detail-item {{
            text-align: center;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
        }}
        
        .detail-label {{
            color: #7f8c8d;
            font-size: 0.9em;
            margin-bottom: 5px;
        }}
        
        .detail-value {{
            font-size: 1.3em;
            font-weight: bold;
            color: #2c3e50;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        }}
        
        .stat-number {{
            font-size: 2.2em;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        .stat-label {{
            color: #7f8c8d;
            font-size: 1em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .drops-count {{ color: #e74c3c; }}
        .tables-count {{ color: #3498db; }}
        .max-drop {{ color: #8e44ad; }}
        .game-id {{ color: #27ae60; }}
        
        .section {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        }}
        
        .section h2 {{
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 1.6em;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        
        .drop-item {{
            background: white;
            border: 1px solid #dee2e6;
            border-left: 4px solid #e74c3c;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 12px;
            transition: all 0.3s ease;
        }}
        
        .drop-item:hover {{
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            transform: translateX(5px);
        }}
        
        .drop-info {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .drop-details {{
            flex: 1;
        }}
        
        .drop-value {{
            font-weight: bold;
            font-size: 1.3em;
            color: #e74c3c;
        }}
        
        .drop-meta {{
            color: #7f8c8d;
            font-size: 0.9em;
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <button class="back-btn" onclick="window.history.back()">← Voltar ao Dashboard</button>
        
        <div class="header">
            <h1>⚽ {game_details['match_name']}</h1>
            <p>Análise Ultimate de Drops e Tabelas</p>
        </div>
        
        <div class="match-info">
            <div class="match-title">{game_details['match_name']}</div>
            <div class="match-details">
                <div class="detail-item">
                    <div class="detail-label">🏆 Liga</div>
                    <div class="detail-value">{game_details['league']}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">📊 Placar</div>
                    <div class="detail-value">{game_details['score']}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">⏱️ Tempo</div>
                    <div class="detail-value">{game_details['time_in_game']}'</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">📋 Status</div>
                    <div class="detail-value">{game_details['status']}</div>
                </div>
            </div>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number game-id">{game_id}</div>
                <div class="stat-label">ID do Jogo</div>
            </div>
            <div class="stat-card">
                <div class="stat-number drops-count">{drops_count}</div>
                <div class="stat-label">Drops Detectados</div>
            </div>
            <div class="stat-card">
                <div class="stat-number tables-count">{tables_count}</div>
                <div class="stat-label">Tabelas Disponíveis</div>
            </div>
            <div class="stat-card">
                <div class="stat-number max-drop">{max_drop:.1f}%</div>
                <div class="stat-label">Maior Drop</div>
            </div>
        </div>
        
        <div class="section">
            <h2>🚨 Drops Detectados ({drops_count} total)</h2>
        """
        
        # Ordena drops por magnitude
        sorted_drops = sorted(game_drops, key=lambda x: (
            x.get('drop_magnitude', 0) or
            abs(x.get('percentage_change', 0)) or
            abs(x.get('home_change', 0)) or
            abs(x.get('away_change', 0)) or
            0
        ), reverse=True)
        
        for i, drop in enumerate(sorted_drops):
            # Tenta diferentes campos para obter informações do drop
            drop_magnitude = (
                drop.get('drop_magnitude', 0) or
                abs(drop.get('percentage_change', 0)) or
                abs(drop.get('home_change', 0)) or
                abs(drop.get('away_change', 0)) or
                0
            )
            
            drop_type = drop.get('drop_type', drop.get('type', 'N/A'))
            table_type = drop.get('table_type', 'N/A')
            timestamp = drop.get('timestamp', drop.get('time', 'N/A'))
            score = drop.get('score', 'N/A')
            time_in_game = drop.get('time_in_game', 'N/A')
            home_odds = drop.get('home_odds', drop.get('home', 'N/A'))
            away_odds = drop.get('away_odds', drop.get('away', 'N/A'))
            
            html_content += f"""
            <div class="drop-item">
                <div class="drop-info">
                    <div class="drop-details">
                        <strong>#{i+1} - {table_type.upper()} - {drop_type.upper()}</strong><br>
                        <div class="drop-meta">
                            📅 {timestamp} | ⚽ {score} | ⏱️ {time_in_game}' | 🏠 {home_odds} | 🚪 {away_odds}
                        </div>
                    </div>
                    <div class="drop-value">
                        {drop_magnitude:.1f}%
                    </div>
                </div>
            </div>
            """
        
        html_content += "</div>"
        
        # Seção de tabelas (se existirem)
        if game_tables:
            html_content += """
        <div class="section">
            <h2>📊 Tabelas do Jogo</h2>
            <p>Dados históricos das odds para análise detalhada.</p>
        </div>
            """
        
        html_content += """
    </div>
</body>
</html>
        """
        
        return html_content
    
    def generate_complete_system(self):
        """Gera sistema completo de dashboard"""
        
        if not self.load_data():
            return False
            
        # Encontra drops nos dados
        drops_list, drops_key = self.find_drops_in_data()
        if not drops_list:
            return False
            
        # Processa dados de drops
        games_list = self.process_drops_data(drops_list)
        if not games_list:
            print("❌ Nenhum jogo processado")
            return False
            
        print("\n🎨 Gerando dashboard principal...")
        main_dashboard = self.create_main_dashboard_html(games_list, len(drops_list))
        
        # Salva dashboard principal
        with open('dashboard_ultimate.html', 'w', encoding='utf-8') as f:
            f.write(main_dashboard)
        print("✅ Dashboard principal salvo: dashboard_ultimate.html")
        
        # Gera páginas individuais dos jogos
        print("\n🎮 Gerando páginas individuais dos jogos...")
        games_created = 0
        
        for game in games_list:
            game_id = game['game_id']
            game_drops = game['drops']
            game_tables = self.games_data.get(game_id, {}).get('tables', {})
            game_details = game['details']
            
            game_page = self.create_game_page_html(game_id, game_drops, game_tables, game_details)
            
            filename = f'game_{game_id}.html'
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(game_page)
            
            games_created += 1
            if games_created <= 10:  # Mostra apenas os primeiros 10
                print(f"  ✅ Página do jogo {game_id} ({game_details['match_name']}) criada: {filename}")
        
        if games_created > 10:
            print(f"  ... e mais {games_created - 10} páginas criadas")
        
        print(f"\n🎯 Sistema Ultimate gerado com sucesso!")
        print(f"📂 Dashboard principal: dashboard_ultimate.html")
        print(f"🎮 Páginas de jogos criadas: {games_created}")
        print(f"📊 Total de drops: {len(drops_list):,}")
        print(f"🔑 Fonte dos drops: {drops_key}")
        print(f"🌐 Abra 'dashboard_ultimate.html' no navegador")
        
        return True

if __name__ == "__main__":
    print("🚀 Iniciando geração do Dashboard Ultimate...")
    
    system = UltimateDashboard()
    success = system.generate_complete_system()
    
    if not success:
        print("\n❌ Falha ao gerar sistema de dashboard")
    else:
        print("\n🎉 Dashboard Ultimate funcionando perfeitamente!")
        print("\n📋 Recursos do sistema:")
        print("   ✅ Dashboard principal com informações detalhadas dos jogos")
        print("   ✅ Nomes dos times, ligas, placares e tempo de jogo")
        print("   ✅ Páginas individuais para cada jogo")
        print("   ✅ Navegação por clique")
        print("   ✅ Análise detalhada de drops")
        print("   ✅ Interface moderna e responsiva")