# =============================================================================
# medline_download/__init__.py
# =============================================================================
"""
Medline PDF letöltő modul - Medline API tartalmak PDF-be mentése
"""

__version__ = "1.0.0"
__author__ = "Medical Chatbot Team"
__description__ = "Medline Plus API tartalmak letöltése és PDF generálás"

from .download_manager import MedlineDownloadManager
from .config import MEDLINE_DOWNLOAD_CONFIG

# Fő interfész függvények
async def download_medline_pdfs(topics, patient_data=None):
    """
    Medline témák letöltése PDF-be
    
    Args:
        topics: Lista MedlineTopicSummary objektumokból
        patient_data: Opcionális beteg adatok a PDF-hez
        
    Returns:
        Dict: {
            'success': bool,
            'pdf_files': List[str],
            'errors': List[str]
        }
    """
    manager = MedlineDownloadManager()
    return await manager.download_topics_to_pdf(topics, patient_data)

def get_download_status():
    """Letöltés státuszának lekérése"""
    manager = MedlineDownloadManager()
    return manager.get_status()

__all__ = [
    'download_medline_pdfs',
    'get_download_status',
    'MedlineDownloadManager',
    'MEDLINE_DOWNLOAD_CONFIG'
]