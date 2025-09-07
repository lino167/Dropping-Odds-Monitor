#!/usr/bin/env python3
"""
Configurador do Sistema de Monitoramento de Drops

Este módulo fornece uma interface para configurar e gerenciar
o sistema de monitoramento em tempo real de drops de odds.
"""

import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class AlertThresholds:
    """Configuração de limites para alertas."""
    # Limites por tipo de aposta (porcentagem de queda)
    bet_1x2: float = 5.0
    bet_total: float = 8.0
    bet_handicap: float = 6.0
    bet_total_ht: float = 10.0
    bet_1x2_ht: float = 7.0
    
    # Limites de severidade
    low_threshold: float = 5.0
    medium_threshold: float = 10.0
    high_threshold: float = 20.0
    critical_threshold: float = 30.0
    
    # Filtros de odds
    min_odds: float = 1.10
    max_odds: float = 50.0
    
    # Configurações temporais
    time_window_minutes: int = 60
    min_data_points: int = 2

@dataclass
class MonitoringProfile:
    """Perfil de monitoramento."""
    name: str
    description: str
    game_ids: List[str]
    extraction_interval_minutes: int
    alert_thresholds: AlertThresholds
    auto_dashboard: bool = True
    max_history_files: int = 50
    output_directory: str = "monitoring_data"
    
