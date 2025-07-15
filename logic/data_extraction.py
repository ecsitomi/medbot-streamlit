# =============================================================================
# logic/data_extraction.py
# =============================================================================
"""
Orvosi adatok kinyerése és feldolgozása.
JAVÍTOTT VERZIÓ - kontextus figyelembevétellel és validációval.
"""
import re
import streamlit as st
from core import get_openai_client, TOOL_SCHEMA, update_state_from_function_output

# ===== KONTEXTUS TRACKING =====

def get_current_question_context():
    """
    Meghatározza, hogy jelenleg melyik mezőt kérdezzük.
    A chat history utolsó asszisztens üzenetéből következtet.
    JAVÍTOTT VERZIÓ - több kulcsszóval.
    """
    if not st.session_state.chat_history:
        return None
    
    # Utolsó asszisztens üzenet
    last_assistant_message = None
    for msg in reversed(st.session_state.chat_history):
        if msg.get('role') == 'assistant':
            last_assistant_message = msg.get('content', '').lower()
            break
    
    if not last_assistant_message:
        return None
    
    # Kontextus felismerés kulcsszavak alapján - JAVÍTOTT VERZIÓ
    context_patterns = {
        'age': ['hány éves', 'életkor', 'milyen idős', 'hogy hívják'],
        'gender': ['férfi', 'nő', 'fiú', 'lány', 'kislány', 'kisfiú', 'nemét'],
        'duration': ['mióta', 'mennyi ideje', 'mikor kezdődött', 'napja', 'hete', 'hónapja'],
        'severity': ['súlyosság', 'milyen erős', 'enyhe', 'súlyos', 'intenzitás', 'skálán', 'értékelné'],
        'symptoms': ['tünet', 'fáj', 'panasz', 'probléma', 'további tünet', 'milyen tünet'],
        'existing_conditions': [
            'krónikus', 'betegség', 'egészségügyi', 'probléma', 'állapot', 
            'tudnia kellene', 'vérnyomás', 'cukorbetegség', 'allergia', 'betegségei'
        ],
        'medications': [
            'gyógyszer', 'vitamin', 'szed', 'bevesz', 'tabletta', 'kapszula',
            'rendszeresen', 'gyógyszereket', 'vitaminokat', 'készítmény', 'supplement',
            'vérnyomáscsökkentő', 'fájdalomcsillapító', 'orvosság', 'gyógyszert'
        ]
    }
    
    # Prioritás alapú ellenőrzés (specifikusabb mezők előbb)
    priority_order = ['medications', 'existing_conditions', 'severity', 'duration', 'age', 'gender', 'symptoms']
    
    for field in priority_order:
        keywords = context_patterns[field]
        if any(keyword in last_assistant_message for keyword in keywords):
            return field
    
    return None

def validate_extraction_result(field, value, context):
    """
    Validálja a kinyert adatot a kontextus alapján.
    
    Args:
        field (str): Mező neve
        value: Kinyert érték
        context (str): Jelenlegi kérdés kontextusa
        
    Returns:
        bool: True, ha az érték valószínűleg helyes
    """
    if not value or not context:
        return True  # Ha nincs kontextus, ne blokkoljunk
    
    # Életkor validáció
    if field == 'age':
        if context != 'age':
            return False  # Csak akkor fogadjuk el, ha életkort kérdeztünk
        if isinstance(value, int):
            return 0 < value < 120
        return False
    
    # Időtartam validáció
    if field == 'duration':
        if context != 'duration':
            return False
        # Ellenőrizzük, hogy tartalmaz-e időre utaló szót
        time_keywords = ['nap', 'hét', 'hónap', 'év', 'óta', 'tegnap', 'ma', 'múlt']
        value_str = str(value).lower()
        return any(keyword in value_str for keyword in time_keywords)
    
    # Súlyosság validáció
    if field == 'severity':
        if context != 'severity':
            return False
        valid_severities = ['enyhe', 'súlyos', 'közepes']
        return str(value).lower() in valid_severities
    
    # Nem validáció
    if field == 'gender':
        if context != 'gender':
            return False
        return str(value).lower() in ['férfi', 'nő']
    
    return True  # Egyéb mezők esetén engedélyező

# ===== BŐVÍTETT REGEX MINTÁK (KONTEXTUS FIGYELEMBEVÉTELLEL) =====

