"""
Módulo para integração com LLM e geração de consultas SQL.
"""

import logging
import json
from typing import Optional, Tuple
from openai import OpenAI
from .query_executor import QueryExecutor

logger = logging.getLogger(__name__)


class AIEngine:
    """
    Motor de IA que utiliza LLM para traduzir perguntas em linguagem natural
    para consultas SQL e formatar respostas.
    """

    SYSTEM_PROMPT = """Você é um especialista em análise de dados epidemiológicos do DATASUS.
Sua tarefa é converter perguntas em linguagem natural sobre dados de saúde em consultas SQL válidas para DuckDB.

Regras importantes:
1. Sempre retorne APENAS uma consulta SQL válida, sem explicações adicionais
2. Use apenas as tabelas e colunas disponíveis no banco de dados
3. Para datas, use o formato YYYY-MM-DD
4. Agregue dados por município, estado ou período conforme apropriado
5. Use GROUP BY e ORDER BY para organizar os resultados
6. Limite os resultados a no máximo 100 linhas
7. Se a pergunta for ambígua, faça suposições razoáveis baseadas em contexto epidemiológico

Tabelas disponíveis:
- sim_do: Mortalidade (óbitos) - colunas: data_obito, municipio, estado, causa_morte, idade, sexo
- sih_rd: Internações - colunas: data_internacao, municipio, estado, diagnostico, dias_internacao, tipo_saida
- sia_pa: Produção Ambulatorial - colunas: data_atendimento, municipio, estado, procedimento, quantidade
- ibge_pop: População - colunas: municipio, estado, ano, populacao, faixa_etaria, sexo

Exemplo de pergunta: "Qual o número de óbitos por tuberculose em São Paulo em 2020?"
Resposta esperada: SELECT COUNT(*) as total_obitos FROM sim_do WHERE causa_morte LIKE '%tuberculose%' AND estado = 'SP' AND YEAR(data_obito) = 2020"""

    def __init__(
        self,
        api_key: str,
        api_base: Optional[str] = None,
        model: str = "gpt-4.1-mini",
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
        if api_base:
            self.client = OpenAI(api_key=api_key, base_url=api_base)
        else:
            self.client = OpenAI(api_key=api_key)

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
        try:
            logger.info(f"Gerando SQL para pergunta: {user_question}")

            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                system=self.SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_question}],
            )

            sql_query = response.content[0].text.strip()

            # Remover markdown code blocks se presentes
            if sql_query.startswith("```"):
                sql_query = sql_query.split("```")[1]
                if sql_query.startswith("sql"):
                    sql_query = sql_query[3:]
                sql_query = sql_query.strip()

            logger.debug(f"SQL gerado: {sql_query}")
            return sql_query

        except Exception as e:
            logger.error(f"Erro ao gerar SQL: {e}")
            raise

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
        try:
            logger.info("Formatando resposta...")

            prompt = f"""Baseado na seguinte pergunta e resultados de banco de dados, 
forneça uma resposta clara, concisa e informativa em português.

Pergunta: {user_question}

Resultados do banco de dados:
{query_results}

Resposta:"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
            )

            formatted_response = response.content[0].text.strip()
            logger.debug(f"Resposta formatada: {formatted_response}")
            return formatted_response

        except Exception as e:
            logger.error(f"Erro ao formatar resposta: {e}")
            raise

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
        try:
            logger.info(f"Respondendo pergunta: {user_question}")

            # 1. Gerar SQL
            sql_query = self.generate_sql_query(user_question)

            # 2. Validar SQL
            if not self.query_executor.validate_query(sql_query):
                logger.warning("SQL gerado não passou na validação")
                return (
                    user_question,
                    sql_query,
                    "Erro: A consulta SQL gerada não é válida. Tente reformular sua pergunta.",
                )

            # 3. Executar consulta
            results_df = self.query_executor.execute(sql_query)

            # 4. Formatar resultados
            if results_df.empty:
                formatted_response = "Nenhum resultado encontrado para sua consulta."
            else:
                results_str = results_df.to_string()
                formatted_response = self.format_response(user_question, results_str)

            logger.info("Pergunta respondida com sucesso")
            return (user_question, sql_query, formatted_response)

        except Exception as e:
            logger.error(f"Erro ao responder pergunta: {e}")
            raise

    def close(self):
        """Fecha recursos."""
        self.query_executor.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
