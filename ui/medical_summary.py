# =============================================================================
# ui/medical_summary.py
# =============================================================================
"""
Orvosi összefoglaló megjelenítése.
"""
import streamlit as st
from logic import is_evaluation_complete

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