# =============================================================================
# logic/chat_processor.py
# =============================================================================
"""
Chat input feldolgozása és válaszgenerálás.
JAVÍTOTT VERZIÓ - redundáns válaszok és kontextus problémák megoldásával.
"""
import streamlit as st
from core import has_sufficient_data
from .data_extraction import extract_all_medical_info
from .gpt_communication import generate_diagnosis, generate_alt_therapy, generate_specialist_advice
from .medical_analysis import triage_decision, alternative_recommendations

# ===== ÚJ IMPORTOK =====
from .symptom_graph import (
    has_reasoning_questions_available,
    get_next_reasoning_question,
    get_reasoning_context
)
from .prompt_builder import (
    build_complete_prompt,
    build_reasoning_question_prompt
)

# ===== SESSION STATE KIEGÉSZÍTÉSEK =====
def initialize_reasoning_session_state():
    """Session state inicializálás a reasoning funkciókhoz."""
    if "asked_reasoning_questions" not in st.session_state:
        st.session_state.asked_reasoning_questions = set()
    
    if "reasoning_phase" not in st.session_state:
        st.session_state.reasoning_phase = False
    
    if "reasoning_questions_exhausted" not in st.session_state:
        st.session_state.reasoning_questions_exhausted = False
    
    if "last_extracted_data" not in st.session_state:
        st.session_state.last_extracted_data = {}

def get_missing_required_fields():
    """
    Hiányzó kötelező mezők meghatározása.
    
    Returns:
        list: Hiányzó mezők listája prioritás sorrendben
    """
    data = st.session_state.patient_data
    missing_fields = []
    
    # Prioritás sorrend
    priority_order = [
        'symptoms',
        'additional_symptoms', 
        'duration',
        'severity',
        'age',
        'gender',
        'existing_conditions',
        'medications'
    ]
    
    for field in priority_order:
        if field == 'symptoms':
            symptoms_count = len(data.get('symptoms', []))
            if symptoms_count == 0:
                missing_fields.append('symptoms')
        elif field == 'additional_symptoms':
            symptoms_count = len(data.get('symptoms', []))
            if symptoms_count == 1 and not st.session_state.asked_for_more_symptoms:
                missing_fields.append('additional_symptoms')
        elif field in ['existing_conditions', 'medications']:
            field_data = data.get(field)
            has_data = isinstance(field_data, list) and len(field_data) > 0  # ← EGYSZERŰ
            
            if not has_data:
                missing_fields.append(field)
        else:
            if not data.get(field):
                missing_fields.append(field)
    
    return missing_fields

def should_use_reasoning_questions():
    """
    Eldönti, hogy reasoning kérdéseket kell-e használni.
    
    Returns:
        bool: True, ha reasoning kérdéseket kell használni
    """
    # Ha már az értékelési fázisban vagyunk, nem kell reasoning
    if st.session_state.triage_level:
        return False
    
    # Ha nincs elég tünet, nem használunk reasoning-t
    symptoms = st.session_state.patient_data.get('symptoms', [])
    if len(symptoms) < 1:
        return False
    
    # Ha már kimerítettük a reasoning kérdéseket
    if st.session_state.reasoning_questions_exhausted:
        return False
    
    # Ha vannak elérhető reasoning kérdések
    return has_reasoning_questions_available(
        symptoms, 
        st.session_state.asked_reasoning_questions
    )

