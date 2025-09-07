#!/usr/bin/env python3
"""
Sistema Completo de Monitoramento de Drops

Este é o script principal que integra todos os componentes:
- Monitor em tempo real
- Configurador de perfis
- Analisador de drops
- Dashboard de visualização
- Sistema de alertas
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from typing import Optional

# Importa componentes do sistema
from real_time_monitor import RealTimeMonitor, MonitorConfig
from monitor_config import MonitorConfigurator, MonitoringProfile
from drop_analyzer import DropAnalyzer
from drop_dashboard import DropDashboard

class DropMonitoringSystem:
    """Sistema principal de monitoramento de drops."""
    
    def __init__(self):
        """Inicializa o sistema."""
        self.configurator = MonitorConfigurator()
        self.current_monitor: Optional[RealTimeMonitor] = None
        
    def list_profiles(self):
        """Lista perfis disponíveis."""
        profiles = self.configurator.list_profiles()
        
        print(f"\n📋 Perfis de Monitoramento Disponíveis ({len(profiles)}):")
        print("=" * 50)
        
        for i, profile_name in enumerate(profiles, 1):
            profile = self.configurator.get_profile(profile_name)
            print(f"{i:2d}. {profile.name}")
            print(f"     📝 {profile.description}")
            print(f"     🎯 Jogos: {len(profile.game_ids)} | ⏱️ {profile.extraction_interval_minutes}min")
            print()
    
    def show_profile_details(self, profile_name: str):
        """Mostra detalhes de um perfil.
        
        Args:
            profile_name: Nome do perfil
        """
        self.configurator.print_profile_details(profile_name)
    
    def start_monitoring(self, profile_name: str):
        """Inicia monitoramento com um perfil específico.
        
        Args:
            profile_name: Nome do perfil para usar
        """
        profile = self.configurator.get_profile(profile_name)
        if not profile:
            print(f"❌ Perfil '{profile_name}' não encontrado")
            return False
        
        # Converte perfil para configuração do monitor
        config = self._profile_to_monitor_config(profile)
        
        # Cria e inicia monitor
        self.current_monitor = RealTimeMonitor(config)
        
        print(f"\n🚀 Iniciando monitoramento com perfil '{profile_name}'")
        print(f"   📊 Jogos: {', '.join(profile.game_ids)}")
        print(f"   ⏱️ Intervalo: {profile.extraction_interval_minutes} minutos")
        print(f"   📁 Saída: {profile.output_directory}")
        print("\n⚠️ Pressione Ctrl+C para parar o monitoramento")
        
        try:
            self.current_monitor.start_monitoring()
            return True
        except KeyboardInterrupt:
            print("\n⏹️ Monitoramento interrompido pelo usuário")
            return True
        except Exception as e:
            print(f"❌ Erro no monitoramento: {str(e)}")
            return False
    
    def _profile_to_monitor_config(self, profile: MonitoringProfile) -> MonitorConfig:
        """Converte perfil de monitoramento para configuração do monitor.
        
        Args:
            profile: Perfil de monitoramento
            
        Returns:
            MonitorConfig: Configuração do monitor
        """
        # Converte AlertThresholds para dicionário
        alert_thresholds = {
            '1x2': profile.alert_thresholds.bet_1x2,
            'total': profile.alert_thresholds.bet_total,
            'handicap': profile.alert_thresholds.bet_handicap,
            'total_ht': profile.alert_thresholds.bet_total_ht,
            '1x2_ht': profile.alert_thresholds.bet_1x2_ht,
            'low_threshold': profile.alert_thresholds.low_threshold,
            'medium_threshold': profile.alert_thresholds.medium_threshold,
            'high_threshold': profile.alert_thresholds.high_threshold,
            'critical_threshold': profile.alert_thresholds.critical_threshold,
            'min_odds': profile.alert_thresholds.min_odds,
            'max_odds': profile.alert_thresholds.max_odds,
            'time_window_minutes': profile.alert_thresholds.time_window_minutes,
            'min_data_points': profile.alert_thresholds.min_data_points
        }
        
        return MonitorConfig(
            game_ids=profile.game_ids,
            extraction_interval_seconds=profile.extraction_interval_minutes * 60,
            alert_thresholds=alert_thresholds,
            auto_dashboard=profile.auto_dashboard,
            max_history_files=profile.max_history_files,
            output_directory=profile.output_directory
        )
    
    def analyze_existing_data(self, data_directory: str = "."):
        """Analisa dados existentes para detectar drops.
        
        Args:
            data_directory: Diretório com arquivos de extração
        """
        print(f"\n🔍 Analisando dados existentes em '{data_directory}'...")
        
        # Cria analisador
        analyzer = DropAnalyzer()
        
        # Encontra arquivos de extração
        extraction_files = [
            f for f in os.listdir(data_directory)
            if f.startswith('unified_extraction_') and f.endswith('.json')
        ]
        
        if not extraction_files:
            print("❌ Nenhum arquivo de extração encontrado")
            return
        
        print(f"📁 Encontrados {len(extraction_files)} arquivos de extração")
        
        # Carrega e analisa dados
        for file in extraction_files:
            file_path = os.path.join(data_directory, file)
            print(f"   📊 Carregando {file}...")
            analyzer.load_extraction_data(file_path)
        
        # Executa análise
        print("\n🔬 Executando análise de drops...")
        results = analyzer.analyze_all_games()
        
        if not results:
            print("❌ Nenhum resultado de análise")
            return
        
        # Mostra estatísticas
        total_alerts = sum(len(game_results.get('alerts', [])) for game_results in results.values())
        
        print(f"\n📈 Resultados da Análise:")
        print(f"   🎯 Jogos analisados: {len(results)}")
        print(f"   🚨 Total de alertas: {total_alerts}")
        
        # Salva relatório
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"drop_analysis_report_{timestamp}.json"
        
        analyzer.save_analysis_report(report_file)
        print(f"   💾 Relatório salvo: {report_file}")
        
        # Gera dashboard
        print("\n🎨 Gerando dashboard...")
        dashboard = DropDashboard(analyzer)
        dashboard_file = f"drop_dashboard_{timestamp}.html"
        dashboard.generate_html_dashboard(dashboard_file)
        print(f"   🌐 Dashboard salvo: {dashboard_file}")
        
        return report_file, dashboard_file
    
    def create_profile_interactive(self):
        """Cria perfil interativamente."""
        profile = self.configurator.interactive_profile_creator()
        if profile:
            self.configurator.create_profile(profile)
            return True
        return False
    
    def get_monitor_status(self) -> dict:
        """Obtém status do monitor atual.
        
        Returns:
            dict: Status do monitor
        """
        if not self.current_monitor:
            return {'status': 'not_running'}
        
        return self.current_monitor.get_status()

def create_argument_parser():
    """Cria parser de argumentos da linha de comando.
    
    Returns:
        argparse.ArgumentParser: Parser configurado
    """
    parser = argparse.ArgumentParser(
        description='Sistema de Monitoramento de Drops de Odds',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python drop_monitoring_system.py --list-profiles
  python drop_monitoring_system.py --profile balanced --start
  python drop_monitoring_system.py --analyze-data .
  python drop_monitoring_system.py --create-profile
  python drop_monitoring_system.py --profile-details conservative
        """
    )
    
    # Comandos principais
    parser.add_argument('--list-profiles', action='store_true',
                       help='Lista perfis de monitoramento disponíveis')
    
    parser.add_argument('--profile-details', metavar='NAME',
                       help='Mostra detalhes de um perfil específico')
    
    parser.add_argument('--create-profile', action='store_true',
                       help='Cria novo perfil interativamente')
    
    parser.add_argument('--start', action='store_true',
                       help='Inicia monitoramento (requer --profile)')
    
    parser.add_argument('--profile', metavar='NAME',
                       help='Nome do perfil para usar')
    
    parser.add_argument('--analyze-data', metavar='DIRECTORY',
                       help='Analisa dados existentes no diretório especificado')
    
    return parser

