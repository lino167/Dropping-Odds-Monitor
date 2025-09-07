#!/usr/bin/env python3
"""
Sistema Principal de Análise de Drops

Ponto de entrada principal para o sistema de detecção e análise de drops de odds.
Este arquivo organiza e coordena todos os módulos do projeto.

Estrutura do Projeto:
├── analyzers/     - Módulos de análise de drops
├── dashboards/    - Sistemas de dashboard e visualização
├── extractors/    - Módulos de extração de dados
├── systems/       - Sistemas integrados e monitoramento
├── tests/         - Testes e debugging
├── config/        - Arquivos de configuração
├── data/          - Dados, JSONs e HTMLs gerados
├── docs/          - Documentação
└── v2/            - Versão 2 do sistema (arquitetura modular)

Autor: Sistema de Análise de Drops
Versão: 1.0
"""

import os
import sys
from pathlib import Path

# Adiciona os diretórios do projeto ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "analyzers"))
sys.path.insert(0, str(project_root / "dashboards"))
sys.path.insert(0, str(project_root / "extractors"))
sys.path.insert(0, str(project_root / "systems"))

def show_menu():
    """Exibe o menu principal do sistema"""
    print("\n" + "="*60)
    print("🎯 SISTEMA DE ANÁLISE DE DROPS - MENU PRINCIPAL")
    print("="*60)
    print("\n📊 SISTEMAS PRINCIPAIS:")
    print("1. Sistema Robusto de Drops (Recomendado)")
    print("2. Sistema Integrado de Drops")
    print("3. Dashboard Ultimate")
    print("\n🔧 FERRAMENTAS DE EXTRAÇÃO:")
    print("4. Extrator Completo de Dados")
    print("5. Extrator de Dados ao Vivo")
    print("6. Extrator Unificado")
    print("\n📈 ANÁLISE E MONITORAMENTO:")
    print("7. Analisador de Drops")
    print("8. Monitor em Tempo Real")
    print("9. Sistema de Monitoramento de Drops")
    print("\n🎨 DASHBOARDS:")
    print("10. Dashboard Aprimorado")
    print("11. Dashboard Visual")
    print("12. Dashboard de Drops")
    print("\n🧪 TESTES E DEBUG:")
    print("13. Executar Testes")
    print("14. Debug de Estrutura")
    print("\n0. Sair")
    print("="*60)

def run_robust_drops_system():
    """Executa o sistema robusto de drops"""
    try:
        from systems.robust_drops_system import RobustDropsSystem
        print("\n🚀 Iniciando Sistema Robusto de Drops...")
        system = RobustDropsSystem()
        system.start_monitoring(interval_minutes=3, max_cycles=5)
    except ImportError as e:
        print(f"❌ Erro ao importar sistema robusto: {e}")
        print("Verifique se o arquivo está em systems/robust_drops_system.py")
    except Exception as e:
        print(f"❌ Erro ao executar sistema robusto: {e}")

def run_integrated_system():
    """Executa o sistema integrado"""
    try:
        from systems.integrated_drops_system import IntegratedDropsSystem
        print("\n🚀 Iniciando Sistema Integrado...")
        system = IntegratedDropsSystem()
        system.start_monitoring()
    except ImportError as e:
        print(f"❌ Erro ao importar sistema integrado: {e}")
    except Exception as e:
        print(f"❌ Erro ao executar sistema integrado: {e}")

def run_ultimate_dashboard():
    """Executa o dashboard ultimate"""
    try:
        from dashboards.ultimate_dashboard import UltimateDashboard
        print("\n📊 Iniciando Dashboard Ultimate...")
        dashboard = UltimateDashboard()
        dashboard.run()
    except ImportError as e:
        print(f"❌ Erro ao importar dashboard ultimate: {e}")
    except Exception as e:
        print(f"❌ Erro ao executar dashboard ultimate: {e}")

def run_complete_extractor():
    """Executa o extrator completo"""
    try:
        from extractors.complete_extractor import main
        print("\n🔄 Iniciando Extrator Completo...")
        main()
    except ImportError as e:
        print(f"❌ Erro ao importar extrator completo: {e}")
    except Exception as e:
        print(f"❌ Erro ao executar extrator completo: {e}")

def run_live_extractor():
    """Executa o extrator ao vivo"""
    try:
        from extractors.complete_live_extractor import main
        print("\n📡 Iniciando Extrator ao Vivo...")
        main()
    except ImportError as e:
        print(f"❌ Erro ao importar extrator ao vivo: {e}")
    except Exception as e:
        print(f"❌ Erro ao executar extrator ao vivo: {e}")

def run_unified_extractor():
    """Executa o extrator unificado"""
    try:
        from extractors.unified_extractor import main
        print("\n🔗 Iniciando Extrator Unificado...")
        main()
    except ImportError as e:
        print(f"❌ Erro ao importar extrator unificado: {e}")
    except Exception as e:
        print(f"❌ Erro ao executar extrator unificado: {e}")

