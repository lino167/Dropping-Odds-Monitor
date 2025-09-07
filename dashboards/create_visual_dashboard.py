import json
import os
from datetime import datetime
from typing import Dict, List, Any

def load_drops_analysis():
    """Carrega dados da análise de drops"""
    filename = 'final_drop_analysis_20250907_182957.json'
    
    if not os.path.exists(filename):
        print(f"❌ Arquivo não encontrado: {filename}")
        return None
        
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ Dados carregados: {filename}")
        return data
    except Exception as e:
        print(f"❌ Erro ao carregar dados: {e}")
        return None

def load_complete_data():
    """Carrega dados completos dos jogos"""
    filename = 'complete_live_data_20250907_172408.json'
    
    if not os.path.exists(filename):
        print(f"❌ Arquivo não encontrado: {filename}")
        return None
        
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ Dados completos carregados: {filename}")
        return data.get('games_data', {})
    except Exception as e:
        print(f"❌ Erro ao carregar dados completos: {e}")
        return None

def create_comprehensive_dashboard(drops_data: Dict, games_data: Dict) -> str:
    """Cria dashboard completo com drops e tabelas dos jogos"""
    
    # Estatísticas gerais
    total_games = drops_data.get('games_with_drops', 0)
    total_drops = drops_data.get('total_drops_found', 0)
    threshold = drops_data.get('threshold_used', 0)
    
    results_by_game = drops_data.get('results_by_game', {})
    
    # Prepara dados dos jogos com drops
    games_with_drops = []
    all_drops = []
    
    for game_id, game_results in results_by_game.items():
        if game_results.get('drops_found', 0) > 0:
            game_info = {
                'game_id': game_id,
                'drops_count': game_results.get('drops_found', 0),
                'drops': game_results.get('drops', []),
                'tables_data': games_data.get(game_id, {}).get('tables', {})
            }
            games_with_drops.append(game_info)
            
            # Adiciona drops individuais para ranking
            for drop in game_results.get('drops', []):
                drop['game_id'] = game_id
                all_drops.append(drop)
    
    # Ordena jogos por número de drops
    games_with_drops.sort(key=lambda x: x['drops_count'], reverse=True)
    
    # Top 10 maiores drops
    top_drops = sorted(all_drops, key=lambda x: abs(x.get('percentage_change', 0)), reverse=True)[:10]
    
    html_content = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Visual de Drops - Análise Completa</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1800px;
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
        
        .summary-section {{
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
            font-size: 1.6em;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        
        .games-section {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        }}
        
        .game-card {{
            background: #f8f9fa;
            border: 2px solid #dee2e6;
            border-radius: 12px;
            margin-bottom: 25px;
            overflow: hidden;
            transition: all 0.3s ease;
        }}
        
        .game-card:hover {{
            border-color: #3498db;
            box-shadow: 0 5px 15px rgba(52, 152, 219, 0.2);
        }}
        
        .game-header {{
            background: linear-gradient(135deg, #2c3e50, #34495e);
            color: white;
            padding: 20px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .game-header:hover {{
            background: linear-gradient(135deg, #34495e, #2c3e50);
        }}
        
        .game-title {{
            font-size: 1.4em;
            font-weight: bold;
        }}
        
        .drops-badge {{
            background: #e74c3c;
            color: white;
            padding: 8px 15px;
            border-radius: 25px;
            font-size: 1em;
            font-weight: bold;
        }}
        
        .game-content {{
            display: none;
            padding: 25px;
        }}
        
        .game-content.active {{
            display: block;
        }}
        
        .drops-summary {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
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
            font-size: 0.95em;
        }}
        
        .odds-table tr:hover {{
            background: #f8f9fa;
        }}
        
        .drop-highlight {{
            background: #fff3cd !important;
            border-left: 4px solid #ffc107;
        }}
        
        .drop-item {{
            background: white;
            border: 1px solid #dee2e6;
            border-left: 4px solid #e74c3c;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 12px;
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
        
        .top-list {{
            list-style: none;
        }}
        
        .top-item {{
            background: #f8f9fa;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 8px;
            border-left: 4px solid #3498db;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.3s ease;
        }}
        
        .top-item:hover {{
            background: #e9ecef;
            transform: translateX(5px);
        }}
        
        .item-info {{
            flex: 1;
        }}
        
        .item-value {{
            font-weight: bold;
            color: #e74c3c;
            font-size: 1.1em;
        }}
        
        .controls {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
            text-align: center;
            margin-top: 30px;
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
            .summary-section {{
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
            <h1>🎯 Dashboard Visual de Drops</h1>
            <p>Análise Completa de Jogos com Drops Significativos</p>
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

        <div class="summary-section">
            <div class="panel">
                <h2>🏆 Top 10 Jogos com Mais Drops</h2>
                <ul class="top-list">
    """
    
    # Top 10 jogos
    for i, game in enumerate(games_with_drops[:10]):
        html_content += f"""
                    <li class="top-item">
                        <div class="item-info">
                            <strong>#{i+1} - Jogo {game['game_id']}</strong><br>
                            <small>{len(game['tables_data'])} tabelas disponíveis</small>
                        </div>
                        <div class="item-value">{game['drops_count']} drops</div>
                    </li>
        """
    
    html_content += """
                </ul>
            </div>

            <div class="panel">
                <h2>🚨 Top 10 Maiores Drops</h2>
                <ul class="top-list">
        """
    
    # Top 10 drops
    for i, drop in enumerate(top_drops):
        percentage = drop.get('percentage_change', 0)
        html_content += f"""
                    <li class="top-item">
                        <div class="item-info">
                            <strong>#{i+1} - Jogo {drop['game_id']}</strong><br>
                            <small>{drop.get('table_type', 'N/A')} - {drop.get('bet_type', 'N/A')}</small>
                        </div>
                        <div class="item-value {'positive-drop' if percentage > 0 else 'negative-drop'}">
                            {percentage:+.1f}%
                        </div>
                    </li>
        """
    
    html_content += """
                </ul>
            </div>
        </div>

        <div class="games-section">
            <h2>🎮 Análise Detalhada dos Jogos</h2>
            <p style="margin-bottom: 25px; color: #7f8c8d; font-size: 1.1em;">Clique em um jogo para ver suas tabelas completas e drops detalhados</p>
    """
    
    # Jogos detalhados
    for game in games_with_drops:
        game_id = game['game_id']
        drops_count = game['drops_count']
        drops = game['drops']
        tables_data = game['tables_data']
        
        html_content += f"""
            <div class="game-card">
                <div class="game-header" onclick="toggleGame('{game_id}')">
                    <div class="game-title">🎯 Jogo #{game_id}</div>
                    <div class="drops-badge">{drops_count} drops encontrados</div>
                </div>
                <div class="game-content" id="game-{game_id}">
                    <div class="drops-summary">
                        <h3>📊 Resumo dos Drops</h3>
                        <p><strong>Total de drops:</strong> {drops_count}</p>
                        <p><strong>Tabelas com dados:</strong> {len(tables_data)}</p>
                    </div>
        """
        
        # Lista dos drops encontrados
        if drops:
            html_content += """
                    <h3>🚨 Drops Detectados</h3>
            """
            
            for drop in drops:
                percentage = drop.get('percentage_change', 0)
                html_content += f"""
                    <div class="drop-item">
                        <div class="drop-info">
                            <div class="drop-details">
                                <strong>{drop.get('table_type', 'N/A')} - {drop.get('bet_type', 'N/A')}</strong><br>
                                <small>Odds: {drop.get('old_odds', 'N/A')} → {drop.get('new_odds', 'N/A')}</small>
                            </div>
                            <div class="drop-value {'positive-drop' if percentage > 0 else 'negative-drop'}">
                                {percentage:+.1f}%
                            </div>
                        </div>
                    </div>
                """
        
        # Tabelas completas do jogo
        for table_name, table_data in tables_data.items():
            if 'table_data' not in table_data:
                continue
                
            table_items = table_data['table_data']
            if not table_items:
                continue
                
            html_content += f"""
                    <div class="table-section">
                        <div class="table-header">📊 Tabela: {table_name} ({len(table_items)} registros)</div>
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
            
            # Mostra primeiros 20 registros da tabela
            for i, item in enumerate(table_items[:20]):
                # Verifica se este item tem drop
                has_drop = any(drop.get('table_type') == table_name for drop in drops)
                row_class = 'drop-highlight' if has_drop else ''
                
                date_time = item.get('Date', '').split()
                date = date_time[0] if date_time else ''
                time = item.get('Time', '')
                
                html_content += f"""
                                <tr class="{row_class}">
                                    <td>{date}</td>
                                    <td>{time}</td>
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
        
        html_content += """
                </div>
            </div>
        """
    
    html_content += """
        </div>

        <div class="controls">
            <h2 style="margin-bottom: 20px; color: #2c3e50;">🎛️ Controles do Dashboard</h2>
            <button class="btn" onclick="expandAll()">📖 Expandir Todos os Jogos</button>
            <button class="btn" onclick="collapseAll()">📕 Recolher Todos os Jogos</button>
            <button class="btn" onclick="window.print()">🖨️ Imprimir Dashboard</button>
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

        // Animação de entrada
        window.addEventListener('load', () => {
            const elements = document.querySelectorAll('.stat-card, .panel, .game-card');
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

        // Destaque ao passar o mouse nas linhas da tabela
        document.addEventListener('DOMContentLoaded', function() {
            const tableRows = document.querySelectorAll('.odds-table tr');
            tableRows.forEach(row => {
                row.addEventListener('mouseenter', function() {
                    this.style.backgroundColor = '#e3f2fd';
                });
                row.addEventListener('mouseleave', function() {
                    if (!this.classList.contains('drop-highlight')) {
                        this.style.backgroundColor = '';
                    }
                });
            });
        });
    </script>
</body>
</html>
    """
    
    return html_content

def main():
    print("🚀 Criando Dashboard Visual de Drops...")
    
    # Carrega dados de drops
    print("📊 Carregando análise de drops...")
    drops_data = load_drops_analysis()
    if not drops_data:
        return False
    
    # Carrega dados completos dos jogos
    print("🎮 Carregando dados completos dos jogos...")
    games_data = load_complete_data()
    if not games_data:
        return False
    
    # Cria dashboard
    print("🎨 Gerando dashboard HTML...")
    html_content = create_comprehensive_dashboard(drops_data, games_data)
    
    # Salva arquivo
    output_file = 'visual_drops_dashboard.html'
    print(f"💾 Salvando dashboard: {output_file}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n✅ Dashboard criado com sucesso!")
    print(f"📂 Arquivo: {output_file}")
    print(f"🌐 Abra o arquivo no navegador para visualizar")
    print(f"📊 Jogos com drops: {drops_data.get('games_with_drops', 0)}")
    print(f"🚨 Total de drops: {drops_data.get('total_drops_found', 0):,}")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Falha ao criar dashboard")