def detect_data_changes():
    """
    Észleli, hogy változtak-e az adatok a legutóbbi hívás óta.
    
    Returns:
        dict: {
            'has_changes': bool,
            'new_data': dict,
            'changes_summary': str
        }
    """
    current_data = st.session_state.patient_data.copy()
    last_data = st.session_state.get('last_extracted_data', {})
    
    changes = {}
    changes_summary = []
    
    for field, value in current_data.items():
        if field not in last_data or last_data[field] != value:
            changes[field] = value
            
            # Változás leírása
            if field == 'symptoms' and isinstance(value, list):
                if isinstance(last_data.get(field), list):
                    new_symptoms = set(value) - set(last_data[field])
                    if new_symptoms:
                        changes_summary.append(f"Új tünet(ek): {', '.join(new_symptoms)}")
                else:
                    changes_summary.append(f"Tünet(ek): {', '.join(value)}")
            elif field == 'existing_conditions' and isinstance(value, list):
                if isinstance(last_data.get(field), list):
                    new_conditions = set(value) - set(last_data[field])
                    if new_conditions:
                        changes_summary.append(f"Új betegség(ek): {', '.join(new_conditions)}")
                else:
                    changes_summary.append(f"Betegség(ek): {', '.join(value)}")
            elif value and field not in ['symptoms', 'existing_conditions', 'medications']:
                field_names = {
                    'age': 'Életkor',
                    'gender': 'Nem',
                    'duration': 'Időtartam',
                    'severity': 'Súlyosság'
                }
                display_name = field_names.get(field, field)
                changes_summary.append(f"{display_name}: {value}")
    
    # Utolsó adatok frissítése
    st.session_state.last_extracted_data = current_data
    
    return {
        'has_changes': len(changes) > 0,
        'new_data': changes,
        'changes_summary': ' • '.join(changes_summary)
    }

def get_next_question_with_reasoning():
    """
    Következő kérdés kiválasztása reasoning prioritással.
    JAVÍTOTT VERZIÓ - redundancia elkerüléssel.
    """
    try:
        # Reasoning session state inicializálás
        initialize_reasoning_session_state()
        
        symptoms = st.session_state.patient_data.get('symptoms', [])
        
        # 1. REASONING KÉRDÉSEK PRIORITÁSA
        if should_use_reasoning_questions():
            reasoning_question = get_next_reasoning_question(
                symptoms, 
                st.session_state.asked_reasoning_questions
            )
            
            if reasoning_question:
                # Reasoning kérdés GPT-vel természetessé tétel
                prompt_data = build_reasoning_question_prompt(
                    reasoning_question,
                    st.session_state.patient_data,
                    tone="empathetic"  # Empátiát hangsúlyozzuk
                )
                
                # GPT hívás
                from core import get_openai_client
                client = get_openai_client()
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": prompt_data["system"]},
                        {"role": "user", "content": prompt_data["user"]}
                    ],
                    temperature=0.8,
                    max_tokens=300
                )
                
                generated_question = response.choices[0].message.content.strip()
                
                # Kérdés rögzítése (ismétlés elkerülése)
                st.session_state.asked_reasoning_questions.add(reasoning_question)
                st.session_state.reasoning_phase = True
                
                return generated_question
            else:
                # Nincs több reasoning kérdés
                st.session_state.reasoning_questions_exhausted = True
        
        # 2. HAGYOMÁNYOS HIÁNYZÓ MEZŐK
        missing_fields = get_missing_required_fields()
        
        if missing_fields:
            next_field = missing_fields[0]
            
            # Prompt builder használata
            prompt_data = build_complete_prompt(
                next_field,
                st.session_state.patient_data,
                st.session_state.chat_history,
                tone="empathetic"
            )
            
            # GPT hívás
            from core import get_openai_client
            client = get_openai_client()
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": prompt_data["system"]},
                    {"role": "user", "content": prompt_data["user"]}
                ],
                temperature=0.8,
                max_tokens=300
            )
            
            generated_question = response.choices[0].message.content.strip()
            
            # Speciális tracking
            if next_field == "additional_symptoms":
                st.session_state.asked_for_more_symptoms = True
            
            return generated_question
        
        # 3. MINDEN ADAT MEGVAN
        return "Köszönöm az összes információt! Most elkészítem az értékelést."
        
    except Exception as e:
        st.error(f"Hiba a kérdés generálásában: {e}")
        # Fallback az eredeti statikus kérdésre
        return get_next_question_fallback()

