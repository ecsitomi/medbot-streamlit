# =============================================================================
# logic/chat_processor.py
# =============================================================================
"""
Chat input feldolgozása és válaszgenerálás.
"""
import streamlit as st
from core import has_sufficient_data
from .data_extraction import extract_all_medical_info
from .gpt_communication import get_next_question_gpt, generate_diagnosis, generate_alt_therapy, generate_specialist_advice
from .medical_analysis import triage_decision, alternative_recommendations

def process_chat_input_enhanced(user_input):
    """Továbbfejlesztett chat input feldolgozás GPT kérdésekkel."""
    try:
        # Adatok kinyerése
        extract_all_medical_info(user_input)
        
        # Ellenőrizzük az állapotot
        if has_sufficient_data():
            if not st.session_state.triage_level:
                # Értékelés indítása
                data = st.session_state.patient_data
                assistant_reply = "✅ Köszönöm! Összegyűjtöttem az adatokat:\n\n"
                assistant_reply += f"• **Tünetek:** {', '.join(data.get('symptoms', []))}\n"
                if data.get('duration'): 
                    assistant_reply += f"• **Időtartam:** {data['duration']}\n"
                if data.get('severity'): 
                    assistant_reply += f"• **Súlyosság:** {data['severity']}\n"
                if data.get('age'): 
                    assistant_reply += f"• **Életkor:** {data['age']} év\n"
                if data.get('gender'): 
                    assistant_reply += f"• **Nem:** {data['gender']}\n"
                
                assistant_reply += "\n🔄 **Orvosi értékelés készítése...**"
                
                # Értékelések futtatása
                st.session_state.triage_level = triage_decision(st.session_state.patient_data)
                st.session_state.alt_therapy = alternative_recommendations(st.session_state.patient_data["symptoms"])
                st.session_state.diagnosis = generate_diagnosis(st.session_state.patient_data["symptoms"])
                st.session_state.gpt_alt_therapy = generate_alt_therapy(st.session_state.patient_data["symptoms"], st.session_state.diagnosis)
                st.session_state.gpt_specialist_advice = generate_specialist_advice(st.session_state.patient_data["symptoms"], st.session_state.diagnosis)
                
                return assistant_reply
            else:
                return "Az orvosi értékelés már elkészült."
        else:
            # GPT alapú következő kérdés
            next_question = get_next_question_gpt()
            
            # Ha sikerült adatot kinyerni, megerősítjük
            if st.session_state.patient_data.get('symptoms'):
                symptoms = ', '.join(st.session_state.patient_data['symptoms'])
                # Csak akkor teszünk hozzá megerősítést, ha még nincs benne
                if "rögzítettem" not in next_question.lower() and "köszönöm" not in next_question.lower():
                    next_question = f"Köszönöm! Rögzítettem: {symptoms}.\n\n{next_question}"
            
            return next_question

    except Exception as e:
        return f"Hiba történt: {str(e)}. Próbálja újra!"

def is_evaluation_complete():
    """Ellenőrzi, hogy az orvosi értékelés elkészült-e."""
    return bool(st.session_state.triage_level)

def get_evaluation_status():
    """Visszaadja az értékelés státuszát."""
    return {
        "has_sufficient_data": has_sufficient_data(),
        "evaluation_complete": is_evaluation_complete(),
        "triage_done": bool(st.session_state.triage_level),
        "diagnosis_done": bool(st.session_state.diagnosis),
        "therapy_done": bool(st.session_state.gpt_alt_therapy),
        "specialist_done": bool(st.session_state.gpt_specialist_advice)
    }