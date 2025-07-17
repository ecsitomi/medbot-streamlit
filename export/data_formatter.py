# =============================================================================
# export/data_formatter.py
# =============================================================================
"""
Adatok formázása exportáláshoz.
"""
import datetime
import streamlit as st
from medline_integration.integration import add_medline_to_export_data

def create_export_data():
    """Létrehozza az exportálandó adatokat."""
    export_data = st.session_state.patient_data.copy()
    export_data["diagnosis"] = st.session_state.diagnosis
    export_data["triage_level"] = st.session_state.triage_level
    export_data["specialist"] = st.session_state.gpt_specialist_advice
    export_data["alt_therapy"] = st.session_state.alt_therapy
    export_data["gpt_alt_therapy"] = st.session_state.gpt_alt_therapy
    export_data["timestamp"] = datetime.datetime.now().isoformat()
    export_data["case_id"] = f"case-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

    export_data = add_medline_to_export_data(export_data)
    
    return export_data

def format_field_name(field_name):
    """Mezőnevek formázása emberi olvashatósághoz."""
    field_mappings = {
        "age": "Életkor",
        "gender": "Nem",
        "symptoms": "Tünetek",
        "duration": "Időtartam",
        "severity": "Súlyosság",
        "existing_conditions": "Meglévő betegségek",
        "medications": "Gyógyszerek",
        "diagnosis": "Diagnózis",
        "triage_level": "Triage szint",
        "specialist": "Javasolt szakorvos",
        "alt_therapy": "Alternatív terápia",
        "gpt_alt_therapy": "AI alternatív terápia",
        "timestamp": "Időbélyeg",
        "case_id": "Eset azonosító"
    }
    return field_mappings.get(field_name, field_name.replace('_', ' ').title())

def format_field_value(value):
    """Mezőértékek formázása."""
    if isinstance(value, list):
        return ", ".join(value) if value else "Nincs adat"
    elif value is None or value == "":
        return "Nincs adat"
    else:
        return str(value)

def create_structured_export():
    """Strukturált export adatok létrehozása."""
    export_data = create_export_data()
    
    structured_data = {
        "case_info": {
            "case_id": export_data["case_id"],
            "timestamp": export_data["timestamp"]
        },
        "patient_data": {
            "demographics": {
                "age": export_data.get("age"),
                "gender": export_data.get("gender")
            },
            "medical_history": {
                "existing_conditions": export_data.get("existing_conditions", []),
                "medications": export_data.get("medications", [])
            },
            "current_symptoms": {
                "symptoms": export_data.get("symptoms", []),
                "duration": export_data.get("duration"),
                "severity": export_data.get("severity")
            }
        },
        "medical_assessment": {
            "triage_level": export_data.get("triage_level"),
            "diagnosis": export_data.get("diagnosis"),
            "specialist_recommendation": export_data.get("specialist"),
            "alternative_therapies": {
                "manual": export_data.get("alt_therapy"),
                "ai_generated": export_data.get("gpt_alt_therapy")
            }
        }
    }
    
    return structured_data