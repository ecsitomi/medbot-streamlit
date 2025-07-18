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