"""
DATASUS AI Search - Busca inteligente em dados epidemiológicos do DATASUS
"""

__version__ = "0.1.0"
__author__ = "Seu Nome"

from .data_manager import DataManager
from .ai_engine import AIEngine
from .query_executor import QueryExecutor

__all__ = ["DataManager", "AIEngine", "QueryExecutor"]
