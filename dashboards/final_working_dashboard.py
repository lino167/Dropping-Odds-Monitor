import json
import os
from datetime import datetime
from typing import Dict, List, Any

class FinalWorkingDashboard:
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
    
    def process_drops_data(self):
        """Processa os dados de drops encontrados"""
        
        # Usa a lista 'all_drops_found' que contém todos os drops
        all_drops = self.drops_data.get('all_drops_found', [])
        print(f"📊 Total de drops encontrados: {len(all_drops)}")
        
        if not all_drops:
            print("❌ Nenhum drop encontrado na lista 'all_drops_found'")
            return None
        
        # Agrupa drops por jogo
        drops_by_game = {}
        for drop in all_drops:
            game_id = drop.get('game_id', 'unknown')
            if game_id not in drops_by_game:
                drops_by_game[game_id] = []
            drops_by_game[game_id].append(drop)
        
        print(f"🎮 Drops agrupados por {len(drops_by_game)} jogos")
        
        # Cria lista de jogos para o dashboard
        games_list = []
        for game_id, game_drops in drops_by_game.items():
            if len(game_drops) > 0:
                # Calcula maior drop usando drop_magnitude
                max_drop = max([drop.get('drop_magnitude', 0) for drop in game_drops])
                tables_count = len(self.games_data.get(game_id, {}).get('tables', {}))
                
                games_list.append({
                    'game_id': game_id,
                    'drops_count': len(game_drops),
                    'max_drop': max_drop,
                    'tables_count': tables_count,
                    'drops': game_drops
                })
        
        # Ordena por número de drops
        games_list.sort(key=lambda x: x['drops_count'], reverse=True)
        
        print(f"📋 {len(games_list)} jogos processados para o dashboard")
        print(f"🏆 Top 5 jogos com mais drops:")
        for i, game in enumerate(games_list[:5]):
            print(f"   {i+1}. Jogo {game['game_id']}: {game['drops_count']} drops (max: {game['max_drop']:.1f}%)")
        
        return games_list, len(all_drops)
    
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
    <title>Dashboard Final - Jogos com Drops</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
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
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
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
            align-items: center;
            margin-bottom: 15px;
        }}
        
        .game-title {{
            font-size: 1.4em;
            font-weight: bold;
            color: #2c3e50;
        }}
        
        .drops-badge {{
            background: #e74c3c;
            color: white;
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
        }}
        
        .game-stats {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-top: 15px;
        }}
        
        .game-stat {{
            text-align: center;
            padding: 10px;
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
    </style>
</head>
<body>
    <div class="container">
        <div class="success-message">
            🎉 Dashboard funcionando corretamente! Todos os jogos com drops estão sendo exibidos.
        </div>
        
        <div class="header">
            <h1>🎯 Dashboard Final</h1>
            <p>Lista Completa de Jogos com Drops Detectados</p>
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
            html_content += f"""
            <div class="game-card" onclick="openGamePage('{game['game_id']}')">
                <div class="game-header">
                    <div class="game-title">🎮 Jogo #{game['game_id']}</div>
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
                
                <div class="click-hint">👆 Clique para ver detalhes e tabelas completas</div>
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
    
    def create_game_page_html(self, game_id: str, game_drops: List[Dict], game_tables: Dict) -> str:
        """Cria HTML da página individual do jogo"""
        
        drops_count = len(game_drops)
        tables_count = len(game_tables)
        max_drop = max([drop.get('drop_magnitude', 0) for drop in game_drops]) if game_drops else 0
        
        html_content = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jogo #{game_id} - Análise Completa</title>
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
        }}
        
        .positive-drop {{ color: #27ae60; }}
        .negative-drop {{ color: #e74c3c; }}
        
        .drop-meta {{
            color: #7f8c8d;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        
        .table-section {{
            margin-bottom: 30px;
        }}
        
        .table-header {{
            background: #3498db;
            color: white;
            padding: 15px 20px;
            border-radius: 10px 10px 0 0;
            font-weight: bold;
            font-size: 1.2em;
        }}
        
        .odds-table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 0 0 10px 10px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }}
        
        .odds-table th,
        .odds-table td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }}
        
        .odds-table th {{
            background: #ecf0f1;
            font-weight: bold;
            color: #2c3e50;
        }}
        
        .odds-table tr:hover {{
            background: #f8f9fa;
        }}
    </style>
</head>
<body>
    <div class="container">
        <button class="back-btn" onclick="window.history.back()">← Voltar ao Dashboard</button>
        
        <div class="header">
            <h1>🎯 Jogo #{game_id}</h1>
            <p>Análise Completa de Drops e Tabelas</p>
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
        
        # Ordena drops por magnitude (maior primeiro)
        sorted_drops = sorted(game_drops, key=lambda x: x.get('drop_magnitude', 0), reverse=True)
        
        for i, drop in enumerate(sorted_drops):
            drop_magnitude = drop.get('drop_magnitude', 0)
            drop_type = drop.get('drop_type', 'N/A')
            table_type = drop.get('table_type', 'N/A')
            timestamp = drop.get('timestamp', 'N/A')
            score = drop.get('score', 'N/A')
            time_in_game = drop.get('time_in_game', 'N/A')
            home_odds = drop.get('home_odds', 'N/A')
            away_odds = drop.get('away_odds', 'N/A')
            home_change = drop.get('home_change', 0)
            away_change = drop.get('away_change', 0)
            
            html_content += f"""
            <div class="drop-item">
                <div class="drop-info">
                    <div class="drop-details">
                        <strong>#{i+1} - {table_type.upper()} - Drop {drop_type.upper()}</strong><br>
                        <div class="drop-meta">
                            📅 {timestamp} | ⚽ {score} | ⏱️ {time_in_game}' | 
                            🏠 {home_odds} ({home_change:+.0f}%) | 🚪 {away_odds} ({away_change:+.0f}%)
                        </div>
                    </div>
                    <div class="drop-value negative-drop">
                        {drop_magnitude:.1f}%
                    </div>
                </div>
            </div>
            """
        
        html_content += "</div>"
        
        # Seção de tabelas
        if game_tables:
            html_content += """
        <div class="section">
            <h2>📊 Tabelas Completas do Jogo</h2>
            """
            
            for table_name, table_data in game_tables.items():
                if 'table_data' not in table_data or not table_data['table_data']:
                    continue
                    
                table_items = table_data['table_data']
                
                html_content += f"""
            <div class="table-section">
                <div class="table-header">📊 {table_name.upper()} ({len(table_items)} registros)</div>
                <table class="odds-table">
                    <thead>
                        <tr>
                            <th>Data/Hora</th>
                            <th>Tempo</th>
                            <th>Home</th>
                            <th>Draw</th>
                            <th>Away</th>
                            <th>Home %</th>
                            <th>Away %</th>
                        </tr>
                    </thead>
                    <tbody>
                """
                
                # Mostra primeiros 20 registros
                for i, item in enumerate(table_items[:20]):
                    date_time = item.get('Date', '').split()
                    date = date_time[0] if date_time else ''
                    time = item.get('Time', '')
                    
                    html_content += f"""
                        <tr>
                            <td>{date} {time}</td>
                            <td>{item.get('Time', '-')}</td>
                            <td>{item.get('Home', '-')}</td>
                            <td>{item.get('Draw', '-')}</td>
                            <td>{item.get('Away', '-')}</td>
                            <td>{item.get('Home\n (%)', '-')}</td>
                            <td>{item.get('Away\n (%)', '-')}</td>
                        </tr>
                    """
                
                if len(table_items) > 20:
                    html_content += f"""
                        <tr>
                            <td colspan="7" style="text-align: center; color: #7f8c8d; font-style: italic;">
                                ... e mais {len(table_items) - 20} registros
                            </td>
                        </tr>
                    """
                
                html_content += """
                    </tbody>
                </table>
            </div>
                """
            
            html_content += "</div>"
        
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
            
        # Processa dados de drops
        result = self.process_drops_data()
        if not result:
            return False
            
        games_list, total_drops = result
        
        print("\n🎨 Gerando dashboard principal...")
        main_dashboard = self.create_main_dashboard_html(games_list, total_drops)
        
        # Salva dashboard principal
        with open('dashboard_funcionando.html', 'w', encoding='utf-8') as f:
            f.write(main_dashboard)
        print("✅ Dashboard principal salvo: dashboard_funcionando.html")
        
        # Gera páginas individuais dos jogos
        print("\n🎮 Gerando páginas individuais dos jogos...")
        games_created = 0
        
        for game in games_list:
            game_id = game['game_id']
            game_drops = game['drops']
            game_tables = self.games_data.get(game_id, {}).get('tables', {})
            
            game_page = self.create_game_page_html(game_id, game_drops, game_tables)
            
            filename = f'game_{game_id}.html'
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(game_page)
            
            games_created += 1
            if games_created <= 10:  # Mostra apenas os primeiros 10
                print(f"  ✅ Página do jogo {game_id} criada: {filename}")
        
        if games_created > 10:
            print(f"  ... e mais {games_created - 10} páginas criadas")
        
        print(f"\n🎯 Sistema completo gerado com sucesso!")
        print(f"📂 Dashboard principal: dashboard_funcionando.html")
        print(f"🎮 Páginas de jogos criadas: {games_created}")
        print(f"📊 Total de drops: {total_drops:,}")
        print(f"🌐 Abra 'dashboard_funcionando.html' no navegador")
        
        return True

if __name__ == "__main__":
    print("🚀 Iniciando geração do dashboard final funcionando...")
    
    system = FinalWorkingDashboard()
    success = system.generate_complete_system()
    
    if not success:
        print("\n❌ Falha ao gerar sistema de dashboard")
    else:
        print("\n🎉 Dashboard funcionando perfeitamente!")