# 🚦 Dropping Odds Monitor

Bem-vindo ao **Dropping Odds Monitor**!  
Uma solução automatizada para monitorar odds em sites de apostas esportivas, identificar quedas relevantes e enviar alertas em tempo real para o Telegram.

---

## ✨ Funcionalidades

- 🔎 **Web Scraping de Odds**: Coleta automática de odds em sites de apostas.
- 📉 **Detecção de Quedas**: Identifica quedas significativas nas cotações.
- 📲 **Alertas no Telegram**: Notificações instantâneas para seu canal.
- 📊 **Exportação para Excel**: Salva os dados monitorados em arquivos `.xlsx`.
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
   TELEGRAM_TOKEN=seu_token_aqui
   TELEGRAM_CHANNEL_ID=seu_canal_id_aqui
   ```

---

## ▶️ Como Usar

1. **Execute o monitoramento:**
   ```sh
   python monitor.py
   ```

2. **Receba alertas no Telegram:**  
   Os alertas de quedas de odds serão enviados automaticamente para o canal configurado.

3. **Consulte os relatórios:**  
   Os dados coletados e processados serão salvos em arquivos Excel na raiz do projeto.

---

## 📁 Estrutura do Projeto

```
dropping_odds/
│
├── config.py           # Carrega configurações do .env
├── data_extractor.py   # Extrai e processa odds dos sites
├── excel_utils.py      # Manipula exportação para Excel
├── monitor.py          # Script principal de monitoramento
├── telegram_utils.py   # Envio de mensagens para o Telegram
├── requirements.txt    # Dependências do projeto
├── .env.example        # Exemplo de configuração
└── README.md           # Este arquivo
```

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