# =============================================================================
# main.py
# =============================================================================
"""
Medical Chatbot - Fő alkalmazás fájl
Refaktorált verzió moduláris architektúrával.
"""
import streamlit as st
from core import initialize_session_state, reset_session_state, STREAMLIT_CONFIG
from ui import create_dynamic_sidebar, create_chat_interface, create_medical_display
from medline_integration.integration import initialize_medline_integration
from admin_page import display_data_overview, display_appointments_table

def configure_streamlit():
    """Streamlit konfiguráció beállítása."""
    st.set_page_config(**STREAMLIT_CONFIG)

def main():
    """Fő alkalmazás."""
    # Streamlit konfiguráció
    configure_streamlit()
    initialize_medline_integration()

    # Új konzultáció indításának detektálása
    if st.session_state.get("start_new_consultation", False):
        reset_session_state()
        st.session_state.start_new_consultation = False
        st.rerun()
    
    # Session state inicializálás
    initialize_session_state()
    
    # Címsor
    st.title("🩺 Egészségügyi Chatbot Asszisztens")
    
    # Dinamikus sidebar létrehozása
    create_dynamic_sidebar()

    # Chat interface
    create_chat_interface()
    
    # Orvosi összefoglaló megjelenítése
    create_medical_display()

    # Sidebar-ban admin tab
    if st.sidebar.button("🔧 Admin"):
        st.session_state.page = "admin"
    
    if st.session_state.get('page') == 'admin':
        display_data_overview()
        display_appointments_table()

    if st.sidebar.button("🐛 Debug Session State"):
        st.write("### Session State Debug")
        st.json({
            "appointment_data": {
                "has_data": "appointment_data" in st.session_state,
                "keys": list(st.session_state.get("appointment_data", {}).keys()),
                "booking_status": st.session_state.get("appointment_data", {}).get("booking_status")
            }
        })

if __name__ == "__main__":
    main()