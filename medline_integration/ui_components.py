# =============================================================================
# medline_integration/ui_components.py - MODERNIZÁLT VERZIÓ
# =============================================================================
"""
Medline információk megjelenítése modern, kártya alapú designnal
"""
import streamlit as st
from typing import List, Dict, Any
from .data_processor import MedlineTopicSummary, MedlineDataProcessor
from .api_client import MedlineAPIClient
import re

class MedlineUI:
    """
    Modern Medline UI komponensek kártya alapú megjelenítéssel
    """
    
    def __init__(self):
        self.processor = MedlineDataProcessor()
        # Színpaletta a relevancia szintekhez
        self.relevance_colors = {
            'high': '🟢',
            'medium': '🟡', 
            'low': '🔴'
        }
        # Kategória ikonok
        self.category_icons = {
            'symptoms': '🩺',
            'causes': '🔍',
            'treatments': '💊',
            'prevention': '🛡️',
            'when_to_see_doctor': '⚠️'
        }
    
    def display_medline_section(self, diagnosis: str, symptoms: List[str], 
                               max_topics: int = 3, language: str = "en"):
        """
        Modern Medline szekció megjelenítése kártya alapú layouttal
        """
        if not diagnosis and not symptoms:
            return
        
        # Modern fejléc gradiens háttér szimulációval
        st.markdown("""
            <style>
            .medline-header {
                padding: 1rem;
                border-radius: 10px;
                margin-bottom: 1rem;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # Főcím modern stílussal
        st.markdown("## 🏥 **Medline Plus** Egészségügyi Könyvtár")
        st.caption(f"🏛️ Forrás: National Library of Medicine")
              
        search_terms = self._prepare_search_terms(diagnosis, symptoms)
        topics = self._load_medline_data(search_terms, max_topics, language)
    
        if not topics:
            st.error("❌ Nem találhatók releváns Medline Plus információk.")
            return
        
        # Modern témakártyák megjelenítése
        self._display_modern_topic_cards(topics, max_topics)
        
        # Találatok összefoglaló kártya
        self._display_results_summary(topics, max_topics)

        # Keresési információ modern kártyán  
        if search_terms:
            st.info(f"🔍 **Keresési kulcsszavak:** {' • '.join(search_terms)}")

        # Modern disclaimer
        self._display_modern_disclaimer()
    
    def _display_results_summary(self, topics: List[MedlineTopicSummary], max_topics: int):
        """Találatok összefoglaló kártya"""
        st.markdown("---")
        avg_relevance = sum(t.relevance_score for t in topics[:max_topics]) / min(len(topics), max_topics)
        
        # Összefoglaló metrikák
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "📚 Találatok", 
                f"{min(len(topics), max_topics)} témakör",
                delta=f"összesen {len(topics)}"
            )
        
        with col2:
            relevance_icon = self._get_relevance_icon(avg_relevance)
            st.metric(
                "📊 Átlag relevancia",
                f"{avg_relevance:.1f}",
                delta=f"{relevance_icon} szint"
            )
        
        with col3:
            top_score = max(t.relevance_score for t in topics[:max_topics])
            st.metric(
                "🎯 Legjobb egyezés",
                f"{top_score:.1f}",
                delta="pont"
            )   
    
    def _display_modern_topic_cards(self, topics: List[MedlineTopicSummary], max_topics: int):
        """Modern kártya alapú témamegjelenítés - 3 oszlopos grid elrendezésben"""
        
        # Grid elrendezés - 3 oszlop
        num_cols = 3
        topics_to_display = topics[:max_topics]
        num_topics = len(topics_to_display)
        
        # Sorok számának kiszámítása
        num_rows = (num_topics + num_cols - 1) // num_cols
        
        # Grid létrehozása és feltöltése
        for row in range(num_rows):
            cols = st.columns(num_cols)
            
            for col_idx in range(num_cols):
                topic_idx = row * num_cols + col_idx
                
                # Ha van még megjelenítendő topic
                if topic_idx < num_topics:
                    topic = topics_to_display[topic_idx]
                    i = topic_idx + 1
                    
                    with cols[col_idx]:
                        # Az eredeti kód kártya tartalma
                        relevance_level = self._get_relevance_level(topic.relevance_score)
                        relevance_color = self._get_relevance_color_hex(relevance_level)
                        
                        st.markdown("---")
                        
                        # Címsor
                        st.markdown(f"### 📖 {i}. {topic.title}")
                        
                        # Link gomb
                        if topic.url:
                            st.link_button("🔗", topic.url, help="Medline Plus oldal megnyitása")
                        
                        # Rövid összefoglaló elegáns dobozban
                        if topic.snippet:
                            st.markdown(f"""
                                <div style="
                                    background-color: rgba(240, 240, 240, 0.3);
                                    padding: 12px;
                                    border-radius: 8px;
                                    margin: 10px 0;
                                    font-style: italic;
                                ">
                                📝 {topic.snippet}
                                </div>
                            """, unsafe_allow_html=True)
                        
                        # Modern részletek megjelenítés tabs használatával
                        if topic.summary or topic.groups or topic.mesh_terms:
                            with st.expander(f"🔍 További információk", expanded=False):
                                self._display_modern_topic_details(topic)
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        # Margó a kártyák között
                        st.markdown("<br>", unsafe_allow_html=True)
                        '''
    def _display_modern_topic_cards(self, topics: List[MedlineTopicSummary], max_topics: int):
        """Modern kártya alapú témamegjelenítés"""
        
        for i, topic in enumerate(topics[:max_topics], 1):
            # Kártya container színes kerettel
            relevance_level = self._get_relevance_level(topic.relevance_score)
            relevance_color = self._get_relevance_color_hex(relevance_level)
        
            st.markdown("---")
            # Kártya fejléc
            header_col1, header_col2, header_col3 = st.columns([6, 2, 1])
            
            with header_col1:
                st.markdown(f"### 📖 {i}. {topic.title}")
                
            with header_col2:
                pass
            
            with header_col3:
                if topic.url:
                    st.link_button("🔗", topic.url, help="Medline Plus oldal megnyitása")
            
            # Rövid összefoglaló elegáns dobozban
            if topic.snippet:
                st.markdown(f"""
                    <div style="
                        background-color: rgba(240, 240, 240, 0.3);
                        padding: 12px;
                        border-radius: 8px;
                        margin: 10px 0;
                        font-style: italic;
                    ">
                    📝 {topic.snippet}
                    </div>
                """, unsafe_allow_html=True)
            
            # Modern részletek megjelenítés tabs használatával
            if topic.summary or topic.groups or topic.mesh_terms:
                with st.expander(f"🔍 További információk", expanded=False):
                    self._display_modern_topic_details(topic)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Szeparátor következő kártyáig
            if i < min(len(topics), max_topics):
                st.markdown("<br>", unsafe_allow_html=True)
    '''
    def _display_modern_topic_details(self, topic: MedlineTopicSummary):
        """Modern részletek megjelenítés tabokkal"""
        
        # Tab-ok a különböző információkhoz
        detail_tabs = []
        tab_contents = []
        
        # Dinamikusan építjük a tab listát
        if topic.summary and topic.summary != topic.snippet:
            detail_tabs.append("📄 Leírás")
            tab_contents.append('summary')
        
        key_info = self.processor.extract_key_information(topic)
        if any(key_info.values()):
            detail_tabs.append("💡 Kulcsinfók")
            tab_contents.append('key_info')
        
        if topic.groups or topic.mesh_terms or topic.alt_titles:
            detail_tabs.append("🏷️ Címkék")
            tab_contents.append('tags')
        
        if detail_tabs:
            tabs = st.tabs(detail_tabs)
            
            for tab, content_type in zip(tabs, tab_contents):
                with tab:
                    if content_type == 'summary':
                        # Összefoglaló szép formázással
                        summary_text = topic.summary[:1500] + "..." if len(topic.summary) > 1500 else topic.summary
                        st.markdown(f"""
                            <div style="
                                padding: 15px;
                                background: rgba(250, 250, 250, 0.5);
                                border-radius: 8px;
                                line-height: 1.6;
                            ">
                            {summary_text}
                            </div>
                        """, unsafe_allow_html=True)
                    
                    elif content_type == 'key_info':
                        self._display_key_info_cards(key_info)
                    
                    elif content_type == 'tags':
                        self._display_tags_modern(topic)
    
    def _display_key_info_cards(self, key_info: Dict[str, Any]):
        """Kulcsinformációk modern kártya elrendezésben"""
        
        # 2 oszlopos elrendezés a kulcsinfóknak
        col1, col2 = st.columns(2)
        
        info_sections = [
            ('symptoms', 'Tünetek', col1),
            ('causes', 'Lehetséges okok', col2),
            ('treatments', 'Kezelések', col1),
            ('prevention', 'Megelőzés', col2),
            ('when_to_see_doctor', 'Orvoshoz fordulás', col1)
        ]
        
        for key, title, column in info_sections:
            if key_info.get(key):
                with column:
                    icon = self.category_icons.get(key, '📌')
                    st.markdown(f"**{icon} {title}**")
                    
                    # Modern lista megjelenítés
                    for item in key_info[key]:
                        st.markdown(f"""
                            <div style="
                                margin-left: 20px;
                                padding: 5px;
                                border-left: 2px solid #e0e0e0;
                                padding-left: 10px;
                                margin-bottom: 5px;
                            ">
                            • {item}
                            </div>
                        """, unsafe_allow_html=True)
                    st.markdown("")
    
    def _display_tags_modern(self, topic: MedlineTopicSummary):
        """Modern címke megjelenítés"""
        
        # Csoportok badge-ekkel
        if topic.groups:
            st.markdown("**📂 Kategóriák**")
            cols = st.columns(min(len(topic.groups), 3))
            for i, group in enumerate(topic.groups):
                with cols[i % 3]:
                    st.markdown(f"""
                        <span style="
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                            padding: 5px 10px;
                            border-radius: 15px;
                            font-size: 0.9em;
                            display: inline-block;
                            margin: 2px;
                        ">
                        {group}
                        </span>
                    """, unsafe_allow_html=True)
        
        # MeSH kifejezések modern chip-ekkel
        if topic.mesh_terms:
            st.markdown("**🏷️ MeSH címkék**")
            # Chip-szerű megjelenítés
            mesh_html = " ".join([
                f"""<span style="
                    background-color: #e3f2fd;
                    color: #1976d2;
                    padding: 4px 8px;
                    border-radius: 12px;
                    font-size: 0.85em;
                    display: inline-block;
                    margin: 2px;
                    border: 1px solid #90caf9;
                ">{term}</span>"""
                for term in topic.mesh_terms
            ])
            st.markdown(mesh_html, unsafe_allow_html=True)
        
        # Alternatív címek
        if topic.alt_titles:
            st.markdown("**🔄 Alternatív elnevezések**")
            for alt_title in topic.alt_titles:
                st.caption(f"• {alt_title}")
    
    def _display_relevance_indicator(self, score: float):
        """Vizuális relevancia indikátor progress bar-ral"""
        level = self._get_relevance_level(score)
        icon = self.relevance_colors[level]
        
        # Progress bar a relevanciához - pontszám 0-100 között van, normalizáljuk 0-1 közé
        progress_value = min(score / 100.0, 1.0)  # Biztosítjuk hogy max 1.0 legyen
        
        # Színkódolt progress - pontszámot 100-as skálán jelenítjük meg
        if level == 'high':
            st.success(f"{icon} Magas relevancia")
            st.progress(progress_value, text=f"{score:.1f}/100")
        elif level == 'medium':
            st.warning(f"{icon} Közepes relevancia")
            st.progress(progress_value, text=f"{score:.1f}/100")
        else:
            st.error(f"{icon} Alacsony relevancia")
            st.progress(progress_value, text=f"{score:.1f}/100")
    
    def _get_relevance_level(self, score: float) -> str:
        """Relevancia szint meghatározása - a pontszámok tipikusan 0-30 között vannak"""
        if score >= 15:  # Top releváns találatok
            return 'high'
        elif score >= 7:  # Közepesen releváns
            return 'medium'
        else:  # Kevésbé releváns
            return 'low'
    
    def _get_relevance_icon(self, score: float) -> str:
        """Relevancia ikon lekérése"""
        level = self._get_relevance_level(score)
        return self.relevance_colors[level]
    
    def _get_relevance_color_hex(self, level: str) -> str:
        """Relevancia szín hex kódja"""
        colors = {
            'high': '#4caf50',
            'medium': '#ff9800',
            'low': '#f44336'
        }
        return colors.get(level, '#9e9e9e')
    
    def _display_modern_disclaimer(self):
        """Modern disclaimer dizájnnal"""
        st.markdown("<br>", unsafe_allow_html=True)
        
        with st.container():
            st.markdown("""
                <div style="
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 10px;
                    text-align: center;
                ">
                    <h4>📚 Medline Plus Információk</h4>
                    <p style="margin: 10px 0;">
                        A fenti információk az Amerikai Nemzeti Egészségügyi Könyvtár (NLM) 
                        Medline Plus adatbázisából származnak.
                    </p>
                    <p style="margin: 10px 0; font-weight: bold;">
                        ⚠️ Fontos: Ezek az információk kizárólag tájékoztató jellegűek 
                        és nem helyettesítik a szakorvosi konzultációt.
                    </p>
                </div>
            """, unsafe_allow_html=True)
    
    # ✅ Meglévő helper metódusok változatlanul
    def _prepare_search_terms(self, diagnosis: str, symptoms: List[str]) -> List[str]:
        """Keresési kifejezések előkészítése - VÁLTOZATLAN"""
        search_terms = []
        
        if diagnosis:
            cleaned_diagnosis = self._clean_diagnosis(diagnosis)
            if cleaned_diagnosis:
                search_terms.append(cleaned_diagnosis)
        
        for symptom in symptoms[:3]:
            if symptom and symptom.strip():
                search_terms.append(symptom.strip())
        
        return list(set(search_terms))
    
    def _clean_diagnosis(self, diagnosis: str) -> str:
        """Diagnózis tisztítása kereséshez - VÁLTOZATLAN"""
        stop_words = ['lehetséges', 'valószínű', 'esetleg', 'talán', 'lehet', 'a', 'az', 'egy']
        
        cleaned = diagnosis.lower()
        for stop_word in stop_words:
            cleaned = re.sub(rf'\b{stop_word}\b', '', cleaned)
        
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned if len(cleaned) > 2 else ''
    
    def _load_medline_data(self, search_terms: List[str], max_topics: int, language: str) -> List[MedlineTopicSummary]:
        """Medline adatok betöltése és feldolgozása - VÁLTOZATLAN"""
        try:
            client = MedlineAPIClient(language=language)
            
            all_results = []
            for term in search_terms:
                results = client.search_health_topics(term, max_results=5)
                all_results.extend(results)
            
            if not all_results:
                return []
            
            topics = self.processor.process_search_results(
                all_results, 
                search_terms,
                search_terms[0] if search_terms else ''
            )
            
            filtered_topics = self.processor.filter_by_relevance_threshold(topics, threshold=3.0)
            
            return filtered_topics[:max_topics]
            
        except Exception as e:
            st.error(f"Hiba a Medline adatok betöltése során: {e}")
            return []

