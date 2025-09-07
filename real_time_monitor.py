#!/usr/bin/env python3
"""
Monitor de Drops em Tempo Real

Este módulo implementa um sistema de monitoramento contínuo que:
- Executa extrações periódicas
- Detecta drops em tempo real
- Envia alertas imediatos
- Mantém histórico de monitoramento
- Gera relatórios automáticos
"""

import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import threading
from dataclasses import dataclass, asdict
from unified_extractor import UnifiedExtractor
from drop_analyzer import DropAnalyzer, DropAlert
from drop_dashboard import DropDashboard

@dataclass
class MonitorConfig:
    """Configuração do monitor."""
    game_ids: List[str]
    extraction_interval_seconds: int = 300  # 5 minutos
    alert_thresholds: Dict = None
    auto_dashboard: bool = True
    max_history_files: int = 50
    output_directory: str = "monitoring_data"

class RealTimeMonitor:
    """Monitor de drops em tempo real."""
    
    def __init__(self, config: MonitorConfig):
        """Inicializa o monitor.
        
        Args:
            config: Configuração do monitor
        """
        self.config = config
        self.running = False
        self.extractor = None
        self.analyzer = DropAnalyzer(config.alert_thresholds)
        self.last_extraction_data = {}
        self.monitoring_stats = {
            'start_time': None,
            'total_extractions': 0,
            'total_drops_detected': 0,
            'last_extraction_time': None,
            'errors': []
        }
        
        # Cria diretório de saída
        os.makedirs(self.config.output_directory, exist_ok=True)
        
    def start_monitoring(self):
        """Inicia o monitoramento em tempo real."""
        if self.running:
            print("⚠️ Monitor já está em execução")
            return
            
        self.running = True
        self.monitoring_stats['start_time'] = datetime.now().isoformat()
        
        print(f"🚀 Iniciando monitoramento em tempo real...")
        print(f"   📊 Jogos: {', '.join(self.config.game_ids)}")
        print(f"   ⏱️ Intervalo: {self.config.extraction_interval_seconds}s")
        print(f"   📁 Diretório: {self.config.output_directory}")
        
        try:
            self._monitoring_loop()
        except KeyboardInterrupt:
            print("\n⏹️ Monitoramento interrompido pelo usuário")
        except Exception as e:
            print(f"❌ Erro no monitoramento: {str(e)}")
            self.monitoring_stats['errors'].append({
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            })
        finally:
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """Para o monitoramento."""
        self.running = False
        if self.extractor:
            self.extractor.close()
        
        # Salva estatísticas finais
        self._save_monitoring_stats()
        print(f"🛑 Monitoramento finalizado")
        
    def _monitoring_loop(self):
        """Loop principal de monitoramento."""
        while self.running:
            cycle_start = time.time()
            
            print(f"\n🔄 Ciclo de extração - {datetime.now().strftime('%H:%M:%S')}")
            
            # Executa extração para cada jogo
            for game_id in self.config.game_ids:
                if not self.running:
                    break
                    
                try:
                    self._process_game(game_id)
                except Exception as e:
                    print(f"❌ Erro ao processar jogo {game_id}: {str(e)}")
                    self.monitoring_stats['errors'].append({
                        'timestamp': datetime.now().isoformat(),
                        'game_id': game_id,
                        'error': str(e)
                    })
            
            # Atualiza estatísticas
            self.monitoring_stats['total_extractions'] += 1
            self.monitoring_stats['last_extraction_time'] = datetime.now().isoformat()
            
            # Gera dashboard se configurado
            if self.config.auto_dashboard and self.analyzer.alerts:
                self._generate_dashboard()
            
            # Aguarda próximo ciclo
            cycle_time = time.time() - cycle_start
            sleep_time = max(0, self.config.extraction_interval_seconds - cycle_time)
            
            if sleep_time > 0 and self.running:
                print(f"⏳ Aguardando {sleep_time:.1f}s para próximo ciclo...")
                time.sleep(sleep_time)
    
    def _process_game(self, game_id: str):
        """Processa um jogo específico.
        
        Args:
            game_id: ID do jogo para processar
        """
        # Inicializa extrator se necessário
        if not self.extractor:
            self.extractor = UnifiedExtractor()
        
        # Executa extração
        print(f"📊 Extraindo dados do jogo {game_id}...")
        extraction_data = self.extractor.extract_all_data(game_id)
        
        if not extraction_data:
            print(f"❌ Falha na extração do jogo {game_id}")
            return
        
        # Salva dados da extração
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        extraction_file = os.path.join(
            self.config.output_directory,
            f"extraction_{game_id}_{timestamp}.json"
        )
        
        with open(extraction_file, 'w', encoding='utf-8') as f:
            json.dump(extraction_data, f, indent=2, ensure_ascii=False)
        
        # Carrega dados no analisador
        self.analyzer.load_extraction_data(extraction_file)
        
        # Detecta drops se há dados anteriores
        if game_id in self.last_extraction_data:
            new_drops = self._detect_immediate_drops(game_id, extraction_data)
            
            if new_drops:
                self.monitoring_stats['total_drops_detected'] += len(new_drops)
                self._send_alerts(new_drops)
        
        # Atualiza dados da última extração
        self.last_extraction_data[game_id] = extraction_data
        
        # Limpa arquivos antigos
        self._cleanup_old_files()
        
        print(f"✅ Jogo {game_id} processado - {extraction_data['summary']['total_records']} registros")
    
    def _detect_immediate_drops(self, game_id: str, current_data: Dict) -> List[DropAlert]:
        """Detecta drops comparando com a extração anterior.
        
        Args:
            game_id: ID do jogo
            current_data: Dados da extração atual
            
        Returns:
            List[DropAlert]: Novos drops detectados
        """
        previous_data = self.last_extraction_data.get(game_id)
        if not previous_data:
            return []
        
        # Simula análise de drops entre duas extrações
        temp_analyzer = DropAnalyzer(self.config.alert_thresholds)
        
        # Cria dados temporários para análise
        temp_game_data = [previous_data, current_data]
        
        # Analisa cada tipo de aposta
        new_drops = []
        for bet_type in ['1x2', 'total', 'handicap', 'total_ht', '1x2_ht']:
            bet_drops = temp_analyzer._analyze_bet_type_drops(game_id, bet_type, temp_game_data)
            new_drops.extend(bet_drops)
        
        return new_drops
    
    def _send_alerts(self, drops: List[DropAlert]):
        """Envia alertas para drops detectados.
        
        Args:
            drops: Lista de drops detectados
        """
        critical_drops = [d for d in drops if d.severity in ['critical', 'high']]
        
        if critical_drops:
            print(f"\n🚨 ALERTA: {len(critical_drops)} drops críticos detectados!")
            
            for drop in critical_drops[:5]:  # Mostra até 5 alertas
                print(f"   🔥 {drop.bet_type.upper()} {drop.market_type}: "
                      f"{drop.old_value:.3f} → {drop.new_value:.3f} "
                      f"({drop.percentage_change:.1f}% - {drop.severity})")
        
        if len(drops) > len(critical_drops):
            other_drops = len(drops) - len(critical_drops)
            print(f"   ℹ️ +{other_drops} outros drops detectados")
        
        # Salva alertas
        self._save_alerts(drops)
    
    def _save_alerts(self, drops: List[DropAlert]):
        """Salva alertas em arquivo.
        
        Args:
            drops: Lista de drops para salvar
        """
        if not drops:
            return
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        alerts_file = os.path.join(
            self.config.output_directory,
            f"alerts_{timestamp}.json"
        )
        
        alerts_data = {
            'timestamp': datetime.now().isoformat(),
            'total_alerts': len(drops),
            'alerts': [asdict(drop) for drop in drops]
        }
        
        with open(alerts_file, 'w', encoding='utf-8') as f:
            json.dump(alerts_data, f, indent=2, ensure_ascii=False)
    
    def _generate_dashboard(self):
        """Gera dashboard atualizado."""
        try:
            dashboard = DropDashboard(self.analyzer)
            dashboard_file = os.path.join(self.config.output_directory, "live_dashboard.html")
            dashboard.generate_html_dashboard(dashboard_file)
        except Exception as e:
            print(f"⚠️ Erro ao gerar dashboard: {str(e)}")
    
    def _cleanup_old_files(self):
        """Remove arquivos antigos para economizar espaço."""
        try:
            # Lista arquivos de extração
            extraction_files = [
                f for f in os.listdir(self.config.output_directory)
                if f.startswith('extraction_') and f.endswith('.json')
            ]
            
            # Remove arquivos mais antigos se exceder o limite
            if len(extraction_files) > self.config.max_history_files:
                extraction_files.sort()
                files_to_remove = extraction_files[:-self.config.max_history_files]
                
                for file_to_remove in files_to_remove:
                    file_path = os.path.join(self.config.output_directory, file_to_remove)
                    os.remove(file_path)
                    
        except Exception as e:
            print(f"⚠️ Erro na limpeza de arquivos: {str(e)}")
    
    def _save_monitoring_stats(self):
        """Salva estatísticas do monitoramento."""
        stats_file = os.path.join(self.config.output_directory, "monitoring_stats.json")
        
        # Calcula tempo total de monitoramento
        if self.monitoring_stats['start_time']:
            start_time = datetime.fromisoformat(self.monitoring_stats['start_time'])
            total_time = datetime.now() - start_time
            self.monitoring_stats['total_monitoring_time_seconds'] = total_time.total_seconds()
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.monitoring_stats, f, indent=2, ensure_ascii=False)
    
    def get_status(self) -> Dict:
        """Retorna status atual do monitor."""
        return {
            'running': self.running,
            'games_monitored': len(self.config.game_ids),
            'total_extractions': self.monitoring_stats['total_extractions'],
            'total_drops_detected': self.monitoring_stats['total_drops_detected'],
            'last_extraction': self.monitoring_stats['last_extraction_time'],
            'errors_count': len(self.monitoring_stats['errors'])
        }

# Função para configuração rápida
def create_monitor_config(game_ids: List[str], interval_minutes: int = 5) -> MonitorConfig:
    """Cria configuração padrão para o monitor.
    
    Args:
        game_ids: Lista de IDs de jogos para monitorar
        interval_minutes: Intervalo entre extrações em minutos
        
    Returns:
        MonitorConfig: Configuração do monitor
    """
    return MonitorConfig(
        game_ids=game_ids,
        extraction_interval_seconds=interval_minutes * 60,
        alert_thresholds=None,  # Usa padrão
        auto_dashboard=True,
        max_history_files=50,
        output_directory="monitoring_data"
    )

# Função principal para teste
def main():
    """Função principal para teste do monitor."""
    print("🎯 Iniciando Monitor de Drops em Tempo Real")
    
    # Configuração de exemplo
    config = create_monitor_config(
        game_ids=["10519888"],  # Jogo de exemplo
        interval_minutes=2  # Extração a cada 2 minutos para teste
    )
    
    # Cria e inicia monitor
    monitor = RealTimeMonitor(config)
    
    try:
        monitor.start_monitoring()
    except KeyboardInterrupt:
        print("\n⏹️ Parando monitor...")
        monitor.stop_monitoring()

if __name__ == "__main__":
    main()