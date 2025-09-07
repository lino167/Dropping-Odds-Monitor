#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Monitoramento de Drops em Tempo Real
Baseado na estrutura real dos dados extraídos
"""

import json
import time
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import threading
from queue import Queue

@dataclass
class DropAlert:
    """Classe para representar um alerta de drop"""
    game_id: str
    table_type: str
    timestamp: str
    drop_type: str  # 'home' ou 'away'
    magnitude: float
    home_odds: float
    away_odds: float
    draw_odds: Optional[float]
    home_change: float
    away_change: float
    score: str
    time_in_game: str
    alert_time: str

class RealTimeDropMonitor:
    """Monitor de drops em tempo real"""
    
    def __init__(self, threshold: float = 5.0, alert_threshold: float = 10.0):
        self.threshold = threshold
        self.alert_threshold = alert_threshold
        self.is_monitoring = False
        self.alert_queue = Queue()
        self.last_data_hash = None
        self.processed_drops = set()  # Para evitar alertas duplicados
        
        # Configurações de monitoramento
        self.check_interval = 30  # segundos
        self.data_file = "complete_live_data_20250907_172408.json"  # Arquivo de dados
        
        # Estatísticas
        self.stats = {
            'monitoring_started': None,
            'total_checks': 0,
            'total_drops_detected': 0,
            'total_alerts_sent': 0,
            'games_monitored': 0
        }
    
    def extract_percentage_value(self, pct_str: str) -> float:
        """Extrai valor numérico de string de percentual"""
        if not pct_str or pct_str == '-' or pct_str.strip() == '':
            return 0.0
        
        try:
            clean_str = str(pct_str).replace('%', '').replace('+', '').replace('\n', '').strip()
            return float(clean_str)
        except (ValueError, AttributeError):
            return 0.0
    
    def detect_drops_in_game(self, game_data: Dict) -> List[DropAlert]:
        """Detecta drops em um jogo específico e retorna alertas"""
        alerts = []
        
        if 'tables' not in game_data:
            return alerts
        
        game_id = game_data.get('game_id', 'unknown')
        tables = game_data['tables']
        
        for table_name, table_info in tables.items():
            if 'table_data' not in table_info:
                continue
                
            table_data = table_info['table_data']
            if not isinstance(table_data, list):
                continue
            
            # Analisa apenas os dados mais recentes (últimos 10 registros)
            recent_data = table_data[-10:] if len(table_data) > 10 else table_data
            
            for entry in recent_data:
                if not isinstance(entry, dict):
                    continue
                
                # Extrai mudanças percentuais
                home_change_str = entry.get('Home\n (%)', '0')
                away_change_str = entry.get('Away\n (%)', '0')
                
                home_change = self.extract_percentage_value(home_change_str)
                away_change = self.extract_percentage_value(away_change_str)
                
                # Verifica se há drop significativo
                if abs(home_change) >= self.threshold or abs(away_change) >= self.threshold:
                    # Cria ID único para evitar duplicatas
                    drop_id = f"{game_id}_{table_name}_{entry.get('Date', '')}_{home_change}_{away_change}"
                    
                    if drop_id not in self.processed_drops:
                        self.processed_drops.add(drop_id)
                        
                        alert = DropAlert(
                            game_id=game_id,
                            table_type=table_name,
                            timestamp=entry.get('Date', ''),
                            drop_type='home' if abs(home_change) > abs(away_change) else 'away',
                            magnitude=max(abs(home_change), abs(away_change)),
                            home_odds=entry.get('Home', 0),
                            away_odds=entry.get('Away', 0),
                            draw_odds=entry.get('Draw'),
                            home_change=home_change,
                            away_change=away_change,
                            score=entry.get('Score', ''),
                            time_in_game=entry.get('Time', ''),
                            alert_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        )
                        
                        alerts.append(alert)
                        self.stats['total_drops_detected'] += 1
        
        return alerts
    
    def load_current_data(self) -> Optional[Dict]:
        """Carrega dados atuais do arquivo"""
        try:
            if not os.path.exists(self.data_file):
                print(f"⚠️ Arquivo {self.data_file} não encontrado")
                return None
            
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Erro ao carregar dados: {e}")
            return None
    
    def check_for_drops(self) -> List[DropAlert]:
        """Verifica por novos drops"""
        data = self.load_current_data()
        if not data or 'games_data' not in data:
            return []
        
        self.stats['total_checks'] += 1
        games_data = data['games_data']
        self.stats['games_monitored'] = len(games_data)
        
        all_alerts = []
        
        for game_id, game_info in games_data.items():
            alerts = self.detect_drops_in_game(game_info)
            all_alerts.extend(alerts)
        
        return all_alerts
    
    def process_alerts(self, alerts: List[DropAlert]) -> None:
        """Processa alertas encontrados"""
        if not alerts:
            return
        
        # Filtra apenas alertas de alta prioridade
        high_priority_alerts = [alert for alert in alerts if alert.magnitude >= self.alert_threshold]
        
        for alert in high_priority_alerts:
            self.alert_queue.put(alert)
            self.stats['total_alerts_sent'] += 1
            
            # Log do alerta
            print(f"🚨 ALERTA: {alert.game_id} ({alert.table_type}) - {alert.drop_type} {alert.magnitude:.1f}% - {alert.timestamp}")
    
    def monitoring_loop(self) -> None:
        """Loop principal de monitoramento"""
        print(f"🔄 Iniciando monitoramento (threshold: {self.threshold}%, alertas: {self.alert_threshold}%)")
        print(f"📁 Monitorando arquivo: {self.data_file}")
        print(f"⏱️ Intervalo de verificação: {self.check_interval}s")
        
        self.stats['monitoring_started'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        while self.is_monitoring:
            try:
                # Verifica por drops
                alerts = self.check_for_drops()
                
                if alerts:
                    print(f"\n📊 {len(alerts)} drops detectados")
                    self.process_alerts(alerts)
                
                # Mostra estatísticas periodicamente
                if self.stats['total_checks'] % 10 == 0:
                    self.print_stats()
                
                # Aguarda próxima verificação
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                print("\n⏹️ Monitoramento interrompido pelo usuário")
                break
            except Exception as e:
                print(f"❌ Erro no monitoramento: {e}")
                time.sleep(5)  # Aguarda antes de tentar novamente
    
    def print_stats(self) -> None:
        """Imprime estatísticas do monitoramento"""
        print(f"\n📈 ESTATÍSTICAS DO MONITORAMENTO")
        print(f"   Iniciado em: {self.stats['monitoring_started']}")
        print(f"   Verificações: {self.stats['total_checks']}")
        print(f"   Jogos monitorados: {self.stats['games_monitored']}")
        print(f"   Drops detectados: {self.stats['total_drops_detected']}")
        print(f"   Alertas enviados: {self.stats['total_alerts_sent']}")
        print(f"   Drops únicos processados: {len(self.processed_drops)}")
    
    def start_monitoring(self) -> None:
        """Inicia o monitoramento"""
        if self.is_monitoring:
            print("⚠️ Monitoramento já está ativo")
            return
        
        self.is_monitoring = True
        
        # Inicia thread de monitoramento
        monitor_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        monitor_thread.start()
        
        print("✅ Monitoramento iniciado")
        return monitor_thread
    
    def stop_monitoring(self) -> None:
        """Para o monitoramento"""
        self.is_monitoring = False
        print("⏹️ Parando monitoramento...")
    
    def get_pending_alerts(self) -> List[DropAlert]:
        """Retorna alertas pendentes"""
        alerts = []
        while not self.alert_queue.empty():
            alerts.append(self.alert_queue.get())
        return alerts
    
    def save_session_report(self) -> str:
        """Salva relatório da sessão de monitoramento"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"monitoring_report_{timestamp}.json"
        
        report = {
            'session_info': {
                'started': self.stats['monitoring_started'],
                'ended': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'threshold': self.threshold,
                'alert_threshold': self.alert_threshold,
                'check_interval': self.check_interval
            },
            'statistics': self.stats,
            'processed_drops_count': len(self.processed_drops)
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return filename

def main():
    """Função principal - demonstração do monitor"""
    print("🚀 SISTEMA DE MONITORAMENTO DE DROPS EM TEMPO REAL")
    print("=" * 60)
    
    # Cria monitor com configurações
    monitor = RealTimeDropMonitor(
        threshold=5.0,      # Detecta drops >= 5%
        alert_threshold=10.0 # Alerta para drops >= 10%
    )
    
    try:
        # Faz uma verificação inicial para demonstrar
        print("🔍 Fazendo verificação inicial...")
        initial_alerts = monitor.check_for_drops()
        
        if initial_alerts:
            print(f"\n📊 {len(initial_alerts)} drops detectados na verificação inicial:")
            
            # Mostra os 10 maiores drops
            sorted_alerts = sorted(initial_alerts, key=lambda x: x.magnitude, reverse=True)
            for i, alert in enumerate(sorted_alerts[:10], 1):
                print(f"  {i:2d}. {alert.game_id} ({alert.table_type}) - {alert.drop_type} {alert.magnitude:.1f}% - {alert.timestamp}")
            
            # Processa alertas de alta prioridade
            monitor.process_alerts(initial_alerts)
            
            high_priority = [a for a in initial_alerts if a.magnitude >= monitor.alert_threshold]
            if high_priority:
                print(f"\n🚨 {len(high_priority)} alertas de alta prioridade (>= {monitor.alert_threshold}%)")
        else:
            print("❌ Nenhum drop detectado na verificação inicial")
        
        # Mostra estatísticas
        monitor.print_stats()
        
        print(f"\n💡 Para monitoramento contínuo, descomente as linhas do monitoramento em tempo real")
        print(f"📝 O sistema está configurado para detectar drops >= {monitor.threshold}% e alertar >= {monitor.alert_threshold}%")
        
        # Salva relatório
        report_file = monitor.save_session_report()
        print(f"\n💾 Relatório salvo em: {report_file}")
        
        # Monitoramento contínuo (descomentado para demonstração)
        # print("\n🔄 Iniciando monitoramento contínuo...")
        # print("   Pressione Ctrl+C para parar")
        # monitor_thread = monitor.start_monitoring()
        # monitor_thread.join()
        
    except KeyboardInterrupt:
        print("\n⏹️ Programa interrompido")
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if monitor.is_monitoring:
            monitor.stop_monitoring()

if __name__ == "__main__":
    main()