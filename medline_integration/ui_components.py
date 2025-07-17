# =============================================================================
# medline_integration/ui_components.py
# =============================================================================
"""
Medline információk megjelenítése a Streamlit felületen.
"""
import streamlit as st
from typing import List, Dict, Any
from .data_processor import MedlineTopicSummary, MedlineDataProcessor
from .api_client import MedlineAPIClient
import re

class MedlineUI:
    """
    Medline információk megjelenítésére szolgáló UI komponensek.
    """
    
    def __init__(self):
        self.processor = MedlineDataProcessor()
    
    def display_medline_section(self, diagnosis: str, symptoms: List[str], 
                               max_topics: int = 3, language: str = "en"):
        """
        Fő Medline szekció megjelenítése az orvosi összefoglalóban.
        
        Args:
            diagnosis (str): Diagnózis
            symptoms (List[str]): Tünetek listája
            max_topics (int): Maximum megjelenített témák száma
            language (str): Nyelv (en/es)
        """
        if not diagnosis and not symptoms:
            return
        
        st.markdown("---")
        st.markdown("### 🏥 Medline Plus - Egészségügyi Információk")
        
        # Keresési kifejezések előkészítése
        search_terms = self._prepare_search_terms(diagnosis, symptoms)
        
        if not search_terms:
            st.info("Nincs megfelelő keresési kifejezés a Medline kereséshez.")
            return
        
        # Medline adatok betöltése
        with st.spinner("Medline Plus információk betöltése..."):
            topics = self._load_medline_data(search_terms, max_topics, language)
        
        if not topics:
            st.warning("Nem találhatók releváns Medline Plus információk.")
            return
        
        # Témák megjelenítése
        self._display_topics(topics, max_topics)
        
        # Disclaimer
        self._display_disclaimer()
    
    def _prepare_search_terms(self, diagnosis: str, symptoms: List[str]) -> List[str]:
        """Keresési kifejezések előkészítése."""
        search_terms = []
        
        # Diagnózis hozzáadása
        if diagnosis:
            cleaned_diagnosis = self._clean_diagnosis(diagnosis)
            if cleaned_diagnosis:
                search_terms.append(cleaned_diagnosis)
        
        # Tünetek hozzáadása (max 3)
        for symptom in symptoms[:3]:
            if symptom and symptom.strip():
                search_terms.append(symptom.strip())
        
        return list(set(search_terms))  # Duplikátumok eltávolítása
    
    def _clean_diagnosis(self, diagnosis: str) -> str:
        """Diagnózis tisztítása kereséshez."""
        # Felesleges szavak eltávolítása
        stop_words = ['lehetséges', 'valószínű', 'esetleg', 'talán', 'lehet', 'a', 'az', 'egy']
        
        cleaned = diagnosis.lower()
        for stop_word in stop_words:
            cleaned = re.sub(rf'\b{stop_word}\b', '', cleaned)
        
        # Szóközök normalizálása
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned if len(cleaned) > 2 else ''
    
    def _load_medline_data(self, search_terms: List[str], max_topics: int, language: str) -> List[MedlineTopicSummary]:
        """Medline adatok betöltése és feldolgozása."""
        try:
            client = MedlineAPIClient(language=language)
            
            # Összes keresési kifejezés keresése
            all_results = []
            for term in search_terms:
                results = client.search_health_topics(term, max_results=5)
                all_results.extend(results)
            
            if not all_results:
                return []
            
            # Feldolgozás és rangsorolás
            topics = self.processor.process_search_results(
                all_results, 
                search_terms,  # symptoms helyett search_terms
                search_terms[0] if search_terms else ''  # diagnosis helyett első search_term
            )
            
            # Relevancia szűrés
            filtered_topics = self.processor.filter_by_relevance_threshold(topics, threshold=3.0)
            
            return filtered_topics[:max_topics]
            
        except Exception as e:
            st.error(f"Hiba a Medline adatok betöltése során: {e}")
            return []
    
    def _display_topics(self, topics: List[MedlineTopicSummary], max_topics: int):
        """Témák megjelenítése."""
        for i, topic in enumerate(topics[:max_topics]):
            with st.expander(f"📖 {topic.title}", expanded=(i == 0)):
                self._display_single_topic(topic)
    
    def _display_single_topic(self, topic: MedlineTopicSummary):
        """Egyetlen téma részletes megjelenítése."""
        # Alapinformációk
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Összefoglaló
            if topic.snippet:
                st.markdown(f"**Rövid leírás:** {topic.snippet}")
            
            # Teljes összefoglaló (ha van)
            if topic.summary and topic.summary != topic.snippet:
                with st.expander("🔍 Részletes leírás"):
                    # Összefoglaló rövidítése, ha túl hosszú
                    summary_text = topic.summary
                    if len(summary_text) > 1000:
                        summary_text = summary_text[:1000] + "..."
                    st.markdown(summary_text)
        
        with col2:
            # Relevancia pontszám
            st.metric("Relevancia", f"{topic.relevance_score:.1f}")
            
            # Medline Plus link
            if topic.url:
                st.markdown(f"🔗 [Medline Plus]({topic.url})")
        
        # Kategóriák és címkék
        if topic.groups or topic.mesh_terms or topic.alt_titles:
            st.markdown("**Kategóriák és címkék:**")
            
            # Csoportok
            if topic.groups:
                groups_text = ", ".join(topic.groups)
                st.markdown(f"📂 **Csoportok:** {groups_text}")
            
            # MeSH kifejezések
            if topic.mesh_terms:
                mesh_text = ", ".join(topic.mesh_terms)
                st.markdown(f"🏷️ **MeSH:** {mesh_text}")
            
            # Alternatív címek
            if topic.alt_titles:
                alt_titles_text = ", ".join(topic.alt_titles)
                st.markdown(f"🔄 **Alternatív címek:** {alt_titles_text}")
        
        # Kulcsinformációk kinyerése
        key_info = self.processor.extract_key_information(topic)
        self._display_key_information(key_info)
    
    def _display_key_information(self, key_info: Dict[str, Any]):
        """Kulcsinformációk megjelenítése."""
        if not any(key_info.values()):
            return
        
        st.markdown("**Kulcsinformációk:**")
        
        # Tünetek
        if key_info.get('symptoms'):
            with st.expander("🩺 Tünetek"):
                for symptom in key_info['symptoms']:
                    st.markdown(f"• {symptom}")
        
        # Okok
        if key_info.get('causes'):
            with st.expander("🔍 Lehetséges okok"):
                for cause in key_info['causes']:
                    st.markdown(f"• {cause}")
        
        # Kezelések
        if key_info.get('treatments'):
            with st.expander("💊 Kezelések"):
                for treatment in key_info['treatments']:
                    st.markdown(f"• {treatment}")
        
        # Megelőzés
        if key_info.get('prevention'):
            with st.expander("🛡️ Megelőzés"):
                for prevention in key_info['prevention']:
                    st.markdown(f"• {prevention}")
        
        # Mikor kell orvoshoz fordulni
        if key_info.get('when_to_see_doctor'):
            with st.expander("⚠️ Mikor kell orvoshoz fordulni"):
                for advice in key_info['when_to_see_doctor']:
                    st.markdown(f"• {advice}")
    
    def _display_disclaimer(self):
        """Jogi disclaimer megjelenítése."""
        st.markdown("---")
        st.info("""
        **📚 Medline Plus információk:** 
        A fenti információk a Medline Plus adatbázisából származnak, 
        amely az Amerikai Nemzeti Egészségügyi Könyvtár (NLM) szolgáltatása. 
        Ezek az információk kizárólag tájékoztató jellegűek és nem helyettesítik 
        a szakorvosi konzultációt.
        """)

