# Arquitetura do Sistema de Análise de Drops 2.0

## 📋 Visão Geral

Baseado na análise da página live do dropping-odds.com, o sistema 2.0 será construído com arquitetura modular, orientada a eventos e altamente escalável.

### 🔍 Descobertas da Análise
- **44 jogos** identificados na página live
- **Estrutura de 6 colunas**: País, Liga, Time Casa, Placar, Time Visitante, Tempo
- **1 tabela principal** com dados estruturados
- **Sem filtros** na página (navegação simples)
- **9 scripts** carregados (possível JavaScript para atualizações)

## 🏗️ Arquitetura Modular

```
┌─────────────────────────────────────────────────────────────┐
│                    SISTEMA 2.0                             │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   WEB UI    │  │  REST API   │  │  WEBSOCKET  │        │
│  │  Dashboard  │  │   Server    │  │   Server    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│                    EVENT BUS                                │
│              (Comunicação entre módulos)                   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   SCRAPER   │  │  ANALYZER   │  │  NOTIFIER   │        │
│  │   MODULE    │  │   MODULE    │  │   MODULE    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  DATABASE   │  │    CACHE    │  │   CONFIG    │        │
│  │   MODULE    │  │   MODULE    │  │   MODULE    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## 📦 Módulos Principais

### 1. **Scraper Module** 🕷️
**Responsabilidade**: Extração de dados das páginas

```python
class ScraperModule:
    - LiveGamesExtractor     # Extrai jogos da página live
    - GameDetailsExtractor   # Extrai detalhes específicos do jogo
    - DropDetector          # Detecta drops usando método aprimorado
    - PageMonitor           # Monitora mudanças nas páginas
```

**Funcionalidades**:
- ✅ Extração de jogos ao vivo (44 jogos identificados)
- ✅ Detecção de drops por colunas específicas
- ✅ Monitoramento contínuo de mudanças
- ✅ Tratamento de erros e retry automático

### 2. **Analyzer Module** 📊
**Responsabilidade**: Análise e processamento de dados

```python
class AnalyzerModule:
    - GameDataParser        # Parser estruturado para dados
    - DropAnalyzer          # Análise avançada de drops
    - PatternDetector       # Detecção de padrões
    - RiskCalculator        # Cálculo de riscos
```

**Funcionalidades**:
- ✅ Parser para estrutura de 6 colunas
- ✅ Análise de padrões históricos
- ✅ Cálculo de probabilidades
- ✅ Classificação de oportunidades

### 3. **Notifier Module** 📢
**Responsabilidade**: Envio de notificações e alertas

```python
class NotifierModule:
    - TelegramNotifier      # Notificações via Telegram
    - EmailNotifier         # Notificações via email
    - WebhookNotifier       # Notificações via webhook
    - AlertManager          # Gerenciamento de alertas
```

**Funcionalidades**:
- ✅ Alertas em tempo real
- ✅ Múltiplos canais de notificação
- ✅ Filtros personalizáveis
- ✅ Histórico de alertas

### 4. **Database Module** 🗄️
**Responsabilidade**: Persistência e consulta de dados

```python
class DatabaseModule:
    - GameRepository        # Repositório de jogos
    - DropRepository        # Repositório de drops
    - UserRepository        # Repositório de usuários
    - AnalyticsRepository   # Repositório de analytics
```

**Funcionalidades**:
- ✅ Armazenamento estruturado
- ✅ Consultas otimizadas
- ✅ Backup automático
- ✅ Migração de dados

### 5. **Cache Module** ⚡
**Responsabilidade**: Cache inteligente para performance

```python
class CacheModule:
    - MemoryCache          # Cache em memória
    - RedisCache           # Cache distribuído
    - CacheManager         # Gerenciamento de cache
    - TTLManager           # Gerenciamento de TTL
```

### 6. **Config Module** ⚙️
**Responsabilidade**: Configuração centralizada

```python
class ConfigModule:
    - EnvironmentConfig    # Configurações de ambiente
    - UserConfig           # Configurações de usuário
    - SystemConfig         # Configurações do sistema
    - ConfigValidator      # Validação de configurações
```

## 🔄 Event Bus - Comunicação entre Módulos

### Eventos Principais

```python
# Eventos do Scraper
class ScraperEvents:
    GAMES_DISCOVERED = "scraper.games.discovered"
    DROP_DETECTED = "scraper.drop.detected"
    PAGE_CHANGED = "scraper.page.changed"
    ERROR_OCCURRED = "scraper.error.occurred"

# Eventos do Analyzer
class AnalyzerEvents:
    ANALYSIS_COMPLETED = "analyzer.analysis.completed"
    PATTERN_FOUND = "analyzer.pattern.found"
    RISK_CALCULATED = "analyzer.risk.calculated"

# Eventos do Notifier
class NotifierEvents:
    ALERT_SENT = "notifier.alert.sent"
    NOTIFICATION_FAILED = "notifier.notification.failed"
