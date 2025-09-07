#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detector final de drops - funciona com a estrutura real dos dados
"""

import json
from datetime import datetime
from typing import Dict, List, Any

def load_json_data(filename: str) -> Dict:
    """Carrega dados do arquivo JSON"""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_percentage_value(pct_str: str) -> float:
    """Extrai valor numérico de string de percentual"""
    if not pct_str or pct_str == '-' or pct_str.strip() == '':
        return 0.0
    
    try:
        # Remove %, +, espaços e quebras de linha
        clean_str = str(pct_str).replace('%', '').replace('+', '').replace('\n', '').strip()
        return float(clean_str)
    except (ValueError, AttributeError):
        return 0.0

def detect_drops_in_game(game_data: Dict, threshold: float = 5.0) -> Dict:
    """Detecta drops em um jogo específico"""
    results = {
        'game_id': game_data.get('game_id', 'unknown'),
        'tables_analyzed': 0,
        'total_drops': 0,
        'drops_by_table': {}
    }
    
    if 'tables' not in game_data:
        return results
    
    tables = game_data['tables']
    
    for table_name, table_info in tables.items():
        if 'table_data' not in table_info:
            continue
            
        table_data = table_info['table_data']
        if not isinstance(table_data, list):
            continue
            
        results['tables_analyzed'] += 1
        table_drops = []
        
        for i, entry in enumerate(table_data):
            if not isinstance(entry, dict):
                continue
                
            # Extrai mudanças percentuais
            home_change_str = entry.get('Home\n (%)', '0')
            away_change_str = entry.get('Away\n (%)', '0')
            
            home_change = extract_percentage_value(home_change_str)
            away_change = extract_percentage_value(away_change_str)
            
            # Verifica se há drop significativo
            if abs(home_change) >= threshold or abs(away_change) >= threshold:
                drop_info = {
                    'index': i,
                    'timestamp': entry.get('Date', ''),
                    'time_in_game': entry.get('Time', ''),
                    'score': entry.get('Score', ''),
                    'home_odds': entry.get('Home', 0),
                    'draw_odds': entry.get('Draw', 0),
                    'away_odds': entry.get('Away', 0),
                    'home_change': home_change,
                    'away_change': away_change,
                    'home_change_raw': home_change_str,
                    'away_change_raw': away_change_str,
                    'drop_magnitude': max(abs(home_change), abs(away_change)),
                    'drop_type': 'home' if abs(home_change) > abs(away_change) else 'away'
                }
                table_drops.append(drop_info)
        
        if table_drops:
            results['drops_by_table'][table_name] = table_drops
            results['total_drops'] += len(table_drops)
    
    return results

def analyze_all_games(data: Dict, threshold: float = 5.0) -> Dict:
    """Analisa todos os jogos em busca de drops"""
    analysis_results = {
        'timestamp': datetime.now().strftime('%Y%m%d_%H%M%S'),
        'threshold_used': threshold,
        'games_analyzed': 0,
        'games_with_drops': 0,
        'total_drops_found': 0,
        'results_by_game': {},
        'summary': {
            'top_drops': [],
            'drops_by_table_type': {}
        }
    }
    
    if 'games_data' not in data:
        print("❌ Chave 'games_data' não encontrada")
        return analysis_results
    
    games_data = data['games_data']
    all_drops = []
    
    print(f"🔍 ANALISANDO {len(games_data)} JOGOS (threshold: {threshold}%)")
    print("=" * 60)
    
    for game_id, game_info in games_data.items():
        analysis_results['games_analyzed'] += 1
        
        print(f"\n📊 Analisando jogo {game_id}...")
        
        game_results = detect_drops_in_game(game_info, threshold)
        
        if game_results['total_drops'] > 0:
            analysis_results['games_with_drops'] += 1
            analysis_results['total_drops_found'] += game_results['total_drops']
            analysis_results['results_by_game'][game_id] = game_results
            
            print(f"  ✅ {game_results['total_drops']} drops encontrados em {game_results['tables_analyzed']} tabelas")
            
            # Coleta drops para ranking geral
            for table_name, drops in game_results['drops_by_table'].items():
                for drop in drops:
                    drop['game_id'] = game_id
                    drop['table_type'] = table_name
                    all_drops.append(drop)
                    
                    # Conta por tipo de tabela
                    if table_name not in analysis_results['summary']['drops_by_table_type']:
                        analysis_results['summary']['drops_by_table_type'][table_name] = 0
                    analysis_results['summary']['drops_by_table_type'][table_name] += 1
                
                # Mostra alguns exemplos
                for drop in drops[:2]:  # Primeiros 2 de cada tabela
                    print(f"    🎯 {table_name}: {drop['drop_type']} {drop['drop_magnitude']:.1f}% - {drop['timestamp']}")
        else:
            print(f"  ❌ Nenhum drop encontrado")
    
    # Ordena drops por magnitude
    all_drops.sort(key=lambda x: x['drop_magnitude'], reverse=True)
    analysis_results['summary']['top_drops'] = all_drops[:20]  # Top 20
    
    return analysis_results

def print_summary(results: Dict) -> None:
    """Imprime resumo dos resultados"""
    print(f"\n🎯 RESUMO FINAL")
    print("=" * 50)
    print(f"📊 Jogos analisados: {results['games_analyzed']}")
    print(f"🎮 Jogos com drops: {results['games_with_drops']}")
    print(f"📈 Total de drops: {results['total_drops_found']}")
    print(f"🎚️ Threshold usado: {results['threshold_used']}%")
    
    if results['total_drops_found'] > 0:
        print(f"\n🏆 TOP 10 MAIORES DROPS:")
        for i, drop in enumerate(results['summary']['top_drops'][:10], 1):
            print(f"  {i:2d}. {drop['game_id']} ({drop['table_type']}) - {drop['drop_type']} {drop['drop_magnitude']:.1f}% - {drop['timestamp']}")
        
        print(f"\n📋 DROPS POR TIPO DE TABELA:")
        for table_type, count in results['summary']['drops_by_table_type'].items():
            print(f"  {table_type}: {count} drops")

def save_results(results: Dict, filename: str = None) -> str:
    """Salva resultados em arquivo JSON"""
    if filename is None:
        timestamp = results['timestamp']
        filename = f"final_drop_analysis_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    return filename

def main():
    """Função principal"""
    json_file = "complete_live_data_20250907_172408.json"
    
    print("🚀 DETECTOR FINAL DE DROPS")
    print("=" * 50)
    
    try:
        # Carrega dados
        print(f"📁 Carregando {json_file}...")
        data = load_json_data(json_file)
        
        # Analisa com diferentes thresholds
        thresholds = [3.0, 5.0, 10.0]
        
        for threshold in thresholds:
            print(f"\n" + "=" * 60)
            print(f"🎚️ ANÁLISE COM THRESHOLD {threshold}%")
            print("=" * 60)
            
            results = analyze_all_games(data, threshold)
            print_summary(results)
            
            # Salva apenas se encontrou drops
            if results['total_drops_found'] > 0:
                filename = save_results(results)
                print(f"\n💾 Resultados salvos em: {filename}")
                
                # Para no primeiro threshold que encontrar drops
                break
        
        print(f"\n✅ Análise concluída!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()