def main():
    """Função principal."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Cria sistema
    system = DropMonitoringSystem()
    
    # Processa comandos
    if args.list_profiles:
        system.list_profiles()
    
    elif args.profile_details:
        system.show_profile_details(args.profile_details)
    
    elif args.create_profile:
        if system.create_profile_interactive():
            print("✅ Perfil criado com sucesso")
        else:
            print("❌ Falha na criação do perfil")
    
    elif args.start:
        if not args.profile:
            print("❌ Especifique um perfil com --profile")
            return 1
        
        success = system.start_monitoring(args.profile)
        return 0 if success else 1
    
    elif args.analyze_data:
        try:
            report_file, dashboard_file = system.analyze_existing_data(args.analyze_data)
            print(f"\n✅ Análise concluída:")
            print(f"   📊 Relatório: {report_file}")
            print(f"   🌐 Dashboard: {dashboard_file}")
        except Exception as e:
            print(f"❌ Erro na análise: {str(e)}")
            return 1
    
    else:
        # Modo interativo
        print("\n🎯 Sistema de Monitoramento de Drops")
        print("=" * 40)
        print("Escolha uma opção:")
        print("1. Listar perfis")
        print("2. Ver detalhes de perfil")
        print("3. Criar novo perfil")
        print("4. Iniciar monitoramento")
        print("5. Analisar dados existentes")
        print("0. Sair")
        
        while True:
            try:
                choice = input("\nOpção: ").strip()
                
                if choice == '0':
                    break
                elif choice == '1':
                    system.list_profiles()
                elif choice == '2':
                    profile_name = input("Nome do perfil: ").strip()
                    if profile_name:
                        system.show_profile_details(profile_name)
                elif choice == '3':
                    system.create_profile_interactive()
                elif choice == '4':
                    system.list_profiles()
                    profile_name = input("\nNome do perfil para usar: ").strip()
                    if profile_name:
                        system.start_monitoring(profile_name)
                elif choice == '5':
                    data_dir = input("Diretório de dados [.]: ").strip() or "."
                    try:
                        system.analyze_existing_data(data_dir)
                    except Exception as e:
                        print(f"❌ Erro na análise: {str(e)}")
                else:
                    print("❌ Opção inválida")
                    
            except KeyboardInterrupt:
                print("\n👋 Saindo...")
                break
            except Exception as e:
                print(f"❌ Erro: {str(e)}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())