def run_drop_analyzer():
    """Executa o analisador de drops"""
    try:
        from analyzers.drop_analyzer import DropAnalyzer
        print("\n🔍 Iniciando Analisador de Drops...")
        analyzer = DropAnalyzer()
        # Implementar lógica específica
        print("Analisador iniciado com sucesso!")
    except ImportError as e:
        print(f"❌ Erro ao importar analisador: {e}")
    except Exception as e:
        print(f"❌ Erro ao executar analisador: {e}")

def run_real_time_monitor():
    """Executa o monitor em tempo real"""
    try:
        from systems.real_time_monitor import main
        print("\n⏱️ Iniciando Monitor em Tempo Real...")
        main()
    except ImportError as e:
        print(f"❌ Erro ao importar monitor: {e}")
    except Exception as e:
        print(f"❌ Erro ao executar monitor: {e}")

def run_drop_monitoring_system():
    """Executa o sistema de monitoramento de drops"""
    try:
        from systems.drop_monitoring_system import main
        print("\n📊 Iniciando Sistema de Monitoramento...")
        main()
    except ImportError as e:
        print(f"❌ Erro ao importar sistema de monitoramento: {e}")
    except Exception as e:
        print(f"❌ Erro ao executar sistema de monitoramento: {e}")

def run_enhanced_dashboard():
    """Executa o dashboard aprimorado"""
    try:
        from dashboards.enhanced_dashboard import main
        print("\n✨ Iniciando Dashboard Aprimorado...")
        main()
    except ImportError as e:
        print(f"❌ Erro ao importar dashboard aprimorado: {e}")
    except Exception as e:
        print(f"❌ Erro ao executar dashboard aprimorado: {e}")

def run_visual_dashboard():
    """Executa o dashboard visual"""
    try:
        from dashboards.create_visual_dashboard import main
        print("\n🎨 Iniciando Dashboard Visual...")
        main()
    except ImportError as e:
        print(f"❌ Erro ao importar dashboard visual: {e}")
    except Exception as e:
        print(f"❌ Erro ao executar dashboard visual: {e}")

def run_drop_dashboard():
    """Executa o dashboard de drops"""
    try:
        from dashboards.drop_dashboard import main
        print("\n📈 Iniciando Dashboard de Drops...")
        main()
    except ImportError as e:
        print(f"❌ Erro ao importar dashboard de drops: {e}")
    except Exception as e:
        print(f"❌ Erro ao executar dashboard de drops: {e}")

def run_tests():
    """Executa os testes do sistema"""
    print("\n🧪 Executando Testes...")
    test_files = [
        "tests/test_integrated_drop_system.py",
        "tests/test_real_data_drops.py",
        "tests/test_specific_drops.py"
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"Executando: {test_file}")
            try:
                exec(open(test_file).read())
            except Exception as e:
                print(f"❌ Erro no teste {test_file}: {e}")
        else:
            print(f"⚠️ Arquivo não encontrado: {test_file}")

def run_debug():
    """Executa ferramentas de debug"""
    try:
        from tests.debug_drops_structure import main
        print("\n🔧 Iniciando Debug de Estrutura...")
        main()
    except ImportError as e:
        print(f"❌ Erro ao importar debug: {e}")
    except Exception as e:
        print(f"❌ Erro ao executar debug: {e}")

def main():
    """Função principal"""
    print("🎯 Bem-vindo ao Sistema de Análise de Drops!")
    print(f"📁 Diretório do projeto: {project_root}")
    
    while True:
        show_menu()
        
        try:
            choice = input("\n👉 Escolha uma opção (0-14): ").strip()
            
            if choice == "0":
                print("\n👋 Saindo do sistema. Até logo!")
                break
            elif choice == "1":
                run_robust_drops_system()
            elif choice == "2":
                run_integrated_system()
            elif choice == "3":
                run_ultimate_dashboard()
            elif choice == "4":
                run_complete_extractor()
            elif choice == "5":
                run_live_extractor()
            elif choice == "6":
                run_unified_extractor()
            elif choice == "7":
                run_drop_analyzer()
            elif choice == "8":
                run_real_time_monitor()
            elif choice == "9":
                run_drop_monitoring_system()
            elif choice == "10":
                run_enhanced_dashboard()
            elif choice == "11":
                run_visual_dashboard()
            elif choice == "12":
                run_drop_dashboard()
            elif choice == "13":
                run_tests()
            elif choice == "14":
                run_debug()
            else:
                print("❌ Opção inválida! Escolha um número de 0 a 14.")
                
        except KeyboardInterrupt:
            print("\n\n⏹️ Operação interrompida pelo usuário.")
            break
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
        
        input("\n⏸️ Pressione Enter para continuar...")

if __name__ == "__main__":
    main()