def get_next_question_fallback():
    """
    Fallback kérdésgenerálás, ha a GPT alapú nem működik.
    Az eredeti get_next_question_static() logikája.
    """
    data = st.session_state.patient_data
    symptoms_count = len(data.get("symptoms", []))
    
    if symptoms_count == 0:
        return "Kérem, írja le részletesen, milyen tünetei vannak. Mi fáj, vagy mit tapasztal?"
    elif symptoms_count == 1 and not st.session_state.asked_for_more_symptoms:
        st.session_state.asked_for_more_symptoms = True
        return f"Köszönöm! Ezt a tünetet azonosítottam: {', '.join(data['symptoms'])}. Vannak-e további tünetei? Ha nincs több, írja be: 'nincs több'."
    elif not data.get("duration"):
        symptoms_text = ', '.join(data['symptoms']) if data['symptoms'] else 'a tüneteket'
        return f"Köszönöm a tünetek leírását! Mióta tapasztalja {symptoms_text}? (például: 2 napja, 1 hete, 3 hónapja)"
    elif not data.get("severity"):
        return "Hogyan értékelné tünetei súlyosságát? Enyhének vagy súlyosnak minősítené őket?"
    elif not data.get("age"):
        return "Hány éves Ön? Ez segít a pontosabb értékelésben."
    elif not data.get("gender"):
        return "Kérem, adja meg a biológiai nemét (férfi/nő). Ez is fontos az értékeléshez."
    elif not data.get("existing_conditions"):
        return "Vannak-e ismert krónikus betegségei, allergiái vagy egyéb egészségügyi problémái? Ha nincs, írja be: 'nincs'."
    elif not data.get("medications"):
        return "Szed-e rendszeresen gyógyszereket vagy vitaminokat? Ha nem, írja be: 'nincs'."
    else:
        return "Köszönöm az összes információt! Most elkészítem az értékelést."

def process_chat_input_enhanced(user_input):
    """
    Továbbfejlesztett chat input feldolgozás.
    JAVÍTOTT VERZIÓ - redundancia elkerüléssel és jobb megerősítésekkel.
    """
    try:
        # 1. ADATOK KINYERÉSE (javított extraction)
        extract_all_medical_info(user_input)
        
        # 2. ELLENŐRIZZÜK AZ ÁLLAPOTOT
        if has_sufficient_data():
            if not st.session_state.triage_level:
                # Értékelés indítása
                data = st.session_state.patient_data
                assistant_reply = "✅ Köszönöm! Összegyűjtöttem az adatokat:\n\n"
                
                # Adatok megjelenítése
                if data.get('symptoms'):
                    assistant_reply += f"• **Tünetek:** {', '.join(data['symptoms'])}\n"
                if data.get('duration'): 
                    assistant_reply += f"• **Időtartam:** {data['duration']}\n"
                if data.get('severity'): 
                    assistant_reply += f"• **Súlyosság:** {data['severity']}\n"
                if data.get('age'): 
                    assistant_reply += f"• **Életkor:** {data['age']} év\n"
                if data.get('gender'): 
                    assistant_reply += f"• **Nem:** {data['gender']}\n"
                if data.get('existing_conditions'):
                    assistant_reply += f"• **Betegségek:** {', '.join(data['existing_conditions'])}\n"
                
                assistant_reply += "\n🔄 **Értékelés készítése...**"
                
                # Értékelések futtatása (eredeti logika)
                st.session_state.triage_level = triage_decision(st.session_state.patient_data)
                st.session_state.alt_therapy = alternative_recommendations(st.session_state.patient_data["symptoms"])
                st.session_state.diagnosis = generate_diagnosis(st.session_state.patient_data["symptoms"])
                st.session_state.gpt_alt_therapy = generate_alt_therapy(st.session_state.patient_data["symptoms"], st.session_state.diagnosis)
                st.session_state.gpt_specialist_advice = generate_specialist_advice(st.session_state.patient_data["symptoms"], st.session_state.diagnosis)
                
                return assistant_reply
            else:
                return "Az értékelés már elkészült."
        else:
            # 3. ADATVÁLTOZÁSOK ÉSZLELÉSE
            data_changes = detect_data_changes()
            
            # 4. INTELLIGENS KÖVETKEZŐ KÉRDÉS
            next_question = get_next_question_with_reasoning()
            
            # 5. MEGERŐSÍTÉS HOZZÁADÁSA (JAVÍTOTT LOGIKA)
            if data_changes['has_changes'] and data_changes['changes_summary']:
                # Csak akkor adjunk megerősítést, ha tényleg változtak az adatok
                if not any(phrase in next_question.lower() for phrase in [
                    'köszönöm', 'rögzítettem', 'azonosítottam', 'értem', 'megértem'
                ]):
                    # Reasoning kérdések esetén más megerősítés
                    if st.session_state.reasoning_phase:
                        confirmation = f"Értem. {data_changes['changes_summary']}.\n\n"
                    else:
                        confirmation = f"Köszönöm! Rögzítettem: {data_changes['changes_summary']}.\n\n"
                    
                    next_question = confirmation + next_question
            
            return next_question

    except Exception as e:
        return f"Hiba történt: {str(e)}. Próbálja újra!"

