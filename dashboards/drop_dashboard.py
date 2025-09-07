#!/usr/bin/env python3
"""
Dashboard de Visualização de Drops de Odds

Este módulo cria um dashboard HTML interativo para visualizar
os drops detectados pelo analisador de odds.

Funcionalidades:
- Dashboard HTML responsivo
- Gráficos de estatísticas
- Tabelas de drops por severidade
- Filtros por tipo de aposta
- Exportação de relatórios
"""

import json
import os
from datetime import datetime
from typing import Dict, List
from drop_analyzer import DropAnalyzer

class DropDashboard:
    """Gerador de dashboard para visualização de drops."""
    
    def __init__(self, analyzer: DropAnalyzer):
        """Inicializa o dashboard.
        
        Args:
            analyzer: Instância do DropAnalyzer com dados carregados
        """
        self.analyzer = analyzer
        self.stats = analyzer.get_drop_statistics()
        
    def generate_html_dashboard(self, output_file: str = "drop_dashboard.html") -> bool:
        """Gera dashboard HTML completo.
        
        Args:
            output_file: Nome do arquivo HTML de saída
            
        Returns:
            bool: True se gerado com sucesso
        """
        try:
            html_content = self._build_html_content()
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            print(f"✅ Dashboard HTML gerado: {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao gerar dashboard: {str(e)}")
            return False
    
    def _build_html_content(self) -> str:
        """Constrói o conteúdo HTML completo do dashboard."""
        return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard de Drops de Odds</title>
    <style>
        {self._get_css_styles()}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Dashboard de Drops de Odds</h1>
            <p class="subtitle">Análise de mudanças significativas nas odds de apostas</p>
            <div class="timestamp">Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}</div>
        </header>
        
        <div class="stats-grid">
            {self._build_stats_cards()}
        </div>
        
        <div class="charts-section">
            <div class="chart-container">
                <h3>📈 Drops por Severidade</h3>
                <canvas id="severityChart"></canvas>
            </div>
            <div class="chart-container">
                <h3>🎯 Drops por Tipo de Aposta</h3>
                <canvas id="betTypeChart"></canvas>
            </div>
        </div>
        
        <div class="tables-section">
            {self._build_drops_tables()}
        </div>
        
        <div class="alerts-section">
            <h3>🚨 Alertas Críticos e de Alta Severidade</h3>
            {self._build_critical_alerts_table()}
        </div>
    </div>
    
    <script>
        {self._get_javascript_code()}
    </script>