# =============================================================================
# Kiegészítő UI komponensek
# =============================================================================

class MedlineSearchWidget:
    """
    Interaktív Medline keresés widget.
    """
    
    def __init__(self):
        self.client = MedlineAPIClient()
        self.processor = MedlineDataProcessor()
    
    def display_search_interface(self):
        """Keresési interfész megjelenítése."""
        st.markdown("### 🔍 Medline Plus Keresés")
        
        # Keresési forma
        with st.form("medline_search_form"):
            search_term = st.text_input(
                "Keresési kifejezés:", 
                placeholder="pl. fejfájás, migraine, headache"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                max_results = st.selectbox("Eredmények száma:", [3, 5, 10], index=0)
            with col2:
                language = st.selectbox("Nyelv:", [("Angol", "en"), ("Spanyol", "es")], index=0)
            
            submitted = st.form_submit_button("🔍 Keresés")
        
        if submitted and search_term:
            self._perform_search(search_term, max_results, language[1])
    
    def _perform_search(self, search_term: str, max_results: int, language: str):
        """Keresés végrehajtása és eredmények megjelenítése."""
        with st.spinner("Keresés folyamatban..."):
            try:
                client = MedlineAPIClient(language=language)
                results = client.search_health_topics(search_term, max_results)
                
                if not results:
                    st.warning("Nincs találat a keresési kifejezésre.")
                    return
                
                # Eredmények feldolgozása
                topics = self.processor.process_search_results(
                    results, [search_term], search_term
                )
                
                # Eredmények megjelenítése
                st.success(f"Találatok száma: {len(topics)}")
                
                ui = MedlineUI()
                for topic in topics:
                    with st.expander(f"📖 {topic.title}"):
                        ui._display_single_topic(topic)
                        
            except Exception as e:
                st.error(f"Hiba a keresés során: {e}")

# =============================================================================
# Segédfüggvények
# =============================================================================

def display_medline_connection_status():
    """Medline kapcsolat állapotának megjelenítése."""
    try:
        from .api_client import test_medline_connection
        
        if test_medline_connection():
            st.success("✅ Medline Plus kapcsolat aktív")
        else:
            st.error("❌ Medline Plus kapcsolat nem elérhető")
    except Exception as e:
        st.error(f"❌ Medline Plus kapcsolat hiba: {e}")

def create_medline_export_data(topics: List[MedlineTopicSummary]) -> Dict[str, Any]:
    """Medline adatok exportálási formátumba alakítása."""
    export_data = {
        'medline_topics': [topic.to_dict() for topic in topics],
        'total_topics': len(topics),
        'average_relevance': sum(topic.relevance_score for topic in topics) / len(topics) if topics else 0,
        'top_relevance': max(topic.relevance_score for topic in topics) if topics else 0
    }
    
    return export_data

# =============================================================================
# Medline integráció a meglévő medical_summary.py-ba
# =============================================================================

def integrate_medline_to_medical_summary(diagnosis: str, symptoms: List[str]):
    """
    Medline szekció integrálása a meglévő medical_summary.py-ba.
    
    Ezt a függvényt hívd meg a display_medical_summary() végén.
    """
    # Ellenőrizzük, hogy van-e diagnosis vagy symptoms
    if not diagnosis and not symptoms:
        return
    
    # Medline UI létrehozása és megjelenítése
    medline_ui = MedlineUI()
    medline_ui.display_medline_section(diagnosis, symptoms)

# =============================================================================
# Streamlit sidebar integráció
# =============================================================================

def add_medline_sidebar_options():
    """Medline opciók hozzáadása a sidebar-hoz."""
    with st.sidebar:
        # Teljes Medline szekció egy expander-ben
        with st.expander("🏥 Medline Plus Keresés"):
            # Kapcsolat állapot
            display_medline_connection_status()
            
            # Medline keresés engedélyezése
            enable_medline = st.checkbox("Medline Plus keresés engedélyezése", value=True)
            
            if enable_medline:
                st.markdown("**⚙️ Keresési beállítások:**")
                
                max_topics = st.slider("Maximum témák száma:", 1, 10, 3)
                language = st.selectbox("Keresési nyelv:", [("Angol", "en"), ("Spanyol", "es")], index=0)
                relevance_threshold = st.slider("Relevancia küszöb:", 1.0, 10.0, 3.0, 0.5)
                cache_enabled = st.checkbox("Cache engedélyezése", value=True)
                
                # Beállítások mentése session state-be
                st.session_state.medline_enabled = True
                st.session_state.medline_max_topics = max_topics
                st.session_state.medline_language = language[1]
                st.session_state.medline_relevance_threshold = relevance_threshold
                st.session_state.medline_cache_enabled = cache_enabled
            else:
                st.session_state.medline_enabled = False