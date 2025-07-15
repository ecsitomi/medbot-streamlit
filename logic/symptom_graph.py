# =============================================================================
# logic/symptom_graph.py
# =============================================================================
"""
Tünet-összefüggések és intelligens follow-up kérdések kezelése.
A meglévő medical chatbot tüneteivel kompatibilis reasoning motor.
"""

# Tünet-kapcsolati szabályok a meglévő tünetekkel
# Kulcs: tuple a tünetekből, Érték: follow-up kérdések listája
SYMPTOM_DEPENDENCIES = {
    # Fertőzéses tünetek kombinációja
    ("láz", "fáradtság"): [
        "Milyen magas volt legutóbb a láza? (pl. 38°C, 39°C)",
        "Jól tudott aludni az éjjel, vagy zavarta a betegség?"
    ],
    
    ("láz", "torokfájás"): [
        "Nehezére esik a nyelés?",
        "Van-e köhögése is a torokfájás mellett?"
    ],
    
    ("láz", "köhögés"): [
        "Milyen típusú a köhögése? (száraz vagy váladékos)",
        "Van-e mellkasi fájdalma a köhögéskor?"
    ],
    
    # Emésztőrendszeri problémák
    ("hányás", "hasmenés"): [
        "Hány alkalommal fordult elő a hányás az elmúlt 24 órában?",
        "Van-e hasfájása is a tünetek mellett?"
    ],
    
    ("hasmenés", "fáradtság"): [
        "Elegendő folyadékot fogyaszt? (fontos a kiszáradás elkerülése)",
        "Van-e szédülése is?"
    ],
    
    # Neurológiai/általános tünetek
    ("fejfájás", "fáradtság"): [
        "Milyen jellegű a fejfájása? (tompa, lüktető, szúró)",
        "Befolyásolja-e a fény vagy a zaj a fejfájását?"
    ],
    
    ("fejfájás", "láz"): [
        "Van-e nyaki merevsége?",
        "Émelyeg vagy hányinger is társul a fejfájáshoz?"
    ],
    
    # Légúti problémák
    ("torokfájás", "köhögés"): [
        "Mikor rosszabb a torokfájás? (reggel, este, nyeléskor)",
        "Látható-e valamilyen elváltozás a torokban? (vörösség, foltok)"
    ]
}

# Egyedi tünetek esetén is adhatunk speciális kérdéseket
SINGLE_SYMPTOM_QUESTIONS = {
    "fejfájás": [
        "Hol érzi leginkább a fejfájást? (homlok, halánték, tarkó)"
    ],
    
    "láz": [
        "Mérte-e a testhőmérsékletét? Ha igen, mennyi volt?"
    ],
    
    "köhögés": [
        "Mikor rosszabb a köhögés? (éjjel, reggel, fizikai aktivitáskor)"
    ],
    
    "torokfájás": [
        "A torokfájás mellett van-e duzzadt nyirokcsomó a nyakán?"
    ],
    
    "hasmenés": [
        "Milyen gyakori a hasmenés? (naponta hányszor)"
    ],
    
    "hányás": [
        "Mi váltotta ki a hányást? (étkezés, szag, mozgás)"
    ],
    
    "fáradtság": [
        "A fáradtság mikor jelentkezik leginkább? (reggel, este, egész nap)"
    ]
}

def get_symptom_combinations(symptoms_list):
    """
    Megkeresi az összes lehetséges tünet-kombinációt a SYMPTOM_DEPENDENCIES alapján.
    
    Args:
        symptoms_list (list): A páciens tüneteinek listája
        
    Returns:
        list: Talált kombinációk kulcsai
    """
    if not symptoms_list or len(symptoms_list) < 2:
        return []
    
    found_combinations = []
    symptoms_set = set(symptoms_list)
    
    for combo_key in SYMPTOM_DEPENDENCIES.keys():
        if set(combo_key).issubset(symptoms_set):
            found_combinations.append(combo_key)
    
    return found_combinations

