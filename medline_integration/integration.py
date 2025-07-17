# =============================================================================
# medline_integration/integration.py
# =============================================================================
"""
Medline Plus integráció a meglévő medical chatbot rendszerbe.
Ez a fájl köti össze a Medline funkcionalitást a meglévő modulokkal.
"""
import streamlit as st
from typing import List, Dict, Any, Optional
from .api_client import MedlineAPIClient, create_medline_client, test_medline_connection
from .data_processor import MedlineDataProcessor, MedlineTopicSummary, medline_cache
from .ui_components import MedlineUI, MedlineSearchWidget, integrate_medline_to_medical_summary

class MedlineIntegration:
    """
    Medline Plus integráció központi osztálya.
    Kezeli a Medline funkciók integrálását a medical chatbot-ba.
    """
    
    def __init__(self):
        self.client = None
        self.processor = MedlineDataProcessor()
        self.ui = MedlineUI()
        self.search_widget = MedlineSearchWidget()
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Medline-specifikus session state inicializálása."""
        if 'medline_enabled' not in st.session_state:
            st.session_state.medline_enabled = True
        
        if 'medline_max_topics' not in st.session_state:
            st.session_state.medline_max_topics = 3
        
        if 'medline_language' not in st.session_state:
            st.session_state.medline_language = 'en'
        
        if 'medline_topics' not in st.session_state:
            st.session_state.medline_topics = []
        
        if 'medline_last_search_terms' not in st.session_state:
            st.session_state.medline_last_search_terms = []
    
    def initialize_client(self, language: str = None) -> bool:
        """
        Medline API kliens inicializálása.
        
        Args:
            language (str): Nyelv kódja (en/es)
            
        Returns:
            bool: Sikerült-e inicializálni
        """
        try:
            if language is None:
                language = st.session_state.get('medline_language', 'en')
            
            self.client = create_medline_client(language)
            return True
            
        except Exception as e:
            st.error(f"Medline kliens inicializálási hiba: {e}")
            return False
    
    def is_medline_enabled(self) -> bool:
        """Ellenőrzi, hogy a Medline funkció engedélyezve van-e."""
        return st.session_state.get('medline_enabled', True)
    
    def should_fetch_medline_data(self, diagnosis: str, symptoms: List[str]) -> bool:
        """
        Eldönti, hogy szükséges-e Medline adatok lekérése.
        
        Args:
            diagnosis (str): Diagnózis
            symptoms (List[str]): Tünetek listája
            
        Returns:
            bool: Szükséges-e a lekérés
        """
        if not self.is_medline_enabled():
            return False
        
        if not diagnosis and not symptoms:
            return False
        
        # Ellenőrizzük, hogy változtak-e a keresési kifejezések
        current_search_terms = self._prepare_search_terms(diagnosis, symptoms)
        last_search_terms = st.session_state.get('medline_last_search_terms', [])
        
        return current_search_terms != last_search_terms
    
    def _prepare_search_terms(self, diagnosis: str, symptoms: List[str]) -> List[str]:
        """Keresési kifejezések előkészítése."""
        search_terms = []
        
        if diagnosis:
            search_terms.append(diagnosis.strip())
        
        for symptom in symptoms[:3]:  # Max 3 tünet
            if symptom and symptom.strip():
                search_terms.append(symptom.strip())
        
        return sorted(list(set(search_terms)))  # Duplikátumok eltávolítása és rendezés
    
    def fetch_and_process_medline_data(self, diagnosis: str, symptoms: List[str]) -> List[MedlineTopicSummary]:
        """
        Medline adatok lekérése és feldolgozása.
        
        Args:
            diagnosis (str): Diagnózis
            symptoms (List[str]): Tünetek listája
            
        Returns:
            List[MedlineTopicSummary]: Feldolgozott témák
        """
        if not self.should_fetch_medline_data(diagnosis, symptoms):
            return st.session_state.get('medline_topics', [])
        
        # Kliens inicializálása
        if not self.client:
            if not self.initialize_client():
                return []
        
        search_terms = self._prepare_search_terms(diagnosis, symptoms)
        max_topics = st.session_state.get('medline_max_topics', 3)
        
        try:
            # Cache ellenőrzés
            cache_key = f"{'-'.join(search_terms)}-{max_topics}"
            cached_results = medline_cache.get(cache_key)
            
            if cached_results:
                topics = self.processor.process_search_results(
                    cached_results, symptoms, diagnosis
                )
            else:
                # Új keresés
                all_results = []
                for term in search_terms:
                    results = self.client.search_health_topics(term, max_results=5)
                    all_results.extend(results)
                
                if all_results:
                    # Cache-be mentés
                    medline_cache.set(cache_key, all_results)
                    
                    # Feldolgozás
                    topics = self.processor.process_search_results(
                        all_results, symptoms, diagnosis
                    )
                else:
                    topics = []
            
            # Relevancia szűrés
            filtered_topics = self.processor.filter_by_relevance_threshold(topics, threshold=3.0)
            final_topics = filtered_topics[:max_topics]
            
            # Session state frissítése
            st.session_state.medline_topics = final_topics
            st.session_state.medline_last_search_terms = search_terms
            
            return final_topics
            
        except Exception as e:
            st.error(f"Medline adatok lekérési hiba: {e}")
            return []
    
    def display_medline_section(self, diagnosis: str, symptoms: List[str]):
        """
        Medline szekció megjelenítése.
        
        Args:
            diagnosis (str): Diagnózis
            symptoms (List[str]): Tünetek listája
        """
        if not self.is_medline_enabled():
            return
        
        topics = self.fetch_and_process_medline_data(diagnosis, symptoms)
        
        if topics:
            self.ui.display_medline_section(
                diagnosis, 
                symptoms, 
                max_topics=st.session_state.get('medline_max_topics', 3),
                language=st.session_state.get('medline_language', 'en')
            )
    
    def add_to_export_data(self, export_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Medline adatok hozzáadása az exportálási adatokhoz.
        
        Args:
            export_data (Dict): Meglévő export adatok
            
        Returns:
            Dict: Kibővített export adatok
        """
        if not self.is_medline_enabled():
            return export_data
        
        topics = st.session_state.get('medline_topics', [])
        
        if topics:
            from .ui_components import create_medline_export_data
            medline_export = create_medline_export_data(topics)
            export_data['medline_plus'] = medline_export
        
        return export_data
    
    def add_sidebar_options(self):
        """Medline opciók hozzáadása a sidebar-hoz."""
        from .ui_components import add_medline_sidebar_options
        add_medline_sidebar_options()
    
    def display_search_widget(self):
        """Medline keresési widget megjelenítése."""
        self.search_widget.display_search_interface()
    
    def get_medline_status(self) -> Dict[str, Any]:
        """
        Medline integráció státuszának lekérése.
        
        Returns:
            Dict: Státusz információk
        """
        return {
            'enabled': self.is_medline_enabled(),
            'client_initialized': self.client is not None,
            'connection_test': test_medline_connection(),
            'cached_topics_count': len(st.session_state.get('medline_topics', [])),
            'last_search_terms': st.session_state.get('medline_last_search_terms', []),
            'settings': {
                'max_topics': st.session_state.get('medline_max_topics', 3),
                'language': st.session_state.get('medline_language', 'en')
            }
        }