def enhanced_age_extraction(user_input, context=None):
    """
    Bővített életkor felismerés KONTEXTUS figyelembevétellel.
    """
    if st.session_state.patient_data.get('age'):
        return None
    
    # CSAK akkor próbáljuk meg, ha életkort kérdezünk
    if context != 'age':
        return None
    
    lower_input = user_input.lower().strip()
    
    # Életkor minták
    age_patterns = [
        r'\b(\d{1,2})\s*év',
        r'\b(\d{1,2})\s*éves',
        r'^(\d{1,2})$',  # Csak szám, DE csak életkor kontextusban
        r'(\d{1,2})\s*(?:éves vagyok|vagyok)',
    ]
    
    for pattern in age_patterns:
        match = re.search(pattern, lower_input)
        if match:
            try:
                age = int(match.group(1))
                if 0 < age < 120:
                    return age
            except (ValueError, IndexError):
                continue
    
    return None

def enhanced_duration_extraction(user_input, context=None):
    """
    Bővített időtartam felismerés KONTEXTUS figyelembevétellel.
    """
    if st.session_state.patient_data.get('duration'):
        return None
    
    # CSAK akkor próbáljuk meg, ha időtartamot kérdezünk
    if context != 'duration':
        return None
    
    lower_input = user_input.lower().strip()
    
    # Időtartam minták
    duration_patterns = [
        r'(\d+)\s*nap(?:ja|ig|ot)?',
        r'(\d+)\s*hét(?:e|ig|et)?',
        r'(\d+)\s*hónap(?:ja|ig|ot)?',
        r'(\d+)\s*(?:éve|év)',
        r'\btegnap(?:óta)?',
        r'\bma(?:\s+(?:óta|reggel(?:óta)?))?',
        r'\bmúlt\s+hét(?:en)?',
        r'\bpár\s+nap(?:ja)?',
        r'\begy(?:\s+|-)?hét(?:e)?',
        r'\begy\s+hónap(?:ja)?',
    ]
    
    for pattern in duration_patterns:
        match = re.search(pattern, lower_input)
        if match:
            # Kontextust is ellenőrizzük
            return user_input.strip()
    
    # Csak időtartam kontextusban fogadjuk el
    time_keywords = ['óta', 'múlt', 'elmúlt', 'kezdet', 'kezdődött', 'napja', 'hete']
    if any(keyword in lower_input for keyword in time_keywords):
        return user_input.strip()
    
    return None

def enhanced_severity_extraction(user_input, context=None):
    """
    Bővített súlyosság felismerés KONTEXTUS figyelembevétellel.
    """
    if st.session_state.patient_data.get('severity'):
        return None
    
    # CSAK akkor próbáljuk meg, ha súlyosságot kérdezünk
    if context != 'severity':
        return None
    
    lower_input = user_input.lower().strip()
    
    severity_patterns = {
        'súlyos': [
            r'\bsúlyos(?:an)?\b', r'\berős(?:en)?\b', r'\bnagyon(?:\s+(?:fáj|rossz|kellemetlen))\b',
            r'\bborzasztó(?:an)?\b', r'\biszonyú(?:an)?\b', r'\belviselhetetlen\b',
            r'\bkezelhetetlen\b', r'\bmegszüntethetetlen\b', r'^szúlyos$'  # Elírás kezelés
        ],
        'enyhe': [
            r'\benyhe(?:n)?\b', r'\bkis(?:sé)?\b', r'\bkicsit\b', r'\bgyenge(?:n)?\b',
            r'\bkevéssé\b', r'\bnem\s+(?:nagyon|túl)\b', r'\belfogadható\b', r'\balig\b', r'\bledz\b'
        ],
        'közepes': [
        r'\bközepes(?:en)?\b', r'\bnem túl erős\b', r'\bzavaró\b', r'\bnem vészes\b'
    ]
    }
    
    for severity, patterns in severity_patterns.items():
        for pattern in patterns:
            if re.search(pattern, lower_input):
                return severity
    
    return None

def enhanced_gender_extraction(user_input, context=None):
    """
    Bővített nem felismerés KONTEXTUS figyelembevétellel.
    """
    if st.session_state.patient_data.get('gender'):
        return None
    
    # CSAK akkor próbáljuk meg, ha nemet kérdezünk
    if context != 'gender':
        return None
    
    lower_input = user_input.lower().strip()
    
    gender_patterns = {
        'férfi': [
            r'\bférfi\b', r'\bffi\b', r'^férfi$', r'^f$',
            r'\bkisfiú\b', r'\bfiú\b', r'^kisfiú$'
        ],
        'nő': [
            r'\bnő\b', r'\bnői\b', r'^nő$', r'^n$',
            r'\bkislány\b', r'\blány\b', r'^kislány$'
        ]
    }
    
    for gender, patterns in gender_patterns.items():
        for pattern in patterns:
            if re.search(pattern, lower_input):
                return gender
    
    return None

