import json
import os
from typing import Dict, Any

def analyze_data_structure():
    """Analisa a estrutura dos dados para entender como encontrar drops"""
    
    # Tenta carregar diferentes arquivos
    files_to_check = [
        'complete_live_data_20250907_172408.json',
        'final_drop_analysis_20250907_182957.json', 
        'monitoring_report_20250907_183101.json'
    ]
    
    for filename in files_to_check:
        if os.path.exists(filename):
            print(f"\n📂 Analisando arquivo: {filename}")
            
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                print(f"🔍 Chaves principais: {list(data.keys())}")
                
                # Se for arquivo de análise de drops
                if 'drops_by_game' in data:
                    print("\n📊 ARQUIVO DE ANÁLISE DE DROPS ENCONTRADO!")
                    print(f"Total de drops: {data.get('total_drops', 0)}")
                    print(f"Jogos com drops: {len(data.get('drops_by_game', {}))}")
                    
                    # Mostra estrutura dos drops
                    drops_by_game = data.get('drops_by_game', {})
                    if drops_by_game:
                        first_game = list(drops_by_game.keys())[0]
                        first_game_data = drops_by_game[first_game]
                        print(f"\n🎮 Exemplo - Jogo {first_game}:")
                        print(f"Estrutura: {list(first_game_data.keys())}")
                        
                        if 'drops' in first_game_data:
                            drops = first_game_data['drops']
                            print(f"Total de drops neste jogo: {len(drops)}")
                            
                            if drops:
                                print("\n📋 Exemplo de drop:")
                                example_drop = drops[0]
                                for key, value in example_drop.items():
                                    print(f"  {key}: {value}")
                    
                    return data
                
                # Se for arquivo de dados completos
                elif 'games_data' in data:
                    print("\n📊 ARQUIVO DE DADOS COMPLETOS ENCONTRADO!")
                    games_data = data['games_data']
                    print(f"Total de jogos: {len(games_data)}")
                    
                    # Analisa estrutura de um jogo
                    first_game_id = list(games_data.keys())[0]
                    first_game = games_data[first_game_id]
                    print(f"\n🎮 Exemplo - Jogo {first_game_id}:")
                    print(f"Estrutura: {list(first_game.keys())}")
                    
                    if 'tables' in first_game:
                        tables = first_game['tables']
                        print(f"Tabelas disponíveis: {list(tables.keys())}")
                        
                        # Analisa primeira tabela
                        first_table_name = list(tables.keys())[0]
                        first_table = tables[first_table_name]
                        print(f"\n📊 Tabela {first_table_name}:")
                        print(f"Estrutura: {list(first_table.keys())}")
                        
                        if 'table_data' in first_table:
                            table_data = first_table['table_data']
                            print(f"Itens na tabela: {len(table_data)}")
                            
                            if table_data:
                                print("\n📋 Exemplo de item:")
                                example_item = table_data[0]
                                for key, value in example_item.items():
                                    print(f"  {key}: {value}")
                                    
                                # Procura por campos de percentage_change
                                percentage_fields = [k for k in example_item.keys() if 'percentage' in k.lower()]
                                if percentage_fields:
                                    print(f"\n📈 Campos de porcentagem encontrados: {percentage_fields}")
                                    for field in percentage_fields:
                                        print(f"  {field}: {example_item[field]}")
                
                # Se for arquivo de monitoramento
                elif 'monitoring_stats' in data:
                    print("\n📊 ARQUIVO DE MONITORAMENTO ENCONTRADO!")
                    stats = data.get('monitoring_stats', {})
                    print(f"Estatísticas: {stats}")
                    
                    if 'alerts' in data:
                        alerts = data['alerts']
                        print(f"Total de alertas: {len(alerts)}")
                        
                        if alerts:
                            print("\n🚨 Exemplo de alerta:")
                            example_alert = alerts[0]
                            for key, value in example_alert.items():
                                print(f"  {key}: {value}")
                    
                    return data
                    
            except Exception as e:
                print(f"❌ Erro ao analisar {filename}: {e}")
    
    print("\n❌ Nenhum arquivo de dados encontrado")
    return None

