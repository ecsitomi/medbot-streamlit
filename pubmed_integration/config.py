# pubmed_integration/config.py
"""
PubMed integráció konfigurációs beállítások
"""
from pathlib import Path

# Alap könyvtárak
BASE_DIR = Path(__file__).parent.parent
PUBMED_DATA_DIR = BASE_DIR / "pubmed_data"
PUBMED_DATA_DIR.mkdir(exist_ok=True)

PUBMED_CONFIG = {
    # Keresési beállítások
    "search": {
        "max_results": 5,  # Maximum hány publikációt kérjünk le
        "min_relevance_score": 0.7,
    },
    
    # LLM beállítások
    "llm": {
        "model": "gpt-4",
        "temperature": 0.2,
        "max_tokens": 2000
    },
    
    # Nyelvi beállítások
    "language": {
        "search_language": "en",  # PubMed keresés angol nyelven
        "output_language": "hu"   # Kimenet magyar nyelven
    }
}