class MonitorConfigurator:
    """Configurador do sistema de monitoramento."""
    
    def __init__(self, config_file: str = "monitor_profiles.json"):
        """Inicializa o configurador.
        
        Args:
            config_file: Arquivo de configuração dos perfis
        """
        self.config_file = config_file
        self.profiles = self._load_profiles()
    
    def _load_profiles(self) -> Dict[str, MonitoringProfile]:
        """Carrega perfis de configuração.
        
        Returns:
            Dict[str, MonitoringProfile]: Perfis carregados
        """
        if not os.path.exists(self.config_file):
            return self._create_default_profiles()
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            profiles = {}
            for name, profile_data in data.items():
                # Reconstrói AlertThresholds
                thresholds_data = profile_data.pop('alert_thresholds', {})
                alert_thresholds = AlertThresholds(**thresholds_data)
                
                # Reconstrói MonitoringProfile
                profile = MonitoringProfile(
                    alert_thresholds=alert_thresholds,
                    **profile_data
                )
                profiles[name] = profile
            
            return profiles
            
        except Exception as e:
            print(f"⚠️ Erro ao carregar perfis: {str(e)}")
            return self._create_default_profiles()
    
    def _create_default_profiles(self) -> Dict[str, MonitoringProfile]:
        """Cria perfis padrão.
        
        Returns:
            Dict[str, MonitoringProfile]: Perfis padrão
        """
        profiles = {}
        
        # Perfil Conservador
        profiles['conservative'] = MonitoringProfile(
            name='conservative',
            description='Monitoramento conservador - detecta apenas drops significativos',
            game_ids=["10519888"],
            extraction_interval_minutes=10,
            alert_thresholds=AlertThresholds(
                bet_1x2=8.0,
                bet_total=12.0,
                bet_handicap=10.0,
                bet_total_ht=15.0,
                bet_1x2_ht=12.0,
                low_threshold=8.0,
                medium_threshold=15.0,
                high_threshold=25.0,
                critical_threshold=40.0
            )
        )
        
        # Perfil Agressivo
        profiles['aggressive'] = MonitoringProfile(
            name='aggressive',
            description='Monitoramento agressivo - detecta drops menores',
            game_ids=["10519888"],
            extraction_interval_minutes=3,
            alert_thresholds=AlertThresholds(
                bet_1x2=3.0,
                bet_total=5.0,
                bet_handicap=4.0,
                bet_total_ht=6.0,
                bet_1x2_ht=4.0,
                low_threshold=3.0,
                medium_threshold=7.0,
                high_threshold=15.0,
                critical_threshold=25.0
            )
        )
        
        # Perfil Balanceado
        profiles['balanced'] = MonitoringProfile(
            name='balanced',
            description='Monitoramento balanceado - configuração padrão',
            game_ids=["10519888"],
            extraction_interval_minutes=5,
            alert_thresholds=AlertThresholds()  # Usa valores padrão
        )
        
        # Perfil Multi-Jogos
        profiles['multi_game'] = MonitoringProfile(
            name='multi_game',
            description='Monitoramento de múltiplos jogos',
            game_ids=["10519888", "10519889", "10519890"],
            extraction_interval_minutes=8,
            alert_thresholds=AlertThresholds(
                bet_1x2=6.0,
                bet_total=9.0,
                bet_handicap=7.0,
                bet_total_ht=12.0,
                bet_1x2_ht=8.0
            ),
            max_history_files=100
        )
        
        return profiles
    
    def save_profiles(self):
        """Salva perfis no arquivo de configuração."""
        try:
            # Converte perfis para dicionário serializável
            data = {}
            for name, profile in self.profiles.items():
                profile_dict = asdict(profile)
                data[name] = profile_dict
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Perfis salvos em {self.config_file}")
            
        except Exception as e:
            print(f"❌ Erro ao salvar perfis: {str(e)}")
    
    def get_profile(self, name: str) -> Optional[MonitoringProfile]:
        """Obtém um perfil específico.
        
        Args:
            name: Nome do perfil
            
        Returns:
            Optional[MonitoringProfile]: Perfil encontrado ou None
        """
        return self.profiles.get(name)
    
    def list_profiles(self) -> List[str]:
        """Lista nomes dos perfis disponíveis.
        
        Returns:
            List[str]: Nomes dos perfis
        """
        return list(self.profiles.keys())
    
    def create_profile(self, profile: MonitoringProfile) -> bool:
        """Cria um novo perfil.
        
        Args:
            profile: Perfil para criar
            
        Returns:
            bool: True se criado com sucesso
        """
        if profile.name in self.profiles:
            print(f"⚠️ Perfil '{profile.name}' já existe")
            return False
        
        self.profiles[profile.name] = profile
        self.save_profiles()
        print(f"✅ Perfil '{profile.name}' criado")
        return True
    
    def update_profile(self, name: str, profile: MonitoringProfile) -> bool:
        """Atualiza um perfil existente.
        
        Args:
            name: Nome do perfil para atualizar
            profile: Novos dados do perfil
            
        Returns:
            bool: True se atualizado com sucesso
        """
        if name not in self.profiles:
            print(f"⚠️ Perfil '{name}' não encontrado")
            return False
        
        self.profiles[name] = profile
        self.save_profiles()
        print(f"✅ Perfil '{name}' atualizado")
        return True
    
    def delete_profile(self, name: str) -> bool:
        """Remove um perfil.
        
        Args:
            name: Nome do perfil para remover
            
        Returns:
            bool: True se removido com sucesso
        """
        if name not in self.profiles:
            print(f"⚠️ Perfil '{name}' não encontrado")
            return False
        
        del self.profiles[name]
        self.save_profiles()
        print(f"✅ Perfil '{name}' removido")
        return True
    
    def print_profile_details(self, name: str):
        """Exibe detalhes de um perfil.
        
        Args:
            name: Nome do perfil
        """
        profile = self.get_profile(name)
        if not profile:
            print(f"❌ Perfil '{name}' não encontrado")
            return
        
        print(f"\n📋 Perfil: {profile.name}")
        print(f"   📝 Descrição: {profile.description}")
        print(f"   🎯 Jogos: {', '.join(profile.game_ids)}")
        print(f"   ⏱️ Intervalo: {profile.extraction_interval_minutes} minutos")
        print(f"   📁 Diretório: {profile.output_directory}")
        print(f"   📊 Dashboard automático: {'Sim' if profile.auto_dashboard else 'Não'}")
        print(f"   📚 Máx. arquivos histórico: {profile.max_history_files}")
        
        print(f"\n   🚨 Limites de Alerta:")
        thresholds = profile.alert_thresholds
        print(f"      1x2: {thresholds.bet_1x2}%")
        print(f"      Total: {thresholds.bet_total}%")
        print(f"      Handicap: {thresholds.bet_handicap}%")
        print(f"      Total HT: {thresholds.bet_total_ht}%")
        print(f"      1x2 HT: {thresholds.bet_1x2_ht}%")
        
        print(f"\n   📈 Severidade:")
        print(f"      Baixa: {thresholds.low_threshold}%")
        print(f"      Média: {thresholds.medium_threshold}%")
        print(f"      Alta: {thresholds.high_threshold}%")
        print(f"      Crítica: {thresholds.critical_threshold}%")
    
    def interactive_profile_creator(self) -> Optional[MonitoringProfile]:
        """Interface interativa para criar perfil.
        
        Returns:
            Optional[MonitoringProfile]: Perfil criado ou None
        """
        print("\n🛠️ Criador Interativo de Perfil")
        print("=" * 40)
        
        try:
            # Informações básicas
            name = input("Nome do perfil: ").strip()
            if not name:
                print("❌ Nome é obrigatório")
                return None
            
            description = input("Descrição: ").strip() or f"Perfil {name}"
            
            # IDs dos jogos
            game_ids_input = input("IDs dos jogos (separados por vírgula): ").strip()
            game_ids = [gid.strip() for gid in game_ids_input.split(',') if gid.strip()]
            
            if not game_ids:
                game_ids = ["10519888"]  # Padrão
                print(f"Usando jogo padrão: {game_ids[0]}")
            
            # Intervalo
            interval_input = input("Intervalo entre extrações (minutos) [5]: ").strip()
            interval = int(interval_input) if interval_input.isdigit() else 5
            
            # Limites de alerta
            print("\nConfiguração de limites (pressione Enter para usar padrão):")
            
            thresholds = AlertThresholds()
            
            # Pergunta sobre cada limite
            limits = [
                ('bet_1x2', '1x2', thresholds.bet_1x2),
                ('bet_total', 'Total', thresholds.bet_total),
                ('bet_handicap', 'Handicap', thresholds.bet_handicap),
                ('bet_total_ht', 'Total HT', thresholds.bet_total_ht),
                ('bet_1x2_ht', '1x2 HT', thresholds.bet_1x2_ht)
            ]
            
            for attr, display_name, default in limits:
                value_input = input(f"{display_name} [{default}%]: ").strip()
                if value_input:
                    try:
                        setattr(thresholds, attr, float(value_input))
                    except ValueError:
                        print(f"⚠️ Valor inválido para {display_name}, usando padrão")
            
            # Cria perfil
            profile = MonitoringProfile(
                name=name,
                description=description,
                game_ids=game_ids,
                extraction_interval_minutes=interval,
                alert_thresholds=thresholds
            )
            
            return profile
            
        except KeyboardInterrupt:
            print("\n⏹️ Criação cancelada")
            return None
        except Exception as e:
            print(f"❌ Erro na criação: {str(e)}")
            return None

