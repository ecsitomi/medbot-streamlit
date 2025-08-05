# =============================================================================
# main.py - JAVÍTOTT VERZIÓ
# =============================================================================
"""
Medical Chatbot - Fő alkalmazás fájl
Refaktorált verzió moduláris architektúrával.
JAVÍTVA: Duplikált Medline sidebar hívás eltávolítása
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
    
    # ✅ JAVÍTETT: Medline integráció inicializálása SIDEBAR HÍVÁS NÉLKÜL
    # A sidebar opciók most a create_dynamic_sidebar()-ban jelennek meg
    initialize_medline_integration_without_sidebar()

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

def initialize_medline_integration_without_sidebar():
    """
    ✅ ÚJ: Medline integráció inicializálása sidebar opciók NÉLKÜL.
    A sidebar opciók most közvetlenül a create_dynamic_sidebar()-ban jelennek meg.
    """
    try:
        from medline_integration.integration import medline_integration
        
        # Csak a kliens inicializálása, sidebar opciók NÉLKÜL
        medline_integration.initialize_client()
        
    except ImportError:
        # Ha nincs medline integráció, ne törjön el az alkalmazás
        pass
    except Exception as e:
        st.error(f"Medline integráció inicializálási hiba: {e}")

if __name__ == "__main__":
    main()