```

### Fluxo de Eventos

```
1. ScraperModule detecta jogos → GAMES_DISCOVERED
2. AnalyzerModule processa → ANALYSIS_COMPLETED
3. Se drop detectado → DROP_DETECTED
4. AnalyzerModule calcula risco → RISK_CALCULATED
5. NotifierModule envia alerta → ALERT_SENT
6. DatabaseModule salva dados → DATA_PERSISTED
```

## 🚀 Implementação por Etapas

### **Etapa 1: Core Infrastructure** (Atual)
- ✅ Event Bus básico
- ✅ Config Module
- ✅ Logging System
- ✅ Base classes para módulos

### **Etapa 2: Scraper Module** 
- 🔄 LiveGamesExtractor (baseado na análise)
- 🔄 Enhanced DropDetector
- 🔄 PageMonitor

### **Etapa 3: Database & Cache**
- 📋 Database Module
- 📋 Cache Module
- 📋 Data repositories

### **Etapa 4: Analyzer Module**
- 📋 GameDataParser
- 📋 PatternDetector
- 📋 RiskCalculator

### **Etapa 5: Notifier Module**
- 📋 Multi-channel notifications
- 📋 Alert management
- 📋 User preferences

### **Etapa 6: Web Interface**
- 📋 Dashboard
- 📋 REST API
- 📋 WebSocket real-time

## 📁 Estrutura de Diretórios

```
v2/
├── core/                    # Infraestrutura central
│   ├── __init__.py
│   ├── event_bus.py        # Sistema de eventos
│   ├── base_module.py      # Classe base para módulos
│   ├── exceptions.py       # Exceções customizadas
│   └── utils.py           # Utilitários gerais
├── modules/                # Módulos principais
│   ├── scraper/           # Módulo de scraping
│   │   ├── __init__.py
│   │   ├── live_extractor.py
│   │   ├── drop_detector.py
│   │   └── page_monitor.py
│   ├── analyzer/          # Módulo de análise
│   │   ├── __init__.py
│   │   ├── game_parser.py
│   │   ├── pattern_detector.py
│   │   └── risk_calculator.py
│   ├── notifier/          # Módulo de notificações
│   │   ├── __init__.py
│   │   ├── telegram.py
│   │   ├── email.py
│   │   └── webhook.py
│   ├── database/          # Módulo de banco de dados
│   │   ├── __init__.py
│   │   ├── repositories.py
│   │   ├── models.py
│   │   └── migrations.py
│   ├── cache/             # Módulo de cache
│   │   ├── __init__.py
│   │   ├── memory.py
│   │   ├── redis.py
│   │   └── manager.py
│   └── config/            # Módulo de configuração
│       ├── __init__.py
│       ├── settings.py
│       ├── validator.py
│       └── loader.py
├── api/                   # API REST
│   ├── __init__.py
│   ├── routes.py
│   ├── middleware.py
│   └── schemas.py
├── web/                   # Interface web
│   ├── static/
│   ├── templates/
│   └── app.py
├── tests/                 # Testes
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── config/                # Arquivos de configuração
│   ├── development.yaml
│   ├── production.yaml
│   └── test.yaml
├── docs/                  # Documentação
├── requirements.txt       # Dependências
├── docker-compose.yml     # Docker setup
└── main.py               # Ponto de entrada
```

## 🔧 Tecnologias e Dependências

### **Core**
- **Python 3.12+**: Linguagem principal
- **AsyncIO**: Programação assíncrona
- **Pydantic**: Validação de dados
- **Loguru**: Sistema de logging avançado

### **Scraping**
- **Selenium**: Automação web
- **BeautifulSoup**: Parsing HTML
- **aiohttp**: Cliente HTTP assíncrono

### **Database**
- **SQLAlchemy**: ORM
- **Alembic**: Migrações
- **PostgreSQL**: Banco principal
- **Redis**: Cache e filas

### **API & Web**
- **FastAPI**: Framework web
- **WebSockets**: Comunicação real-time
- **Jinja2**: Templates
- **Uvicorn**: Servidor ASGI

### **Monitoramento**
- **Prometheus**: Métricas
- **Grafana**: Dashboards
- **Sentry**: Error tracking

## 📊 Métricas e Monitoramento

### **KPIs do Sistema**
- **Uptime**: >99.5%
- **Latência de detecção**: <30 segundos
- **Taxa de falsos positivos**: <5%
- **Jogos monitorados**: 40+ simultâneos

### **Alertas de Sistema**
- Falha na extração de dados
- Alta latência de resposta
- Erro de conectividade
- Cache miss rate alto

## 🔒 Segurança

### **Medidas Implementadas**
- Rate limiting para APIs
- Validação de entrada rigorosa
- Logs de auditoria
- Configurações sensíveis em variáveis de ambiente
- HTTPS obrigatório em produção

## 🚀 Deploy e Escalabilidade

### **Containerização**
```yaml
# docker-compose.yml
services:
  app:
    build: .
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://...
  
  postgres:
    image: postgres:15
    
  redis:
    image: redis:7-alpine
```

### **Escalabilidade Horizontal**
- Múltiplas instâncias do scraper
- Load balancer para API
- Cache distribuído
- Filas para processamento assíncrono

## 📈 Roadmap de Evolução

### **Versão 2.1** (1 mês)
- Machine Learning para detecção de padrões
- API pública para terceiros
- Mobile app

### **Versão 2.2** (3 meses)
- Suporte a múltiplos sites
- Sistema de usuários e permissões
- Analytics avançados

### **Versão 3.0** (6 meses)
- IA para predição de drops
- Marketplace de estratégias
- Integração com casas de apostas

---

**Status**: 🔄 Em desenvolvimento  
**Próximo passo**: Implementar Core Infrastructure  
**Estimativa**: 2-3 dias para base funcional