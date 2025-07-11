# =============================================================================
# core/__init__.py
# =============================================================================
"""
Core modul - alapvető funkcionalitások.
"""
from .config import (
    get_openai_client, 
    STREAMLIT_CONFIG, 
    TOOL_SCHEMA, 
    ALTERNATIVE_TIPS,
    WELCOME_MESSAGE,
    DEFAULT_PATIENT_DATA
)
from .session import initialize_session_state, reset_session_state
from .utils import get_data_hash, has_sufficient_data, update_state_from_function_output

__all__ = [
    'get_openai_client',
    'STREAMLIT_CONFIG',
    'TOOL_SCHEMA',
    'ALTERNATIVE_TIPS',
    'WELCOME_MESSAGE',
    'DEFAULT_PATIENT_DATA',
    'initialize_session_state',
    'reset_session_state',
    'get_data_hash',
    'has_sufficient_data',
    'update_state_from_function_output'
]
