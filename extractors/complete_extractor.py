#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extrator Completo - Sistema Integrado
Combina extração da página live com extração detalhada de cada jogo individual
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'v2'))

from modules.scraper.live_extractor import LiveGamesExtractor
from modules.scraper.event_extractor import EventExtractor
from datetime import datetime
import json
import time
from typing import List, Dict, Optional

class CompleteExtractor:
    """
    Extrator completo que combina dados da página live com dados detalhados de cada jogo
    """
    
    def __init__(self, headless: bool = True, max_games: int = 10):
        """
        Inicializar extrator completo
        
        Args:
            headless: Executar em modo headless
            max_games: Máximo de jogos para extrair dados detalhados
        """
        self.headless = headless
        self.max_games = max_games
        self.live_extractor = LiveGamesExtractor(headless=headless)
        self.event_extractor = EventExtractor(headless=headless)
        
        # Estatísticas
        self.stats = {
            "session_start": datetime.now().isoformat(),
            "live_games_found": 0,
            "games_with_id": 0,
            "detailed_extractions": 0,
            "total_odds_records": 0,
            "failed_extractions": 0,
            "processing_time": 0
        }
    
    def extract_complete_data(self, bet_types: List[str] = None) -> Dict:
        """
        Extrai dados completos: página live + detalhes de cada jogo
        
        Args:
            bet_types: Tipos de apostas para extrair (padrão: ['1x2'])
            
        Returns:
            Dicionário com todos os dados extraídos
        """
        if bet_types is None:
            bet_types = ['1x2']
        
        start_time = time.time()
        
        print("=" * 80)
        print("🏆 EXTRATOR COMPLETO - DROPPING ODDS")
        print("=" * 80)
        print(f"📅 Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"🎲 Tipos de aposta: {', '.join(bet_types)}")
        print(f"🎯 Máximo de jogos detalhados: {self.max_games}")
        print()
        
        try:
            # Fase 1: Extrair jogos da página live
            print("🔄 FASE 1: Extraindo jogos da página live...")
            print("-" * 50)
            
            live_games = self.live_extractor.extract_live_games()
            
            if not live_games:
                print("❌ Nenhum jogo encontrado na página live")
                return self._create_empty_result()
            
            self.stats["live_games_found"] = len(live_games)
            
            # Filtrar jogos com ID
            games_with_id = [game for game in live_games if game.game_id]
            self.stats["games_with_id"] = len(games_with_id)
            
            print(f"✅ {len(live_games)} jogos encontrados")
            print(f"🆔 {len(games_with_id)} jogos com ID disponível")
            print()
            
            if not games_with_id:
                print("❌ Nenhum jogo com ID encontrado para extração detalhada")
                return self._create_result_with_live_only(live_games)
            
            # Fase 2: Extrair dados detalhados dos jogos
            print("🔄 FASE 2: Extraindo dados detalhados dos jogos...")
            print("-" * 50)
            
            # Limitar número de jogos
            games_to_process = games_with_id[:self.max_games]
            print(f"📊 Processando {len(games_to_process)} jogos")
            print()
            
            detailed_data = []
            
            for i, game in enumerate(games_to_process, 1):
                print(f"🎯 Jogo {i}/{len(games_to_process)}: {game.home_team} vs {game.away_team}")
                print(f"   🆔 ID: {game.game_id} | 🏆 Liga: {game.league}")
                
                game_detailed_data = {
                    "live_info": game.to_dict(),
                    "odds_data": {}
                }
                
                # Extrair para cada tipo de aposta
                for bet_type in bet_types:
                    try:
                        print(f"   📈 Extraindo {bet_type}...", end=" ")
                        
                        event_data = self.event_extractor.extract_event_data(game.game_id, bet_type)
                        game_detailed_data["odds_data"][bet_type] = event_data.to_dict()
                        
                        self.stats["total_odds_records"] += event_data.total_records
                        
                        print(f"✅ {event_data.total_records} registros")
                        
                    except Exception as e:
                        print(f"❌ Erro: {str(e)[:50]}...")
                        self.stats["failed_extractions"] += 1
                        continue
                
                detailed_data.append(game_detailed_data)
                self.stats["detailed_extractions"] += 1
                print()
            
            # Calcular tempo de processamento
            self.stats["processing_time"] = time.time() - start_time
            
            # Criar resultado final
            result = {
                "extraction_info": {
                    "timestamp": datetime.now().isoformat(),
                    "bet_types": bet_types,
                    "max_games_limit": self.max_games,
                    "processing_time_seconds": self.stats["processing_time"]
                },
                "live_games": [game.to_dict() for game in live_games],
                "detailed_games": detailed_data,
                "statistics": self.stats.copy()
            }
            
            # Exibir resumo
            self._display_summary(result)
            
            return result
            
        except Exception as e:
            print(f"❌ Erro durante extração completa: {e}")
            import traceback
            traceback.print_exc()
            return self._create_empty_result()
    
    def _create_empty_result(self) -> Dict:
        """Criar resultado vazio em caso de erro"""
        return {
            "extraction_info": {
                "timestamp": datetime.now().isoformat(),
                "error": "No data extracted"
            },
            "live_games": [],
            "detailed_games": [],
            "statistics": self.stats.copy()
        }
    
    def _create_result_with_live_only(self, live_games) -> Dict:
        """Criar resultado apenas com dados live"""
        return {
            "extraction_info": {
                "timestamp": datetime.now().isoformat(),
                "note": "Only live data available - no games with ID for detailed extraction"
            },
            "live_games": [game.to_dict() for game in live_games],
            "detailed_games": [],
            "statistics": self.stats.copy()
        }
    
    def _display_summary(self, result: Dict):
        """Exibir resumo dos resultados"""
        print("📊 RESUMO DA EXTRAÇÃO COMPLETA")
        print("=" * 80)
        
        stats = result["statistics"]
        
        print(f"🎮 Jogos encontrados (live): {stats['live_games_found']}")
        print(f"🆔 Jogos com ID: {stats['games_with_id']}")
        print(f"📈 Extrações detalhadas: {stats['detailed_extractions']}")
        print(f"📝 Total de registros de odds: {stats['total_odds_records']}")
        print(f"❌ Extrações falhadas: {stats['failed_extractions']}")
        print(f"⏱️ Tempo de processamento: {stats['processing_time']:.1f}s")
        
        if stats['detailed_extractions'] > 0:
            avg_records = stats['total_odds_records'] / stats['detailed_extractions']
            print(f"📊 Média de registros por jogo: {avg_records:.1f}")
        
        print()
        
        # Taxa de sucesso
        if stats['games_with_id'] > 0:
            success_rate = (stats['detailed_extractions'] / min(stats['games_with_id'], self.max_games)) * 100
            print(f"✅ Taxa de sucesso: {success_rate:.1f}%")
        
        print()
    
    def save_results(self, result: Dict, filename: Optional[str] = None) -> str:
        """Salvar resultados em arquivo JSON"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"complete_extraction_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Dados salvos em: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Erro ao salvar arquivo: {e}")
            return ""
    
    def close(self):
        """Fechar recursos"""
        try:
            self.live_extractor.close()
            self.event_extractor.close()
        except Exception as e:
            print(f"⚠️ Erro ao fechar recursos: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

def main():
    """
    Função principal
    """
    # Configurações
    MAX_GAMES = 5  # Limitar para teste
    BET_TYPES = ['1x2']  # Pode expandir para ['1x2', 'ou', 'ah']
    
    with CompleteExtractor(headless=True, max_games=MAX_GAMES) as extractor:
        # Extrair dados completos
        result = extractor.extract_complete_data(bet_types=BET_TYPES)
        
        # Salvar resultados
        if result and result.get('detailed_games'):
            filename = extractor.save_results(result)
            
            print("🎯 PRÓXIMOS PASSOS:")
            print("-" * 50)
            print(f"📁 Arquivo gerado: {filename}")
            print("📊 Use os dados para análise de padrões")
            print("🔄 Execute novamente para monitoramento contínuo")
            print("📈 Expanda para mais tipos de apostas conforme necessário")
        
        print("\n✅ Extração completa finalizada!")

if __name__ == "__main__":
    main()