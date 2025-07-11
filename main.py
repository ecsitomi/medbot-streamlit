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

def configure_streamlit():
    """Streamlit konfiguráció beállítása."""
    st.set_page_config(**STREAMLIT_CONFIG)

def main():
    """Fő alkalmazás."""
    # Streamlit konfiguráció
    configure_streamlit()

    # Új konzultáció indításának detektálása
    if st.session_state.get("start_new_consultation", False):
        reset_session_state()
        st.session_state.start_new_consultation = False
        st.experimental_rerun()  # vagy st.rerun()
    
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

if __name__ == "__main__":
    main()