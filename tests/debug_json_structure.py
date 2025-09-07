#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de debug para examinar a estrutura do JSON
"""

import json
from typing import Any, Dict

def main():
    """Função principal"""
    json_file = "complete_live_data_20250907_172408.json"
    
    print("🔍 ANALISANDO ESTRUTURA DO JSON")
    print("=" * 50)
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📁 Arquivo carregado: {json_file}")
        print(f"📊 Tipo raiz: {type(data)}")
        
        if isinstance(data, dict):
            print(f"🔑 Chaves principais: {list(data.keys())}")
            
            # Verifica games_data
            if 'games_data' in data:
                games_data = data['games_data']
                print(f"\n📊 games_data: {type(games_data)}")
                
                if isinstance(games_data, dict):
                    game_ids = list(games_data.keys())[:3]
                    print(f"🎮 Primeiros 3 IDs de jogos: {game_ids}")
                    
                    # Examina primeiro jogo
                    if game_ids:
                        first_game_id = game_ids[0]
                        first_game = games_data[first_game_id]
                        print(f"\n🎯 ESTRUTURA DO JOGO {first_game_id}:")
                        print(f"   Tipo: {type(first_game)}")
                        
                        if isinstance(first_game, dict):
                            print(f"   Chaves: {list(first_game.keys())}")
                            
                            # Verifica tabelas
                            if 'tables' in first_game:
                                tables = first_game['tables']
                                print(f"\n📋 TABELAS DISPONÍVEIS:")
                                print(f"   Tipo: {type(tables)}")
                                
                                if isinstance(tables, dict):
                                    table_names = list(tables.keys())
                                    print(f"   Nomes: {table_names}")
                                    
                                    # Examina primeira tabela
                                    if table_names:
                                        first_table_name = table_names[0]
                                        first_table = tables[first_table_name]
                                        print(f"\n📊 TABELA {first_table_name}:")
                                        print(f"   Tipo: {type(first_table)}")
                                        
                                        if isinstance(first_table, dict):
                                            print(f"   Chaves: {list(first_table.keys())}")
                                            
                                            # Verifica table_data
                                            if 'table_data' in first_table:
                                                table_data = first_table['table_data']
                                                print(f"\n📋 TABLE_DATA:")
                                                print(f"   Tipo: {type(table_data)}")
                                                
                                                if isinstance(table_data, list):
                                                    print(f"   Quantidade de itens: {len(table_data)}")
                                                    
                                                    if len(table_data) > 0:
                                                        first_item = table_data[0]
                                                        print(f"\n📝 PRIMEIRO ITEM:")
                                                        print(f"   Tipo: {type(first_item)}")
                                                        
                                                        if isinstance(first_item, dict):
                                                            print(f"   Chaves: {list(first_item.keys())}")
                                                            print(f"\n📄 EXEMPLO COMPLETO:")
                                                            for key, value in first_item.items():
                                                                print(f"     {key}: {value} ({type(value).__name__})")
                                                            
                                                            # Verifica se tem mudanças percentuais
                                                            if 'Home\n (%)' in first_item or 'Away\n (%)' in first_item:
                                                                print(f"\n✅ ENCONTRADAS MUDANÇAS PERCENTUAIS!")
                                                                home_change = first_item.get('Home\n (%)', 'N/A')
                                                                away_change = first_item.get('Away\n (%)', 'N/A')
                                                                print(f"   Home: {home_change}")
                                                                print(f"   Away: {away_change}")
                                                                
                                                                # Procura por drops significativos
                                                                print(f"\n🔍 PROCURANDO DROPS SIGNIFICATIVOS...")
                                                                drops_found = 0
                                                                for i, item in enumerate(table_data[:20]):  # Primeiros 20
                                                                    if isinstance(item, dict):
                                                                        home_pct = item.get('Home\n (%)', '0%')
                                                                        away_pct = item.get('Away\n (%)', '0%')
                                                                        
                                                                        try:
                                                                            home_val = float(str(home_pct).replace('%', '').replace('+', ''))
                                                                            away_val = float(str(away_pct).replace('%', '').replace('+', ''))
                                                                            
                                                                            if abs(home_val) >= 5 or abs(away_val) >= 5:
                                                                                drops_found += 1
                                                                                if drops_found <= 3:  # Mostra apenas os primeiros 3
                                                                                    print(f"   🎯 Drop {drops_found}: Home {home_val}%, Away {away_val}% - {item.get('Date', 'N/A')}")
                                                                        except:
                                                                            pass
                                                                
                                                                if drops_found > 3:
                                                                    print(f"   ... e mais {drops_found - 3} drops encontrados!")
                                                                elif drops_found == 0:
                                                                    print(f"   ❌ Nenhum drop >= 5% encontrado nos primeiros 20 itens")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()