# 🎯 Sistema de Análise de Drops

Sistema completo para detecção, análise e monitoramento de drops de odds do dropping-odds.com.

## 📁 Estrutura do Projeto

```
analise_drop/
├── 📊 analyzers/          # Módulos de análise de drops
│   ├── drop_analyzer.py           # Analisador principal de drops
│   ├── final_drop_detector.py     # Detector final de drops
│   ├── fix_drops_detection.py     # Correções de detecção
│   └── analyze_*.py               # Analisadores específicos
│
├── 🎨 dashboards/         # Sistemas de dashboard e visualização
│   ├── ultimate_dashboard.py      # Dashboard principal (Recomendado)
│   ├── enhanced_dashboard.py      # Dashboard aprimorado
│   ├── drop_dashboard.py          # Dashboard específico de drops
│   ├── create_visual_dashboard.py # Dashboard visual
│   └── fixed_dashboard_system.py  # Sistema de dashboard corrigido
│
├── 🔄 extractors/         # Módulos de extração de dados
│   ├── complete_extractor.py      # Extrator completo
│   ├── complete_live_extractor.py # Extrator ao vivo
│   ├── unified_extractor.py       # Extrator unificado
│   ├── automated_data_extractor.py # Extrator automatizado
│   └── *_extractor.py             # Extractors específicos (1x2, handicap, total, etc.)
│
├── ⚙️ systems/            # Sistemas integrados e monitoramento
│   ├── robust_drops_system.py     # Sistema robusto (RECOMENDADO) 🌟
│   ├── integrated_drops_system.py # Sistema integrado
│   ├── drop_monitoring_system.py  # Sistema de monitoramento
│   ├── real_time_monitor.py       # Monitor em tempo real
│   ├── complete_flow_system.py    # Sistema de fluxo completo
│   └── interactive_click_recorder.py # Gravador de cliques
│
├── 🧪 tests/              # Testes e debugging
│   ├── test_*.py                  # Arquivos de teste
│   ├── debug_*.py                 # Ferramentas de debug
│   └── test_integrated_drop_system.py # Teste do sistema integrado
│
├── ⚙️ config/             # Arquivos de configuração
│   ├── requirements.txt           # Dependências do projeto
│   └── monitor_config.py          # Configurações de monitoramento
│
├── 📄 data/               # Dados, JSONs e HTMLs gerados
│   ├── *.json                     # Dados extraídos
│   ├── *.html                     # Dashboards gerados
│   └── screenshots/               # Screenshots do sistema
│
├── 📚 docs/               # Documentação
│   └── README.md                  # Este arquivo
│
├── 🔧 v2/                 # Versão 2 (Arquitetura modular)
│   ├── core/                      # Núcleo do sistema
│   └── modules/                   # Módulos específicos
│
├── main.py                # 🚀 PONTO DE ENTRADA PRINCIPAL
├── .env                   # Variáveis de ambiente
└── .gitignore            # Arquivos ignorados pelo Git
```

## 🚀 Como Usar

### Método Recomendado - Menu Principal

```bash
python main.py
```

O menu principal oferece acesso organizado a todos os sistemas:

- **Sistema Robusto de Drops** (Opção 1) - Recomendado para uso geral
- **Extractors** - Para coleta de dados
- **Dashboards** - Para visualização
- **Testes** - Para debugging e validação

### Execução Direta de Sistemas

#### 🌟 Sistema Robusto (Recomendado)
```bash
python systems/robust_drops_system.py
```

#### Sistema Integrado
```bash
python systems/integrated_drops_system.py
```

#### Dashboard Ultimate
```bash
python dashboards/ultimate_dashboard.py
```

## 🎯 Sistemas Principais

### 1. Sistema Robusto de Drops 🌟
**Arquivo:** `systems/robust_drops_system.py`

**Características:**
- ✅ Extração estável do dropping-odds.com
- ✅ Detecção inteligente de drops com múltiplos níveis
- ✅ Dashboard exclusivo para jogos com drops
- ✅ Sistema de retry automático
- ✅ Persistência de dados históricos
- ✅ Tratamento robusto de erros

**Uso:**
```python
from systems.robust_drops_system import RobustDropsSystem

system = RobustDropsSystem()
system.start_monitoring(interval_minutes=5, max_cycles=10)
```

### 2. Sistema Integrado
**Arquivo:** `systems/integrated_drops_system.py`

**Características:**
- Integração com dropping-odds.com
- Análise avançada de drops
- Dashboard unificado
- Alertas em tempo real

