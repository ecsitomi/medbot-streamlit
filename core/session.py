# =============================================================================
# core/session.py
# =============================================================================
"""
Session state kezelés a medical chatbot számára.
"""
import streamlit as st
from .config import WELCOME_MESSAGE, DEFAULT_PATIENT_DATA

def initialize_session_state():
    """Session state változók inicializálása."""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [WELCOME_MESSAGE]
    
    if "patient_data" not in st.session_state:
        st.session_state.patient_data = DEFAULT_PATIENT_DATA.copy()

    if "triage_level" not in st.session_state:
        st.session_state.triage_level = ""

    if "alt_therapy" not in st.session_state:
        st.session_state.alt_therapy = ""

    if "diagnosis" not in st.session_state:
        st.session_state.diagnosis = ""

    if "gpt_alt_therapy" not in st.session_state:
        st.session_state.gpt_alt_therapy = ""

    if "gpt_specialist_advice" not in st.session_state:
        st.session_state.gpt_specialist_advice = ""

    if "asked_for_more_symptoms" not in st.session_state:
        st.session_state.asked_for_more_symptoms = False

    # Sidebar frissítés tracking
    if "sidebar_last_update" not in st.session_state:
        st.session_state.sidebar_last_update = ""
    
    if "sidebar_container" not in st.session_state:
        st.session_state.sidebar_container = None

def reset_session_state():
    """Session state teljes visszaállítása új konzultációhoz."""
    # EXPLICIT reset minden mezőnek
    st.session_state.chat_history = [WELCOME_MESSAGE]
    st.session_state.patient_data = {
        "age": None,
        "gender": None,
        "symptoms": [],  # Ez a legfontosabb!
        "duration": None,
        "severity": None,
        "existing_conditions": [],
        "medications": []
    }
    st.session_state.triage_level = ""
    st.session_state.alt_therapy = ""
    st.session_state.diagnosis = ""
    st.session_state.gpt_alt_therapy = ""
    st.session_state.gpt_specialist_advice = ""
    st.session_state.asked_for_more_symptoms = False
    st.session_state.sidebar_last_update = ""