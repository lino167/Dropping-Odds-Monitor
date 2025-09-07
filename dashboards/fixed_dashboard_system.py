import json
import os
from datetime import datetime
from typing import Dict, List, Any

class FixedDashboardSystem:
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
    
    def create_game_page(self, game_id: str, game_drops: List[Dict], game_tables: Dict) -> str:
        """Cria página individual do jogo"""
        
        drops_count = len(game_drops)
        tables_count = len(game_tables)
        
        # Calcula estatísticas do jogo
        max_drop = max([abs(drop.get('percentage_change', 0)) for drop in game_drops]) if game_drops else 0
        
        html_content = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jogo #{game_id} - Análise Detalhada</title>
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
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
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
            transition: transform 0.3s ease;
        }}
        
        .stat-card:hover {{ transform: translateY(-5px); }}
        
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
        
        .drop-highlight {{
            background: #fff3cd !important;
            border-left: 4px solid #ffc107;
        }}
        
        .no-data {{
            text-align: center;
            color: #7f8c8d;
            font-style: italic;
            padding: 40px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <button class="back-btn" onclick="window.history.back()">← Voltar ao Dashboard</button>
        
        <div class="header">
            <h1>🎯 Jogo #{game_id}</h1>
            <p>Análise Detalhada de Drops e Tabelas</p>
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
        """
        
        # Seção de drops
        if game_drops:
            html_content += """
        <div class="section">
            <h2>🚨 Drops Detectados</h2>
            """
            
            for i, drop in enumerate(game_drops):
                percentage = drop.get('percentage_change', 0)
                html_content += f"""
            <div class="drop-item">
                <div class="drop-info">
                    <div class="drop-details">
                        <strong>#{i+1} - {drop.get('table_type', 'N/A')} - {drop.get('bet_type', 'N/A')}</strong><br>
                        <small>Odds: {drop.get('old_odds', 'N/A')} → {drop.get('new_odds', 'N/A')}</small>
                    </div>
                    <div class="drop-value {'positive-drop' if percentage > 0 else 'negative-drop'}">
                        {percentage:+.1f}%
                    </div>
                </div>
            </div>
                """
            
            html_content += "</div>"
        
        # Seção de tabelas
        if game_tables:
            html_content += """
        <div class="section">
            <h2>📊 Tabelas Completas</h2>
            """
            
            for table_name, table_data in game_tables.items():
                if 'table_data' not in table_data or not table_data['table_data']:
                    continue
                    
                table_items = table_data['table_data']
                
                html_content += f"""
            <div class="table-section">
                <div class="table-header">📊 {table_name} ({len(table_items)} registros)</div>
                <table class="odds-table">
                    <thead>
                        <tr>
                            <th>Data</th>
                            <th>Hora</th>
                            <th>Home</th>
                            <th>Draw</th>
                            <th>Away</th>
                            <th>Home %</th>
                            <th>Away %</th>
                        </tr>
                    </thead>
                    <tbody>
                """
                
                # Mostra todos os registros (limitado a 50 para performance)
                for i, item in enumerate(table_items[:50]):
                    date_time = item.get('Date', '').split()
                    date = date_time[0] if date_time else ''
                    time = item.get('Time', '')
                    
                    html_content += f"""
                        <tr>
                            <td>{date}</td>
                            <td>{time}</td>
                            <td>{item.get('Home', '-')}</td>
                            <td>{item.get('Draw', '-')}</td>
                            <td>{item.get('Away', '-')}</td>
                            <td>{item.get('Home\n (%)', '-')}</td>
                            <td>{item.get('Away\n (%)', '-')}</td>
                        </tr>
                    """
                
                if len(table_items) > 50:
                    html_content += f"""
                        <tr>
                            <td colspan="7" style="text-align: center; color: #7f8c8d; font-style: italic;">
                                ... e mais {len(table_items) - 50} registros
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

    <script>
        // Animação de entrada
        window.addEventListener('load', () => {
            const elements = document.querySelectorAll('.stat-card, .section, .drop-item');
            elements.forEach((el, index) => {
                el.style.opacity = '0';
                el.style.transform = 'translateY(20px)';
                
                setTimeout(() => {
                    el.style.transition = 'all 0.6s ease';
                    el.style.opacity = '1';
                    el.style.transform = 'translateY(0)';
                }, index * 50);
            });
        });
    </script>
</body>
</html>
        """
        
        return html_content
    
    def create_main_dashboard(self) -> str:
        """Cria dashboard principal com lista de jogos"""
        
        if not self.drops_data or not self.games_data:
            return None
            
        results_by_game = self.drops_data.get('results_by_game', {})
        total_games = self.drops_data.get('games_with_drops', 0)
        total_drops = self.drops_data.get('total_drops_found', 0)
        threshold = self.drops_data.get('threshold_used', 0)
        
        # Prepara lista de jogos com drops
        games_list = []
        for game_id, game_results in results_by_game.items():
            if game_results.get('drops_found', 0) > 0:
                drops = game_results.get('drops', [])
                max_drop = max([abs(drop.get('percentage_change', 0)) for drop in drops]) if drops else 0
                
                games_list.append({
                    'game_id': game_id,
                    'drops_count': game_results.get('drops_found', 0),
                    'max_drop': max_drop,
                    'tables_count': len(self.games_data.get(game_id, {}).get('tables', {}))
                })
        
        # Ordena por número de drops
        games_list.sort(key=lambda x: x['drops_count'], reverse=True)
        
        html_content = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard de Drops - Lista de Jogos</title>
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
        .threshold {{ color: #8e44ad; }}
        
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
        
        .no-games {{
            text-align: center;
            color: #7f8c8d;
            font-size: 1.2em;
            padding: 60px;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Dashboard de Drops</h1>
            <p>Lista de Jogos com Drops Significativos</p>
            <p style="color: #7f8c8d; margin-top: 10px;">Threshold: {threshold}% | Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}</p>
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
                <div class="stat-number avg-drops">{total_drops/total_games if total_games > 0 else 0:.1f}</div>
                <div class="stat-label">Drops por Jogo</div>
            </div>
            <div class="stat-card">
                <div class="stat-number threshold">{threshold}%</div>
                <div class="stat-label">Threshold Usado</div>
            </div>
        </div>
        """
        
        if games_list:
            html_content += """
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
                
                <div class="click-hint">👆 Clique para ver detalhes completos</div>
            </div>
                """
            
            html_content += "</div>"
        else:
            html_content += """
        <div class="no-games">
            <h2>😔 Nenhum jogo encontrado</h2>
            <p>Não foram encontrados jogos com drops no threshold especificado.</p>
        </div>
            """
        
        html_content += """
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
    
    def generate_all_files(self):
        """Gera dashboard principal e páginas individuais dos jogos"""
        
        if not self.load_data():
            return False
            
        print("🎨 Gerando dashboard principal...")
        main_dashboard = self.create_main_dashboard()
        
        if not main_dashboard:
            print("❌ Erro ao gerar dashboard principal")
            return False
            
        # Salva dashboard principal
        with open('dashboard_principal.html', 'w', encoding='utf-8') as f:
            f.write(main_dashboard)
        print("✅ Dashboard principal salvo: dashboard_principal.html")
        
        # Gera páginas individuais dos jogos
        results_by_game = self.drops_data.get('results_by_game', {})
        games_created = 0
        
        print("🎮 Gerando páginas individuais dos jogos...")
        for game_id, game_results in results_by_game.items():
            if game_results.get('drops_found', 0) > 0:
                game_drops = game_results.get('drops', [])
                game_tables = self.games_data.get(game_id, {}).get('tables', {})
                
                game_page = self.create_game_page(game_id, game_drops, game_tables)
                
                filename = f'game_{game_id}.html'
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(game_page)
                
                games_created += 1
                print(f"  ✅ Página do jogo {game_id} criada: {filename}")
        
        print(f"\n🎯 Sistema completo gerado com sucesso!")
        print(f"📂 Dashboard principal: dashboard_principal.html")
        print(f"🎮 Páginas de jogos criadas: {games_created}")
        print(f"🌐 Abra 'dashboard_principal.html' no navegador para começar")
        
        return True

if __name__ == "__main__":
    print("🚀 Iniciando geração do sistema de dashboard corrigido...")
    
    system = FixedDashboardSystem()
    success = system.generate_all_files()
    
    if not success:
        print("\n❌ Falha ao gerar sistema de dashboard")