"""
Módulo para integração com LLM e geração de consultas SQL.
"""

import logging
import re
from typing import List, Optional, Tuple
from openai import OpenAI
from query_executor import QueryExecutor

logger = logging.getLogger(__name__)


SYSTEM_PROMPT_SQL = """Você é um especialista em análise de dados epidemiológicos do DATASUS (Departamento de Informática do SUS, Brasil).
Sua tarefa é converter perguntas em linguagem natural sobre dados de saúde em consultas SQL válidas para DuckDB.

Regras OBRIGATÓRIAS:
1. Retorne APENAS o código SQL, sem nenhum texto adicional, sem markdown, sem explicações.
2. Use apenas as tabelas e colunas listadas abaixo.
3. Sempre use LIMIT 100 no máximo.
4. Para filtros de estado, use a sigla de 2 letras (ex: 'SP', 'RJ', 'MG').
5. Para filtros de ano, use a função YEAR() ou EXTRACT(YEAR FROM coluna).
6. Use COUNT(*) para contagens, SUM() para somas, AVG() para médias.
7. Sempre use GROUP BY quando houver agregações com outras colunas.
8. Use ORDER BY para ordenar resultados de forma relevante.

{schema_section}

CÓDIGOS (erro comum):
- CAUSABAS (SIM) e DIAG_PRINC (SIH) guardam códigos CID-10, como 'A150' ou 'I219', nunca o nome da doença.
  Filtre pela categoria de 3 caracteres: LEFT(CAUSABAS, 3) BETWEEN 'A15' AND 'A19' (tuberculose).
  Grupos úteis: tuberculose A15-A19; circulatório I00-I99; infarto I21-I22; AVC I60-I69;
  neoplasias C00-D48; diabetes E10-E14; pneumonia J12-J18; agressões X85-Y09; causas externas V01-Y98.
- CODMUNRES tem 6 dígitos e começa pelo código IBGE da UF (SP = '35', RJ = '33', MG = '31').

EXEMPLOS:
Pergunta: "Quantos óbitos por tuberculose em São Paulo em 2020?"
SQL: SELECT COUNT(*) AS total_obitos FROM sim_do WHERE LEFT(CAUSABAS, 3) BETWEEN 'A15' AND 'A19' AND CODMUNRES LIKE '35%' AND YEAR(DTOBITO) = 2020

Pergunta: "Número de internações por doenças cardiovasculares em 2020"
SQL: SELECT COUNT(*) AS total_internacoes FROM sih_rd WHERE LEFT(DIAG_PRINC, 1) = 'I' AND YEAR(DT_INTER) = 2020
"""

SYSTEM_PROMPT_ANSWER = """Você é um especialista em saúde pública e epidemiologia do SUS.
Sua tarefa é descrever, em português, o resultado de uma consulta ao banco do DATASUS.

Regras obrigatórias:
- Use SOMENTE os números que aparecem no resultado abaixo. Nunca invente, estime, arredonde para
  "cerca de" nem traga números de memória, de outros anos ou de outras fontes.
- Não compare com anos, lugares ou grupos que não estejam no resultado.
- Se o resultado for zero ou vazio, diga isso e sugira conferir o filtro ou se os dados do
  recorte estão carregados; não complete com estimativas.
- Seja direto: até 5 frases ou uma tabela curta. Números com separador de milhar.
"""


def _numero_br(valor) -> str:
    """1234567.891 -> '1.234.567,89'; inteiro sem casas decimais."""
    if isinstance(valor, bool):
        return str(valor)
    if isinstance(valor, int) or (isinstance(valor, float) and valor.is_integer()):
        return f"{int(valor):,}".replace(",", ".")
    if isinstance(valor, float):
        return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return str(valor)


def resposta_de_um_valor(coluna: str, valor) -> str:
    """Resposta direta para resultado de uma linha e uma coluna, sem chamar o modelo."""
    try:
        import numpy as np

        if isinstance(valor, np.generic):
            valor = valor.item()
    except ImportError:
        pass
    rotulo = str(coluna).replace("_", " ").strip()
    return f"Resultado ({rotulo}): **{_numero_br(valor)}**."


