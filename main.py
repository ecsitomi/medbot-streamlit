# =============================================================================
# main.py 
# =============================================================================
"""
Medical Chatbot - Fő alkalmazás fájl
"""
import streamlit as st
from core import initialize_session_state, reset_session_state, STREAMLIT_CONFIG
from ui import create_dynamic_sidebar, create_chat_interface, create_medical_display
from medline_integration.integration import initialize_medline_integration
from logic import is_evaluation_complete
from admin_page import display_data_overview, display_appointments_table


def configure_streamlit():
    #"""Streamlit konfiguráció beállítása."""
    st.set_page_config(**STREAMLIT_CONFIG)

def appointment_admin():
    if st.session_state.get('page') == 'admin':
        display_data_overview()
        display_appointments_table()

def main():
    """Fő alkalmazás."""
    # Streamlit konfiguráció
    configure_streamlit()

    # Új konzultáció indításának detektálása
    if st.session_state.get("start_new_consultation", False):
        reset_session_state()
        st.session_state.start_new_consultation = False
        st.rerun()
    
    # Session state inicializálás
    initialize_session_state()
    
    # Címsor
    st.title("🩺 Egészségügyi Chatbot Asszisztens")
    
    # Dinamikus sidebar létrehozása (itt jelennek meg a Medline opciók)
    create_dynamic_sidebar()

    # Chat interface
    if not is_evaluation_complete():
        create_chat_interface()
    
    # Orvosi összefoglaló megjelenítése
    create_medical_display()

    # Időpont admin
    appointment_admin()

    

if __name__ == "__main__":
    main()