</body>
</html>
        """
    
    def _get_css_styles(self) -> str:
        """Retorna estilos CSS para o dashboard."""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        header {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
            margin-bottom: 15px;
        }
        
        .timestamp {
            font-size: 0.9em;
            opacity: 0.8;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }
        
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            text-align: center;
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-card .icon {
            font-size: 2.5em;
            margin-bottom: 15px;
        }
        
        .stat-card .value {
            font-size: 2.2em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }
        
        .stat-card .label {
            color: #7f8c8d;
            font-size: 1.1em;
        }
        
        .charts-section {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            padding: 30px;
        }
        
        .chart-container {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        }
        
        .chart-container h3 {
            margin-bottom: 20px;
            color: #2c3e50;
            text-align: center;
        }
        
        .tables-section {
            padding: 30px;
            background: #f8f9fa;
        }
        
        .table-container {
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            margin-bottom: 30px;
        }
        
        .table-header {
            background: #34495e;
            color: white;
            padding: 20px;
            font-size: 1.3em;
            font-weight: bold;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ecf0f1;
        }
        
        th {
            background: #bdc3c7;
            font-weight: bold;
            color: #2c3e50;
        }
        
        tr:hover {
            background: #f8f9fa;
        }
        
        .severity-low { color: #27ae60; font-weight: bold; }
        .severity-medium { color: #f39c12; font-weight: bold; }
        .severity-high { color: #e74c3c; font-weight: bold; }
        .severity-critical { color: #8e44ad; font-weight: bold; }
        
        .alerts-section {
            padding: 30px;
        }
        
        .alert-item {
            background: white;
            border-left: 5px solid #e74c3c;
            padding: 15px 20px;
            margin-bottom: 15px;
            border-radius: 0 10px 10px 0;
            box-shadow: 0 3px 10px rgba(0,0,0,0.1);
        }
        
        .alert-critical {
            border-left-color: #8e44ad;
            background: #fdf2ff;
        }
        
        .alert-high {
            border-left-color: #e74c3c;
            background: #fff5f5;
        }
        
        @media (max-width: 768px) {
            .charts-section {
                grid-template-columns: 1fr;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
        }
        """
    
    def _build_stats_cards(self) -> str:
        """Constrói cards de estatísticas."""
        stats = self.stats
        
        return f"""
        <div class="stat-card">
            <div class="icon">📊</div>
            <div class="value">{stats.get('total_drops', 0)}</div>
            <div class="label">Total de Drops</div>
        </div>
        
        <div class="stat-card">
            <div class="icon">📈</div>
            <div class="value">{stats.get('average_drop_percentage', 0):.1f}%</div>
            <div class="label">Drop Médio</div>
        </div>
        
        <div class="stat-card">
            <div class="icon">🔥</div>
            <div class="value">{stats.get('max_drop_percentage', 0):.1f}%</div>
            <div class="label">Maior Drop</div>
        </div>
        
        <div class="stat-card">
            <div class="icon">🎯</div>
            <div class="value">{len(stats.get('by_bet_type', {}))}</div>
            <div class="label">Tipos de Aposta</div>
        </div>
        
        <div class="stat-card">
            <div class="icon">🚨</div>
            <div class="value">{stats.get('by_severity', {}).get('critical', 0) + stats.get('by_severity', {}).get('high', 0)}</div>
            <div class="label">Alertas Críticos</div>
        </div>
        
        <div class="stat-card">
            <div class="icon">⚠️</div>
            <div class="value">{stats.get('by_severity', {}).get('medium', 0)}</div>
            <div class="label">Alertas Médios</div>
        </div>
        """
    
    def _build_drops_tables(self) -> str:
        """Constrói tabelas de drops por tipo."""
        tables_html = ""
        
        # Agrupa alertas por tipo de aposta
        alerts_by_type = {}
        for alert in self.analyzer.alerts:
            bet_type = alert.bet_type
            if bet_type not in alerts_by_type:
                alerts_by_type[bet_type] = []
            alerts_by_type[bet_type].append(alert)
        
        for bet_type, alerts in alerts_by_type.items():
            # Ordena por percentual de mudança (maior primeiro)
            alerts.sort(key=lambda x: x.percentage_change, reverse=True)
            
            tables_html += f"""
            <div class="table-container">
                <div class="table-header">
                    🎯 Drops em {bet_type.upper()} ({len(alerts)} alertas)
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>Mercado</th>
                            <th>Odds Anterior</th>
                            <th>Odds Nova</th>
                            <th>Drop %</th>
                            <th>Severidade</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            # Mostra apenas os top 10 drops para cada tipo
            for alert in alerts[:10]:
                timestamp = datetime.fromisoformat(alert.timestamp.replace('Z', '+00:00')).strftime('%H:%M:%S')
                severity_class = f"severity-{alert.severity}"
                
                tables_html += f"""
                        <tr>
                            <td>{timestamp}</td>
                            <td>{alert.market_type.title()}</td>
                            <td>{alert.old_value:.3f}</td>
                            <td>{alert.new_value:.3f}</td>
                            <td>{alert.percentage_change:.1f}%</td>
                            <td class="{severity_class}">{alert.severity.title()}</td>
                        </tr>
                """
            
            tables_html += """
                    </tbody>
                </table>
            </div>
            """
        
        return tables_html
    
    def _build_critical_alerts_table(self) -> str:
        """Constrói tabela de alertas críticos."""
        critical_alerts = [alert for alert in self.analyzer.alerts 
                          if alert.severity in ['critical', 'high']]
        
        if not critical_alerts:
            return "<p>✅ Nenhum alerta crítico detectado.</p>"
        
        # Ordena por percentual de mudança
        critical_alerts.sort(key=lambda x: x.percentage_change, reverse=True)
        
        html = """
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Tipo</th>
                        <th>Mercado</th>
                        <th>Timestamp</th>
                        <th>Drop %</th>
                        <th>Odds: Antes → Depois</th>
                        <th>Severidade</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for alert in critical_alerts[:20]:  # Top 20 alertas críticos
            timestamp = datetime.fromisoformat(alert.timestamp.replace('Z', '+00:00')).strftime('%H:%M:%S')
            severity_class = f"severity-{alert.severity}"
            
            html += f"""
                    <tr>
                        <td>{alert.bet_type.upper()}</td>
                        <td>{alert.market_type.title()}</td>
                        <td>{timestamp}</td>
                        <td>{alert.percentage_change:.1f}%</td>
                        <td>{alert.old_value:.3f} → {alert.new_value:.3f}</td>
                        <td class="{severity_class}">{alert.severity.title()}</td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
        </div>
        """
        
        return html
    
    def _get_javascript_code(self) -> str:
        """Retorna código JavaScript para os gráficos."""
        severity_data = self.stats.get('by_severity', {})
        bet_type_data = self.stats.get('by_bet_type', {})
        
        return f"""
        // Gráfico de severidade
        const severityCtx = document.getElementById('severityChart').getContext('2d');
        new Chart(severityCtx, {{
            type: 'doughnut',
            data: {{
                labels: {list(severity_data.keys())},
                datasets: [{{
                    data: {list(severity_data.values())},
                    backgroundColor: [
                        '#27ae60',  // low
                        '#f39c12',  // medium
                        '#e74c3c',  // high
                        '#8e44ad'   // critical
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        position: 'bottom'
                    }}
                }}
            }}
        }});
        
        // Gráfico de tipos de aposta
        const betTypeCtx = document.getElementById('betTypeChart').getContext('2d');
        new Chart(betTypeCtx, {{
            type: 'bar',
            data: {{
                labels: {list(bet_type_data.keys())},
                datasets: [{{
                    label: 'Número de Drops',
                    data: {list(bet_type_data.values())},
                    backgroundColor: [
                        '#3498db',
                        '#e74c3c',
                        '#f39c12',
                        '#27ae60',
                        '#9b59b6'
                    ],
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{
                        beginAtZero: true
                    }}
                }},
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }}
            }}
        }});
        """

# Função principal para gerar dashboard
def main():
    """Função principal para gerar dashboard."""
    print("🎯 Gerando dashboard de drops...")
    
    # Inicializa analisador
    analyzer = DropAnalyzer()
    
    # Analisa diretório atual
    current_dir = os.getcwd()
    total_alerts = analyzer.analyze_directory(current_dir)
    
    if total_alerts > 0:
        # Gera dashboard
        dashboard = DropDashboard(analyzer)
        dashboard.generate_html_dashboard()
        
        print(f"✅ Dashboard gerado com {total_alerts} drops detectados")
        print(f"📊 Abra o arquivo 'drop_dashboard.html' no navegador para visualizar")
    else:
        print("ℹ️ Nenhum drop detectado para gerar dashboard")

if __name__ == "__main__":
    main()