### 3. Dashboard Ultimate
**Arquivo:** `dashboards/ultimate_dashboard.py`

**Características:**
- Interface moderna e responsiva
- Visualização de dados históricos
- Análise detalhada de drops
- Estatísticas em tempo real

## 🔧 Configuração

### Dependências

Instale as dependências do arquivo `config/requirements.txt`:

```bash
pip install -r config/requirements.txt
```

**Principais dependências:**
- `selenium` - Automação web
- `beautifulsoup4` - Parsing HTML
- `requests` - Requisições HTTP
- `pandas` - Manipulação de dados
- `numpy` - Computação numérica

### Configuração do Chrome Driver

O sistema usa Selenium com Chrome. Certifique-se de ter:
1. Google Chrome instalado
2. ChromeDriver compatível com sua versão do Chrome
3. ChromeDriver no PATH do sistema

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# Configurações do sistema
DEBUG=True
LOG_LEVEL=INFO

# Configurações de monitoramento
MONITOR_INTERVAL=300  # 5 minutos
MAX_RETRIES=3
TIMEOUT_SECONDS=30

# Thresholds de drops
DROP_THRESHOLD_LOW=3.0
DROP_THRESHOLD_MEDIUM=7.0
DROP_THRESHOLD_HIGH=15.0
DROP_THRESHOLD_CRITICAL=25.0
```

## 📊 Funcionalidades

### Detecção de Drops

- **Níveis de Severidade:**
  - 🟢 Low (3-7%)
  - 🟡 Medium (7-15%)
  - 🟠 High (15-25%)
  - 🔴 Critical (>25%)

- **Tipos de Aposta Monitorados:**
  - 1 (Vitória do time da casa)
  - X (Empate)
  - 2 (Vitória do time visitante)

### Extração de Dados

- **Fontes:**
  - dropping-odds.com (principal)
  - Dados históricos locais
  - APIs complementares

- **Dados Extraídos:**
  - Informações dos jogos
  - Odds em tempo real
  - Histórico de mudanças
  - Estatísticas de drops

### Dashboards

- **Tipos Disponíveis:**
  - Dashboard Robusto (foco em drops detectados)
  - Dashboard Ultimate (análise completa)
  - Dashboard Visual (gráficos e estatísticas)
  - Dashboard de Drops (específico para drops)

## 🧪 Testes

### Executar Todos os Testes
```bash
python main.py  # Opção 13 no menu
```

### Testes Específicos
```bash
python tests/test_integrated_drop_system.py
python tests/test_real_data_drops.py
python tests/debug_drops_structure.py
```

## 📈 Monitoramento

### Logs do Sistema

Os sistemas geram logs detalhados:
- ✅ Jogos extraídos
- 🚨 Drops detectados
- ❌ Erros e exceções
- 📊 Estatísticas de performance

### Arquivos Gerados

- **Dados:** `data/*.json`
- **Dashboards:** `data/*.html`
- **Histórico:** `data/drops_history.json`
- **Screenshots:** `data/screenshots/`

## 🔍 Troubleshooting

### Problemas Comuns

1. **ChromeDriver não encontrado**
   - Baixe o ChromeDriver compatível
   - Adicione ao PATH do sistema

2. **Timeout na extração**
   - Verifique conexão com internet
   - Aumente TIMEOUT_SECONDS no .env

3. **Nenhum drop detectado**
   - Verifique se há jogos ao vivo
   - Ajuste thresholds no .env

4. **Erro de importação**
   - Verifique se está executando da raiz do projeto
   - Instale dependências: `pip install -r config/requirements.txt`

### Debug

```bash
python main.py  # Opção 14 - Debug de Estrutura
```

## 🤝 Contribuição

1. Faça fork do projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📝 Changelog

### v1.0 - Organização do Projeto
- ✅ Estrutura organizada em pastas funcionais
- ✅ Menu principal unificado (main.py)
- ✅ Sistema robusto de drops implementado
- ✅ Documentação completa
- ✅ Testes organizados

## 📄 Licença

Este projeto é de uso interno para análise de drops de odds.

## 📞 Suporte

Para suporte e dúvidas:
1. Consulte este README
2. Execute os testes de debug
3. Verifique os logs do sistema
4. Use o menu principal para navegação

---

**🎯 Sistema de Análise de Drops - Versão Organizada**

*Desenvolvido para detecção inteligente e monitoramento de drops de odds em tempo real.*