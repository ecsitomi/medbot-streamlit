# =============================================================================
# core/utils.py
# =============================================================================
"""
Segédfunkciók a medical chatbot számára.
"""
import json
import hashlib
import streamlit as st

def get_data_hash():
    """Patient data hash a változások követéséhez."""
    data_str = json.dumps(st.session_state.patient_data, sort_keys=True)
    return hashlib.md5(data_str.encode()).hexdigest()

def has_sufficient_data():
    """Ellenőrzi, hogy van-e elegendő adat az orvosi értékeléshez."""
    data = st.session_state.patient_data
    
    # Kötelező mezők
    has_age = data.get("age") is not None
    has_gender = data.get("gender") is not None and data.get("gender") != ""
    has_duration = data.get("duration") is not None and data.get("duration") != ""
    has_severity = data.get("severity") is not None and data.get("severity") != ""
    
    # Tünetek: legalább 1 tünet kell, vagy ha már megkérdeztük a többit
    symptoms_count = len(data.get("symptoms", []))
    has_symptoms = symptoms_count >= 1 and (symptoms_count >= 2 or st.session_state.asked_for_more_symptoms)
    
    return has_age and has_gender and has_symptoms and has_duration and has_severity

def update_state_from_function_output(output):
    """Function call output alapján frissíti a session state-t."""
    try:
        parsed = json.loads(output)
        for key in parsed:
            if key in st.session_state.patient_data:
                current_value = st.session_state.patient_data[key]
                new_value = parsed[key]
                
                # Lista mezők esetén egyesítsük az értékeket (ne írjuk felül)
                if key in ["symptoms", "existing_conditions", "medications"] and isinstance(new_value, list):
                    if isinstance(current_value, list):
                        # Csak új elemeket adjunk hozzá
                        for item in new_value:
                            if item and item not in current_value:
                                current_value.append(item)
                    else:
                        st.session_state.patient_data[key] = new_value
                else:
                    # Egyszerű mezők esetén csak akkor írjuk felül, ha nincs még érték
                    if not current_value:
                        st.session_state.patient_data[key] = new_value
    except Exception as e:
        st.error(f"Hiba a function output feldolgozásában: {e}")
