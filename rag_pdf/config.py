# =============================================================================
# rag_pdf/config.py
# =============================================================================
"""
RAG modul konfigurációs beállítások
"""
import os
from pathlib import Path

# Alap könyvtárak
BASE_DIR = Path(__file__).parent.parent
MEDLINE_PDF_DIR = BASE_DIR / "medline_data" / "pdfs"
RAG_DATA_DIR = BASE_DIR / "rag_data"
CHROMA_PERSIST_DIR = RAG_DATA_DIR / "chroma_db"

# Könyvtárak létrehozása
RAG_DATA_DIR.mkdir(exist_ok=True)
CHROMA_PERSIST_DIR.mkdir(exist_ok=True)

RAG_CONFIG = {
    # Embedding beállítások
    "embedding": {
        "model": "text-embedding-3-small",
        "chunk_size": 1000,
        "chunk_overlap": 200,
    },
    
    # Chroma beállítások
    "chroma": {
        "persist_directory": str(CHROMA_PERSIST_DIR),
        "collection_name": "medline_pdfs"
    },
    
    # LLM beállítások
    "llm": {
        "model": "gpt-4",
        "temperature": 0.3,
        "max_tokens": 2000
    },
    
    # RAG beállítások
    "rag": {
        "top_k": 5,  # Hány releváns chunk-ot használjon
        "score_threshold": 0.7  # Relevancia küszöb
    },
    
    # Könyvtárak
    "paths": {
        "pdf_dir": str(MEDLINE_PDF_DIR),
        "rag_data_dir": str(RAG_DATA_DIR),
        "chroma_persist_dir": str(CHROMA_PERSIST_DIR)
    }
}