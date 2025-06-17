# 🚦 Dropping Odds Monitor

Um bot em Python que monitora a queda de odds em sites de apostas esportivas, analisa os dados dos jogos em tempo real e envia alertas para um canal do Telegram. Utiliza o Supabase para registrar os alertas enviados e evitar duplicatas.

---

## ✨ Funcionalidades Principais

- 🔎 **Scraping em Tempo Real**: Coleta dados de odds continuamente usando Selenium.
- 🧠 **Lógica de Alerta Customizável**: Analisa dados com base em regras personalizadas (queda de odds, placar, tempo de jogo, etc.).
- 📲 **Notificações no Telegram**: Envia alertas instantâneos e bem formatados para um chat ou canal do Telegram.
- ☁️ **Registro na Nuvem com Supabase**: Salva cada alerta enviado em um banco de dados, garantindo que nenhum alerta para o mesmo jogo seja enviado mais de uma vez.
- ⚙️ **Configuração Segura**: Utiliza um arquivo `.env` para gerenciar chaves de API e outras informações sensíveis de forma segura.
- 💪 **Robusto e Autônomo**: Projetado para rodar continuamente, com tratamento de erros para lidar com dados inesperados ou falhas de rede.

---

## 💻 Tecnologias Utilizadas

- **Linguagem**: Python 3.9+
- **Web Scraping**: Selenium, BeautifulSoup4
- **Manipulação de Dados**: Pandas
- **Banco de Dados**: Supabase (PostgreSQL)
- **Notificações**: API do Telegram
- **Dependências**: `python-dotenv`, `requests`

---

## 🚀 Requisitos

- **Python 3.9** ou superior
- **Google Chrome** instalado
- Conta no **Telegram** e credenciais de um Bot (token e chat ID)
- Conta gratuita no **[Supabase](https://supabase.com/)**

---

## 🛠️ Guia de Instalação e Configuração

### 1. Clonar o Repositório

```bash
git clone https://github.com/lino167/Dropping-Odds-Monitor.git
cd seu-repositorio
```

### 2. Criar um Ambiente Virtual (Recomendado)

```bash
python -m venv venv
# Ativar o ambiente
# No Windows:
venv\Scripts\activate
# No macOS/Linux:
source venv/bin/activate
```

### 3. Instalar as Dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar o Supabase

- **Crie um Projeto:** Faça login no Supabase e crie um novo projeto.
- **Crie a Tabela de Alertas:**
  - No menu lateral, vá para Table Editor.
  - Clique em "Create a new table".
  - Nomeie a tabela como `alertas_enviados`.
  - Desmarque "Enable Row Level Security (RLS)" para facilitar os testes.
  - Adicione as seguintes colunas:

| Nome da Coluna           | Tipo (Type) | Observações                                 |
|--------------------------|-------------|---------------------------------------------|
| id                       | int8        | (Padrão - Deixe como está)                  |
| created_at               | timestamptz | (Padrão - Deixe como está)                  |
| game_id                  | text        | **Chave Primária (Primary Key)**            |
| liga                     | text        |                                             |
| times                    | text        |                                             |
| favorito                 | text        |                                             |
| odd_inicial_favorito     | float8      | Número com casas decimais                   |
| odd_atual_favorito       | float8      | Número com casas decimais                   |
| queda_odd_favorito       | float8      | Número com casas decimais                   |
| linha_gols_inicial       | text        |                                             |
| odd_linha_gols_inicial   | float8      | Número com casas decimais                   |
| linha_gols_atual         | text        |                                             |
| odd_linha_gols_atual     | float8      | Número com casas decimais                   |
| drop_total               | float8      | Número com casas decimais                   |
| placar                   | text        |                                             |
| tempo_jogo               | int8        | Número inteiro (ex: 39)                     |
| url                      | text        |                                             |
| mensagem_html            | text        |                                             |

- **Obtenha suas Chaves de API:**
  - No menu lateral, vá em Project Settings > API.
  - Copie a Project URL e a chave anon public.

### 5. Configurar o Arquivo `.env`

Crie um arquivo `.env` na raiz do projeto com o seguinte conteúdo:

```env
# Chaves do seu bot do Telegram (obtenha com o @BotFather)
TELEGRAM_BOT_TOKEN="SEU_TOKEN_AQUI"
TELEGRAM_CHAT_ID="SEU_CHAT_ID_AQUI"

# Chaves do seu projeto Supabase
SUPABASE_URL="SUA_URL_DO_PROJETO_SUPABASE_AQUI"
SUPABASE_KEY="SUA_CHAVE_ANON_PUBLIC_AQUI"
```

---

## ▶️ Como Executar

Com tudo configurado, rode o script principal:

```bash
python monitor.py
```

O bot começará a monitorar os jogos, e você verá os logs de atividade no terminal. Quando um alerta for gerado, ele será enviado para o seu Telegram e registrado no Supabase.

---

## 📁 Estrutura do Projeto

```
.
├── venv/                # Ambiente virtual do Python
├── .env                 # Suas chaves e segredos (NÃO ENVIE PARA O GITHUB)
├── alert_manager.py     # Lógica de geração e envio de alertas
├── config.py            # Configurações e variáveis de ambiente
├── data_extractor.py    # Extração de dados de odds
├── excel_utils.py       # Funções para exportação para Excel
├── monitor.py           # Script principal de monitoramento
├── requirements.txt     # Dependências do projeto
└── README.md            # Este arquivo
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