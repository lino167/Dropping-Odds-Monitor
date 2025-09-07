#!/usr/bin/env python3
"""
Teste de Detecção de Drops em Dados Reais

Este script testa a detecção de drops usando os dados reais
extraídos, trabalhando com a estrutura atual do arquivo JSON.
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Any

# Adicionar o diretório v2 ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'v2'))

from modules.scraper.drop_detector import EnhancedDropDetector, DropInfo
from monitor_config import AlertThresholds

def analyze_json_structure(data: Dict) -> None:
    """
    Analisa a estrutura do arquivo JSON para entender como os dados estão organizados.
    """
    print("🔍 ANALISANDO ESTRUTURA DO ARQUIVO JSON")
    print("=" * 60)
    
    print(f"Chaves principais: {list(data.keys())}")
    
    if 'extraction_info' in data:
        info = data['extraction_info']
        print(f"\n📊 Informações da extração:")
        print(f"   Timestamp: {info.get('timestamp', 'N/A')}")
        print(f"   Total de jogos: {info.get('total_games', 'N/A')}")
        print(f"   Tipos de tabela: {info.get('table_types', [])}")
    
    if 'live_games_summary' in data:
        summary = data['live_games_summary']
        print(f"\n🎮 Resumo dos jogos: {len(summary)} jogos encontrados")
        if summary:
            first_game = summary[0]
            print(f"   Exemplo: {first_game.get('home_team', 'N/A')} vs {first_game.get('away_team', 'N/A')}")
            print(f"   Game ID: {first_game.get('game_id', 'N/A')}")

def find_game_data_sections(data: Dict) -> List[str]:
    """
    Procura por seções que contenham dados de jogos individuais.
    """
    game_sections = []
    
    def search_recursive(obj, path="", depth=0):
        if depth > 10:  # Evitar recursão muito profunda
            return
            
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                
                # Procurar por listas que contenham dados de odds
                if isinstance(value, list) and len(value) > 0:
                    first_item = value[0]
                    if isinstance(first_item, dict):
                        # Verificar se tem colunas típicas de odds
                        keys = set(first_item.keys())
                        odds_indicators = {'Home', 'Away', 'Draw', 'Home\n (%)', 'Away\n (%)', 'Date', 'Time', 'Score'}
                        if len(odds_indicators.intersection(keys)) >= 3:
                            game_sections.append(current_path)
                            continue
                
                # Procurar por estruturas que contenham 'data'
                elif isinstance(value, dict) and 'data' in value:
                    if isinstance(value['data'], list) and len(value['data']) > 0:
                        first_item = value['data'][0]
                        if isinstance(first_item, dict):
                            keys = set(first_item.keys())
                            odds_indicators = {'Home', 'Away', 'Draw', 'Home\n (%)', 'Away\n (%)'}
                            if odds_indicators.intersection(keys):
                                game_sections.append(current_path)
                                continue
                
                # Continuar busca recursiva
                if isinstance(value, (dict, list)):
                    search_recursive(value, current_path, depth + 1)
        
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                current_path = f"{path}[{i}]" if path else f"[{i}]"
                if isinstance(item, (dict, list)):
                    search_recursive(item, current_path, depth + 1)
    
    search_recursive(data)
    return game_sections

def extract_table_data_from_section(data: Dict, section_path: str) -> Dict:
    """
    Extrai dados de uma seção específica do JSON.
    """
    parts = section_path.split('.')
    current = data
    
    for part in parts:
        if part in current:
            current = current[part]
        else:
            return {}
    
    return current

def convert_to_detector_format(raw_data: Dict) -> Dict:
    """
    Converte os dados brutos para o formato esperado pelo detector.
    """
    if 'data' not in raw_data:
        return {'data': []}
    
    converted_data = []
    
    for item in raw_data['data']:
        if isinstance(item, dict):
            # Converter nomes de colunas para formato padrão
            converted_item = {}
            
            for key, value in item.items():
                # Mapear colunas específicas
                if key == 'Home\n (%)':
                    converted_item['home_percentage'] = value
                elif key == 'Away\n (%)':
                    converted_item['away_percentage'] = value
                elif key == 'Home':
                    converted_item['home_odds'] = value
                elif key == 'Away':
                    converted_item['away_odds'] = value
                elif key == 'Draw':
                    converted_item['draw_odds'] = value
                else:
                    # Manter outros campos como estão
                    converted_item[key.lower().replace(' ', '_')] = value
            
            converted_data.append(converted_item)
    
    return {'data': converted_data}

def detect_drops_in_real_data(data_section, threshold=5.0):
    """Detecta drops nos dados reais baseado em mudanças percentuais"""
    drops_found = []
    
    try:
        if not isinstance(data_section, dict) or 'data' not in data_section:
            return drops_found
            
        data_list = data_section['data']
        if not isinstance(data_list, list) or len(data_list) < 1:
            return drops_found
            
        for i, entry in enumerate(data_list):
            if not isinstance(entry, dict):
                continue
                
            # Verifica mudanças percentuais diretas nos dados
            home_change_str = entry.get('Home\n (%)', '0%')
            away_change_str = entry.get('Away\n (%)', '0%')
            
            try:
                home_change = float(str(home_change_str).replace('%', '').replace('+', ''))
                away_change = float(str(away_change_str).replace('%', '').replace('+', ''))
                
                # Detecta drops significativos
                if abs(home_change) >= threshold or abs(away_change) >= threshold:
                    drop_info = {
                        'timestamp': entry.get('Date', ''),
                        'time_in_game': entry.get('Time', ''),
                        'score': entry.get('Score', ''),
                        'home_odds': entry.get('Home', 0),
                        'draw_odds': entry.get('Draw', 0),
                        'away_odds': entry.get('Away', 0),
                        'home_change': home_change,
                        'away_change': away_change,
                        'drop_type': 'home' if abs(home_change) >= threshold else 'away',
                        'drop_magnitude': max(abs(home_change), abs(away_change))
                    }
                    drops_found.append(drop_info)
                    
            except (ValueError, AttributeError):
                continue
                
    except Exception as e:
        print(f"Erro ao detectar drops: {e}")
        
    return drops_found

def test_drop_detection_on_sections(data: Dict, sections: List[str]) -> Dict[str, List[DropInfo]]:
    """
    Testa a detecção de drops nas seções encontradas.
    """
    print("\n🎯 TESTANDO DETECÇÃO DE DROPS")
    print("=" * 60)
    
    # Configuração
    config = AlertThresholds()
    detector = EnhancedDropDetector(config.drop_thresholds)
    
    all_results = {}
    total_drops = 0
    
    # Testar mais seções para encontrar drops reais
    sections_to_test = sections[:10]  # Aumentado para 10
    
    for i, section_path in enumerate(sections_to_test, 1):
        print(f"\n📊 SEÇÃO {i}: {section_path}")
        print("-" * 40)
        
        try:
            # Extrair dados da seção
            raw_data = extract_table_data_from_section(data, section_path)
            
            if not raw_data:
                print("❌ Dados não encontrados nesta seção")
                continue
            
            # Converter para formato do detector
            table_data = convert_to_detector_format(raw_data)
            
            if not table_data['data']:
                print("❌ Nenhum dado válido encontrado")
                continue
            
            print(f"✅ {len(table_data['data'])} registros encontrados")
            
            # Primeiro tenta com detector original
            drops = detector.detect_drops(table_data, '1x2')
            
            # Se não encontrar drops, tenta com detector de dados reais
            if not drops:
                real_drops = detect_drops_in_real_data(table_data, threshold=5.0)
                if real_drops:
                    print(f"🎯 {len(real_drops)} drops detectados (método alternativo):")
                    for j, drop in enumerate(real_drops[:3], 1):
                        print(f"   {j}. {drop['timestamp']}: Home {drop['home_change']}%, Away {drop['away_change']}%")
                    if len(real_drops) > 3:
                        print(f"   ... e mais {len(real_drops) - 3} drops")
                    # Converter para formato DropInfo se necessário
                    drops = []  # Manter vazio para compatibilidade
                else:
                    print("❌ Nenhum drop detectado (threshold: 5%)")
            else:
                print(f"🎯 {len(drops)} drops detectados:")
                for j, drop in enumerate(drops[:3], 1):
                    print(f"   {j}. Linha {drop.row_index} - {drop.column_name}: {drop.new_value}")
                if len(drops) > 3:
                    print(f"   ... e mais {len(drops) - 3} drops")
            
            all_results[section_path] = drops
            total_drops += len(drops)
            
        except Exception as e:
            print(f"❌ Erro ao processar seção: {e}")
            all_results[section_path] = []
    
    print(f"\n📈 RESUMO FINAL")
    print("=" * 40)
    print(f"Seções testadas: {len(sections_to_test)}")
    print(f"Total de drops detectados: {total_drops}")
    
    return all_results

def save_results(results: Dict[str, List[DropInfo]], sections: List[str]):
    """
    Salva os resultados do teste.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"real_data_drop_test_{timestamp}.json"
    
    # Converter para formato serializável
    serializable_results = {}
    
    for section_path, drops in results.items():
        serializable_results[section_path] = []
        
        for drop in drops:
            drop_dict = {
                "table_type": drop.table_type,
                "row_index": drop.row_index,
                "column_name": drop.column_name,
                "drop_type": drop.drop_type.value if hasattr(drop.drop_type, 'value') else str(drop.drop_type),
                "confidence": drop.confidence.value if hasattr(drop.confidence, 'value') else str(drop.confidence),
                "new_value": drop.new_value,
                "percentage_change": drop.percentage_change,
                "detection_method": drop.detection_method,
                "timestamp": drop.detected_at.isoformat() if drop.detected_at else None
            }
            serializable_results[section_path].append(drop_dict)
    
    # Criar resultado final
    final_results = {
        "test_timestamp": timestamp,
        "test_description": "Teste de detecção de drops em dados reais",
        "sections_found": sections,
        "sections_tested": list(results.keys()),
        "total_drops": sum(len(drops) for drops in results.values()),
        "results": serializable_results
    }
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(final_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Resultados salvos em: {filename}")
        
    except Exception as e:
        print(f"❌ Erro ao salvar: {e}")

def main():
    """
    Função principal do teste.
    """
    print("🚀 TESTE DE DETECÇÃO DE DROPS EM DADOS REAIS")
    print("=" * 80)
    
    json_file = "complete_live_data_20250907_172408.json"
    
    if not os.path.exists(json_file):
        print(f"❌ Arquivo {json_file} não encontrado!")
        return
    
    try:
        # Carregar dados
        print(f"📂 Carregando: {json_file}")
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ Arquivo carregado com sucesso")
        
        # Analisar estrutura
        analyze_json_structure(data)
        
        # Procurar seções com dados de jogos
        print("\n🔍 PROCURANDO SEÇÕES COM DADOS DE ODDS")
        print("=" * 60)
        
        sections = find_game_data_sections(data)
        
        if not sections:
            print("❌ Nenhuma seção com dados de odds encontrada")
            return
        
        print(f"✅ {len(sections)} seções encontradas:")
        for i, section in enumerate(sections[:5], 1):  # Mostrar apenas as 5 primeiras
            print(f"   {i}. {section}")
        if len(sections) > 5:
            print(f"   ... e mais {len(sections) - 5} seções")
        
        # Testar detecção de drops
        results = test_drop_detection_on_sections(data, sections)
        
        # Salvar resultados
        save_results(results, sections)
        
        print("\n✅ Teste concluído com sucesso!")
        
        print("\n📋 PRÓXIMOS PASSOS:")
        print("1. Revisar os drops detectados")
        print("2. Ajustar thresholds conforme necessário")
        print("3. Implementar monitoramento em tempo real")
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()