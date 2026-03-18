# 🏥 DATASUS AI Search

> Consulte dados epidemiológicos do DATASUS usando linguagem natural. Basta digitar sua pergunta — a IA gera a consulta SQL, executa no banco local e devolve a resposta formatada.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](#-testes)

---

## 🌟 O que é?

**DATASUS AI Search** é uma aplicação Python que integra dados públicos do [DATASUS](https://datasus.saude.gov.br/) com modelos de linguagem (LLMs) para permitir consultas epidemiológicas em português simples. Você não precisa saber SQL — basta fazer uma pergunta como faria a um colega especialista.

**Exemplos de perguntas:**

| Pergunta | Sistema DATASUS |
|---|---|
| "Qual a prevalência de tuberculose em São Paulo em 2018?" | SIM (Mortalidade) |
| "Número de internações por doenças cardiovasculares em 2020" | SIH (Internações) |
| "Quais as 10 principais causas de morte no Brasil em 2019?" | SIM (Mortalidade) |
| "Quantos procedimentos ambulatoriais em Minas Gerais em 2021?" | SIA (Ambulatorial) |
| "Taxa de mortalidade infantil por estado em 2022" | SIM + IBGE |

---

## 🏗️ Arquitetura

```
Pergunta do usuário
        │
        ▼
┌───────────────┐     ┌─────────────────┐     ┌──────────────────┐
│   AIEngine    │────▶│  QueryExecutor  │────▶│  DuckDB (local)  │
│  (LLM / SQL)  │◀────│  (executa SQL)  │◀────│  dados DATASUS   │
└───────────────┘     └─────────────────┘     └──────────────────┘
        │
        ▼
  Resposta formatada
```

O fluxo completo é:
1. O usuário faz uma pergunta em linguagem natural.
2. O **AIEngine** envia a pergunta + esquema do banco ao LLM, que gera uma consulta SQL.
3. O **QueryExecutor** valida e executa o SQL no banco DuckDB local.
4. Os resultados brutos são enviados de volta ao LLM para formatação da resposta final.
5. A resposta é exibida ao usuário na interface web ou no terminal.

---

## 📊 Dados Disponíveis

Os dados são baixados diretamente dos servidores FTP do DATASUS via biblioteca [`datasus-db`](https://pypi.org/project/datasus-db/):

| Dataset | Sistema | Conteúdo |
|---|---|---|
| `sim_do` | SIM | Declarações de Óbito — mortalidade, causas, perfil demográfico |
| `sih_rd` | SIH | AIH Reduzida — internações hospitalares, diagnósticos, permanência |
| `sia_pa` | SIA | Produção Ambulatorial — procedimentos, atendimentos |
| `ibge_pop` | IBGE | Dados populacionais por município, sexo e faixa etária |

---

## 🚀 Instalação e Uso

### Pré-requisitos

- Python 3.11 ou superior
- Chave de API de um LLM compatível com a API da OpenAI (OpenAI, Anthropic via proxy, Ollama, etc.)

### 1. Clone o repositório

```bash
git clone https://github.com/fabianofilho/datasus-ai-search.git
cd datasus-ai-search
```

### 2. Crie o ambiente virtual e instale as dependências

```bash
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

### 3. Configure as variáveis de ambiente

```bash
cp .env.example .env
# Edite o .env com sua chave de API
```

```env
OPENAI_API_KEY=sk-sua-chave-aqui
# LLM_API_BASE=http://localhost:11434/v1   # Para Ollama local
# LLM_MODEL=gpt-4.1-mini
```

### 4. Inicialize o banco de dados

Na primeira execução, os dados do DATASUS precisam ser baixados e importados:

```bash
# Via CLI
python src/cli.py --init

# Ou especificando apenas alguns datasets
python src/cli.py --init --datasets sim_do sih_rd
```

> **Atenção:** O download pode levar vários minutos dependendo da sua conexão, pois os arquivos do DATASUS são grandes.

### 5. Faça sua primeira consulta

**Via interface web (recomendado):**

```bash
streamlit run src/app.py
```

Acesse `http://localhost:8501` no navegador.

**Via linha de comando:**

```bash
python src/cli.py "Qual o número de internações por doenças cardiovasculares em São Paulo em 2020?"

# Para ver o SQL gerado
python src/cli.py --show-sql "Quantos óbitos por tuberculose em 2018?"
```

---

## 🖥️ Interface Web

A interface Streamlit oferece:

- Campo de texto para a pergunta em linguagem natural
- Seleção de modelo de LLM (GPT-4.1-mini, GPT-4.1-nano, Gemini, etc.)
- Botões de exemplo para perguntas comuns
- Exibição da resposta formatada e do SQL gerado
- Histórico das últimas consultas da sessão

---

## 🧪 Testes

```bash
python -m pytest tests/ -v
```

---

## 🔧 Configuração Avançada

### Usando Ollama (LLM local, sem custo de API)

```bash
# Instale o Ollama: https://ollama.ai
ollama pull llama3

# Configure o .env
LLM_API_BASE=http://localhost:11434/v1
LLM_MODEL=llama3
OPENAI_API_KEY=ollama  # qualquer valor não vazio
```

### Usando outros provedores compatíveis

Qualquer provedor que implemente a API da OpenAI pode ser usado. Basta configurar `LLM_API_BASE` e `LLM_MODEL`.

---

## 📁 Estrutura do Projeto

```
datasus-ai-search/
├── src/
│   ├── __init__.py
│   ├── data_manager.py     # Download e gestão dos dados do DATASUS
│   ├── ai_engine.py        # Integração com LLM (geração de SQL e resposta)
│   ├── query_executor.py   # Execução segura de SQL no DuckDB
│   ├── app.py              # Interface web (Streamlit)
│   └── cli.py              # Interface de linha de comando
├── tests/
│   └── test_query_executor.py
├── data/                   # Banco DuckDB (gerado automaticamente, não versionado)
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🤝 Contribuindo

Contribuições são muito bem-vindas! Abra uma *issue* ou envie um *pull request*.

1. Faça um Fork do projeto
2. Crie sua branch (`git checkout -b feature/minha-feature`)
3. Commit suas mudanças (`git commit -m 'feat: adiciona suporte a SINAN'`)
4. Push para a branch (`git push origin feature/minha-feature`)
5. Abra um Pull Request

---

## 📝 Licença

Distribuído sob a Licença MIT. Veja [LICENSE](LICENSE) para mais informações.

---

## 🙏 Agradecimentos

- [datasus-db](https://pypi.org/project/datasus-db/) — acesso programático aos dados do DATASUS
- [DuckDB](https://duckdb.org/) — banco de dados analítico local de alta performance
- [Streamlit](https://streamlit.io/) — framework para interfaces de dados em Python
- [DATASUS / Ministério da Saúde](https://datasus.saude.gov.br/) — pelos dados públicos de saúde