# =============================================================================
# Modernizált Kereső Widget
# =============================================================================

class MedlineSearchWidget:
    """
    Modern interaktív Medline keresés widget
    """
    
    def __init__(self):
        self.client = MedlineAPIClient()
        self.processor = MedlineDataProcessor()
    
    def display_search_interface(self):
        """Modern keresési interfész"""
        
        # Modern fejléc gradiens háttérrel
        st.markdown("""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                text-align: center;
            ">
                <h2>🔍 Medline Plus Keresés</h2>
                <p>Keress az egészségügyi információk tárházában</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Modern keresési forma
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                search_term = st.text_input(
                    "🔎 Mit keresel?",
                    placeholder="pl. fejfájás, migraine, diabetes...",
                    label_visibility="collapsed"
                )
            
            with col2:
                search_clicked = st.button("🚀 Keresés", type="primary", use_container_width=True)
        
        # Keresési opciók modern togglekkel
        with st.expander("⚙️ Keresési beállítások", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                max_results = st.select_slider(
                    "Találatok száma:",
                    options=[3, 5, 10, 15],
                    value=5
                )
            
            with col2:
                language = st.radio(
                    "Nyelv:",
                    options=[("en", "🇺🇸 Angol"), ("es", "🇪🇸 Spanyol")],
                    format_func=lambda x: x[1],
                    horizontal=True
                )
            
            with col3:
                sort_by = st.selectbox(
                    "Rendezés:",
                    ["Relevancia", "Dátum", "Forrás"]
                )
        
        # Keresés végrehajtása
        if search_clicked and search_term:
            self._perform_modern_search(search_term, max_results, language[0])
    
    def _perform_modern_search(self, search_term: str, max_results: int, language: str):
        """Modern keresés végrehajtása"""
        
        # Betöltés animáció
        with st.spinner(f"🔄 Keresés: '{search_term}'..."):
            try:
                client = MedlineAPIClient(language=language)
                results = client.search_health_topics(search_term, max_results)
                
                if not results:
                    st.warning("😔 Nincs találat a keresési kifejezésre.")
                    return
                
                topics = self.processor.process_search_results(
                    results, [search_term], search_term
                )
                
                # Találatok összefoglaló
                st.success(f"✅ {len(topics)} találat a következőre: **{search_term}**")
                
                # Modern eredmények megjelenítése
                ui = MedlineUI()
                ui._display_modern_topic_cards(topics, len(topics))
                        
            except Exception as e:
                st.error(f"❌ Hiba a keresés során: {e}")

# =============================================================================
# Modernizált segédfüggvények
# =============================================================================

def add_medline_sidebar_options():
    """Modern Medline opciók a sidebar-ban"""
    with st.sidebar:
        st.markdown("""
            <div style="
                background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
                color: white;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 15px;
                text-align: center;
            ">
                <h3>🏥 Medline Plus</h3>
            </div>
        """, unsafe_allow_html=True)
        
        # Kapcsolat állapot modern indikátorral
        display_medline_connection_status()
        
        # Modern toggle switch
        enable_medline = st.toggle(
            "Medline keresés aktiválása",
            value=st.session_state.get('medline_enabled', True),
            key="medline_toggle"
        )
        
        if enable_medline:
            st.markdown("### ⚙️ Beállítások")
            
            # Modern slider
            max_topics = st.slider(
                "📚 Max témák",
                min_value=1,
                max_value=10,
                value=3,
                help="Maximálisan megjelenített témák száma"
            )
            
            # Modern select
            language = st.selectbox(
                "🌐 Nyelv",
                options=[("en", "🇺🇸 Angol"), ("es", "🇪🇸 Spanyol")],
                format_func=lambda x: x[1],
                index=0
            )
            
            # Relevancia vizualizáció
            relevance_threshold = st.slider(
                "🎯 Relevancia szűrő",
                min_value=1.0,
                max_value=30.0,
                value=3.0,
                step=1.0,
                help="Minimum relevancia pontszám (tipikus értékek: 3-25)"
            )
            
            # Modern checkbox
            cache_enabled = st.checkbox(
                "💾 Gyorsítótár használata",
                value=True,
                help="Gyorsabb betöltés ismételt kereséseknél"
            )
            
            # Beállítások mentése
            st.session_state.medline_enabled = True
            st.session_state.medline_max_topics = max_topics
            st.session_state.medline_language = language[0]
            st.session_state.medline_relevance_threshold = relevance_threshold
            st.session_state.medline_cache_enabled = cache_enabled
        else:
            st.session_state.medline_enabled = False

def display_medline_connection_status():
    """Modern kapcsolat státusz megjelenítése"""
    try:
        from .api_client import test_medline_connection
        
        if test_medline_connection():
            st.markdown("""
                <div style="
                    background-color: #d4edda;
                    color: #155724;
                    padding: 10px;
                    border-radius: 5px;
                    border: 1px solid #c3e6cb;
                    margin-bottom: 10px;
                ">
                    ✅ <strong>Kapcsolat aktív</strong>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="
                    background-color: #f8d7da;
                    color: #721c24;
                    padding: 10px;
                    border-radius: 5px;
                    border: 1px solid #f5c6cb;
                    margin-bottom: 10px;
                ">
                    ❌ <strong>Kapcsolat nem elérhető</strong>
                </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"❌ Kapcsolat hiba: {e}")

# ✅ Többi függvény változatlan
def create_medline_export_data(topics: List[MedlineTopicSummary]) -> Dict[str, Any]:
    """Medline adatok exportálási formátumba alakítása - VÁLTOZATLAN"""
    export_data = {
        'medline_topics': [topic.to_dict() for topic in topics],
        'total_topics': len(topics),
        'average_relevance': sum(topic.relevance_score for topic in topics) / len(topics) if topics else 0,
        'top_relevance': max(topic.relevance_score for topic in topics) if topics else 0
    }
    
    return export_data

def integrate_medline_to_medical_summary(diagnosis: str, symptoms: List[str]):
    """Medline szekció integrálása - VÁLTOZATLAN"""
    if not diagnosis and not symptoms:
        return
    
    medline_ui = MedlineUI()
    medline_ui.display_medline_section(diagnosis, symptoms)