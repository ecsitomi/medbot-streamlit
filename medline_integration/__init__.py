# =============================================================================
# medline_integration/__init__.py
# =============================================================================
"""
Medline Plus API integráció a medical chatbot számára.

Ez a modul a következő funkcionalitásokat nyújtja:
- Medline Plus API kliens
- Egészségügyi adatok feldolgozása és rangsorolása
- Streamlit UI komponensek
- Integráció a meglévő medical chatbot rendszerrel

Használat:
    from medline_integration import medline_integration
    medline_integration.display_medline_section(diagnosis, symptoms)
"""

# Verzió információ
__version__ = "1.0.0"
__author__ = "Medical Chatbot Team"
__description__ = "Medline Plus API integráció az egészségügyi chatbot számára"

# Fő komponensek importálása
from .api_client import (
    MedlineAPIClient,
    MedlineRateLimiter,
    create_medline_client,
    test_medline_connection
)

from .data_processor import (
    MedlineDataProcessor,
    MedlineTopicSummary,
    MedlineCache,
    medline_cache
)

from .ui_components import (
    MedlineUI,
    MedlineSearchWidget,
    integrate_medline_to_medical_summary,
    add_medline_sidebar_options,
    display_medline_connection_status,
    create_medline_export_data
)

from .integration import (
    MedlineIntegration,
    medline_integration,
    initialize_medline_integration,
    integrate_medline_to_medical_summary_wrapper,
    add_medline_to_export_data,
    display_medline_search_page,
    get_medline_integration_status,
    debug_medline_integration,
    clear_medline_cache
)

# Publikus API
__all__ = [
    # Fő integráció
    'medline_integration',
    'initialize_medline_integration',
    
    # Integráció függvények
    'integrate_medline_to_medical_summary_wrapper',
    'add_medline_to_export_data',
    'display_medline_search_page',
    'get_medline_integration_status',
    
    # API kliens
    'MedlineAPIClient',
    'create_medline_client',
    'test_medline_connection',
    
    # Adatfeldolgozás
    'MedlineDataProcessor',
    'MedlineTopicSummary',
    'medline_cache',
    
    # UI komponensek
    'MedlineUI',
    'MedlineSearchWidget',
    'add_medline_sidebar_options',
    'display_medline_connection_status',
    
    # Debugging
    'debug_medline_integration',
    'clear_medline_cache',
    
    # Konstansok
    '__version__',
    '__author__',
    '__description__'
]

# =============================================================================
# Konfigurációs konstansok
# =============================================================================

# Medline API konfigurációk
MEDLINE_API_CONFIG = {
    'base_url': 'https://wsearch.nlm.nih.gov/ws/query',
    'rate_limit': 80,  # kérések per perc
    'timeout': 10,     # másodperc
    'max_retries': 3,
    'default_language': 'en',
    'supported_languages': ['en', 'es']
}

# Cache konfigurációk
CACHE_CONFIG = {
    'default_duration_hours': 24,
    'max_cache_size': 1000,
    'cleanup_interval_hours': 6
}

# UI konfigurációk
UI_CONFIG = {
    'max_topics_display': 10,
    'default_max_topics': 3,
    'relevance_threshold': 3.0,
    'summary_max_length': 1000
}

# =============================================================================
# Inicializálási ellenőrzések
# =============================================================================

def _check_dependencies():
    """Szükséges dependenciák ellenőrzése."""
    required_packages = [
        'streamlit',
        'requests',
        'xml.etree.ElementTree'  # Built-in
    ]
    
    missing_packages = []
    
    for package in required_packages:
        if package == 'xml.etree.ElementTree':
            continue  # Built-in modul
        
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        raise ImportError(f"Hiányzó dependenciák: {', '.join(missing_packages)}")

def _validate_configuration():
    """Konfiguráció validálása."""
    # API URL ellenőrzés
    if not MEDLINE_API_CONFIG['base_url'].startswith('https://'):
        raise ValueError("Medline API URL-nek HTTPS-t kell használnia")
    
    # Rate limit ellenőrzés
    if MEDLINE_API_CONFIG['rate_limit'] > 85:
        raise ValueError("Rate limit nem lehet nagyobb mint 85 kérés/perc")
    
    # Nyelvek ellenőrzés
    if MEDLINE_API_CONFIG['default_language'] not in MEDLINE_API_CONFIG['supported_languages']:
        raise ValueError("Alapértelmezett nyelv nem támogatott")

# Inicializálási ellenőrzések futtatása
try:
    _check_dependencies()
    _validate_configuration()
except Exception as e:
    import warnings
    warnings.warn(f"Medline integráció inicializálási figyelmeztetés: {e}")

# =============================================================================
# Segédfüggvények
# =============================================================================

def get_module_info():
    """Modul információk lekérése."""
    return {
        'version': __version__,
        'author': __author__,
        'description': __description__,
        'api_config': MEDLINE_API_CONFIG,
        'cache_config': CACHE_CONFIG,
        'ui_config': UI_CONFIG
    }

def reset_all_caches():
    """Összes cache törlése."""
    medline_cache.clear()

def get_health_check():
    """Medline integráció health check."""
    try:
        # Dependenciák ellenőrzés
        _check_dependencies()
        
        # Konfiguráció ellenőrzés
        _validate_configuration()
        
        # API kapcsolat teszt
        connection_ok = test_medline_connection()
        
        return {
            'status': 'healthy' if connection_ok else 'degraded',
            'dependencies': 'ok',
            'configuration': 'ok',
            'api_connection': connection_ok,
            'cache_size': len(medline_cache.cache),
            'module_version': __version__
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'module_version': __version__
        }