# =============================================================================
# Globális Medline integráció példány
# =============================================================================

# Egyetlen globális példány a teljes alkalmazásban
medline_integration = MedlineIntegration()

# =============================================================================
# Integrációs függvények a meglévő kódhoz
# =============================================================================

def initialize_medline_integration():
    """
    Medline integráció inicializálása az alkalmazás indításakor.
    Hívd meg ezt a main.py-ban, a configure_streamlit() után.
    """
    global medline_integration
    
    # Kliens inicializálása
    medline_integration.initialize_client()
    
    # Sidebar opciók hozzáadása
    medline_integration.add_sidebar_options()

def integrate_medline_to_medical_summary_wrapper(diagnosis: str, symptoms: List[str]):
    """
    Wrapper függvény a medical_summary.py integrálásához.
    Hívd meg ezt a display_medical_summary() végén.
    """
    global medline_integration
    
    try:
        medline_integration.display_medline_section(diagnosis, symptoms)
    except Exception as e:
        st.error(f"Medline integráció hiba: {e}")

def add_medline_to_export_data(export_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Medline adatok hozzáadása az exportálási adatokhoz.
    Hívd meg ezt a create_export_data() függvényben.
    """
    global medline_integration
    
    try:
        return medline_integration.add_to_export_data(export_data)
    except Exception as e:
        st.error(f"Medline export hiba: {e}")
        return export_data

def display_medline_search_page():
    """
    Önálló Medline keresési oldal megjelenítése.
    Használható mint külön Streamlit oldal vagy tab.
    """
    global medline_integration
    
    st.title("🏥 Medline Plus Keresés")
    
    # Státusz megjelenítése
    status = medline_integration.get_medline_status()
    if status['connection_test']:
        st.success("✅ Medline Plus kapcsolat aktív")
    else:
        st.error("❌ Medline Plus kapcsolat nem elérhető")
    
    # Keresési widget
    medline_integration.display_search_widget()

def get_medline_integration_status() -> Dict[str, Any]:
    """
    Medline integráció státuszának lekérése külső modulok számára.
    
    Returns:
        Dict: Státusz információk
    """
    global medline_integration
    return medline_integration.get_medline_status()

# =============================================================================
# Debugging és monitoring
# =============================================================================

def debug_medline_integration():
    """Debug információk a Medline integrációról."""
    global medline_integration
    
    status = medline_integration.get_medline_status()
    
    st.markdown("### 🔍 Medline Integration Debug Info")
    st.json(status)
    
    # Cache információk
    st.markdown("### 🗄️ Cache Info")
    st.write(f"Cache size: {len(medline_cache.cache)}")
    
    # Session state információk
    st.markdown("### 📊 Session State")
    medline_session_data = {
        key: value for key, value in st.session_state.items() 
        if key.startswith('medline_')
    }
    st.json(medline_session_data)

def clear_medline_cache():
    """Medline cache törlése."""
    medline_cache.clear()
    st.success("Medline cache törölve!")

# =============================================================================
# Migráció segítő függvények
# =============================================================================

def migrate_existing_medical_summary():
    """
    Segítő függvény a meglévő medical_summary.py migrálásához.
    
    Ezt add hozzá a ui/medical_summary.py display_medical_summary() végéhez:
    
    ```python
    # Medline Plus integráció
    from medline_integration.integration import integrate_medline_to_medical_summary_wrapper
    integrate_medline_to_medical_summary_wrapper(st.session_state.diagnosis, st.session_state.patient_data.get('symptoms', []))
    ```
    """
    pass

def migrate_existing_export():
    """
    Segítő függvény a meglévő export/data_formatter.py migrálásához.
    
    Ezt add hozzá a create_export_data() végéhez:
    
    ```python
    # Medline Plus adatok hozzáadása
    from medline_integration.integration import add_medline_to_export_data
    export_data = add_medline_to_export_data(export_data)
    ```
    """
    pass

def migrate_existing_main():
    """
    Segítő függvény a meglévő main.py migrálásához.
    
    Ezt add hozzá a main() függvény elejéhez:
    
    ```python
    # Medline integráció inicializálása
    from medline_integration.integration import initialize_medline_integration
    initialize_medline_integration()
    ```
    """
    pass