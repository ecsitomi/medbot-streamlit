# =============================================================================
# ui/medical_summary.py 
# =============================================================================
"""
Orvosi összefoglaló megjelenítése.
"""
import streamlit as st
from logic import is_evaluation_complete
from medline_integration.integration import integrate_medline_to_medical_summary_wrapper
from appointment_system.integration import integrate_appointment_booking
from admin_page import display_data_overview, display_appointments_table
from pathlib import Path
from datetime import datetime
import re
import json

# Streamlitre kell
try:
    import pysqlite3
    import sys
    sys.modules["sqlite3"] = pysqlite3
except ImportError:
    print("⚠️ pysqlite3-binary nem elérhető – SQLite override sikertelen")

try:
    from appointment_system.integration import integrate_appointment_booking
except ImportError:
    # Fallback, ha az appointment system nincs telepítve
    def integrate_appointment_booking(gpt_specialist_advice, patient_data, diagnosis):
        pass

def display_medical_summary():
    """Tabos elrendezésű orvosi összefoglaló és kiegészítő fülek."""
    if not is_evaluation_complete(): #ITT FUT A CHAT LOGIKA, HA NINCS MEG MINDEN ADAT AKKOR CSAK KÉRDEZ, HA MEGVAN AKKOR JÖN AZ ÖSSZEGZÉS
        return

    # Előkészítő függvény a későbbi modulokhoz
    def prepare_patient_data_for_analysis():
        patient_data_for_analysis = st.session_state.patient_data.copy()
        patient_data_for_analysis['diagnosis'] = st.session_state.get('diagnosis', '')
        patient_data_for_analysis['case_id'] = st.session_state.get(
            'case_id', f"case-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
        return patient_data_for_analysis

    # Tabok definiálása
    tabs = st.tabs([
        "📋 Elemzés",
        "🧬 Medline",
        "📥 Medline PDF",
        "🧠 RAG elemzés",
        "🔬 PubMed",
        "📅 Időpontfoglalás",
        "💬 Chat",
        "📊 Foglalások"
    ])

    # --- AI Összefoglaló ---
    with tabs[0]:
        st.markdown("### 📋 AI Összefoglaló")
        # Elsődleges orvosi értékelés
        if st.session_state.get('triage_level'):
            st.info(f"**🏥 Sürgősségi értékelés:**  {st.session_state.triage_level}")
        # Diagnózis
        if st.session_state.get('diagnosis'):
            st.success(f"**🔬 Lehetséges diagnózis:**  {st.session_state.diagnosis}")
        # AI alternatív terápia
        if st.session_state.get('gpt_alt_therapy'):
            st.success(f"**🧠 Javasoltok a tünetek enyhítés:**  {st.session_state.gpt_alt_therapy}")
        # Szakorvos javaslat
        if st.session_state.get('gpt_specialist_advice'):
            st.success(f"**👨‍⚕️ Javasolt szakorvos:**  {st.session_state.gpt_specialist_advice}")
        st.markdown("---")

    # --- Medline integráció ---
    with tabs[1]:
        # Medline integráció összefoglalóba
        integrate_medline_to_medical_summary_wrapper(
            st.session_state.diagnosis,
            st.session_state.patient_data.get('symptoms', [])
        )
    
    # --- Medline PDF Letöltés ---
    with tabs[2]:
        if st.session_state.get('medline_topics') and len(st.session_state.medline_topics) > 0:
            st.markdown("---")
            st.markdown("### 📥 Medline Információk Letöltése")
            col1, col2 = st.columns([3, 1])
            with col1:
                st.info(f"**{len(st.session_state.medline_topics)} Medline témakör érhető el**\n- Teljes leírások\n- Orvosi kifejezések\n- Kapcsolódó információk")
            with col2:
                combine_pdf = st.checkbox("Egyesített PDF", value=False, key="medline_combined_pdf")

            # PDF letöltés indítása
            if st.button("📥 Letöltés indítása", type="primary", key="start_medline_download"):
                import asyncio
                from medline_download import download_medline_pdfs, get_download_status

                progress_bar = st.progress(0.0)
                status_text = st.empty()

                async def run_download():
                    patient_data = {
                        'case_id': st.session_state.get('case_id', 'unknown'),
                        'diagnosis': st.session_state.get('diagnosis', ''),
                        'symptoms': st.session_state.patient_data.get('symptoms', [])
                    }
                    return await download_medline_pdfs(st.session_state.medline_topics, patient_data)

                with st.spinner("Medline információk letöltése..."):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result = loop.run_until_complete(run_download())
                        if result['success']:
                            st.session_state.medline_downloaded_pdfs = result['pdf_files']
                            st.success(f"✅ Sikeres letöltés! {len(result['pdf_files'])} fájl.")
                            st.rerun()
                        else:
                            st.error("❌ Letöltés sikertelen!")
                            for err in result.get('errors', []):
                                st.error(err)
                    finally:
                        loop.close()
        else:
            st.warning("Először generálj Medline témaköröket az AI összefoglaló fülön.")

        # Letöltött PDF-ek listája
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
                                key=f"download_pdf_{i}"
                            )
                    except Exception as e:
                        st.error(f"Hiba fájl olvasásakor: {pdf_file} - {e}")
            if st.button("🗑️ PDF lista törlése", key="clear_pdf_list"):
                st.session_state.medline_downloaded_pdfs = []
                st.rerun()

    # --- RAG Elemzés ---
    with tabs[3]:
        if st.session_state.get('medline_downloaded_pdfs'):
            rag_results = st.session_state.get('rag_analysis_results')

            # Ha még nincs eredmény, akkor mutassuk a gombot
            if not rag_results:
                st.markdown("### 🧠 RAG Alapú Elemzés")
                st.info("Mélyelemzés a letöltött dokumentumok alapján.")
                if st.button("🔍 Elemzés indítása", type="primary", key="start_rag_analysis"):
                    from rag_pdf import run_rag_analysis
                    patient_data_for_rag = prepare_patient_data_for_analysis()
                    rag_results = run_rag_analysis(patient_data_for_rag)
                    st.session_state['rag_analysis_results'] = rag_results
                    st.rerun()

            # Ha már van eredmény, jelenítsük meg
            else:
                st.markdown("### 🧠 RAG Elemzés Eredménye")
                st.success(f"📋 {rag_results.get('patient_condition', 'Nincs információ')}")
                st.success(f"💊 {rag_results.get('symptom_management', 'Nincs információ')}")
                st.success(f"👨‍⚕️ {rag_results.get('recommended_specialist', 'Nincs információ')}")
                st.success(f"ℹ️ {rag_results.get('additional_info', 'Nincs információ')}")
                st.markdown("---")

                '''
                # Letöltési lehetőség JSON-ként
                if rag_results.get('timestamp'):
                    st.download_button(
                        label="📥 RAG JSON letöltése",
                        data=json.dumps(rag_results, ensure_ascii=False, indent=2),
                        file_name=f"{st.session_state.get('case_id','case')}_rag.json",
                        mime="application/json"
                    )
                '''
        else:
            st.warning("Előbb töltsd le a Medline PDF-eket a Medline fülön.")


    # --- PubMed Elemzés ---
    with tabs[4]:
        pubmed_results = st.session_state.get('pubmed_analysis_results')
        if not pubmed_results:
            if st.session_state.get('rag_analysis_results'):
                st.markdown("### 🔬 PubMed Mélykutatás")
                st.info("Tudományos publikációk elemzése a PubMed adatbázisból.")
                if st.button("🔬 Kutatás indítása", type="primary", key="start_pubmed_analysis"):
                    from pubmed_integration import run_pubmed_analysis
                    patient_data_for_pubmed = prepare_patient_data_for_analysis()
                    pubmed_results = run_pubmed_analysis(
                        patient_data=patient_data_for_pubmed,
                        rag_results=st.session_state.get('rag_analysis_results')
                    )
                    st.session_state['pubmed_analysis_results'] = pubmed_results
                    st.rerun()
            else:
                st.warning("Előbb futtasd a RAG elemzést a RAG fülön.")
        else:
            st.markdown("### 🧠 PubMed Kutatás Eredménye")
            st.success(f"📚 1. __Legfrissebb kutatási eredmények:__ {pubmed_results.get('research_findings', 'Nincs információ')}")
            st.success(f"💊 2. __Ajánlott kezelési módszerek:__ {pubmed_results.get('treatment_methods', 'Nincs információ')}")
            st.success(f"📋 3. __Klinikai irányelvek:__ {pubmed_results.get('clinical_guidelines', 'Nincs információ')}")
            st.success(f"📈 4. __Prognózis és kilátások:__ {pubmed_results.get('prognosis', 'Nincs információ')}")
            st.success(f"🔍 5. __További javasolt vizsgálatok:__ {pubmed_results.get('further_tests', 'Nincs információ')}")
            st.markdown("---")
            
    # --- Időpontfoglalás ---
    with tabs[5]:
        integrate_appointment_booking(
            st.session_state.gpt_specialist_advice,
            st.session_state.patient_data,
            st.session_state.diagnosis
        )

    # --- Páciens adatok és Chat előzmények ---
    with tabs[6]:
        st.markdown("### 💬 Chat Előzmények")
        if any(v for v in st.session_state.patient_data.values() if v):
            with st.expander("📊 Összegyűjtött adatok", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    data = st.session_state.patient_data
                    if data.get('age'):
                        st.write(f"**Életkor:** {data['age']} év")
                    if data.get('gender'):
                        st.write(f"**Nem:** {data['gender']}")
                    if data.get('duration'):
                        st.write(f"**Időtartam:** {data['duration']}")
                    if data.get('severity'):
                        st.write(f"**Súlyosság:** {data['severity']}\n")
                with col2:
                    if data.get('symptoms'):
                        st.write(f"**Tünetek:** {', '.join(data['symptoms'])}")
                    if data.get('existing_conditions'):
                        st.write(f"**Betegségek:** {', '.join(data['existing_conditions'])}")
                    if data.get('medications'):
                        st.write(f"**Gyógyszerek:** {', '.join(data['medications'])}")
        else:
            st.info("Nincsenek elérhető páciensek adatok még.")

        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        st.markdown("---")

    with tabs[7]:
        display_data_overview()
        display_appointments_table()


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
    # Orvosi összefoglaló (csak ha kész az értékelés)
    display_medical_summary()
