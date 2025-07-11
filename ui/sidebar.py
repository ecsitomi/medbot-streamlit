# =============================================================================
# ui/sidebar.py
# =============================================================================
"""
Sidebar komponensek és adatgyűjtés státusz.
"""
import streamlit as st
import json
from core import get_data_hash, reset_session_state
from logic import is_evaluation_complete
from export import create_export_data, generate_pdf

def create_legal_disclaimers():
    """Jogi nyilatkozatok megjelenítése."""
    with st.expander("📄 Jogi nyilatkozat", expanded=False):
        st.markdown("""
        **Fontos:** Ez az alkalmazás nem minősül orvosi tanácsadásnak. 
        Az itt megjelenített információk kizárólag tájékoztató jellegűek. 
        Tünetei alapján mindig konzultáljon egészségügyi szakemberrel.
        """)
    
    with st.expander("🔒 Adatvédelem (GDPR)", expanded=False):
        st.markdown("""
        A megadott adatokat nem tároljuk és nem továbbítjuk harmadik fél számára. 
        Az alkalmazás célja kizárólag a felhasználó önálló tájékozódásának támogatása. 
        Az adatokat kizárólag az aktuális munkamenet során, ideiglenesen használjuk fel.
        """)

def display_data_collection_status():
    """Adatgyűjtés állapotának megjelenítése."""
    # Adatok hash ellenőrzése
    current_hash = get_data_hash()
    
    # Ha van adat, akkor megjelenítjük a státuszt
    if any(v for v in st.session_state.patient_data.values() if v):
        st.markdown("### 📊 Adatgyűjtés állapota")
        data = st.session_state.patient_data
        
        # Progress tracking
        total_fields = 7
        completed_fields = 0
        
        status_map = {
            "age": "👤 Életkor",
            "gender": "👤 Nem", 
            "symptoms": "🩺 Tünetek",
            "duration": "⏰ Időtartam",
            "severity": "⚠️ Súlyosság",
            "existing_conditions": "🏥 Betegségek",
            "medications": "💊 Gyógyszerek"
        }
        
        for key, label in status_map.items():
            value = data.get(key)
            if key == "symptoms":
                symptoms_count = len(value) if value else 0
                if symptoms_count >= 2:
                    st.success(f"✅ {label}: {symptoms_count} tünet")
                    completed_fields += 1
                elif symptoms_count == 1 and st.session_state.asked_for_more_symptoms:
                    st.success(f"✅ {label}: {symptoms_count} tünet (elegendő)")
                    completed_fields += 1
                elif symptoms_count == 1:
                    st.warning(f"⏳ {label}: {symptoms_count} tünet (folyamatban)")
                else:
                    st.error(f"❌ {label}: Hiányzik")
            else:
                if value and value != "nincs":
                    st.success(f"✅ {label}")
                    completed_fields += 1
                else:
                    st.error(f"❌ {label}: Hiányzik")
        
        # Progress bar
        progress = completed_fields / total_fields
        st.progress(progress, text=f"Adatgyűjtés: {completed_fields}/{total_fields}")
        
        if completed_fields == total_fields:
            st.success("🎉 Minden adat összegyűlt! Az orvosi értékelés elkészülhet.")
    
    # Hash mentése
    st.session_state.sidebar_last_update = current_hash

def display_export_options():
    """Exportálási lehetőségek megjelenítése."""
    if is_evaluation_complete():
        st.markdown("### 📄 Exportálás")
        
        export_data = create_export_data()
        
        # JSON export
        st.download_button(
            label="📄 JSON letöltése",
            data=json.dumps(export_data, indent=2, ensure_ascii=False),
            file_name=f"{export_data['case_id']}.json",
            mime="application/json"
        )
        
        # PDF export
        pdf_data = generate_pdf(export_data)
        if pdf_data:
            st.download_button(
                label="📑 PDF letöltése",
                data=pdf_data,
                file_name=f"{export_data['case_id']}.pdf",
                mime="application/pdf"
            )

def display_reset_button():
    """Új konzultáció gomb megjelenítése."""
    if st.button("🔄 Új konzultáció"):
        reset_session_state()
        st.session_state.patient_data = {
            "age": None,
            "gender": None,
            "symptoms": [],  # <-- Ez volt a probléma!
            "duration": None,
            "severity": None,
            "existing_conditions": [],
            "medications": []
        }
        #st.session_state.chat_history = [get_welcome_message()]
        st.session_state.triage_level = ""
        st.session_state.alt_therapy = ""
        st.session_state.diagnosis = ""
        st.session_state.gpt_alt_therapy = ""
        st.session_state.gpt_specialist_advice = ""
        st.session_state.asked_for_more_symptoms = False
        st.session_state.start_new_consultation = True
        st.experimental_rerun()

def create_dynamic_sidebar():
    """Dinamikusan frissülő sidebar."""
    with st.sidebar:
        st.markdown("### ℹ️ Információk")
        
        # Jogi nyilatkozatok
        create_legal_disclaimers()
        
        # Adatgyűjtés státusz
        status_container = st.empty()
        with status_container.container():
            display_data_collection_status()
        
        # Exportálás opciók
        display_export_options()
        
        # Reset gomb
        display_reset_button()