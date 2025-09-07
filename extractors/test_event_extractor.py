#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste do EventExtractor - Extração de dados de páginas individuais de jogos
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'v2'))

from modules.scraper.event_extractor import EventExtractor
from modules.scraper.live_extractor import LiveGamesExtractor
from datetime import datetime
import json

def test_single_event_extraction():
    """
    Testa a extração de dados de um evento específico
    """
    print("=" * 70)
    print("🎯 TESTE DE EXTRAÇÃO DE EVENTO INDIVIDUAL")
    print("=" * 70)
    print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    # Configurar extrator
    extractor = EventExtractor(headless=True)
    
    try:
        # Testar com o game ID de exemplo
        game_id = "10519888"
        bet_type = "1x2"
        
        print(f"🔄 Extraindo dados do jogo ID: {game_id} (tipo: {bet_type})")
        print(f"🌐 URL: https://dropping-odds.com/event.php?id={game_id}&t={bet_type}")
        print()
        
        # Extrair dados
        event_data = extractor.extract_event_data(game_id, bet_type)
        
        # Exibir resultados
        print("✅ EXTRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 50)
        print(f"🏆 Título: {event_data.title}")
        print(f"🆔 Game ID: {event_data.game_id}")
        print(f"🎲 Tipo de Aposta: {event_data.bet_type}")
        print(f"📊 Total de Registros: {event_data.total_records}")
        print(f"⏰ Timestamp: {event_data.extraction_timestamp}")
        print()
        
        if event_data.odds_records:
            print("📈 PRIMEIROS 10 REGISTROS DE ODDS:")
            print("-" * 50)
            
            for i, record in enumerate(event_data.odds_records[:10], 1):
                print(f"📝 Registro {i:02d}:")
                print(f"   📅 Data: {record.date}")
                print(f"   ⏰ Hora: {record.time}")
                print(f"   ⚽ Placar: {record.score}")
                print(f"   🏠 Casa: {record.home_odds}")
                print(f"   🤝 Empate: {record.draw_odds}")
                print(f"   🏃 Visitante: {record.away_odds}")
                if record.home_percentage != "-":
                    print(f"   📊 % Casa: {record.home_percentage}")
                if record.away_percentage != "-":
                    print(f"   📊 % Visitante: {record.away_percentage}")
                print()
            
            if len(event_data.odds_records) > 10:
                print(f"... e mais {len(event_data.odds_records) - 10} registros")
                print()
        
        # Estatísticas dos dados
        print("📊 ANÁLISE DOS DADOS:")
        print("=" * 50)
        
        if event_data.odds_records:
            # Odds médias
            home_odds = [r.home_odds for r in event_data.odds_records if r.home_odds > 0]
            draw_odds = [r.draw_odds for r in event_data.odds_records if r.draw_odds > 0]
            away_odds = [r.away_odds for r in event_data.odds_records if r.away_odds > 0]
            
            if home_odds:
                print(f"🏠 Odds Casa - Mín: {min(home_odds):.3f}, Máx: {max(home_odds):.3f}, Média: {sum(home_odds)/len(home_odds):.3f}")
            if draw_odds:
                print(f"🤝 Odds Empate - Mín: {min(draw_odds):.3f}, Máx: {max(draw_odds):.3f}, Média: {sum(draw_odds)/len(draw_odds):.3f}")
            if away_odds:
                print(f"🏃 Odds Visitante - Mín: {min(away_odds):.3f}, Máx: {max(away_odds):.3f}, Média: {sum(away_odds)/len(away_odds):.3f}")
            
            # Registros com placar
            records_with_score = sum(1 for r in event_data.odds_records if r.score and r.score != "")
            print(f"⚽ Registros com placar: {records_with_score}")
            
            # Período de dados
            dates = [r.date for r in event_data.odds_records if r.date]
            if dates:
                print(f"📅 Período: {min(dates)} até {max(dates)}")
        
        # Salvar dados em JSON
        output_file = f"event_data_{game_id}_{bet_type}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(event_data.to_dict(), f, indent=2, ensure_ascii=False)
        
        print(f"💾 Dados salvos em: {output_file}")
        
        # Estatísticas do extrator
        stats = extractor.get_stats()
        print()
        print("📈 ESTATÍSTICAS DO EXTRATOR:")
        print("=" * 50)
        print(f"📊 Total de extrações: {stats['total_extractions']}")
        print(f"✅ Extrações bem-sucedidas: {stats['successful_extractions']}")
        print(f"❌ Extrações falhadas: {stats['failed_extractions']}")
        print(f"📝 Registros extraídos: {stats['records_extracted']}")
        
        return event_data
        
    except Exception as e:
        print(f"❌ Erro durante extração: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        extractor.close()

def test_multiple_games_extraction():
    """
    Testa a extração de múltiplos jogos da página live
    """
    print("\n" + "=" * 70)
    print("🎮 TESTE DE EXTRAÇÃO DE MÚLTIPLOS JOGOS")
    print("=" * 70)
    
    # Primeiro, obter lista de jogos da página live
    live_extractor = LiveGamesExtractor(headless=True)
    event_extractor = EventExtractor(headless=True)
    
    try:
        print("🔄 Obtendo lista de jogos da página live...")
        games = live_extractor.extract_live_games()
        
        if not games:
            print("❌ Nenhum jogo encontrado na página live")
            return
        
        print(f"✅ {len(games)} jogos encontrados")
        
        # Extrair dados dos primeiros 3 jogos com game_id
        games_with_id = [game for game in games if game.game_id]
        
        if not games_with_id:
            print("❌ Nenhum jogo com ID encontrado")
            return
        
        print(f"🆔 {len(games_with_id)} jogos com ID disponíveis")
        print("📊 Extraindo dados dos primeiros 3 jogos...")
        print()
        
        extracted_events = []
        
        for i, game in enumerate(games_with_id[:3], 1):
            try:
                print(f"🎯 Jogo {i}/3: {game.home_team} vs {game.away_team} (ID: {game.game_id})")
                
                event_data = event_extractor.extract_event_data(game.game_id, "1x2")
                extracted_events.append(event_data)
                
                print(f"   ✅ {event_data.total_records} registros extraídos")
                
            except Exception as e:
                print(f"   ❌ Erro: {e}")
                continue
        
        print()
        print("📊 RESUMO DA EXTRAÇÃO MÚLTIPLA:")
        print("=" * 50)
        print(f"🎮 Jogos processados: {len(extracted_events)}/3")
        
        total_records = sum(event.total_records for event in extracted_events)
        print(f"📝 Total de registros: {total_records}")
        
        if extracted_events:
            avg_records = total_records / len(extracted_events)
            print(f"📊 Média de registros por jogo: {avg_records:.1f}")
        
        return extracted_events
        
    except Exception as e:
        print(f"❌ Erro durante extração múltipla: {e}")
        import traceback
        traceback.print_exc()
        return []
    
    finally:
        live_extractor.close()
        event_extractor.close()

def main():
    """
    Função principal de teste
    """
    print("🏆 TESTE DO SISTEMA DE EXTRAÇÃO DE EVENTOS INDIVIDUAIS")
    print("=" * 70)
    
    # Teste 1: Extração de evento único
    event_data = test_single_event_extraction()
    
    # Teste 2: Extração de múltiplos jogos (opcional)
    if event_data:
        response = input("\n🤔 Deseja testar extração de múltiplos jogos? (s/n): ")
        if response.lower() in ['s', 'sim', 'y', 'yes']:
            test_multiple_games_extraction()
    
    print("\n✅ Testes concluídos!")

if __name__ == "__main__":
    main()