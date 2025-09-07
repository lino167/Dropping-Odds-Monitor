#!/usr/bin/env python3
"""
Teste Integrado do Sistema de Detecção de Drops

Este script testa o sistema completo de detecção de drops
usando dados reais extraídos das páginas de odds.
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, List

# Adicionar o diretório v2 ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'v2'))

from modules.scraper.drop_detector import EnhancedDropDetector, DropInfo
from monitor_config import AlertThresholds

def load_real_data() -> Dict[str, Dict]:
    """
    Carrega dados reais do arquivo JSON extraído.
    """
    json_file = "complete_live_data_20250907_172408.json"
    
    if not os.path.exists(json_file):
        print(f"❌ Arquivo {json_file} não encontrado!")
        return {}
    
    print(f"📂 Carregando dados de: {json_file}")
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ Dados carregados: {len(data)} jogos encontrados")
        return data
    
    except Exception as e:
        print(f"❌ Erro ao carregar dados: {e}")
        return {}

def test_drop_detection_on_real_data(data: Dict) -> Dict[str, List[DropInfo]]:
    """
    Testa a detecção de drops em dados reais.
    """
    print("\n🔍 INICIANDO TESTE DE DETECÇÃO DE DROPS EM DADOS REAIS")
    print("=" * 80)
    
    # Configuração
    config = AlertThresholds()
    detector = EnhancedDropDetector(config.drop_thresholds)
    
    # Tipos de tabela para testar
    table_types = ["1x2", "total", "handicap", "total_ht", "1x2_ht"]
    
    all_results = {}
    total_drops = 0
    
    # Verificar se existe a estrutura de jogos
    if 'games_data' not in data:
        print("❌ Estrutura 'games_data' não encontrada no arquivo JSON")
        return {}
    
    games_data = data['games_data']
    
    # Testar apenas os primeiros 3 jogos para não sobrecarregar
    games_to_test = list(games_data.keys())[:3]
    
    for game_id in games_to_test:
        game_data = games_data[game_id]
        print(f"\n🎯 TESTANDO JOGO: {game_id}")
        print("-" * 50)
        
        game_results = {}
        
        for table_type in table_types:
            if table_type in game_data:
                table_data = game_data[table_type]
                
                try:
                    drops = detector.detect_drops(table_data, table_type)
                    game_results[table_type] = drops
                    
                    if drops:
                        print(f"✅ {table_type.upper()}: {len(drops)} drops detectados")
                        for i, drop in enumerate(drops[:2], 1):  # Mostrar apenas os 2 primeiros
                            print(f"   {i}. Linha {drop.row_index} - {drop.column_name}: {drop.new_value}")
                        if len(drops) > 2:
                            print(f"   ... e mais {len(drops) - 2} drops")
                    else:
                        print(f"❌ {table_type.upper()}: Nenhum drop detectado")
                        
                    total_drops += len(drops)
                    
                except Exception as e:
                    print(f"❌ {table_type.upper()}: Erro na detecção - {e}")
                    game_results[table_type] = []
            else:
                print(f"⚠️  {table_type.upper()}: Dados não encontrados")
                game_results[table_type] = []
        
        all_results[game_id] = game_results
    
    print(f"\n📊 RESUMO FINAL")
    print("=" * 50)
    print(f"Jogos testados: {len(games_to_test)}")
    print(f"Total de drops detectados: {total_drops}")
    
    return all_results

def save_results(results: Dict[str, List[DropInfo]], filename: str = None):
    """
    Salva os resultados em arquivo JSON.
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"integrated_drop_test_results_{timestamp}.json"
    
    # Converter DropInfo para dicionário serializável
    serializable_results = {}
    
    for game_id, game_results in results.items():
        serializable_results[game_id] = {}
        
        for table_type, drops in game_results.items():
            serializable_results[game_id][table_type] = []
            
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
                serializable_results[game_id][table_type].append(drop_dict)
    
    # Adicionar metadados
    final_results = {
        "test_timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "test_description": "Teste integrado de detecção de drops em dados reais",
        "games_tested": list(results.keys()),
        "table_types": ["1x2", "total", "handicap", "total_ht", "1x2_ht"],
        "results": serializable_results
    }
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(final_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Resultados salvos em: {filename}")
        
    except Exception as e:
        print(f"❌ Erro ao salvar resultados: {e}")

def main():
    """
    Função principal do teste integrado.
    """
    print("🚀 SISTEMA INTEGRADO DE DETECÇÃO DE DROPS")
    print("=" * 80)
    print("Este teste usa dados reais extraídos para validar")
    print("a detecção de drops em todas as 5 tabelas de odds.")
    print("\nColunas monitoradas por tabela:")
    print("• 1X2: home%, away%")
    print("• TOTAL: drop")
    print("• HANDICAP: sharpness")
    print("• TOTAL_HT: drop")
    print("• 1X2_HT: home%, away%")
    
    try:
        # Carregar dados reais
        data = load_real_data()
        
        if not data:
            print("❌ Não foi possível carregar os dados. Teste cancelado.")
            return
        
        # Executar teste de detecção
        results = test_drop_detection_on_real_data(data)
        
        # Salvar resultados
        save_results(results)
        
        print("\n✅ Teste integrado concluído com sucesso!")
        print("\n📋 PRÓXIMOS PASSOS:")
        print("1. Revisar os resultados salvos")
        print("2. Ajustar thresholds se necessário")
        print("3. Integrar com sistema de monitoramento em tempo real")
        print("4. Implementar sistema de alertas")
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()