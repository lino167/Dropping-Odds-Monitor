import json
import os
from datetime import datetime
from typing import Dict, List, Any

class FixDropsDetection:
    def __init__(self):
        self.drops_data = None
        self.games_data = None
        
    def load_and_analyze_data(self):
        """Carrega e analisa todos os dados para encontrar onde estão os drops reais"""
        
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
    
    def find_real_drops(self):
        """Encontra onde estão os drops reais nos dados"""
        
        print("\n🔍 Procurando drops reais nos dados...\n")
        
        # Verifica estrutura completa dos dados de drops
        print("📊 Estrutura completa dos dados de drops:")
        for key, value in self.drops_data.items():
            if isinstance(value, dict):
                print(f"   {key}: dict com {len(value)} itens")
                if key == 'results_by_game' and len(value) > 0:
                    first_game_id = list(value.keys())[0]
                    first_game = value[first_game_id]
                    print(f"      Exemplo (jogo {first_game_id}): {first_game}")
            elif isinstance(value, list):
                print(f"   {key}: lista com {len(value)} itens")
                if len(value) > 0:
                    print(f"      Primeiro item: {value[0]}")
            else:
                print(f"   {key}: {value}")
        
        # Procura por drops em diferentes locais
        print("\n🔍 Procurando drops em diferentes estruturas...")
        
        # Verifica se há uma lista de drops global
        if 'all_drops' in self.drops_data:
            all_drops = self.drops_data['all_drops']
            print(f"✅ Encontrada lista 'all_drops' com {len(all_drops)} itens")
            if len(all_drops) > 0:
                print(f"   Primeiro drop: {all_drops[0]}")
                return self.create_dashboard_with_all_drops(all_drops)
        
        # Verifica se há drops em uma estrutura diferente
        if 'drops_detected' in self.drops_data:
            drops_detected = self.drops_data['drops_detected']
            print(f"✅ Encontrada lista 'drops_detected' com {len(drops_detected)} itens")
            if len(drops_detected) > 0:
                print(f"   Primeiro drop: {drops_detected[0]}")
                return self.create_dashboard_with_detected_drops(drops_detected)
        
        # Verifica se há drops em summary
        if 'summary' in self.drops_data:
            summary = self.drops_data['summary']
            print(f"✅ Encontrado 'summary': {summary}")
            if 'drops_by_game' in summary:
                drops_by_game = summary['drops_by_game']
                print(f"   drops_by_game: {len(drops_by_game)} jogos")
                return self.create_dashboard_with_summary_drops(drops_by_game)
        
        # Se não encontrou, vamos procurar em todas as chaves
        print("\n🔍 Procurando em todas as chaves...")
        for key, value in self.drops_data.items():
            if isinstance(value, list) and len(value) > 0:
                first_item = value[0]
                if isinstance(first_item, dict) and ('percentage_change' in first_item or 'drop' in str(first_item).lower()):
                    print(f"✅ Possíveis drops encontrados em '{key}' com {len(value)} itens")
                    print(f"   Primeiro item: {first_item}")
                    return self.create_dashboard_with_drops_list(key, value)
        
        print("❌ Não foi possível encontrar a estrutura de drops")
        return False
    
    def create_dashboard_with_drops_list(self, drops_key: str, drops_list: List[Dict]) -> bool:
        """Cria dashboard usando uma lista de drops encontrada"""
        
        print(f"\n🎨 Criando dashboard com drops de '{drops_key}'...")
        
        # Agrupa drops por jogo
        drops_by_game = {}
        for drop in drops_list:
            game_id = drop.get('game_id', 'unknown')
            if game_id not in drops_by_game:
                drops_by_game[game_id] = []
            drops_by_game[game_id].append(drop)
        
        print(f"📊 Drops agrupados por {len(drops_by_game)} jogos")
        
        # Cria lista de jogos para o dashboard
        games_list = []
        for game_id, game_drops in drops_by_game.items():
            if len(game_drops) > 0:
                max_drop = max([abs(drop.get('percentage_change', 0)) for drop in game_drops])
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
        
        print(f"🎮 {len(games_list)} jogos com drops para o dashboard")
        
        # Gera dashboard principal
        main_dashboard = self.create_main_dashboard_html(games_list, len(drops_list))
        
        with open('dashboard_corrigido.html', 'w', encoding='utf-8') as f:
            f.write(main_dashboard)
        print("✅ Dashboard principal salvo: dashboard_corrigido.html")
        
        # Gera páginas individuais
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
            if games_created <= 5:  # Mostra apenas os primeiros 5
                print(f"  ✅ Página do jogo {game_id} criada: {filename}")
        
        if games_created > 5:
            print(f"  ... e mais {games_created - 5} páginas criadas")
        
        print(f"\n🎯 Sistema corrigido gerado com sucesso!")
        print(f"📂 Dashboard principal: dashboard_corrigido.html")
        print(f"🎮 Páginas de jogos criadas: {games_created}")
        
        return True
    
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
    <title>Dashboard Corrigido - Lista de Jogos</title>
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
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Dashboard Corrigido</h1>
            <p>Lista de Jogos com Drops Detectados</p>
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
                <div class="stat-label">Status</div>
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
                
                <div class="click-hint">👆 Clique para ver detalhes completos</div>
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
        }}
        
        .drop-info {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .drop-value {{
            font-weight: bold;
            font-size: 1.3em;
        }}
        
        .positive-drop {{ color: #27ae60; }}
        .negative-drop {{ color: #e74c3c; }}
    </style>
</head>
<body>
    <div class="container">
        <button class="back-btn" onclick="window.history.back()">← Voltar ao Dashboard</button>
        
        <div class="header">
            <h1>🎯 Jogo #{game_id}</h1>
            <p>Análise Detalhada de Drops</p>
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
            <h2>🚨 Drops Detectados</h2>
        """
        
        for i, drop in enumerate(game_drops):
            percentage = drop.get('percentage_change', 0)
            table_type = drop.get('table_type', 'N/A')
            bet_type = drop.get('bet_type', 'N/A')
            old_odds = drop.get('old_odds', 'N/A')
            new_odds = drop.get('new_odds', 'N/A')
            
            html_content += f"""
            <div class="drop-item">
                <div class="drop-info">
                    <div class="drop-details">
                        <strong>#{i+1} - {table_type} - {bet_type}</strong><br>
                        <small>Odds: {old_odds} → {new_odds}</small>
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
</body>
</html>
        """
        
        return html_content

if __name__ == "__main__":
    print("🚀 Iniciando correção do sistema de dashboard...")
    
    system = FixDropsDetection()
    if system.load_and_analyze_data():
        system.find_real_drops()
    else:
        print("❌ Falha ao carregar dados")