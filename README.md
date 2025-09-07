# 🚦 Dropping Odds Monitor v2.0

Um sistema modular em Python para monitoramento e análise de odds em tempo real de sites de apostas esportivas. Esta versão 2.0 apresenta uma arquitetura completamente redesenhada com foco em modularidade, escalabilidade e facilidade de manutenção.

## ✨ Principais Melhorias da v2.0

### 🏗️ **Arquitetura Modular**
- Sistema baseado em módulos independentes e reutilizáveis
- Separação clara de responsabilidades
- Facilita manutenção e expansão do sistema

### 🎯 **Extração Aprimorada**
- Captura completa de dados dos jogos ao vivo
- Extração do Game ID único para cada partida
- Taxa de sucesso de 100% na captura de dados
- Suporte a múltiplas ligas e países

### 📊 **Dados Estruturados**
- Informações completas: liga, times, placar, tempo, país, URL
- Identificação única de cada jogo
- Timestamp de extração
- Estrutura de dados padronizada

## 🚀 Funcionalidades

- **🔎 Scraping em Tempo Real**: Coleta dados de jogos ao vivo usando Selenium
- **🆔 Identificação Única**: Captura Game ID para rastreamento preciso
- **📈 Dados Estruturados**: Informações organizadas e padronizadas
- **🏗️ Arquitetura Modular**: Sistema extensível e maintível
- **⚡ Alta Performance**: Otimizado para processamento eficiente

## 💻 Tecnologias Utilizadas

- **Linguagem**: Python 3.9+
- **Web Scraping**: Selenium, BeautifulSoup4
- **Manipulação de Dados**: Pandas, NumPy
- **Arquitetura**: Padrão modular com event bus
- **Dependências**: Listadas em `requirements.txt`

## 🛠️ Instalação

### 1. Clonar o Repositório
```bash
git clone https://github.com/lino167/Dropping-Odds-Monitor.git
cd Dropping-Odds-Monitor
```

### 2. Criar Ambiente Virtual
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 4. Configurar Ambiente
Crie um arquivo `.env` na raiz do projeto:
```env
# Configurações do sistema
DEBUG=True
HEADLESS=True
```

## ▶️ Como Usar

### Extração Básica de Dados
```bash
python main_extractor.py
```

### Sistema Completo v2.0
```bash
python v2/test_v2_system.py
```

## 📁 Estrutura do Projeto

```
.
├── v2/                     # Sistema v2.0
│   ├── core/               # Módulos base
│   │   ├── base_module.py  # Classe base para módulos
│   │   ├── event_bus.py    # Sistema de eventos
│   │   ├── exceptions.py   # Exceções customizadas
│   │   └── utils.py        # Utilitários gerais
│   ├── modules/            # Módulos funcionais
│   │   └── scraper/        # Módulo de extração
│   │       ├── live_extractor.py  # Extrator de jogos ao vivo
│   │       └── game_monitor.py    # Monitor de jogos
│   └── test_v2_system.py   # Teste do sistema v2.0
├── main_extractor.py       # Script principal de extração
├── requirements.txt        # Dependências
├── .env                    # Variáveis de ambiente
├── .gitignore             # Arquivos ignorados pelo Git
└── README.md              # Este arquivo
```

## 🎯 Exemplo de Saída

```
🏆 EXTRATOR DE JOGOS AO VIVO - DROPPING ODDS
============================================================
📅 Data/Hora: 07/01/2025 15:30:45

🔄 Iniciando extração...
✅ 40 jogos extraídos com sucesso!

📊 DADOS EXTRAÍDOS:
============================================================

🎮 JOGO 01
   🏆 Liga: Spain Regional League
   🏠 Casa: CD Bolanego
   ⚽ Placar: 0:2
   🏃 Visitante: CD Quintanar
   ⏰ Tempo: 73:23
   🆔 Game ID: 10620717

📈 ESTATÍSTICAS:
============================================================
📊 Total de jogos: 40
🆔 Jogos com ID: 40
📊 Taxa de captura de ID: 100.0%
🏆 Ligas diferentes: 31
🌍 Países diferentes: 15
```

## 🔧 Configuração Avançada

### Variáveis de Ambiente (.env)
```env
# Modo de execução
DEBUG=True
HEADLESS=True

# Configurações do scraper
SCRAPER_TIMEOUT=30
SCRAPER_RETRY_COUNT=3

# URLs
BASE_URL=https://dropping-odds.com/index.php?view=live
```

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 📬 Contato

Para dúvidas ou sugestões, abra uma issue no repositório.

---

**v2.0** - Sistema completamente redesenhado com arquitetura modular e extração aprimorada.