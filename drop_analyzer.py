#!/usr/bin/env python3
"""
Analisador de Drops de Odds

Este módulo implementa funcionalidades para análise de drops (quedas) nas odds
dos diferentes tipos de apostas extraídos pelo sistema unificado.

Funcionalidades:
- Detecção de drops significativos em odds
- Análise de padrões temporais
- Cálculo de percentuais de mudança
- Identificação de tendências
- Sistema de alertas configurável
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import statistics
from dataclasses import dataclass

@dataclass
class DropAlert:
    """Classe para representar um alerta de drop."""
    bet_type: str
    game_id: str
    timestamp: str
    old_value: float
    new_value: float
    percentage_change: float
    severity: str  # 'low', 'medium', 'high', 'critical'
    market_type: str  # 'home', 'draw', 'away', 'over', 'under', etc.

class DropAnalyzer:
    """Analisador principal de drops de odds."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Inicializa o analisador de drops.
        
        Args:
            config: Configurações personalizadas para detecção de drops
        """
        self.config = config or self._get_default_config()
        self.historical_data = {}
        self.alerts = []
        
    def _get_default_config(self) -> Dict:
        """Retorna configuração padrão para detecção de drops."""
        return {
            'thresholds': {
                '1x2': {
                    'low': 5.0,      # 5% de mudança
                    'medium': 10.0,   # 10% de mudança
                    'high': 20.0,     # 20% de mudança
                    'critical': 30.0  # 30% de mudança
                },
                'total': {
                    'low': 3.0,
                    'medium': 7.0,
                    'high': 15.0,
                    'critical': 25.0
                },
                'handicap': {
                    'low': 4.0,
                    'medium': 8.0,
                    'high': 18.0,
                    'critical': 28.0
                },
                'total_ht': {
                    'low': 4.0,
                    'medium': 9.0,
                    'high': 18.0,
                    'critical': 27.0
                },
                '1x2_ht': {
                    'low': 6.0,
                    'medium': 12.0,
                    'high': 22.0,
                    'critical': 32.0
                }
            },
            'min_odds_value': 1.01,  # Odds mínimas para considerar
            'max_odds_value': 50.0,  # Odds máximas para considerar
            'time_window_minutes': 30,  # Janela de tempo para análise
            'min_data_points': 3  # Mínimo de pontos de dados para análise
        }
    
    def load_extraction_data(self, file_path: str) -> bool:
        """Carrega dados de extração de um arquivo JSON.
        
        Args:
            file_path: Caminho para o arquivo JSON de extração
            
        Returns:
            bool: True se carregado com sucesso, False caso contrário
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            game_id = data.get('game_id')
            if not game_id:
                print(f"❌ Game ID não encontrado no arquivo: {file_path}")
                return False
                
            # Armazena dados históricos
            if game_id not in self.historical_data:
                self.historical_data[game_id] = []
                
            self.historical_data[game_id].append(data)
            print(f"✅ Dados carregados para jogo {game_id}: {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao carregar arquivo {file_path}: {str(e)}")
            return False
    
    def analyze_drops_for_game(self, game_id: str) -> List[DropAlert]:
        """Analisa drops para um jogo específico.
        
        Args:
            game_id: ID do jogo para análise
            
        Returns:
            List[DropAlert]: Lista de alertas de drops detectados
        """
        if game_id not in self.historical_data:
            print(f"❌ Dados históricos não encontrados para jogo {game_id}")
            return []
            
        game_data = self.historical_data[game_id]
        if len(game_data) < self.config['min_data_points']:
            print(f"⚠️ Dados insuficientes para análise do jogo {game_id}")
            return []
            
        alerts = []
        
        # Analisa cada tipo de aposta
        for bet_type in ['1x2', 'total', 'handicap', 'total_ht', '1x2_ht']:
            bet_alerts = self._analyze_bet_type_drops(game_id, bet_type, game_data)
            alerts.extend(bet_alerts)
            
        return alerts
    
    def _analyze_bet_type_drops(self, game_id: str, bet_type: str, game_data: List[Dict]) -> List[DropAlert]:
        """Analisa drops para um tipo específico de aposta.
        
        Args:
            game_id: ID do jogo
            bet_type: Tipo de aposta (1x2, total, etc.)
            game_data: Dados históricos do jogo
            
        Returns:
            List[DropAlert]: Alertas detectados para este tipo de aposta
        """
        alerts = []
        
        # Extrai dados do tipo de aposta
        bet_data_series = []
        for extraction in game_data:
            bet_data = extraction.get('bet_types', {}).get(bet_type)
            if bet_data and bet_data.get('data'):
                bet_data_series.append({
                    'timestamp': extraction.get('extraction_time'),
                    'data': bet_data['data']
                })
        
        if len(bet_data_series) < 2:
            return alerts
            
        # Compara extrações consecutivas
        for i in range(1, len(bet_data_series)):
            prev_data = bet_data_series[i-1]['data']
            curr_data = bet_data_series[i]['data']
            timestamp = bet_data_series[i]['timestamp']
            
            # Analisa drops baseado no tipo de aposta
            if bet_type in ['1x2', '1x2_ht']:
                alerts.extend(self._analyze_1x2_drops(game_id, bet_type, prev_data, curr_data, timestamp))
            elif bet_type in ['total', 'total_ht']:
                alerts.extend(self._analyze_total_drops(game_id, bet_type, prev_data, curr_data, timestamp))
            elif bet_type == 'handicap':
                alerts.extend(self._analyze_handicap_drops(game_id, bet_type, prev_data, curr_data, timestamp))
                
        return alerts
    
    def _analyze_1x2_drops(self, game_id: str, bet_type: str, prev_data: List[Dict], 
                          curr_data: List[Dict], timestamp: str) -> List[DropAlert]:
        """Analisa drops em apostas 1x2."""
        alerts = []
        
        # Cria mapeamento por timestamp para comparação
        prev_map = {item['date_time']: item for item in prev_data}
        
        for curr_item in curr_data:
            date_time = curr_item['date_time']
            if date_time in prev_map:
                prev_item = prev_map[date_time]
                
                # Analisa cada mercado (home, draw, away)
                markets = [
                    ('home', 'home_odds'),
                    ('draw', 'draw_odds'),
                    ('away', 'away_odds')
                ]
                
                for market_name, odds_field in markets:
                    alert = self._check_odds_drop(
                        game_id, bet_type, market_name, timestamp,
                        prev_item.get(odds_field), curr_item.get(odds_field)
                    )
                    if alert:
                        alerts.append(alert)
                        
        return alerts
    
    def _analyze_total_drops(self, game_id: str, bet_type: str, prev_data: List[Dict], 
                           curr_data: List[Dict], timestamp: str) -> List[DropAlert]:
        """Analisa drops em apostas de totais."""
        alerts = []
        
        prev_map = {f"{item['date_time']}_{item.get('handicap', '')}": item for item in prev_data}
        
        for curr_item in curr_data:
            key = f"{curr_item['date_time']}_{curr_item.get('handicap', '')}"
            if key in prev_map:
                prev_item = prev_map[key]
                
                # Analisa over e under
                markets = [
                    ('over', 'over_odds'),
                    ('under', 'under_odds')
                ]
                
                for market_name, odds_field in markets:
                    alert = self._check_odds_drop(
                        game_id, bet_type, market_name, timestamp,
                        prev_item.get(odds_field), curr_item.get(odds_field)
                    )
                    if alert:
                        alerts.append(alert)
                        
        return alerts
    
    def _analyze_handicap_drops(self, game_id: str, bet_type: str, prev_data: List[Dict], 
                              curr_data: List[Dict], timestamp: str) -> List[DropAlert]:
        """Analisa drops em apostas de handicap."""
        alerts = []
        
        prev_map = {f"{item['date_time']}_{item.get('handicap', '')}": item for item in prev_data}
        
        for curr_item in curr_data:
            key = f"{curr_item['date_time']}_{curr_item.get('handicap', '')}"
            if key in prev_map:
                prev_item = prev_map[key]
                
                # Analisa home e away
                markets = [
                    ('home', 'home_odds'),
                    ('away', 'away_odds')
                ]
                
                for market_name, odds_field in markets:
                    alert = self._check_odds_drop(
                        game_id, bet_type, market_name, timestamp,
                        prev_item.get(odds_field), curr_item.get(odds_field)
                    )
                    if alert:
                        alerts.append(alert)
                        
        return alerts
    
    def _check_odds_drop(self, game_id: str, bet_type: str, market_type: str, 
                        timestamp: str, old_odds: str, new_odds: str) -> Optional[DropAlert]:
        """Verifica se houve um drop significativo nas odds.
        
        Args:
            game_id: ID do jogo
            bet_type: Tipo de aposta
            market_type: Tipo de mercado (home, away, over, under, etc.)
            timestamp: Timestamp da detecção
            old_odds: Odds antigas (string)
            new_odds: Odds novas (string)
            
        Returns:
            DropAlert ou None se não houver drop significativo
        """
        try:
            # Converte odds para float
            old_val = float(old_odds) if old_odds and old_odds not in ['', '-'] else None
            new_val = float(new_odds) if new_odds and new_odds not in ['', '-'] else None
            
            if not old_val or not new_val:
                return None
                
            # Verifica se as odds estão dentro dos limites configurados
            if (old_val < self.config['min_odds_value'] or old_val > self.config['max_odds_value'] or
                new_val < self.config['min_odds_value'] or new_val > self.config['max_odds_value']):
                return None
                
            # Calcula percentual de mudança (drop = diminuição das odds)
            if old_val > new_val:  # Drop detectado
                percentage_change = ((old_val - new_val) / old_val) * 100
                
                # Determina severidade baseada nos thresholds
                thresholds = self.config['thresholds'].get(bet_type, self.config['thresholds']['1x2'])
                
                if percentage_change >= thresholds['critical']:
                    severity = 'critical'
                elif percentage_change >= thresholds['high']:
                    severity = 'high'
                elif percentage_change >= thresholds['medium']:
                    severity = 'medium'
                elif percentage_change >= thresholds['low']:
                    severity = 'low'
                else:
                    return None  # Mudança não significativa
                    
                return DropAlert(
                    bet_type=bet_type,
                    game_id=game_id,
                    timestamp=timestamp,
                    old_value=old_val,
                    new_value=new_val,
                    percentage_change=percentage_change,
                    severity=severity,
                    market_type=market_type
                )
                
        except (ValueError, TypeError):
            return None
            
        return None
    
    def get_drop_statistics(self, game_id: Optional[str] = None) -> Dict:
        """Retorna estatísticas dos drops detectados.
        
        Args:
            game_id: ID específico do jogo (opcional)
            
        Returns:
            Dict: Estatísticas dos drops
        """
        filtered_alerts = self.alerts
        if game_id:
            filtered_alerts = [alert for alert in self.alerts if alert.game_id == game_id]
            
        if not filtered_alerts:
            return {'total_drops': 0}
            
        stats = {
            'total_drops': len(filtered_alerts),
            'by_severity': {},
            'by_bet_type': {},
            'by_market_type': {},
            'average_drop_percentage': 0,
            'max_drop_percentage': 0,
            'min_drop_percentage': 0
        }
        
        # Calcula estatísticas
        percentages = [alert.percentage_change for alert in filtered_alerts]
        stats['average_drop_percentage'] = statistics.mean(percentages)
        stats['max_drop_percentage'] = max(percentages)
        stats['min_drop_percentage'] = min(percentages)
        
        # Agrupa por severidade
        for alert in filtered_alerts:
            stats['by_severity'][alert.severity] = stats['by_severity'].get(alert.severity, 0) + 1
            stats['by_bet_type'][alert.bet_type] = stats['by_bet_type'].get(alert.bet_type, 0) + 1
            stats['by_market_type'][alert.market_type] = stats['by_market_type'].get(alert.market_type, 0) + 1
            
        return stats
    
    def analyze_all_games(self) -> Dict:
        """Analisa todos os jogos carregados e retorna resultados.
        
        Returns:
            Dict: Resultados da análise por jogo
        """
        results = {}
        
        for game_id in self.historical_data.keys():
            game_alerts = [alert for alert in self.alerts if alert.game_id == game_id]
            
            results[game_id] = {
                'alerts': [
                    {
                        'bet_type': alert.bet_type,
                        'game_id': alert.game_id,
                        'timestamp': alert.timestamp,
                        'old_value': alert.old_value,
                        'new_value': alert.new_value,
                        'percentage_change': round(alert.percentage_change, 2),
                        'severity': alert.severity,
                        'market_type': alert.market_type
                    }
                    for alert in game_alerts
                ],
                'total_alerts': len(game_alerts),
                'severity_breakdown': self._get_severity_breakdown(game_alerts)
            }
        
        return results
    
    def _get_severity_breakdown(self, alerts: List[DropAlert]) -> Dict[str, int]:
        """Calcula breakdown de severidade para uma lista de alertas.
        
        Args:
            alerts: Lista de alertas
            
        Returns:
            Dict[str, int]: Contagem por severidade
        """
        breakdown = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        
        for alert in alerts:
            if alert.severity in breakdown:
                breakdown[alert.severity] += 1
        
        return breakdown
    
    def save_analysis_report(self, output_file: str) -> bool:
        """Salva relatório de análise em arquivo JSON.
        
        Args:
            output_file: Caminho do arquivo de saída
            
        Returns:
            bool: True se salvo com sucesso
        """
        try:
            report = {
                'analysis_timestamp': datetime.now().isoformat(),
                'config': self.config,
                'total_games_analyzed': len(self.historical_data),
                'total_alerts': len(self.alerts),
                'statistics': self.get_drop_statistics(),
                'alerts': [
                    {
                        'bet_type': alert.bet_type,
                        'game_id': alert.game_id,
                        'timestamp': alert.timestamp,
                        'old_value': alert.old_value,
                        'new_value': alert.new_value,
                        'percentage_change': round(alert.percentage_change, 2),
                        'severity': alert.severity,
                        'market_type': alert.market_type
                    }
                    for alert in self.alerts
                ]
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
                
            print(f"✅ Relatório de análise salvo: {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao salvar relatório: {str(e)}")
            return False
    
    def analyze_directory(self, directory_path: str) -> int:
        """Analisa todos os arquivos de extração em um diretório.
        
        Args:
            directory_path: Caminho do diretório com arquivos JSON
            
        Returns:
            int: Número de alertas detectados
        """
        if not os.path.exists(directory_path):
            print(f"❌ Diretório não encontrado: {directory_path}")
            return 0
            
        json_files = [f for f in os.listdir(directory_path) if f.endswith('.json') and 'unified_extraction' in f]
        
        if not json_files:
            print(f"❌ Nenhum arquivo de extração encontrado em: {directory_path}")
            return 0
            
        print(f"🔍 Analisando {len(json_files)} arquivos de extração...")
        
        # Carrega todos os arquivos
        for json_file in sorted(json_files):
            file_path = os.path.join(directory_path, json_file)
            self.load_extraction_data(file_path)
            
        # Analisa drops para cada jogo
        total_alerts = 0
        for game_id in self.historical_data.keys():
            game_alerts = self.analyze_drops_for_game(game_id)
            self.alerts.extend(game_alerts)
            total_alerts += len(game_alerts)
            
            if game_alerts:
                print(f"🚨 {len(game_alerts)} drops detectados para jogo {game_id}")
                
        return total_alerts

# Função principal para teste
def main():
    """Função principal para teste do analisador."""
    print("🎯 Iniciando análise de drops de odds...")
    
    # Inicializa analisador
    analyzer = DropAnalyzer()
    
    # Analisa diretório atual
    current_dir = os.getcwd()
    total_alerts = analyzer.analyze_directory(current_dir)
    
    if total_alerts > 0:
        print(f"\n📊 Análise concluída: {total_alerts} drops detectados")
        
        # Mostra estatísticas
        stats = analyzer.get_drop_statistics()
        print(f"\n📈 Estatísticas dos drops:")
        print(f"   📋 Total: {stats['total_drops']}")
        print(f"   📊 Drop médio: {stats.get('average_drop_percentage', 0):.2f}%")
        print(f"   🔥 Maior drop: {stats.get('max_drop_percentage', 0):.2f}%")
        
        if stats.get('by_severity'):
            print(f"\n🚨 Por severidade:")
            for severity, count in stats['by_severity'].items():
                print(f"   {severity}: {count}")
                
        # Salva relatório
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"drop_analysis_report_{timestamp}.json"
        analyzer.save_analysis_report(report_file)
        
        # Mostra alguns alertas de exemplo
        print(f"\n🔍 Exemplos de drops detectados:")
        for i, alert in enumerate(analyzer.alerts[:5]):
            print(f"   {i+1}. {alert.bet_type.upper()} - {alert.market_type}: {alert.old_value:.3f} → {alert.new_value:.3f} ({alert.percentage_change:.1f}% - {alert.severity})")
            
    else:
        print("ℹ️ Nenhum drop significativo detectado")

if __name__ == "__main__":
    main()