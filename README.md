# 🏥 DATASUS AI Search

Uma aplicação inteligente que permite consultar dados epidemiológicos do DATASUS usando linguagem natural. Basta fazer uma pergunta e a Inteligência Artificial se encarrega de traduzi-la para uma consulta SQL, executá-la em um banco de dados local e retornar a resposta formatada.

## 🌟 Características

- **Busca em Linguagem Natural**: Faça perguntas como "Qual o número de internações por doenças cardiovasculares em São Paulo em 2020?"
- **Banco de Dados Local Rápido**: Utiliza DuckDB para consultas analíticas de alta performance.
- **Dados Oficiais**: Integração direta com os servidores FTP do DATASUS via biblioteca `datasus-db`.
- **Interface Amigável**: Interface web construída com Streamlit, fácil de usar e configurar.
- **Flexibilidade de LLM**: Suporte para OpenAI e outros modelos compatíveis com a API da OpenAI.

## 📊 Dados Disponíveis

O sistema pode importar e consultar os seguintes conjuntos de dados do DATASUS:
- **SIM (Mortalidade)**: Dados de óbitos, causas, perfil demográfico.
- **SIH (Internações)**: Dados hospitalares, diagnósticos, tempo de permanência.
- **SIA (Ambulatorial)**: Produção ambulatorial, procedimentos realizados.
- **IBGE**: Dados populacionais para cálculo de taxas e prevalências.

## 🚀 Como Começar

### Pré-requisitos

- Python 3.11 ou superior
- Uma chave de API de um LLM (OpenAI, Anthropic, etc.)

### Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/datasus-ai-search.git
cd datasus-ai-search
```

2. Crie um ambiente virtual e ative-o:
```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente (opcional):
```bash
cp .env.example .env
# Edite o arquivo .env com sua chave de API
```

### Executando a Aplicação

Inicie a interface web com o Streamlit:

```bash
streamlit run src/app.py
```

A aplicação será aberta no seu navegador padrão (geralmente em `http://localhost:8501`).

## 💡 Como Usar

1. Na barra lateral, insira sua **Chave de API do LLM**.
2. Clique em **Inicializar BD** para baixar os dados do DATASUS e criar o banco local (isso pode levar alguns minutos na primeira vez).
3. Digite sua pergunta na área principal. Exemplos:
   - *"Qual foi a prevalência de tuberculose em São Paulo em 2018?"*
   - *"Quantos óbitos por COVID-19 ocorreram no Brasil em 2021?"*
   - *"Qual é a taxa de mortalidade infantil por estado em 2022?"*
4. Clique em **Buscar** e aguarde a resposta da IA!

## 🏗️ Arquitetura

O projeto é composto por três módulos principais:
- `DataManager`: Gerencia o download e atualização dos dados do DATASUS para o DuckDB.
- `AIEngine`: Integra-se com o LLM para traduzir perguntas em SQL e formatar as respostas.
- `QueryExecutor`: Executa as consultas SQL de forma segura no banco de dados local.

## 🤝 Contribuindo

Contribuições são muito bem-vindas! Sinta-se à vontade para abrir *issues* ou enviar *pull requests*.

1. Faça um Fork do projeto
2. Crie sua Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Faça o Commit de suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Faça o Push para a Branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🙏 Agradecimentos

- [datasus-db](https://pypi.org/project/datasus-db/) - Biblioteca incrível para acesso aos dados do DATASUS.
- [DuckDB](https://duckdb.org/) - Banco de dados analítico de alta performance.
- [Streamlit](https://streamlit.io/) - Framework para criação de interfaces de dados.
