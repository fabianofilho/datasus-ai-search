"""
Módulo para integração com LLM e geração de consultas SQL.
"""

import logging
import re
from typing import Optional, Tuple
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

EXEMPLOS:
Pergunta: "Quantos óbitos por tuberculose em São Paulo em 2020?"
SQL: SELECT COUNT(*) as total_obitos FROM sim_do WHERE LOWER(CAUSABAS) LIKE '%tuberculose%' AND CODMUNRES LIKE '35%' AND YEAR(DTOBITO) = 2020

Pergunta: "Número de internações por doenças cardiovasculares em 2020"
SQL: SELECT COUNT(*) as total_internacoes, YEAR(DT_INTER) as ano FROM sih_rd WHERE LOWER(DIAG_PRINC) LIKE '%cardiovascular%' AND YEAR(DT_INTER) = 2020 GROUP BY ano
"""

SYSTEM_PROMPT_ANSWER = """Você é um especialista em saúde pública e epidemiologia, com profundo conhecimento do sistema de saúde brasileiro (SUS).
Sua tarefa é interpretar resultados de consultas ao banco de dados do DATASUS e formular uma resposta clara, informativa e em português.

Diretrizes:
- Seja objetivo e direto na resposta.
- Contextualize os números (ex: compare com anos anteriores se relevante).
- Mencione limitações dos dados quando pertinente.
- Use linguagem acessível, mas precisa do ponto de vista epidemiológico.
- Se os dados forem insuficientes ou inconclusivos, diga isso claramente.
- Formate números grandes com separadores de milhar.
"""


class AIEngine:
    """
    Motor de IA que utiliza LLM para traduzir perguntas em linguagem natural
    para consultas SQL e formatar respostas com base nos dados do DATASUS.
    """

    def __init__(
        self,
        api_key: str,
        api_base: Optional[str] = None,
        model: str = "llama-3.3-70b-versatile",
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

    def _build_schema_section(self) -> str:
        """
        Constrói a seção de esquema do banco de dados para o prompt do LLM.

        Returns:
            String com o esquema das tabelas disponíveis.
        """
        tables = self.query_executor.list_tables()
        if not tables:
            return "TABELAS DISPONÍVEIS: Nenhuma tabela encontrada no banco de dados."

        schema_lines = ["TABELAS DISPONÍVEIS:"]
        for table in tables:
            schema = self.query_executor.get_table_schema(table)
            cols = ", ".join([f"{col} ({dtype})" for col, dtype in schema.items()])
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

    def generate_sql_query(self, user_question: str) -> str:
        """
        Gera uma consulta SQL baseada na pergunta do usuário.

        Args:
            user_question: Pergunta em linguagem natural.

        Returns:
            Consulta SQL gerada pelo LLM.

        Raises:
            Exception: Se houver erro na chamada da API.
        """
        schema_section = self._build_schema_section()
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
            max_tokens=1000,
        )

        formatted_response = response.choices[0].message.content.strip()
        logger.debug(f"Resposta formatada: {formatted_response}")
        return formatted_response

    def answer_question(self, user_question: str) -> Tuple[str, str, str]:
        """
        Responde uma pergunta do usuário sobre dados do DATASUS.

        Args:
            user_question: Pergunta em linguagem natural.

        Returns:
            Tupla contendo (pergunta, consulta_sql, resposta_formatada).

        Raises:
            Exception: Se houver erro em qualquer etapa.
        """
        logger.info(f"Respondendo pergunta: {user_question}")

        # 1. Gerar SQL
        sql_query = self.generate_sql_query(user_question)

        # 2. Validar SQL
        if not self.query_executor.validate_query(sql_query):
            logger.warning("SQL gerado não passou na validação, tentando novamente...")
            # Tentar uma segunda vez com instrução mais explícita
            retry_question = (
                f"{user_question}\n\n"
                "IMPORTANTE: A última SQL gerada foi inválida. "
                "Gere uma SQL mais simples e garantidamente válida para DuckDB."
            )
            sql_query = self.generate_sql_query(retry_question)

            if not self.query_executor.validate_query(sql_query):
                return (
                    user_question,
                    sql_query,
                    "Não foi possível gerar uma consulta válida para essa pergunta. "
                    "Tente reformulá-la de forma mais específica.",
                )

        # 3. Executar consulta
        results_df = self.query_executor.execute(sql_query)

        # 4. Formatar resultados
        if results_df.empty:
            formatted_response = (
                "Nenhum resultado encontrado para sua consulta. "
                "Verifique se os dados para o período e localidade solicitados estão disponíveis no banco."
            )
        else:
            results_str = results_df.to_string(index=False)
            formatted_response = self.format_response(user_question, results_str)

        logger.info("Pergunta respondida com sucesso")
        return (user_question, sql_query, formatted_response)

    def close(self):
        """Fecha recursos."""
        self.query_executor.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
