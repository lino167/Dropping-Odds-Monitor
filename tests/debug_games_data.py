import json
import os

def debug_games_structure():
    """Debug da estrutura dos dados para entender por que os jogos não aparecem"""
    
    print("🔍 Debugando estrutura dos dados...\n")
    
    # Carrega dados de drops
    drops_file = 'final_drop_analysis_20250907_182957.json'
    if os.path.exists(drops_file):
        with open(drops_file, 'r', encoding='utf-8') as f:
            drops_data = json.load(f)
        
        print(f"📊 Arquivo de drops: {drops_file}")
        print(f"   Chaves principais: {list(drops_data.keys())}")
        
        if 'results_by_game' in drops_data:
            results_by_game = drops_data['results_by_game']
            print(f"   Total de jogos nos resultados: {len(results_by_game)}")
            
            # Mostra primeiros 5 jogos
            game_ids = list(results_by_game.keys())[:5]
            print(f"   Primeiros 5 IDs de jogos: {game_ids}")
            
            for game_id in game_ids:
                game_result = results_by_game[game_id]
                drops_found = game_result.get('drops_found', 0)
                drops_list = game_result.get('drops', [])
                
                print(f"\n   🎮 Jogo {game_id}:")
                print(f"      - Drops encontrados: {drops_found}")
                print(f"      - Lista de drops: {len(drops_list)} itens")
                
                if drops_list:
                    first_drop = drops_list[0]
                    print(f"      - Primeiro drop: {first_drop}")
                    
                    # Verifica se tem percentage_change
                    if 'percentage_change' in first_drop:
                        percentage = first_drop['percentage_change']
                        print(f"      - Percentage change: {percentage}%")
                        print(f"      - Abs percentage: {abs(percentage)}%")
        else:
            print("   ❌ Chave 'results_by_game' não encontrada")
    else:
        print(f"❌ Arquivo não encontrado: {drops_file}")
        return
    
    print("\n" + "="*60 + "\n")
    
    # Carrega dados dos jogos
    games_file = 'complete_live_data_20250907_172408.json'
    if os.path.exists(games_file):
        with open(games_file, 'r', encoding='utf-8') as f:
            complete_data = json.load(f)
        
        print(f"📊 Arquivo de jogos: {games_file}")
        print(f"   Chaves principais: {list(complete_data.keys())}")
        
        if 'games_data' in complete_data:
            games_data = complete_data['games_data']
            print(f"   Total de jogos nos dados: {len(games_data)}")
            
            # Mostra primeiros 3 jogos
            game_ids = list(games_data.keys())[:3]
            print(f"   Primeiros 3 IDs de jogos: {game_ids}")
            
            for game_id in game_ids:
                game_data = games_data[game_id]
                tables = game_data.get('tables', {})
                
                print(f"\n   🎮 Jogo {game_id}:")
                print(f"      - Chaves: {list(game_data.keys())}")
                print(f"      - Tabelas: {len(tables)} ({list(tables.keys())[:3]})")
        else:
            print("   ❌ Chave 'games_data' não encontrada")
    else:
        print(f"❌ Arquivo não encontrado: {games_file}")
    
    print("\n" + "="*60 + "\n")
    
    # Testa lógica de filtragem
    print("🧪 Testando lógica de filtragem...")
    
    if 'results_by_game' in drops_data and 'games_data' in complete_data:
        results_by_game = drops_data['results_by_game']
        games_data = complete_data['games_data']
        
        games_with_drops = []
        
        for game_id, game_results in results_by_game.items():
            drops_found = game_results.get('drops_found', 0)
            print(f"   Jogo {game_id}: {drops_found} drops")
            
            if drops_found > 0:
                drops = game_results.get('drops', [])
                max_drop = max([abs(drop.get('percentage_change', 0)) for drop in drops]) if drops else 0
                tables_count = len(games_data.get(game_id, {}).get('tables', {}))
                
                games_with_drops.append({
                    'game_id': game_id,
                    'drops_count': drops_found,
                    'max_drop': max_drop,
                    'tables_count': tables_count
                })
                
                print(f"      ✅ Adicionado: {drops_found} drops, max: {max_drop:.1f}%, tabelas: {tables_count}")
        
        print(f"\n🎯 Total de jogos filtrados: {len(games_with_drops)}")
        
        if games_with_drops:
            print("\n📋 Lista de jogos com drops:")
            for game in games_with_drops[:10]:  # Mostra apenas os primeiros 10
                print(f"   - Jogo {game['game_id']}: {game['drops_count']} drops, max {game['max_drop']:.1f}%")
        else:
            print("\n❌ Nenhum jogo passou no filtro!")
    
    print("\n🔍 Debug concluído!")

if __name__ == "__main__":
    debug_games_structure()