def enhanced_simple_response_extraction(user_input, context=None):
    """
    Egyszerű válaszok felismerése KONTEXTUS figyelembevétellel.
    """
    extracted = {}
    input_trimmed = user_input.strip()
    
    # Kontextus alapú extraction
    if context == 'age':
        age = enhanced_age_extraction(input_trimmed, context)
        if age:
            extracted['age'] = age
    
    elif context == 'duration':
        duration = enhanced_duration_extraction(input_trimmed, context)
        if duration:
            extracted['duration'] = duration
    
    elif context == 'severity':
        severity = enhanced_severity_extraction(input_trimmed, context)
        if severity:
            extracted['severity'] = severity
    
    elif context == 'gender':
        gender = enhanced_gender_extraction(input_trimmed, context)
        if gender:
            extracted['gender'] = gender
    
    # Negatív válasz bármilyen kontextusban
    if detect_negative_response(input_trimmed):
        st.session_state.asked_for_more_symptoms = True

    # Negatív válasz bármilyen kontextusban
    if detect_negative_response(user_input):
        st.session_state.asked_for_more_symptoms = True

        # ÚJ: tárold üres listával a negatív választ
        if context == 'existing_conditions' and not st.session_state.patient_data.get('existing_conditions'):
            st.session_state.patient_data['existing_conditions'] = []
            st.session_state.negatives_logged.add('existing_conditions')

        if context == 'medications' and not st.session_state.patient_data.get('medications'):
            st.session_state.patient_data['medications'] = []
            st.session_state.negatives_logged.add('medications')
    
    return extracted

def detect_negative_response(user_input):
    """Negatív válaszok felismerése (változatlan)."""
    lower_input = user_input.lower().strip()
    
    negative_patterns = [
        r'\bnincs?(?:\s+(?:több|más|egyéb))?\b',
        r'\bnem\s+(?:tudok|tudnék|ismerek)\b',
        r'\bsemmi(?:\s+(?:más|több|egyéb))?\b',
        r'\bcsak\s+ennyi\b',
        r'\bmás\s+nincs?\b',
        r'\btöbb\s+nincs?\b',
        r'\bnincs\s+ilyen?\b',
    ]
    
    for pattern in negative_patterns:
        if re.search(pattern, lower_input):
            return True
    
    return False

# ===== EREDETI FÜGGVÉNYEK (VÁLTOZATLAN) =====

def extract_medical_info_with_gpt(user_input):
    """GPT alapú adatkinyerés function call-lal. JAVÍTOTT VERZIÓ."""
    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": """Te egy egészségügyi asszisztens vagy. Kinyered az egészségügyi adatokat a szövegből.