def is_evaluation_complete():
    """Ellenőrzi, hogy az értékelés elkészült-e. (EREDETI - VÁLTOZATLAN)"""
    return bool(st.session_state.triage_level)

def get_evaluation_status():
    """
    Visszaadja az értékelés státuszát.
    BŐVÍTETT VERZIÓ - reasoning státusz információkkal.
    """
    status = {
        "has_sufficient_data": has_sufficient_data(),
        "evaluation_complete": is_evaluation_complete(),
        "triage_done": bool(st.session_state.triage_level),
        "diagnosis_done": bool(st.session_state.diagnosis),
        "therapy_done": bool(st.session_state.gpt_alt_therapy),
        "specialist_done": bool(st.session_state.gpt_specialist_advice)
    }
    
    # Reasoning státusz hozzáadása
    if hasattr(st.session_state, 'reasoning_phase'):
        symptoms = st.session_state.patient_data.get('symptoms', [])
        status.update({
            "reasoning_phase": st.session_state.reasoning_phase,
            "reasoning_questions_available": has_reasoning_questions_available(
                symptoms, 
                getattr(st.session_state, 'asked_reasoning_questions', set())
            ),
            "reasoning_questions_exhausted": getattr(st.session_state, 'reasoning_questions_exhausted', False),
            "asked_reasoning_count": len(getattr(st.session_state, 'asked_reasoning_questions', set()))
        })
    
    return status

# ===== DEBUGGING ÉS MONITORING FUNKCIÓK =====

def get_chat_processing_debug_info():
    """Debug információk a chat feldolgozásról."""
    symptoms = st.session_state.patient_data.get('symptoms', [])
    
    debug_info = {
        'patient_data': st.session_state.patient_data,
        'missing_fields': get_missing_required_fields(),
        'has_sufficient_data': has_sufficient_data(),
        'should_use_reasoning': should_use_reasoning_questions(),
        'reasoning_context': get_reasoning_context(symptoms) if symptoms else None,
        'evaluation_status': get_evaluation_status(),
        'data_changes': detect_data_changes()
    }
    
    return debug_info

def log_chat_processing_step(step_name, details):
    """Chat feldolgozási lépések logolása (csak development módban)."""
    if st.secrets.get("DEBUG_MODE", False):
        print(f"🔍 Chat Processing - {step_name}: {details}")

# ===== EREDETI FÜGGVÉNYEK KOMPATIBILITÁS MEGŐRZÉSE =====

def get_next_question_gpt():
    """
    Kompatibilitási wrapper az eredeti get_next_question_gpt() függvényhez.
    Most a get_next_question_with_reasoning() implementációt használja.
    """
    return get_next_question_with_reasoning()