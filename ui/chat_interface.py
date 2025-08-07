# =============================================================================
# ui/chat_interface.py
# =============================================================================
"""
Chat felhasználói felület komponensek.
"""
import streamlit as st
from core import get_data_hash
from logic import process_chat_input_enhanced, is_evaluation_complete

def display_chat_history():
    """Chat történet megjelenítése."""
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def handle_chat_input():
    """Chat input kezelése és feldolgozása."""
    if prompt := st.chat_input("Írja le a tüneteit vagy tegyen fel kérdést..."):
        # Data hash mentése MIELŐTT feldolgozzuk
        old_hash = get_data_hash()
        
        # Ellenőrizzük, hogy volt-e már értékelés
        had_evaluation = is_evaluation_complete()
        
        # Felhasználói üzenet hozzáadása
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # Felhasználói üzenet megjelenítése
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # AI válasz generálása
        with st.chat_message("assistant"):
            with st.spinner("Elemzés folyamatban..."):
                response = process_chat_input_enhanced(prompt)
                st.markdown(response)
        
        # AI válasz hozzáadása a történethez
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        
        # Ellenőrizzük a változásokat
        new_hash = get_data_hash()
        data_changed = old_hash != new_hash
        evaluation_just_completed = not had_evaluation and is_evaluation_complete()
        
        # Ha adat változott VAGY az értékelés most fejeződött be
        if data_changed or evaluation_just_completed:
            st.rerun()

def create_chat_interface():
    """Teljes chat interface létrehozása."""
    # Chat történet megjelenítése
    display_chat_history()
    
    # Chat input kezelése
    handle_chat_input()