FONTOS SZABÁLYOK:
- Ha a felhasználó azt mondja, hogy "nincs", "nem", "semmi", "nem szedek", "nincsenek", akkor NE adj vissza üres listát
- Negatív válaszok esetén egyszerűen NE hívd meg a function-t
- Csak akkor használd a function call-t, ha konkrét adatot találsz (tünetet, gyógyszert, betegséget, stb.)
- "nincs" = ne csinálj semmit, ne hívd a function-t"""},
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
    """
    Kézi információ kinyerés JAVÍTOTT VERZIÓ - kontextus figyelembevétellel.
    """
    lower_input = user_input.lower()
    extracted_anything = False
    
    # Kontextus meghatározása
    context = get_current_question_context()

    # 🔍 DEBUG INFORMÁCIÓK
    print(f"🔍 DEBUG - User input: '{user_input}'")
    print(f"🔍 DEBUG - Context: {context}")
    print(f"🔍 DEBUG - Current medications: {st.session_state.patient_data.get('medications')}")
    
    # Negatív válasz ellenőrzése
    is_negative = detect_negative_response(user_input)
    print(f"🔍 DEBUG - Is negative response: {is_negative}")
    
    # === KONTEXTUS ALAPÚ EXTRACTION ===
    simple_extracted = enhanced_simple_response_extraction(user_input, context)
    for field, value in simple_extracted.items():
        if not st.session_state.patient_data.get(field):
            # Validáció
            if validate_extraction_result(field, value, context):
                st.session_state.patient_data[field] = value
                extracted_anything = True
    
    # === TÜNETFELISMERÉS (EREDETI - VÁLTOZATLAN) ===
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
    
    # === KRÓNIKUS BETEGSÉGEK FELISMERÉSE ===
    if context == 'existing_conditions' or not context:
        chronic_conditions = {
            'magas vérnyomás': ['magas vérnyomás', 'hipertónia', 'vérnyomás'],
            'cukorbetegség': ['cukorbetegség', 'diabétesz', 'diabetes'],
            'asztma': ['asztma', 'légúti', 'légzés'],
            'allergia': ['allergia', 'allergiás', 'túlérzékenység']
        }
        
        for condition, keywords in chronic_conditions.items():
            if any(keyword in lower_input for keyword in keywords):
                current_conditions = st.session_state.patient_data.get('existing_conditions', [])
                if condition not in current_conditions:
                    current_conditions.append(condition)
                    st.session_state.patient_data['existing_conditions'] = current_conditions
                    extracted_anything = True

    # === EGYETLEN NEGATÍV VÁLASZ KEZELÉS (DUPLIKÁLT RÉSZ TÖRÖLVE) ===
    # Kontextus alapú negatív válasz kezelés
    # === NEGATÍV VÁLASZ KEZELÉS ===
    if detect_negative_response(user_input):
        print(f"🔍 DEBUG - Negative response detected!")
        
        if context == 'existing_conditions' and not st.session_state.patient_data.get('existing_conditions'):
            print(f"🔍 DEBUG - Setting existing_conditions to ['nincs']")
            st.session_state.patient_data['existing_conditions'] = ["nincs"]
            extracted_anything = True

        if context == 'medications' and not st.session_state.patient_data.get('medications'):
            print(f"🔍 DEBUG - Setting medications to ['nincs']")
            st.session_state.patient_data['medications'] = ["nincs"]
            extracted_anything = True
        else:
            print(f"🔍 DEBUG - Medications NOT set because context={context} or medications already exists: {st.session_state.patient_data.get('medications')}")
    
    print(f"🔍 DEBUG - Final medications: {st.session_state.patient_data.get('medications')}")
    print(f"🔍 DEBUG - Extracted anything: {extracted_anything}")
    
    return extracted_anything

    # === NEGATÍV VÁLASZOK KEZELÉSE (EGYETLEN HELYEN) ===
    """Negatív válaszok felismerése JAVÍTOTT VERZIÓ."""
def detect_negative_response(user_input):
    lower_input = user_input.lower().strip()
    
    negative_patterns = [
        # Eredeti minták
        r'\bnincs?(?:\s+(?:több|más|egyéb))?\b',
        r'\bnem\s+(?:tudok|tudnék|ismerek)\b',
        r'\bsemmi(?:\s+(?:más|több|egyéb))?\b',
        r'\bcsak\s+ennyi\b',
        r'\bmás\s+nincs?\b',
        r'\btöbb\s+nincs?\b',
        r'\bnincs\s+ilyen?\b',
        
        # ÚJ minták a gyógyszerekhez
        r'\bnem\s+szedek?\b',
        r'\bnem\s+szedtem\b',
        r'\bnem\s+veszek?\b',
        r'\bnem\s+használok?\b',
        r'\bsemmit\s+(?:nem\s+)?szedek?\b',
        r'\bsemmilyen\s+gyógyszert?\b',
        r'\begyáltalán\s+(?:nem|nincs)\b',
        
        # Dühös válaszok 
        r'\bnem\s+szedek\s+bazdmeg\b',
        r'\bfaszom\s+(?:nem|nincs)\b',
        r'\bbasszus\s+(?:nem|nincs)\b',
        
        # Egyszerű tagadások
        r'^nem$',
        r'^nincs$',
        r'^semmi$',
        r'^semmit$',
        r'^semmilyent$',
    ]
    
    for pattern in negative_patterns:
        if re.search(pattern, lower_input):
            return True
    
    return False

def process_special_cases(user_input):
    """Speciális esetek kezelése (változatlan)."""
    if detect_negative_response(user_input):
        st.session_state.asked_for_more_symptoms = True
        return True
    return False

def extract_all_medical_info(user_input):
    """
    Komplett adatkinyerési folyamat JAVÍTOTT VERZIÓ.
    """
    # 1. GPT alapú kinyerés próbálkozás
    gpt_success = extract_medical_info_with_gpt(user_input)
    
    # 2. Manual extraction MINDIG fusson le (negatív válaszok miatt)
    manual_success = manual_extract_info(user_input)
    
    # 3. Speciális esetek
    special_case = process_special_cases(user_input)
    
    return gpt_success or manual_success or special_case

# ===== DEBUGGING FUNKCIÓK =====

def debug_extraction_with_context(user_input):
    """Debug funkció kontextus információkkal."""
    context = get_current_question_context()
    print(f"🔍 Debug extraction:")
    print(f"Input: '{user_input}'")
    print(f"Context: {context}")
    
    # Tesztelés
    simple_result = enhanced_simple_response_extraction(user_input, context)
    print(f"Simple extraction result: {simple_result}")
    
    # Validáció tesztelés
    for field, value in simple_result.items():
        valid = validate_extraction_result(field, value, context)
        print(f"Validation {field}={value}: {valid}")
    
    return {
        'context': context,
        'extraction': simple_result,
        'chat_history_last': st.session_state.chat_history[-1] if st.session_state.chat_history else None
    }