#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script principal para extração de dados de jogos ao vivo
Exibe os dados extraídos de forma organizada
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'v2'))

from modules.scraper.live_extractor import LiveGamesExtractor
from datetime import datetime

def main():
    """Função principal para extração e exibição dos dados"""
    print("=" * 60)
    print("🏆 EXTRATOR DE JOGOS AO VIVO - DROPPING ODDS")
    print("=" * 60)
    print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    extractor = LiveGamesExtractor(headless=True)
    
    try:
        print("🔄 Iniciando extração...")
        games = extractor.extract_live_games()
        
        if not games:
            print("❌ Nenhum jogo encontrado.")
            return
        
        print(f"✅ {len(games)} jogos extraídos com sucesso!")
        print()
        
        # Exibir dados organizados
        print("📊 DADOS EXTRAÍDOS:")
        print("=" * 60)
        
        for i, game in enumerate(games, 1):
            print(f"🎮 JOGO {i:02d}")
            print(f"   🏆 Liga: {game.league}")
            print(f"   🏠 Casa: {game.home_team}")
            print(f"   ⚽ Placar: {game.score}")
            print(f"   🏃 Visitante: {game.away_team}")
            print(f"   ⏰ Tempo: {game.time}")
            print(f"   🆔 Game ID: {game.game_id}")
            if game.country:
                print(f"   🌍 País: {game.country}")
            if game.game_url:
                print(f"   🔗 URL: {game.game_url}")
            print()
        
        # Estatísticas
        print("📈 ESTATÍSTICAS:")
        print("=" * 60)
        print(f"📊 Total de jogos: {len(games)}")
        
        games_with_id = sum(1 for game in games if game.game_id)
        print(f"🆔 Jogos com ID: {games_with_id}")
        print(f"📊 Taxa de captura de ID: {(games_with_id/len(games)*100):.1f}%")
        
        # Ligas únicas
        unique_leagues = set(game.league for game in games if game.league)
        print(f"🏆 Ligas diferentes: {len(unique_leagues)}")
        
        # Países únicos
        unique_countries = set(game.country for game in games if game.country)
        print(f"🌍 Países diferentes: {len(unique_countries)}")
        
        print()
        print("✅ Extração concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante a extração: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("🔄 Finalizando...")

if __name__ == "__main__":
    main()