def get_suggested_followup_questions(symptoms_list, asked_questions=None):
    """
    Tünet-alapú follow-up kérdések generálása.
    
    Args:
        symptoms_list (list): A páciens tüneteinek listája
        asked_questions (set, optional): Már feltett kérdések (ismétlés elkerülése)
        
    Returns:
        dict: {
            'combination_questions': [...],  # Tünet-kombináció alapú kérdések
            'single_questions': [...],       # Egyedi tünet kérdések
            'source_combinations': [...]     # Melyik kombinációból jöttek a kérdések
        }
    """
    if asked_questions is None:
        asked_questions = set()
    
    result = {
        'combination_questions': [],
        'single_questions': [],
        'source_combinations': []
    }
    
    # Kombinációs kérdések keresése
    combinations = get_symptom_combinations(symptoms_list)
    
    for combo in combinations:
        questions = SYMPTOM_DEPENDENCIES[combo]
        for question in questions:
            if question not in asked_questions:
                result['combination_questions'].append(question)
                result['source_combinations'].append(combo)
    
    # Egyedi tünet kérdések (ha nincs kombináció, vagy kiegészítésként)
    if not result['combination_questions']:
        for symptom in symptoms_list:
            if symptom in SINGLE_SYMPTOM_QUESTIONS:
                questions = SINGLE_SYMPTOM_QUESTIONS[symptom]
                for question in questions:
                    if question not in asked_questions:
                        result['single_questions'].append(question)
    
    return result

def has_reasoning_questions_available(symptoms_list, asked_questions=None):
    """
    Ellenőrzi, hogy vannak-e elérhető reasoning kérdések.
    
    Args:
        symptoms_list (list): A páciens tüneteinek listája
        asked_questions (set, optional): Már feltett kérdések
        
    Returns:
        bool: True, ha vannak elérhető kérdések
    """
    suggestions = get_suggested_followup_questions(symptoms_list, asked_questions)
    return bool(suggestions['combination_questions'] or suggestions['single_questions'])

def get_next_reasoning_question(symptoms_list, asked_questions=None):
    """
    A következő reasoning kérdés kiválasztása prioritás alapján.
    
    Prioritás:
    1. Kombinációs kérdések (több tünet összefüggése)
    2. Egyedi tünet kérdések
    
    Args:
        symptoms_list (list): A páciens tüneteinek listája
        asked_questions (set, optional): Már feltett kérdések
        
    Returns:
        str or None: A következő kérdés, vagy None ha nincs több
    """
    suggestions = get_suggested_followup_questions(symptoms_list, asked_questions)
    
    # Prioritás: kombinációs kérdések először
    if suggestions['combination_questions']:
        return suggestions['combination_questions'][0]
    
    # Ha nincs kombinációs, akkor egyedi
    if suggestions['single_questions']:
        return suggestions['single_questions'][0]
    
    return None

def get_reasoning_context(symptoms_list):
    """
    Kontextus információ a reasoning kérdésekhez (debugging/logging célra).
    
    Args:
        symptoms_list (list): A páciens tüneteinek listája
        
    Returns:
        dict: Kontextus információk
    """
    combinations = get_symptom_combinations(symptoms_list)
    
    return {
        'total_symptoms': len(symptoms_list),
        'symptoms': symptoms_list,
        'found_combinations': combinations,
        'has_combinations': len(combinations) > 0,
        'available_single_questions': [s for s in symptoms_list if s in SINGLE_SYMPTOM_QUESTIONS]
    }

# Teszteléshez és debugging célra
def _debug_symptom_analysis(symptoms_list):
    """
    Debug információk a tünet elemzésről.
    Csak development/testing célra.
    """
    print(f"🔍 Symptom Analysis Debug:")
    print(f"Input symptoms: {symptoms_list}")
    
    context = get_reasoning_context(symptoms_list)
    print(f"Context: {context}")
    
    suggestions = get_suggested_followup_questions(symptoms_list)
    print(f"Suggestions: {suggestions}")
    
    next_question = get_next_reasoning_question(symptoms_list)
    print(f"Next reasoning question: {next_question}")
    
    return {
        'context': context,
        'suggestions': suggestions,
        'next_question': next_question
    }