def create_dashboard_from_drops_file(drops_data: Dict[str, Any]) -> str:
    """Cria dashboard usando arquivo de análise de drops"""
    
    if 'drops_by_game' not in drops_data:
        return None
        
    drops_by_game = drops_data['drops_by_game']
    total_drops = drops_data.get('total_drops', 0)
    
    # Estatísticas
    total_games = len(drops_by_game)
    
    # Top jogos com mais drops
    top_games = sorted(drops_by_game.items(), 
                      key=lambda x: len(x[1].get('drops', [])), 
                      reverse=True)[:10]
    
    # Todos os drops para ranking
    all_drops = []
    for game_id, game_data in drops_by_game.items():
        for drop in game_data.get('drops', []):
            drop['game_id'] = game_id
            all_drops.append(drop)
    
    # Top drops por porcentagem
    top_drops = sorted(all_drops, key=lambda x: abs(x.get('percentage_change', 0)), reverse=True)[:10]
    
    html_content = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard de Drops - Análise Detalhada</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333; min-height: 100vh;
        }}
        .container {{ max-width: 1600px; margin: 0 auto; padding: 20px; }}
        .header {{ 
            background: rgba(255, 255, 255, 0.95); border-radius: 15px; 
            padding: 30px; margin-bottom: 30px; 
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1); text-align: center;
        }}
        .header h1 {{ color: #2c3e50; font-size: 2.5em; margin-bottom: 10px; font-weight: 700; }}
        .stats-grid {{ 
            display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 20px; margin-bottom: 30px;
        }}
        .stat-card {{ 
            background: rgba(255, 255, 255, 0.95); border-radius: 15px; 
            padding: 25px; text-align: center; 
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1); transition: transform 0.3s ease;
        }}
        .stat-card:hover {{ transform: translateY(-5px); }}
        .stat-number {{ font-size: 2.2em; font-weight: bold; margin-bottom: 10px; }}
        .stat-label {{ color: #7f8c8d; font-size: 1em; text-transform: uppercase; letter-spacing: 1px; }}
        .games-count {{ color: #3498db; }}
        .drops-count {{ color: #e74c3c; }}
        .avg-drops {{ color: #f39c12; }}
        .max-drop {{ color: #8e44ad; }}
        .panel {{ 
            background: rgba(255, 255, 255, 0.95); border-radius: 15px; 
            padding: 25px; box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1); margin-bottom: 30px;
        }}
        .panel h2 {{ 
            color: #2c3e50; margin-bottom: 20px; font-size: 1.5em; 
            border-bottom: 3px solid #3498db; padding-bottom: 10px;
        }}
        .game-card {{ 
            background: #f8f9fa; border: 1px solid #dee2e6; 
            border-radius: 10px; margin-bottom: 20px; overflow: hidden;
        }}
        .game-header {{ 
            background: #2c3e50; color: white; padding: 15px 20px; 
            cursor: pointer; display: flex; justify-content: space-between; align-items: center;
        }}
        .game-header:hover {{ background: #34495e; }}
        .game-title {{ font-size: 1.2em; font-weight: bold; }}
        .drops-badge {{ 
            background: #e74c3c; color: white; padding: 5px 12px; 
            border-radius: 20px; font-size: 0.9em;
        }}
        .game-content {{ display: none; padding: 20px; }}
        .game-content.active {{ display: block; }}
        .drop-item {{ 
            background: white; border: 1px solid #dee2e6; 
            border-radius: 8px; padding: 15px; margin-bottom: 10px;
            border-left: 4px solid #e74c3c;
        }}
        .drop-info {{ display: flex; justify-content: space-between; align-items: center; }}
        .drop-details {{ flex: 1; }}
        .drop-value {{ font-weight: bold; font-size: 1.2em; }}
        .positive-drop {{ color: #27ae60; }}
        .negative-drop {{ color: #e74c3c; }}
        .top-list {{ list-style: none; }}
        .top-item {{ 
            background: #f8f9fa; padding: 12px 15px; margin-bottom: 8px; 
            border-radius: 8px; border-left: 4px solid #3498db; 
            display: flex; justify-content: space-between; align-items: center;
        }}
        .top-item:hover {{ background: #e9ecef; }}
        .item-info {{ flex: 1; }}
        .item-value {{ font-weight: bold; color: #e74c3c; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Dashboard de Drops - Análise Detalhada</h1>
            <p>Visualização completa dos jogos com drops significativos</p>
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
                <div class="stat-number max-drop">{abs(top_drops[0].get('percentage_change', 0)) if top_drops else 0:.1f}%</div>
                <div class="stat-label">Maior Drop</div>
            </div>
        </div>

        <div class="panel">
            <h2>🏆 Top 10 Jogos com Mais Drops</h2>
            <ul class="top-list">
    """
    
    # Top jogos
    for game_id, game_data in top_games:
        drops_count = len(game_data.get('drops', []))
        html_content += f"""
                <li class="top-item">
                    <div class="item-info">
                        <strong>Jogo #{game_id}</strong><br>
                        <small>{game_data.get('table_type', 'N/A')} - {drops_count} drops</small>
                    </div>
                    <div class="item-value">{drops_count} drops</div>
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
        percentage = drop.get('percentage_change', 0)
        html_content += f"""
                <li class="top-item">
                    <div class="item-info">
                        <strong>Jogo #{drop['game_id']}</strong><br>
                        <small>{drop.get('table_type', 'N/A')} - {drop.get('bet_type', 'N/A')}</small><br>
                        <small>{drop.get('timestamp', 'N/A')}</small>
                    </div>
                    <div class="item-value {'positive-drop' if percentage > 0 else 'negative-drop'}">
                        {percentage:+.1f}%
                    </div>
                </li>
        """
    
    html_content += """
            </ul>
        </div>

        <div class="panel">
            <h2>🎮 Jogos Detalhados com Drops</h2>
            <p style="margin-bottom: 20px; color: #7f8c8d;">Clique em um jogo para ver seus drops detalhados</p>
    """
    
    # Jogos detalhados
    for game_id, game_data in drops_by_game.items():
        drops = game_data.get('drops', [])
        if not drops:
            continue
            
        html_content += f"""
            <div class="game-card">
                <div class="game-header" onclick="toggleGame('{game_id}')">
                    <div class="game-title">🎯 Jogo #{game_id}</div>
                    <div class="drops-badge">{len(drops)} drops</div>
                </div>
                <div class="game-content" id="game-{game_id}">
        """
        
        # Drops do jogo
        for i, drop in enumerate(drops):
            percentage = drop.get('percentage_change', 0)
            html_content += f"""
                    <div class="drop-item">
                        <div class="drop-info">
                            <div class="drop-details">
                                <strong>{drop.get('table_type', 'N/A')} - {drop.get('bet_type', 'N/A')}</strong><br>
                                <small>Odds: {drop.get('old_odds', 'N/A')} → {drop.get('new_odds', 'N/A')}</small><br>
                                <small>Timestamp: {drop.get('timestamp', 'N/A')}</small>
                            </div>
                            <div class="drop-value {'positive-drop' if percentage > 0 else 'negative-drop'}">
                                {percentage:+.1f}%
                            </div>
                        </div>
                    </div>
            """
        
        html_content += """
                </div>
            </div>
        """
    
    html_content += """
        </div>
    </div>

    <script>
        function toggleGame(gameId) {
            const content = document.getElementById('game-' + gameId);
            content.classList.toggle('active');
        }
    </script>
</body>
</html>
    """
    
    return html_content

if __name__ == "__main__":
    print("🔍 Analisando estrutura dos dados...")
    data = analyze_data_structure()
    
    if data and 'drops_by_game' in data:
        print("\n🎨 Criando dashboard a partir dos dados de drops...")
        html_content = create_dashboard_from_drops_file(data)
        
        if html_content:
            with open('visual_drops_dashboard.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print("\n✅ Dashboard criado: visual_drops_dashboard.html")
        else:
            print("\n❌ Erro ao gerar HTML do dashboard")
    else:
        print("\n❌ Dados de drops não encontrados")