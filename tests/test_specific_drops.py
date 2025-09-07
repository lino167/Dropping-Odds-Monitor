#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste de Detecção de Drops por Colunas Específicas

Este script testa a detecção de drops usando as colunas específicas de cada tipo de tabela:
- 1x2: colunas home% e away%
- total: coluna drop
- handicap: coluna sharpness
- total_ht: coluna drop
- 1x2_ht: colunas home% e away%
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Any

# Adicionar o diretório v2 ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'v2'))

from modules.scraper.drop_detector import EnhancedDropDetector, DropInfo, DropType, DropConfidence
from monitor_config import AlertThresholds

def create_test_data() -> Dict[str, Dict]:
    """Cria dados de teste simulando as diferentes tabelas com drops"""
    
    test_data = {
        "1x2": {
            "0": {
                "date": "07.09.2025",
                "time": "20:35",
                "score": "0-0",
                "home_odds": "1.571",
                "draw_odds": "3.750",
                "away_odds": "5.000",
                "home_percentage": "-4%",  # Drop significativo
                "away_percentage": "0%",
                "penalty": "0-0",
                "red": "0-0"
            },
            "1": {
                "date": "07.09.2025",
                "time": "20:36",
                "score": "0-0",
                "home_odds": "1.615",
                "draw_odds": "3.750",
                "away_odds": "5.500",
                "home_percentage": "-8%",  # Drop maior
                "away_percentage": "-13%",  # Drop significativo
                "penalty": "0-0",
                "red": "0-0"
            }
        },
        "total": {
            "0": {
                "date": "07.09.2025",
                "time": "20:35",
                "score": "0-0",
                "over_odds": "1.825",
                "handicap": "2.25",
                "under_odds": "1.975",
                "drop": "-12.5",  # Drop significativo
                "sharp": "-0.25",
                "penalty": "0-0",
                "red": "0-0"
            },
            "1": {
                "date": "07.09.2025",
                "time": "20:36",
                "score": "0-0",
                "over_odds": "1.975",
                "handicap": "2.5",
                "under_odds": "1.825",
                "drop": "-15.2",  # Drop maior
                "sharp": "0.25",
                "penalty": "0-0",
                "red": "0-0"
            }
        },
        "handicap": {
            "0": {
                "date": "07.09.2025",
                "time": "20:35",
                "score": "0-0",
                "home_odds": "1.750",
                "handicap": "-0.75",
                "away_odds": "2.050",
                "sharpness": "-12.1",  # Sharpness significativo
                "penalty": "0-0",
                "red": "0-0"
            },
            "1": {
                "date": "07.09.2025",
                "time": "20:36",
                "score": "0-0",
                "home_odds": "2.025",
                "handicap": "-1",
                "away_odds": "1.775",
                "sharpness": "-15.8",  # Sharpness negativo maior
                "penalty": "0-0",
                "red": "0-0"
            }
        },
        "total_ht": {
            "0": {
                "date": "07.09.2025",
                "time": "20:35",
                "score": "0-0",
                "over_odds": "2.075",
                "handicap": "1",
                "under_odds": "1.725",
                "drop": "-14.5",  # Drop significativo
                "penalty": "0-0",
                "red": "0-0"
            },
            "1": {
                "date": "07.09.2025",
                "time": "20:37",
                "score": "0-0",
                "over_odds": "1.700",
                "handicap": "0.75",
                "under_odds": "2.100",
                "drop": "-18.1",  # Drop maior
                "penalty": "0-0",
                "red": "0-0"
            }
        },
        "1x2_ht": {
            "0": {
                "date": "07.09.2025",
                "time": "20:35",
                "score": "0-0",
                "home_odds": "2.100",
                "draw_odds": "2.100",
                "away_odds": "6.000",
                "home_percentage": "0%",
                "away_percentage": "-11%",  # Drop significativo
                "penalty": "0-0",
                "red": "0-0"
            },
            "1": {
                "date": "07.09.2025",
                "time": "20:36",
                "score": "0-0",
                "home_odds": "2.200",
                "draw_odds": "2.100",
                "away_odds": "6.000",
                "home_percentage": "-9%",  # Drop significativo
                "away_percentage": "-11%",  # Drop significativo
                "penalty": "0-0",
                "red": "0-0"
            }
        }
    }
    
    return test_data

