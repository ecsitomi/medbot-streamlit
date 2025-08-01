# pubmed_integration/__init__.py
"""
PubMed integráció a medical chatbot számára.
LangChain alapú PubMed keresés és elemzés.
"""

from .pubmed_analyzer import PubMedAnalyzer, run_pubmed_analysis
from .config import PUBMED_CONFIG

__all__ = [
    'PubMedAnalyzer',
    'run_pubmed_analysis',
    'PUBMED_CONFIG'
]