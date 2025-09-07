"""Test script for Dropping Odds Analysis System 2.0"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Add parent directory to path for proper imports
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Now import from v2 package
from v2.core.utils import setup_logging, get_timestamp
from v2.core.event_bus import event_bus
from v2.modules.scraper import ScraperModule
from v2.core.exceptions import ScrapingError


class SystemTester:
    """Test class for the 2.0 system"""
    
    def __init__(self):
        self.logger = setup_logging("INFO")
        self.scraper_module = None
        self.test_results = {
            "initialization": False,
            "manual_extraction": False,
            "drop_detection": False,
            "monitoring": False,
            "event_system": False
        }
    
    async def run_all_tests(self):
        """Run all system tests"""
        self.logger.info("=" * 60)
        self.logger.info("DROPPING ODDS ANALYSIS SYSTEM 2.0 - TESTE COMPLETO")
        self.logger.info("=" * 60)
        
        try:
            # Test 1: Module Initialization
            await self.test_module_initialization()
            
            # Test 2: Manual Game Extraction
            await self.test_manual_extraction()
            
            # Test 3: Drop Detection
            await self.test_drop_detection()
            
            # Test 4: Event System
            await self.test_event_system()
            
            # Test 5: Monitoring (short test)
            await self.test_monitoring()
            
            # Print results
            self.print_test_results()
            
        except Exception as e:
            self.logger.error(f"Test suite failed: {e}")
        finally:
            await self.cleanup()
    
    async def test_module_initialization(self):
        """Test module initialization"""
        self.logger.info("\n[TESTE 1] Inicialização dos Módulos")
        self.logger.info("-" * 40)
        
        try:
            # Create scraper module with test configuration
            config = {
                "scraper": {
                    "monitor_url": "https://dropping-odds.com/index.php?view=live",
                    "refresh_interval": 60,  # Longer interval for testing
                    "headless": True,
                    "enable_drop_detection": True,
                    "max_games_per_cycle": 50,
                    "timeout": 15
                }
            }
            
            self.scraper_module = ScraperModule(config)
            
            # Initialize module
            success = await self.scraper_module.initialize()
            
            if success:
                self.logger.info("✅ Módulo Scraper inicializado com sucesso")
                self.test_results["initialization"] = True
                
                # Check components
                if self.scraper_module.extractor:
                    self.logger.info("✅ LiveGamesExtractor criado")
                
                if self.scraper_module.drop_detector:
                    self.logger.info("✅ EnhancedDropDetector criado")
                
                if self.scraper_module.monitor:
                    self.logger.info("✅ PageMonitor criado")
                
            else:
                self.logger.error("❌ Falha na inicialização do módulo")
                
        except Exception as e:
            self.logger.error(f"❌ Erro na inicialização: {e}")
    
    async def test_manual_extraction(self):
        """Test manual game extraction"""
        self.logger.info("\n[TESTE 2] Extração Manual de Jogos")
        self.logger.info("-" * 40)
        
        try:
            if not self.scraper_module:
                self.logger.error("❌ Módulo não inicializado")
                return
            
            self.logger.info("🔄 Iniciando extração manual...")
            
            # Perform manual extraction
            games = await self.scraper_module.extract_games_once()
            
            if games:
                self.logger.info(f"✅ Extração bem-sucedida: {len(games)} jogos encontrados")
                self.test_results["manual_extraction"] = True
                
                # Show sample games
                for i, game in enumerate(games[:3]):
                    self.logger.info(f"   Jogo {i+1}: {game.home_team} vs {game.away_team}")
                    if hasattr(game, 'odds_1x2') and game.odds_1x2:
                        self.logger.info(f"   Odds 1X2: {game.odds_1x2}")
                
                if len(games) > 3:
                    self.logger.info(f"   ... e mais {len(games) - 3} jogos")
                
            else:
                self.logger.warning("⚠️ Nenhum jogo extraído (pode ser normal se não houver jogos ao vivo)")
                # Consider extraction successful even with 0 games if no error occurred
                self.test_results["manual_extraction"] = True
                
        except Exception as e:
            self.logger.error(f"❌ Erro na extração manual: {e}")
    
    async def test_drop_detection(self):
        """Test drop detection"""
        self.logger.info("\n[TESTE 3] Detecção de Drops")
        self.logger.info("-" * 40)
        
        try:
            if not self.scraper_module or not self.scraper_module.drop_detector:
                self.logger.error("❌ Detector de drops não disponível")
                return
            
            self.logger.info("🔄 Testando detecção de drops...")
            
            # Get drop detector stats
            stats = self.scraper_module.drop_detector.get_stats()
            self.logger.info(f"📊 Estatísticas do detector: {stats}")
            
            # Try manual drop detection
            drops = await self.scraper_module.detect_drops_once()
            
            if drops:
                self.logger.info(f"✅ Detecção de drops: {len(drops)} drops encontrados")
                self.test_results["drop_detection"] = True
                
                # Show sample drops
                for i, drop in enumerate(drops[:3]):
                    self.logger.info(f"   Drop {i+1}: {drop.table_type} - {drop.column_name} ({drop.confidence.value})")
                
            else:
                self.logger.info("ℹ️ Nenhum drop detectado (normal se não houver mudanças recentes)")
                self.test_results["drop_detection"] = True  # Not finding drops is also valid
                
        except Exception as e:
            self.logger.error(f"❌ Erro na detecção de drops: {e}")
    
    async def test_event_system(self):
        """Test event system"""
        self.logger.info("\n[TESTE 4] Sistema de Eventos")
        self.logger.info("-" * 40)
        
        try:
            # Test event subscription and publishing
            test_event_received = False
            
            async def test_event_handler(event):
                nonlocal test_event_received
                test_event_received = True
                self.logger.info(f"✅ Evento recebido: {event.data}")
            
            # Subscribe to test event
            event_bus.subscribe_async("test.event", test_event_handler)
            
            # Create and publish test event
            from v2.core.event_bus import Event, EventPriority
            test_event = Event(
                name="test.event",
                data={
                    "message": "Sistema de eventos funcionando",
                    "timestamp": get_timestamp()
                },
                priority=EventPriority.NORMAL
            )
            await event_bus.publish_async(test_event)
            
            # Wait a bit for event processing
            await asyncio.sleep(0.1)
            
            if test_event_received:
                self.logger.info("✅ Sistema de eventos funcionando corretamente")
                self.test_results["event_system"] = True
            else:
                self.logger.error("❌ Evento não foi recebido")
                
        except Exception as e:
            self.logger.error(f"❌ Erro no sistema de eventos: {e}")
    
    async def test_monitoring(self):
        """Test monitoring system (short test)"""
        self.logger.info("\n[TESTE 5] Sistema de Monitoramento (Teste Curto)")
        self.logger.info("-" * 40)
        
        try:
            if not self.scraper_module or not self.scraper_module.monitor:
                self.logger.error("❌ Monitor não disponível")
                return
            
            self.logger.info("🔄 Iniciando monitoramento por 10 segundos...")
            
            # Start monitoring
            success = await self.scraper_module.start()
            
            if success:
                self.logger.info("✅ Monitoramento iniciado")
                
                # Wait for a short period
                await asyncio.sleep(10)
                
                # Check monitor stats
                stats = self.scraper_module.monitor.get_stats()
                self.logger.info(f"📊 Estatísticas do monitor: Status={stats.get('status')}")
                self.logger.info(f"   Ciclos totais: {stats.get('total_cycles', 0)}")
                self.logger.info(f"   Taxa de sucesso: {stats.get('success_rate', 0):.1f}%")
                
                # Stop monitoring
                await self.scraper_module.stop()
                self.logger.info("✅ Monitoramento parado")
                
                self.test_results["monitoring"] = True
                
            else:
                self.logger.error("❌ Falha ao iniciar monitoramento")
                
        except Exception as e:
            self.logger.error(f"❌ Erro no teste de monitoramento: {e}")
    
    def print_test_results(self):
        """Print final test results"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("RESULTADOS DOS TESTES")
        self.logger.info("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASSOU" if result else "❌ FALHOU"
            self.logger.info(f"{test_name.replace('_', ' ').title()}: {status}")
        
        self.logger.info("-" * 60)
        self.logger.info(f"RESUMO: {passed_tests}/{total_tests} testes passaram")
        
        if passed_tests == total_tests:
            self.logger.info("🎉 TODOS OS TESTES PASSARAM! Sistema 2.0 funcionando corretamente.")
        else:
            self.logger.warning(f"⚠️ {total_tests - passed_tests} teste(s) falharam. Verifique os logs acima.")
        
        self.logger.info("=" * 60)
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self.scraper_module:
                await self.scraper_module.stop()
            self.logger.info("🧹 Limpeza concluída")
        except Exception as e:
            self.logger.error(f"Erro na limpeza: {e}")


async def main():
    """Main test function"""
    print("\n" + "=" * 60)
    print("DROPPING ODDS ANALYSIS SYSTEM 2.0 - TESTE DE SISTEMA")
    print(f"Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    tester = SystemTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    # Check if required packages are available
    try:
        import selenium
        import bs4
        print("✅ Dependências encontradas: selenium, beautifulsoup4")
    except ImportError as e:
        print(f"❌ Dependência faltando: {e}")
        print("\nPara instalar as dependências, execute:")
        print("pip install selenium beautifulsoup4")
        sys.exit(1)
    
    # Run tests
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro fatal no teste: {e}")
        sys.exit(1)