def test_drop_detection():
    """Testa a detecção de drops para cada tipo de tabela"""
    
    print("=" * 80)
    print("TESTE DE DETECÇÃO DE DROPS POR COLUNAS ESPECÍFICAS")
    print("=" * 80)
    print()
    
    # Configuração
    config = AlertThresholds()
    
    # Dados de teste
    test_data = create_test_data()
    
    # Resultados
    all_results = {}
    
    # Testar cada tipo de tabela
    for table_type, data in test_data.items():
        print(f"\n📊 TESTANDO TABELA: {table_type.upper()}")
        print("-" * 50)
        
        # Criar detector para este tipo de tabela
        detector = EnhancedDropDetector(config.drop_thresholds)
        
        # Detectar drops
        drops = detector._detect_drops_by_specific_columns_test(data, table_type)
        
        # Mostrar resultados
        if drops:
            print(f"✅ {len(drops)} drops detectados:")
            for i, drop in enumerate(drops, 1):
                print(f"  {i}. Linha {drop.row_index} - Coluna '{drop.column_name}'")
                print(f"     Valor: {drop.new_value}")
                print(f"     Mudança: {drop.percentage_change}%")
                print(f"     Confiança: {drop.confidence.value}")
                print(f"     Método: {drop.detection_method}")
                print()
        else:
            print("❌ Nenhum drop detectado")
            
        all_results[table_type] = drops
    
    # Resumo geral
    print("\n" + "=" * 80)
    print("RESUMO GERAL")
    print("=" * 80)
    
    total_drops = sum(len(drops) for drops in all_results.values())
    print(f"Total de drops detectados: {total_drops}")
    print()
    
    for table_type, drops in all_results.items():
        print(f"{table_type.upper()}: {len(drops)} drops")
        
        # Mostrar colunas específicas monitoradas
        if table_type in ["1x2", "1x2_ht"]:
            print(f"  Colunas monitoradas: home%, away%")
        elif table_type in ["total", "total_ht"]:
            print(f"  Colunas monitoradas: drop")
        elif table_type == "handicap":
            print(f"  Colunas monitoradas: sharpness")
    
    print()
    print("✅ Teste concluído com sucesso!")
    
    return all_results

def save_test_results(results: Dict[str, List[DropInfo]]):
    """Salva os resultados do teste em arquivo JSON"""
    
    # Converter DropInfo para dict para serialização
    serializable_results = {}
    
    for table_type, drops in results.items():
        serializable_results[table_type] = []
        
        for drop in drops:
            drop_dict = {
                "table_type": drop.table_type,
                "row_index": drop.row_index,
                "column_name": drop.column_name,
                "drop_type": drop.drop_type.value,
                "confidence": drop.confidence.value,
                "new_value": drop.new_value,
                "percentage_change": drop.percentage_change,
                "detection_method": drop.detection_method,
                "timestamp": drop.detected_at.isoformat() if drop.detected_at else None
            }
            serializable_results[table_type].append(drop_dict)
    
    # Salvar arquivo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_specific_drops_results_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            "test_timestamp": timestamp,
            "test_description": "Teste de detecção de drops por colunas específicas",
            "table_types_tested": list(results.keys()),
            "total_drops_detected": sum(len(drops) for drops in results.values()),
            "results": serializable_results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Resultados salvos em: {filename}")

if __name__ == "__main__":
    try:
        # Executar teste
        results = test_drop_detection()
        
        # Salvar resultados
        save_test_results(results)
        
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()