def main():
    """Função principal para gerenciar configurações."""
    configurator = MonitorConfigurator()
    
    while True:
        print("\n🔧 Configurador de Monitoramento")
        print("=" * 35)
        print("1. Listar perfis")
        print("2. Ver detalhes de perfil")
        print("3. Criar novo perfil")
        print("4. Criar perfil interativo")
        print("5. Remover perfil")
        print("0. Sair")
        
        choice = input("\nEscolha uma opção: ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            profiles = configurator.list_profiles()
            print(f"\n📋 Perfis disponíveis ({len(profiles)}):")
            for i, profile_name in enumerate(profiles, 1):
                profile = configurator.get_profile(profile_name)
                print(f"   {i}. {profile_name} - {profile.description}")
        
        elif choice == '2':
            profile_name = input("Nome do perfil: ").strip()
            configurator.print_profile_details(profile_name)
        
        elif choice == '3':
            # Exemplo de criação programática
            print("\n📝 Exemplo de criação de perfil personalizado")
            print("(Edite o código para personalizar)")
            
        elif choice == '4':
            profile = configurator.interactive_profile_creator()
            if profile:
                configurator.create_profile(profile)
        
        elif choice == '5':
            profile_name = input("Nome do perfil para remover: ").strip()
            if profile_name:
                configurator.delete_profile(profile_name)
        
        else:
            print("❌ Opção inválida")

if __name__ == "__main__":
    main()