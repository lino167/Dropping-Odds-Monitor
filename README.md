# Dropping Odds Monitor

## Visão Geral

O **Dropping Odds Monitor** é uma ferramenta automatizada para monitoramento de odds (cotações) em sites de apostas esportivas. O sistema identifica quedas relevantes nas odds, registra os dados em planilhas Excel e envia alertas em tempo real para um canal do Telegram, facilitando a análise de oportunidades de apostas baseadas em variações do mercado.

---

## Funcionalidades

- **Web Scraping de Odds:** Coleta automática de odds em sites de apostas.
- **Detecção de Quedas:** Identifica quedas significativas nas cotações.
- **Alertas no Telegram:** Envia notificações instantâneas para um canal configurado.
- **Exportação para Excel:** Salva os dados monitorados em arquivos `.xlsx`.
- **Configuração via `.env`:** Permite ajustes rápidos de parâmetros sensíveis e tokens.

---

## Requisitos

- Python 3.8+
- Google Chrome (para uso com Selenium)
- Token de bot e ID do canal do Telegram

---

## Instalação

1. **Clone o repositório:**
   ```sh
   git clone https://github.com/seu-usuario/dropping_odds.git
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
   Crie um arquivo `.env` na raiz do projeto com o seguinte conteúdo:
   ```
   TELEGRAM_TOKEN=seu_token_aqui
   TELEGRAM_CHANNEL_ID=seu_canal_id_aqui
   ```

---

## Uso

1. **Execute o monitoramento:**
   ```sh
   python monitor.py
   ```

2. **Acompanhe os alertas:**
   - Os alertas de quedas de odds serão enviados automaticamente para o canal do Telegram configurado.

3. **Verifique os relatórios:**
   - Os dados coletados e processados serão salvos em arquivos Excel na raiz do projeto.

---

## Estrutura do Projeto

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

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests.

---

## Licença

Este projeto está sob a licença MIT.

---

## Contato

Dúvidas ou sugestões? Entre em contato abra uma issue no repositório.