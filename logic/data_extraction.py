# =============================================================================
# logic/data_extraction.py
# =============================================================================
"""
Orvosi adatok kinyerése és feldolgozása.
"""
import re
import streamlit as st
from core import get_openai_client, TOOL_SCHEMA, update_state_from_function_output

def extract_medical_info_with_gpt(user_input):
    """GPT alapú adatkinyerés function call-lal."""
    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Te egy egészségügyi asszisztens vagy. Kinyered az egészségügyi adatokat a szövegből."},
                {"role": "user", "content": user_input}
            ],
            tools=[TOOL_SCHEMA],
            tool_choice="auto"
        )
        
        reply = response.choices[0].message
        if hasattr(reply, 'tool_calls') and reply.tool_calls:
            for tool_call in reply.tool_calls:
                if tool_call.function.name == "extract_medical_info":
                    update_state_from_function_output(tool_call.function.arguments)
                    return True
    except Exception as e:
        st.error(f"Hiba a GPT adatkinyerésben: {e}")
        return False
    
    return False

def manual_extract_info(user_input):
    """Kézi információ kinyerés, ha a function call nem működik."""
    lower_input = user_input.lower()
    extracted_anything = False
    
    # Tünetek felismerése
    symptom_keywords = {
        'fejfájás': ['fej', 'fejem', 'fejfájás', 'fejfájást', 'fáj a fejem'],
        'torokfájás': ['torok', 'torkom', 'torokfájás', 'torokfájást'],
        'hasmenés': ['hasmenés', 'hasmenést', 'folyós', 'széklet'],
        'láz': ['láz', 'lázas', 'meleg', 'forróság'],
        'köhögés': ['köhög', 'köhögés', 'köhögök', 'köhent'],
        'hányás': ['hány', 'hányok', 'hánytam', 'hányás'],
        'fáradtság': ['fáradt', 'fáradtság', 'kimerült', 'gyenge']
    }
    
    for symptom, keywords in symptom_keywords.items():
        if any(keyword in lower_input for keyword in keywords):
            current_symptoms = st.session_state.patient_data.get('symptoms', [])
            if symptom not in current_symptoms:
                current_symptoms.append(symptom)
                st.session_state.patient_data['symptoms'] = current_symptoms
                extracted_anything = True
    
    # Életkor felismerése
    age_match = re.search(r'(\d{1,2})\s*év', user_input)
    if age_match:
        age = int(age_match.group(1))
        if 0 < age < 120 and not st.session_state.patient_data.get('age'):
            st.session_state.patient_data['age'] = age
            extracted_anything = True
    
    # Nem felismerése
    if 'férfi' in lower_input and not st.session_state.patient_data.get('gender'):
        st.session_state.patient_data['gender'] = 'férfi'
        extracted_anything = True
    elif ('nő' in lower_input or 'női' in lower_input) and not st.session_state.patient_data.get('gender'):
        st.session_state.patient_data['gender'] = 'nő'
        extracted_anything = True
    
    # Időtartam felismerése
    duration_patterns = [
        r'(\d+)\s*nap', r'(\d+)\s*hét', r'(\d+)\s*hónap',
        r'tegnap', r'ma', r'múlt hét'
    ]
    if not st.session_state.patient_data.get('duration'):
        for pattern in duration_patterns:
            if re.search(pattern, lower_input):
                st.session_state.patient_data['duration'] = user_input
                extracted_anything = True
                break
    
    # Súlyosság felismerése
    if not st.session_state.patient_data.get('severity'):
        if any(word in lower_input for word in ['súlyos', 'erős', 'nagyon', 'borzasztó']):
            st.session_state.patient_data['severity'] = 'súlyos'
            extracted_anything = True
        elif any(word in lower_input for word in ['enyhe', 'kis', 'kicsit', 'gyenge']):
            st.session_state.patient_data['severity'] = 'enyhe'
            extracted_anything = True
    
    return extracted_anything

def process_special_cases(user_input):
    """Speciális esetek kezelése (pl. 'nincs több')."""
    lower_input = user_input.lower()
    if any(phrase in lower_input for phrase in ['nincs több', 'más nincs', 'semmi más', 'csak ennyi', 'nincs']):
        st.session_state.asked_for_more_symptoms = True
        return True
    return False

def extract_all_medical_info(user_input):
    """Komplett adatkinyerési folyamat."""
    # GPT alapú kinyerés próbálkozás
    gpt_success = extract_medical_info_with_gpt(user_input)
    
    # Manual extraction fallback
    manual_success = manual_extract_info(user_input)
    
    # Speciális esetek
    special_case = process_special_cases(user_input)
    
    return gpt_success or manual_success or special_case