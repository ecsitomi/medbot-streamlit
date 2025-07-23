# =============================================================================
# medline_download/config.py
# =============================================================================
"""
Konfigurációs beállítások a Medline letöltőhöz
"""
import os
from pathlib import Path

# Alap könyvtárak
BASE_DIR = Path(__file__).parent.parent
MEDLINE_DATA_DIR = BASE_DIR / "medline_data"
CACHE_DIR = MEDLINE_DATA_DIR / "cache"
PDF_DIR = MEDLINE_DATA_DIR / "pdfs"

# Könyvtárak létrehozása
MEDLINE_DATA_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)
PDF_DIR.mkdir(exist_ok=True)

MEDLINE_DOWNLOAD_CONFIG = {
    # API beállítások
    "api": {
        "base_url": "https://wsearch.nlm.nih.gov/ws/query",
        "rate_limit": 80,  # biztonságos limit (max 85)
        "timeout": 30,
        "retries": 3,
        "tool_name": "medical_chatbot_pdf",
        "email": "ecsi.hgh@gmail.com"  
    },
    
    # PDF beállítások
    "pdf": {
        "page_size": "A4",
        "margin_cm": 2,
        "font_size_normal": 11,
        "font_size_title": 16,
        "font_size_subtitle": 14,
        "font_family": "Helvetica",
        "include_toc": True,  # tartalomjegyzék
        "include_metadata": True,
        "include_disclaimer": True
    },
    
    # Cache beállítások
    "cache": {
        "enabled": True,
        "ttl_hours": 24,
        "max_size_mb": 100
    },
    
    # Letöltés beállítások
    "download": {
        "max_concurrent": 3,  # párhuzamos letöltések
        "progress_update_interval": 0.5,  # másodperc
        "filename_pattern": "medline_{topic}_{date}.pdf"
    },
    
    # Könyvtárak
    "paths": {
        "data_dir": str(MEDLINE_DATA_DIR),
        "cache_dir": str(CACHE_DIR),
        "pdf_dir": str(PDF_DIR)
    }
}