class AIEngine:
    """
    Motor de IA que utiliza LLM para traduzir perguntas em linguagem natural
    para consultas SQL e formatar respostas com base nos dados do DATASUS.
    """

    def __init__(
        self,
        api_key: str,
        api_base: Optional[str] = None,
        model: str = "openai/gpt-oss-20b",
        db_path: str = "data/datasus.db",
    ):
        """
        Inicializa o motor de IA.

        Args:
            api_key: Chave da API do LLM.
            api_base: URL base da API (opcional, para LLMs alternativos).
            model: Modelo de LLM a usar.
            db_path: Caminho para o banco de dados DuckDB.
        """
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        self.db_path = db_path
        self.query_executor = QueryExecutor(db_path)

        # Inicializar cliente OpenAI
        client_kwargs = {"api_key": api_key}
        if api_base:
            client_kwargs["base_url"] = api_base
        self.client = OpenAI(**client_kwargs)

    def _build_schema_section(self, tabelas: Optional[List[str]] = None) -> str:
        """
        Constrói a seção de esquema do prompt, só com as tabelas pedidas.

        Mandar o esquema de todas as tabelas fazia o prompt crescer com cada
        dataset baixado (SIM e SIH têm perto de cem colunas cada): mais tokens,
        resposta mais lenta e o limite por minuto do provedor estourando antes.
        Colunas VARCHAR saem só com o nome; as demais levam o tipo.

        Args:
            tabelas: nomes das tabelas relevantes (sem diferenciar maiúsculas);
                se nenhuma existir no banco, usa todas.
        """
        existentes = self.query_executor.list_tables()
        if not existentes:
            return "TABELAS DISPONÍVEIS: Nenhuma tabela encontrada no banco de dados."

        escolhidas = existentes
        if tabelas:
            pedidas = {t.lower() for t in tabelas}
            filtradas = [t for t in existentes if t.lower() in pedidas]
            escolhidas = filtradas or existentes

        schema_lines = ["TABELAS DISPONÍVEIS:"]
        for table in escolhidas:
            schema = self.query_executor.get_table_schema(table)
            cols = ", ".join(
                col if dtype.upper().startswith("VARCHAR") else f"{col} ({dtype})"
                for col, dtype in schema.items()
            )
            schema_lines.append(f"- {table}: {cols}")

        return "\n".join(schema_lines)

    def _clean_sql(self, raw_sql: str) -> str:
        """
        Remove artefatos de markdown e espaços extras de uma string SQL.

        Args:
            raw_sql: SQL bruto retornado pelo LLM.

        Returns:
            SQL limpo.
        """
        # Remover blocos de código markdown
        sql = re.sub(r"```(?:sql)?\s*", "", raw_sql, flags=re.IGNORECASE)
        sql = sql.replace("```", "")
        return sql.strip()

    def generate_sql_query(self, user_question: str, tabelas: Optional[List[str]] = None) -> str:
        """
        Gera uma consulta SQL baseada na pergunta do usuário.

        Args:
            user_question: Pergunta em linguagem natural.

        Returns:
            Consulta SQL gerada pelo LLM.

        Raises:
            Exception: Se houver erro na chamada da API.
        """
        schema_section = self._build_schema_section(tabelas)
        system_prompt = SYSTEM_PROMPT_SQL.format(schema_section=schema_section)

        logger.info(f"Gerando SQL para pergunta: {user_question}")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_question},
            ],
            temperature=0,
            max_tokens=500,
        )

        raw_sql = response.choices[0].message.content
        sql_query = self._clean_sql(raw_sql)
        logger.debug(f"SQL gerado: {sql_query}")
        return sql_query

    def format_response(self, user_question: str, query_results: str) -> str:
        """
        Formata os resultados da consulta em uma resposta natural.

        Args:
            user_question: Pergunta original do usuário.
            query_results: Resultados da consulta em formato de string.

        Returns:
            Resposta formatada em linguagem natural.

        Raises:
            Exception: Se houver erro na chamada da API.
        """
        logger.info("Formatando resposta...")

        user_content = (
            f"Pergunta do usuário: {user_question}\n\n"
            f"Resultados obtidos do banco de dados DATASUS:\n{query_results}\n\n"
            "Formule uma resposta clara e informativa em português."
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_ANSWER},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
            max_tokens=500,
        )

        formatted_response = response.choices[0].message.content.strip()
        logger.debug(f"Resposta formatada: {formatted_response}")
        return formatted_response

    def answer_question(self, user_question: str) -> Tuple[str, str, str]:
        """
        Responde uma pergunta do usuário sobre dados do DATASUS.

        Returns:
            Tupla contendo (pergunta, consulta_sql, resposta_formatada).
        """
        r = self.responder(user_question)
        return (r["question"], r["sql"], r["answer"])

    def responder(self, user_question: str, tabelas: Optional[List[str]] = None) -> dict:
        """
        Gera o SQL, executa uma vez e redige a resposta.

        Devolve também o DataFrame do resultado, para quem chama não precisar rodar
        o SQL de novo. Resultado de um só número (uma contagem, uma soma) é
        respondido aqui mesmo, sem a segunda chamada ao modelo: é o caso mais comum
        e a chamada só reescrevia o número em frase.

        Returns:
            dict com question, sql, answer e df (pandas.DataFrame ou None).
        """
        logger.info(f"Respondendo pergunta: {user_question}")

        sql_query = self.generate_sql_query(user_question, tabelas)

        if not self.query_executor.validate_query(sql_query):
            logger.warning("SQL gerado não passou na validação, tentando novamente...")
            retry_question = (
                f"{user_question}\n\n"
                "IMPORTANTE: A última SQL gerada foi inválida. "
                "Gere uma SQL mais simples e garantidamente válida para DuckDB."
            )
            sql_query = self.generate_sql_query(retry_question, tabelas)

            if not self.query_executor.validate_query(sql_query):
                return {
                    "question": user_question,
                    "sql": sql_query,
                    "answer": "Não foi possível gerar uma consulta válida para essa pergunta. "
                              "Tente reformulá-la de forma mais específica.",
                    "df": None,
                }

        results_df = self.query_executor.execute(sql_query)

        if results_df.empty:
            answer = (
                "Nenhum resultado encontrado para sua consulta. "
                "Verifique se os dados para o período e localidade solicitados estão disponíveis no banco."
            )
        elif results_df.shape == (1, 1):
            answer = resposta_de_um_valor(results_df.columns[0], results_df.iat[0, 0])
        else:
            results_str = results_df.head(30).to_string(index=False)
            answer = self.format_response(user_question, results_str)

        logger.info("Pergunta respondida com sucesso")
        return {"question": user_question, "sql": sql_query, "answer": answer, "df": results_df}

    def close(self):
        """Fecha recursos."""
        self.query_executor.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
