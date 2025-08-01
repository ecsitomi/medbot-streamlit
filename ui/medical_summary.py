# =============================================================================
# ui/medical_summary.py - JAVÍTOTT VERZIÓ
# =============================================================================
"""
Orvosi összefoglaló megjelenítése.
MÓDOSÍTVA: Appointment system integráció hozzáadása - JAVÍTOTT IMPORT
"""
import streamlit as st
from logic import is_evaluation_complete
from medline_integration.integration import integrate_medline_to_medical_summary_wrapper
from appointment_system.integration import integrate_appointment_booking
from pathlib import Path
from datetime import datetime

# JAVÍTOTT IMPORT - helyes függvénynév
try:
    from appointment_system.integration import integrate_appointment_booking
except ImportError:
    # Fallback, ha az appointment system nincs telepítve
    def integrate_appointment_booking(gpt_specialist_advice, patient_data, diagnosis):
        pass

def display_medical_summary():
    """Megjeleníti az orvosi összefoglalót."""
    if not is_evaluation_complete():
        return
    
    st.markdown("---")
    st.markdown("### 📋 Orvosi Összefoglaló")
    
    # Triage értékelés
    if st.session_state.triage_level:
        st.info(f"**🏥 Elsődleges orvosi értékelés:**\n{st.session_state.triage_level}")

    # Diagnózis
    if st.session_state.diagnosis:
        st.info(f"**🔬 Lehetséges diagnózis:**\n{st.session_state.diagnosis}")

    # Kézi alternatív terápia
    if st.session_state.alt_therapy:
        st.success(f"**🌿 Kézi alternatív enyhítő javaslatok:**\n{st.session_state.alt_therapy}")

    # AI alternatív terápia
    if st.session_state.gpt_alt_therapy:
        st.success(f"**🧠 AI által javasolt alternatív enyhítés:**\n{st.session_state.gpt_alt_therapy}")

    # Szakorvos javaslat
    if st.session_state.gpt_specialist_advice:
        st.warning(f"**👨‍⚕️ Javasolt szakorvos:**\n{st.session_state.gpt_specialist_advice}")

    # Medline integráció
    integrate_medline_to_medical_summary_wrapper(
        st.session_state.diagnosis, 
        st.session_state.patient_data.get('symptoms', [])
    )

    # JAVÍTOTT: Appointment system integráció - helyes függvénynév
    integrate_appointment_booking(
        st.session_state.gpt_specialist_advice,
        st.session_state.patient_data,
        st.session_state.diagnosis
    )

    # Medline PDF letöltés opció
    if st.session_state.get('medline_topics') and len(st.session_state.medline_topics) > 0:
        st.markdown("---")
        st.markdown("### 📥 Medline Információk Letöltése")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info(f"""
            **{len(st.session_state.medline_topics)} Medline témakör érhető el letöltésre**
            
            A letöltés PDF formátumban történik, amely tartalmazza:
            - Teljes leírásokat
            - Orvosi kifejezéseket
            - Kapcsolódó információkat
            """)
        
        with col2:
            # Beállítások
            combine_pdf = st.checkbox("Egyesített PDF", value=False, 
                                    key="medline_combined_pdf")
        
        # Ellenőrizzük, hogy vannak-e már letöltött PDF-ek
        if 'medline_downloaded_pdfs' not in st.session_state:
            st.session_state.medline_downloaded_pdfs = []
        
        # Letöltés gomb
        if st.button("📥 Letöltés indítása", type="primary", key="start_medline_download"):
            # Import és letöltés
            import asyncio
            from medline_download import download_medline_pdfs
            
            # Progress bar
            progress_bar = st.progress(0.0)
            status_text = st.empty()
            
            # Async futtatás Streamlit-ben
            async def run_download():
                # Patient data előkészítése
                patient_data = {
                    'case_id': st.session_state.get('case_id', 'unknown'),
                    'diagnosis': st.session_state.get('diagnosis', ''),
                    'symptoms': st.session_state.patient_data.get('symptoms', [])
                }
                
                # Letöltés
                result = await download_medline_pdfs(
                    st.session_state.medline_topics,
                    patient_data
                )
                
                return result
            
            # Progress update (polling)
            from medline_download import get_download_status
            
            # Háttér task indítása
            with st.spinner("Medline információk letöltése..."):
                # Async loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    result = loop.run_until_complete(run_download())
                    
                    # Eredmény megjelenítése
                    if result['success']:
                        # Session state-ben tároljuk a PDF fájlokat
                        st.session_state.medline_downloaded_pdfs = result['pdf_files']
                        
                        st.success(f"""
                        ✅ **Sikeres letöltés!**
                        
                        Létrehozott PDF fájlok: {len(result['pdf_files'])}
                        """)
                        
                        # Rerun hogy megjelenjenek a letöltés gombok
                        st.rerun()
                        
                    else:
                        st.error("❌ Letöltés sikertelen!")
                        for error in result['errors']:
                            st.error(error)
                            
                finally:
                    loop.close()
        
        # PDF letöltő gombok megjelenítése (session state alapján)
        if st.session_state.get('medline_downloaded_pdfs'):
            st.markdown("---")
            st.markdown("### 📄 Letöltött PDF Fájlok")
            
            for i, pdf_file in enumerate(st.session_state.medline_downloaded_pdfs):
                pdf_path = Path("medline_data/pdfs") / pdf_file
                if pdf_path.exists():
                    try:
                        with open(pdf_path, 'rb') as f:
                            st.download_button(
                                label=f"📄 {pdf_file}",
                                data=f.read(),
                                file_name=pdf_file,
                                mime="application/pdf",
                                key=f"download_pdf_{i}_{len(pdf_file)}"  # Egyedi key
                            )
                    except Exception as e:
                        st.error(f"Hiba a fájl olvasásakor: {pdf_file} - {e}")
            
            # Reset gomb a PDF lista törléséhez
            if st.button("🗑️ PDF lista törlése", key="clear_pdf_list"):
                st.session_state.medline_downloaded_pdfs = []
                st.rerun()

    # RAG elemzés gomb
    if st.session_state.get('medline_downloaded_pdfs') and len(st.session_state.medline_downloaded_pdfs) > 0:
        st.markdown("---")
        st.markdown("### 🧠 RAG Alapú Elemzés")
        
        st.info("""
        **Mélyelemzés a letöltött Medline dokumentumok alapján**
        
        A RAG (Retrieval Augmented Generation) elemzés:
        - Feldolgozza a letöltött PDF-eket
        - Releváns információkat keres a beteg állapotához
        - Személyre szabott tanácsokat generál
        """)
        
        if st.button("🔍 RAG Elemzés indítása", type="primary", key="start_rag_analysis"):
            # RAG modul importálása
            from rag_pdf import run_rag_analysis
            
            # Patient data összegyűjtése
            patient_data_for_rag = st.session_state.patient_data.copy()
            patient_data_for_rag['diagnosis'] = st.session_state.get('diagnosis', '')
            patient_data_for_rag['case_id'] = st.session_state.get('case_id', 
                                            f"case-{datetime.now().strftime('%Y%m%d%H%M%S')}")
            
            # RAG elemzés futtatása
            rag_results = run_rag_analysis(patient_data_for_rag)
            
            # Eredmények session state-be mentése
            st.session_state['rag_analysis_results'] = rag_results   

    # PubMed elemzés (ha van RAG eredmény)
    if st.session_state.get('rag_analysis_results'):
        st.markdown("---")
        st.markdown("### 🔬 PubMed Mélykutatás")
        
        st.info("""
        **Tudományos publikációk elemzése a PubMed adatbázisból**
        
        A PubMed elemzés:
        - A világ legnagyobb orvosi publikációs adatbázisát használja
        - Evidencia-alapú kezelési javaslatokat keres
        - A legfrissebb kutatási eredményeket dolgozza fel
        """)
        
        if st.button("🔬 PubMed Elemzés indítása", type="primary", key="start_pubmed_analysis"):
            # PubMed modul importálása
            from pubmed_integration import run_pubmed_analysis
            
            # Elemzés futtatása
            pubmed_results = run_pubmed_analysis(
                patient_data=patient_data_for_rag,
                rag_results=st.session_state.get('rag_analysis_results')
            )
            
            # Eredmények session state-be mentése
            st.session_state['pubmed_analysis_results'] = pubmed_results

def display_patient_data_summary():
    """Páciens adatok összefoglalójának megjelenítése."""
    if not any(v for v in st.session_state.patient_data.values() if v):
        return
    
    data = st.session_state.patient_data
    
    with st.expander("📊 Összegyűjtött adatok", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            if data.get('age'):
                st.write(f"**Életkor:** {data['age']} év")
            if data.get('gender'):
                st.write(f"**Nem:** {data['gender']}")
            if data.get('duration'):
                st.write(f"**Időtartam:** {data['duration']}")
            if data.get('severity'):
                st.write(f"**Súlyosság:** {data['severity']}")
        
        with col2:
            if data.get('symptoms'):
                st.write(f"**Tünetek:** {', '.join(data['symptoms'])}")
            if data.get('existing_conditions'):
                st.write(f"**Betegségek:** {', '.join(data['existing_conditions'])}")
            if data.get('medications'):
                st.write(f"**Gyógyszerek:** {', '.join(data['medications'])}")

def create_medical_display():
    """Teljes orvosi megjelenítő komponens."""
    # Páciens adatok összefoglalója
    display_patient_data_summary()
    
    # Orvosi összefoglaló (csak ha kész az értékelés)
    display_medical_summary()