import json
import os
from datetime import datetime
from typing import Dict, List, Any

class EnhancedDropDashboard:
    def __init__(self, data_file: str = None):
        self.data_file = data_file or self.find_latest_data_file()
        self.drops_data = None
        self.games_data = None
        
    def find_latest_data_file(self) -> str:
        """Encontra o arquivo de dados mais recente"""
        files = [
            'complete_live_data_20250907_172408.json',
            'final_drop_analysis_20250907_182957.json',
            'monitoring_report_20250907_183101.json'
        ]
        
        for file in files:
            if os.path.exists(file):
                return file
        return None
    
    def load_data(self):
        """Carrega os dados dos arquivos"""
        if not self.data_file or not os.path.exists(self.data_file):
            print(f"Arquivo não encontrado: {self.data_file}")
            return False
            
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Se for o arquivo de dados completos
            if 'games_data' in data:
                self.games_data = data['games_data']
                print(f"Carregados dados de {len(self.games_data)} jogos")
                
            # Se for arquivo de análise de drops
            elif 'drops_by_game' in data:
                self.drops_data = data
                print(f"Carregados dados de drops: {data.get('total_drops', 0)} drops")
                
            return True
            
        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
            return False
    
    def extract_game_drops(self, threshold: float = 5.0) -> Dict[str, Any]:
        """Extrai drops dos dados dos jogos"""
        if not self.games_data:
            return {}
            
        games_with_drops = {}
        
        for game_id, game_data in self.games_data.items():
            if not isinstance(game_data, dict) or 'tables' not in game_data:
                continue
                
            game_drops = []
            game_info = {
                'game_id': game_id,
                'drops': [],
                'tables': {},
                'total_drops': 0
            }
            
            # Analisa cada tabela do jogo
            for table_name, table_data in game_data['tables'].items():
                if not isinstance(table_data, dict) or 'table_data' not in table_data:
                    continue
                    
                table_drops = []
                table_info = {
                    'name': table_name,
                    'data': table_data['table_data'],
                    'drops': []
                }
                
                # Analisa cada item da tabela
                for i, item in enumerate(table_data['table_data']):
                    if not isinstance(item, dict):
                        continue
                        
                    # Procura por mudanças percentuais
                    for key, value in item.items():
                        if 'percentage_change' in key and isinstance(value, (int, float)):
                            if abs(value) >= threshold:
                                drop_info = {
                                    'table': table_name,
                                    'item_index': i,
                                    'field': key,
                                    'percentage': value,
                                    'item_data': item,
                                    'timestamp': item.get('date', '') + ' ' + item.get('time', '')
                                }
                                table_drops.append(drop_info)
                                game_drops.append(drop_info)
                
                if table_drops:
                    table_info['drops'] = table_drops
                    game_info['tables'][table_name] = table_info
            
            if game_drops:
                game_info['drops'] = game_drops
                game_info['total_drops'] = len(game_drops)
                games_with_drops[game_id] = game_info
        
        return games_with_drops
    
    def generate_enhanced_html(self, games_with_drops: Dict[str, Any]) -> str:
        """Gera HTML do dashboard aprimorado"""
        
        # Estatísticas gerais
        total_games = len(games_with_drops)
        total_drops = sum(game['total_drops'] for game in games_with_drops.values())
        
        # Top 10 jogos com mais drops
        top_games = sorted(games_with_drops.items(), 
                          key=lambda x: x[1]['total_drops'], 
                          reverse=True)[:10]
        
        # Top 10 maiores drops
        all_drops = []
        for game_id, game_data in games_with_drops.items():
            for drop in game_data['drops']:
                drop['game_id'] = game_id
                all_drops.append(drop)
        
        top_drops = sorted(all_drops, key=lambda x: abs(x['percentage']), reverse=True)[:10]
        
        html_content = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Avançado de Drops - Análise Detalhada</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

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

        .stat-card:hover {{
            transform: translateY(-5px);
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

        .games-count {{ color: #3498db; }}
        .drops-count {{ color: #e74c3c; }}
        .avg-drops {{ color: #f39c12; }}
        .max-drop {{ color: #8e44ad; }}

        .main-content {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }}

        .panel {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        }}

        .panel h2 {{
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 1.5em;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}

        .games-section {{
            grid-column: 1 / -1;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        }}

        .game-card {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 10px;
            margin-bottom: 20px;
            overflow: hidden;
        }}

        .game-header {{
            background: #2c3e50;
            color: white;
            padding: 15px 20px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .game-header:hover {{
            background: #34495e;
        }}

        .game-title {{
            font-size: 1.2em;
            font-weight: bold;
        }}

        .drops-badge {{
            background: #e74c3c;
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.9em;
        }}

        .game-content {{
            display: none;
            padding: 20px;
        }}

        .game-content.active {{
            display: block;
        }}

        .table-section {{
            margin-bottom: 25px;
        }}

        .table-title {{
            background: #3498db;
            color: white;
            padding: 10px 15px;
            border-radius: 8px 8px 0 0;
            font-weight: bold;
        }}

        .odds-table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 0 0 8px 8px;
            overflow: hidden;
        }}

        .odds-table th,
        .odds-table td {{
            padding: 10px 12px;
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

        .drop-value {{
            font-weight: bold;
            color: #e74c3c;
        }}

        .positive-drop {{
            color: #27ae60;
        }}

        .negative-drop {{
            color: #e74c3c;
        }}

        .top-list {{
            list-style: none;
        }}

        .top-item {{
            background: #f8f9fa;
            padding: 12px 15px;
            margin-bottom: 8px;
            border-radius: 8px;
            border-left: 4px solid #3498db;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .top-item:hover {{
            background: #e9ecef;
        }}

        .item-info {{
            flex: 1;
        }}

        .item-value {{
            font-weight: bold;
            color: #e74c3c;
        }}

        .controls {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
            text-align: center;
            margin-bottom: 30px;
        }}

        .btn {{
            background: #3498db;
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 25px;
            font-size: 1em;
            cursor: pointer;
            margin: 0 10px;
            transition: all 0.3s ease;
            font-weight: 600;
        }}

        .btn:hover {{
            background: #2980b9;
            transform: translateY(-2px);
        }}

        @media (max-width: 768px) {{
            .main-content {{
                grid-template-columns: 1fr;
            }}
            
            .container {{
                padding: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Dashboard Avançado de Drops</h1>
            <p>Análise Detalhada de Jogos e Tabelas com Drops Significativos</p>
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
                <div class="stat-number avg-drops">{total_drops/total_games if total_games > 0 else 0:.1f}</div>
                <div class="stat-label">Drops por Jogo</div>
            </div>
            <div class="stat-card">
                <div class="stat-number max-drop">{abs(top_drops[0]['percentage']) if top_drops else 0:.1f}%</div>
                <div class="stat-label">Maior Drop</div>
            </div>
        </div>

        <div class="main-content">
            <div class="panel">
                <h2>🏆 Top 10 Jogos com Mais Drops</h2>
                <ul class="top-list">
        """
        
        # Top jogos
        for game_id, game_data in top_games:
            html_content += f"""
                    <li class="top-item">
                        <div class="item-info">
                            <strong>Jogo #{game_id}</strong><br>
                            <small>{len(game_data['tables'])} tabelas analisadas</small>
                        </div>
                        <div class="item-value">{game_data['total_drops']} drops</div>
                    </li>
            """
        
        html_content += """
                </ul>
            </div>

            <div class="panel">
                <h2>🚨 Top 10 Maiores Drops</h2>
                <ul class="top-list">
        """
        
        # Top drops
        for drop in top_drops:
            html_content += f"""
                    <li class="top-item">
                        <div class="item-info">
                            <strong>Jogo #{drop['game_id']}</strong><br>
                            <small>{drop['table']} - {drop['field']}</small><br>
                            <small>{drop['timestamp']}</small>
                        </div>
                        <div class="item-value {'positive-drop' if drop['percentage'] > 0 else 'negative-drop'}">
                            {drop['percentage']:+.1f}%
                        </div>
                    </li>
            """
        
        html_content += """
                </ul>
            </div>
        </div>

        <div class="games-section">
            <h2>🎮 Jogos Detalhados com Drops</h2>
            <p style="margin-bottom: 20px; color: #7f8c8d;">Clique em um jogo para ver suas tabelas e drops detalhados</p>
        """
        
        # Jogos detalhados
        for game_id, game_data in games_with_drops.items():
            html_content += f"""
            <div class="game-card">
                <div class="game-header" onclick="toggleGame('{game_id}')">
                    <div class="game-title">🎯 Jogo #{game_id}</div>
                    <div class="drops-badge">{game_data['total_drops']} drops</div>
                </div>
                <div class="game-content" id="game-{game_id}">
            """
            
            # Tabelas do jogo
            for table_name, table_info in game_data['tables'].items():
                if not table_info['drops']:
                    continue
                    
                html_content += f"""
                    <div class="table-section">
                        <div class="table-title">📊 Tabela: {table_name} ({len(table_info['drops'])} drops)</div>
                        <table class="odds-table">
                            <thead>
                                <tr>
                                    <th>Data/Hora</th>
                                    <th>Home</th>
                                    <th>Draw</th>
                                    <th>Away</th>
                                    <th>Mudança %</th>
                                    <th>Campo</th>
                                </tr>
                            </thead>
                            <tbody>
                """
                
                # Itens da tabela com drops
                for drop in table_info['drops']:
                    item = drop['item_data']
                    is_drop_row = True
                    
                    html_content += f"""
                                <tr class="{'drop-highlight' if is_drop_row else ''}">
                                    <td>{item.get('date', '')} {item.get('time', '')}</td>
                                    <td>{item.get('home', '-')}</td>
                                    <td>{item.get('draw', '-')}</td>
                                    <td>{item.get('away', '-')}</td>
                                    <td class="drop-value {'positive-drop' if drop['percentage'] > 0 else 'negative-drop'}">
                                        {drop['percentage']:+.1f}%
                                    </td>
                                    <td>{drop['field']}</td>
                                </tr>
                    """
                
                html_content += """
                            </tbody>
                        </table>
                    </div>
                """
            
            html_content += """
                </div>
            </div>
            """
        
        html_content += """
        </div>

        <div class="controls">
            <h2 style="margin-bottom: 20px; color: #2c3e50;">🎛️ Controles</h2>
            <button class="btn" onclick="expandAll()">📖 Expandir Todos</button>
            <button class="btn" onclick="collapseAll()">📕 Recolher Todos</button>
            <button class="btn" onclick="window.print()">🖨️ Imprimir</button>
        </div>
    </div>

    <script>
        function toggleGame(gameId) {
            const content = document.getElementById('game-' + gameId);
            content.classList.toggle('active');
        }

        function expandAll() {
            const contents = document.querySelectorAll('.game-content');
            contents.forEach(content => content.classList.add('active'));
        }

        function collapseAll() {
            const contents = document.querySelectorAll('.game-content');
            contents.forEach(content => content.classList.remove('active'));
        }

        // Efeito de entrada
        window.addEventListener('load', () => {
            const elements = document.querySelectorAll('.stat-card, .panel, .game-card');
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
    
    def create_dashboard(self, output_file: str = 'enhanced_drop_dashboard.html', threshold: float = 5.0):
        """Cria o dashboard completo"""
        print("🔄 Carregando dados...")
        if not self.load_data():
            return False
            
        print("🔍 Extraindo drops dos jogos...")
        games_with_drops = self.extract_game_drops(threshold)
        
        if not games_with_drops:
            print("❌ Nenhum drop encontrado com o threshold especificado")
            return False
            
        print(f"✅ Encontrados {len(games_with_drops)} jogos com drops")
        
        print("🎨 Gerando HTML do dashboard...")
        html_content = self.generate_enhanced_html(games_with_drops)
        
        print(f"💾 Salvando dashboard em {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        print(f"🎯 Dashboard criado com sucesso: {output_file}")
        return True

if __name__ == "__main__":
    # Cria o dashboard
    dashboard = EnhancedDropDashboard()
    
    print("🚀 Iniciando criação do dashboard avançado...")
    success = dashboard.create_dashboard(
        output_file='enhanced_drop_dashboard.html',
        threshold=3.0  # Threshold de 3% para capturar mais drops
    )
    
    if success:
        print("\n✨ Dashboard avançado criado com sucesso!")
        print("📂 Arquivo: enhanced_drop_dashboard.html")
        print("🌐 Abra o arquivo no navegador para visualizar")
    else:
        print("\n❌ Erro ao criar dashboard")