# 🚦 Dropping Odds Monitor

Bem-vindo ao **Dropping Odds Monitor**!  
Uma solução automatizada para monitorar odds em sites de apostas esportivas, identificar quedas e variações relevantes e enviar alertas em tempo real para o Telegram.

---

## ✨ Funcionalidades

- 🔎 **Web Scraping de Odds**: Coleta automática de odds em sites de apostas.
- 🎯 **Detecção Inteligente de Drops**: Identifica automaticamente partidas com drops usando classes CSS (red1, red2, red3).
- 📉 **Detecção de Quedas e Subidas**: Identifica quedas e subidas significativas nas cotações do favorito.
- 🏆 **Análise Inteligente**: Considera apenas cenários relevantes (sem cartões vermelhos, sem pênaltis, favorito empatando ou perdendo, drop relevante na linha de gols).
- ⚡ **Filtragem Otimizada**: Processa apenas partidas que contêm drops detectados, aumentando a eficiência.
- 📲 **Alertas no Telegram**: Notificações automáticas e formatadas como prognóstico, enviadas para seu canal.
- 📊 **Exportação para Excel**: Salva os dados monitorados e os alertas em arquivos `.xlsx`.
- ⚙️ **Configuração via `.env`**: Ajuste rápido de parâmetros sensíveis.

---

## 🚀 Requisitos

- Python 3.8+
- Google Chrome (para Selenium)
- Token do bot e ID do canal do Telegram

---

## 🛠️ Instalação

1. **Clone o repositório:**
   ```sh
   git clone https://github.com/lino167/Dropping-Odds-Monitor.git
   cd dropping_odds
   ```

2. **Crie e ative um ambiente virtual (opcional, mas recomendado):**
   ```sh
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Instale as dependências:**
   ```sh
   pip install -r requirements.txt
   ```

4. **Configure o arquivo `.env`:**
   Crie um arquivo `.env` na raiz do projeto com:
   ```
   TELEGRAM_BOT_TOKEN=seu_token_aqui
   TELEGRAM_CHAT_ID=seu_canal_id_aqui
   ```

---

## ▶️ Como Funciona

O monitor realiza a varredura das odds em tempo real e só envia alertas quando TODOS os critérios abaixo são atendidos:

- **Favorito identificado**: O time com menor odd inicial (home ou away) e odds válidas (>1.01).
- **Drop relevante na linha de gols**: O drop da linha de gols (coluna `drop`) deve ser maior ou igual a 0.40.
- **Sem cartões vermelhos e sem pênaltis**: Ambos os times sem cartões vermelhos e sem pênaltis (0-0).
- **Favorito não está vencendo**: O favorito está empatando ou perdendo no momento do alerta.
- **Variação relevante na odd do favorito**: Queda ou subida de pelo menos 30% em relação à odd inicial.
- **Minuto do jogo**: O alerta só é enviado antes do minuto 80.

Quando todos esses critérios são satisfeitos, o sistema envia um alerta para o Telegram no seguinte formato:

```
🤖 Alerta automático para o jogo [Time da Casa] x [Time Visitante] ([Liga]):
📉 Drop significativo na linha de gols: [valor do drop]
📊 Linha de gols inicial: [handicap inicial] (Odd: [odd inicial])
⚡ Linha de gols atual: [handicap atual] (Odd: [odd atual])
⭐ O favorito é o [nome do favorito] com [queda/subida] de [X]% ([odd inicial] → [odd atual])
🔢 Placar atual: [placar]
⏱️ Minuto: [minuto]
Para mais detalhes, acesse: [link]
⚠️ Lembre-se: este é um alerta automatizado, não é recomendação de aposta.
```

---

## ▶️ Como Usar

1. **Execute o monitoramento:**
   ```sh
   python monitor.py
   ```

2. **Receba alertas no Telegram:**  
   Os alertas de variação de odds serão enviados automaticamente para o canal configurado.

3. **Consulte os relatórios:**  
   Os dados coletados e processados serão salvos em arquivos Excel na raiz do projeto.

---

## 📁 Estrutura do Projeto

```
dropping_odds/
│
├── config.py                    # Carrega configurações do .env
├── data_extractor.py           # Extrai e processa odds dos sites
├── drop_detector.py            # 🆕 Detecta drops usando classes CSS red1/red2/red3
├── excel_utils.py              # Manipula exportação para Excel
├── monitor.py                  # Script principal de monitoramento
├── alert_manager.py            # Lógica de geração e envio de alertas
├── telegram_utils.py           # Envio de mensagens para o Telegram
├── test_drop_detection.py      # 🆕 Script de teste para detecção de drops
├── requirements.txt            # Dependências do projeto
├── .env.example                # Exemplo de configuração
└── README.md                   # Este arquivo
```

## 🎯 Nova Funcionalidade: Detecção de Drops

O sistema agora identifica automaticamente partidas que contêm drops significativos através das classes CSS:

- **red1**: Drops de alta severidade
- **red2**: Drops de média severidade  
- **red3**: Drops de baixa severidade

### Como Funciona:

1. **Verificação Rápida**: O sistema verifica rapidamente se uma partida contém drops antes de processar todos os dados
2. **Filtragem Inteligente**: Apenas partidas com drops detectados são processadas completamente
3. **Otimização de Performance**: Reduz significativamente o tempo de processamento
4. **Alertas Priorizados**: Partidas com drops recebem prioridade no processamento

### Testando a Detecção:

```bash
python test_drop_detection.py
```

Este script permite testar a funcionalidade de detecção em partidas específicas.

---

## 🤝 Contribua

Contribuições são bem-vindas!  
Abra uma issue ou envie um pull request.

---

## 📄 Licença

MIT

---

## 📬 Contato

Dúvidas ou sugestões?  
Abra uma issue no repositório ou entre em contato pelo canal do Telegram configurado.