# =============================================================================
# logic/prompt_builder.py
# =============================================================================
"""
Centralizált GPT prompt építés a medical chatbot számára.
Kompatibilis a meglévő gpt_communication.py struktúrával.
"""

# A meglévő kódból átvett adatmezők és leírásaik
DATA_FIELD_MAPPINGS = {
    "symptoms": {
        "display_name": "Tünetek",
        "description": "Tünetek (fájdalom, diszkomfort, stb.)",
        "examples": "fejfájás, torokfájás, láz, köhögés",
        "question_style": "direct"
    },
    "additional_symptoms": {
        "display_name": "További tünetek", 
        "description": "További tünetek keresése az első után",
        "examples": "további fájdalom, diszkomfort",
        "question_style": "followup"
    },
    "duration": {
        "display_name": "Időtartam",
        "description": "Tünetek időtartama (mióta tart)",
        "examples": "2 napja, 1 hete, 3 hónapja",
        "question_style": "specific"
    },
    "severity": {
        "display_name": "Súlyosság",
        "description": "Súlyosság (enyhe/súlyos)",
        "examples": "enyhe, súlyos, közepes",
        "question_style": "scale"
    },
    "age": {
        "display_name": "Életkor",
        "description": "Életkor",
        "examples": "25, 45, 67",
        "question_style": "simple"
    },
    "gender": {
        "display_name": "Nem",
        "description": "Biológiai Nem (férfi/nő)",
        "examples": "férfi, nő",
        "question_style": "simple"
    },
    "existing_conditions": {
        "display_name": "Krónikus betegségek",
        "description": "Krónikus betegségek, allergiák",
        "examples": "magas vérnyomás, cukorbetegség, allergia",
        "question_style": "optional"
    },
    "medications": {
        "display_name": "Gyógyszerek",
        "description": "Szedett gyógyszerek, vitaminok",
        "examples": "vérnyomáscsökkentő, vitamin D, fájdalomcsillapító",
        "question_style": "optional"
    }
}

# Hangnem és stílus beállítások
TONE_SETTINGS = {
    "friendly": {
        "greeting": "Köszönöm",
        "transition": "Most",
        "politeness": "Kérem",
        "encouragement": "Ez segít a pontosabb értékelésben"
    },
    "professional": {
        "greeting": "Köszönöm az információt",
        "transition": "A következő lépésben",
        "politeness": "Kérem, adja meg", 
        "encouragement": "Ez fontos az értékeléshez"
    },
    "empathetic": {
        "greeting": "Köszönöm, hogy megosztotta",
        "transition": "Ahhoz, hogy jobban segíthessek",
        "politeness": "Ha nem probléma",
        "encouragement": "Minden információ segít abban, hogy jobban megértsem a helyzetét"
    }
}

def build_system_prompt(tone="friendly", language="hu"):
    """
    Egységes system prompt építése a medical chatbot GPT hívásaihoz.
    
    Args:
        tone (str): Hangnem ("friendly", "professional", "empathetic")
        language (str): Nyelv (jelenleg csak "hu" támogatott)
        
    Returns:
        str: A system prompt
    """
    base_prompt = """Te egy tapasztalt egészségügyi asszisztens vagy, aki empátiával és szakértelemmel tesz fel kérdéseket a pácienseknek. Magázódva beszélj.

FELADATOD: Természetes, barátságos kérdést generálni, ami pontosan EGY hiányzó adatot gyűjt be.

SZABÁLYOK:
1. Csak EGY adatot kérdezz meg egyszerre
2. Légy empatikus és természetes
3. Használd a kontextust és a korábbi beszélgetést
4. Rövid, érthető kérdést tégy fel
5. Ha szükséges, adj példákat a válaszhoz
6. Magyar nyelven válaszolj. Magázódva beszélj

ADATMEZŐK MAGYARÁZATA:
- symptoms: Tünetek (fájdalom, diszkomfort, stb.)
- additional_symptoms: További tünetek keresése az első után
- duration: Tünetek időtartama (mióta tart)
- severity: Súlyosság (enyhe/közepes/súlyos)
- age: Életkor
- gender: Nem (férfi/nő)
- existing_conditions: Krónikus betegségek, allergiák
- medications: Szedett gyógyszerek, vitaminok"""

    if tone == "professional":
        base_prompt += "\n\nHANGNEM: Szakmai, de barátságos. Használj orvosi terminológiát, de maradj érthető. Magázódva beszélj"
    elif tone == "empathetic":
        base_prompt += "\n\nHANGNEM: Különösen empatikus és támogató. Hangsúlyozd, hogy érted a páciens helyzetét. Magázódva beszélj vele."
    else:  # friendly (default)
        base_prompt += "\n\nHANGNEM: Természetes, barátságos beszélgetés stílus. Kerüld a túl formális nyelvet. Magázódva beszélj"
    
    return base_prompt

def build_context_summary(current_data, conversation_history=None):
    """
    Kontextus összefoglaló készítése a GPT számára.
    
    Args:
        current_data (dict): Jelenlegi patient_data
        conversation_history (list, optional): Chat history utolsó üzenetei
        
    Returns:
        str: Formázott kontextus összefoglaló
    """
    summary_parts = []
    
    # Jelenlegi adatok összefoglalása
    if current_data:
        data_summary = []
        for key, value in current_data.items():
            if value and value != "nincs":  # Csak a kitöltött mezőket
                field_info = DATA_FIELD_MAPPINGS.get(key, {})
                display_name = field_info.get("display_name", key)
                
                if isinstance(value, list) and value:
                    formatted_value = ", ".join(value)
                else:
                    formatted_value = str(value)
                
                data_summary.append(f"{display_name}: {formatted_value}")
        
        if data_summary:
            summary_parts.append("Jelenlegi adataim a páciensről:")
            summary_parts.extend(data_summary)
        else:
            summary_parts.append("Még nincsenek adatok")
    
    # Beszélgetés történet (utolsó 4 üzenet)
    if conversation_history and len(conversation_history) > 1:
        summary_parts.append("\nLegutóbbi beszélgetés:")
        recent_messages = conversation_history[-4:]  # Utolsó 4 üzenet
        for msg in recent_messages:
            role = "Asszisztens" if msg.get("role") == "assistant" else "Páciens"
            content = msg.get("content", "")
            # Rövidítés hosszú üzenetek esetén
            if len(content) > 150:
                content = content[:150] + "..."
            summary_parts.append(f"{role}: {content}")
    else:
        summary_parts.append("\nEz az első interakció")
    
    return "\n".join(summary_parts)

def build_field_specific_prompt(field_name, current_data, tone="empathetic"):
    """
    Mezőspecifikus prompt rész építése.
    
    Args:
        field_name (str): A hiányzó mező neve
        current_data (dict): Jelenlegi patient_data
        tone (str): Hangnem
        
    Returns:
        str: Mezőspecifikus prompt instrukciók
    """
    field_info = DATA_FIELD_MAPPINGS.get(field_name, {})
    tone_settings = TONE_SETTINGS.get(tone, TONE_SETTINGS["empathetic"])
    
    if not field_info:
        return f"KÖVETKEZŐ HIÁNYZÓ ADAT: {field_name}\n\nKérlek, tegyél fel EGY természetes kérdést, ami ezt az adatot gyűjti be."
    
    prompt_parts = [f"KÖVETKEZŐ HIÁNYZÓ ADAT: {field_name}"]
    
    # Kontextus alapú instrukciók
    if field_name == "additional_symptoms" and current_data.get("symptoms"):
        current_symptoms = ", ".join(current_data["symptoms"])
        prompt_parts.append(f"A páciens már említette: {current_symptoms}")
        prompt_parts.append("Kérdezz rá, vannak-e TOVÁBBI tünetek. Legyen egyértelmű, hogy a már említetteken felül keresel valamit.")
    
    elif field_name == "duration" and current_data.get("symptoms"):
        symptoms_text = ", ".join(current_data["symptoms"])
        prompt_parts.append(f"A páciens tünetei: {symptoms_text}")
        prompt_parts.append("Kérdezz rá az időtartamra természetes módon, példákkal.")
    
    elif field_name == "severity":
        prompt_parts.append("Kérdezz rá a tünetek súlyosságára egyszerű, érthető módon.")
        if tone == "empathetic":
            prompt_parts.append("Légy különösen empatikus, mert a fájdalom/kellemetlenség szubjektív.")
    
    elif field_name in ["existing_conditions", "medications"]:
        prompt_parts.append(f"Ez opcionális információ. Tedd világossá, hogy ha nincs, azt is elmondhatja.")
        prompt_parts.append("Adj példákat, hogy jobban megértsék mit keresel.")
    
    # Stílus és példák
    examples = field_info.get("examples", "")
    if examples:
        prompt_parts.append(f"Példák amikre gondolsz: {examples}")
    
    encouragement = tone_settings.get("encouragement", "")
    if encouragement and field_name not in ["existing_conditions", "medications"]:
        prompt_parts.append(f"Emlékeztesd a páciensre: {encouragement}")
    
    prompt_parts.append("\nKérlek, tegyél fel EGY természetes kérdést, ami ezt az adatot gyűjti be. A kérdés legyen empatikus és a kontextushoz illő. Magázódva beszélj.")
    
    return "\n".join(prompt_parts)

def build_complete_prompt(field_name, current_data, conversation_history=None, tone="empathetic", language="hu"):
    """
    Teljes GPT prompt összeállítása a következő kérdés generálásához.
    Kompatibilis a meglévő get_next_question_gpt() funkcióval.
    
    Args:
        field_name (str): Hiányzó mező neve
        current_data (dict): Jelenlegi patient_data
        conversation_history (list, optional): Chat history
        tone (str): Hangnem
        language (str): Nyelv
        
    Returns:
        dict: {"system": "system_prompt", "user": "user_prompt"}
    """
    system_prompt = build_system_prompt(tone, language)
    
    context_summary = build_context_summary(current_data, conversation_history)
    field_prompt = build_field_specific_prompt(field_name, current_data, tone)
    
    user_prompt = f"""KONTEXTUS:
{context_summary}

{field_prompt}"""
    
    return {
        "system": system_prompt,
        "user": user_prompt
    }

def build_reasoning_question_prompt(reasoning_question, current_data, tone="empathetic", language="hu"):
    """
    Reasoning kérdések esetén speciális prompt (symptom_graph.py-ból jövő kérdésekhez).
    
    Args:
        reasoning_question (str): A symptom_graph.py által javasolt kérdés
        current_data (dict): Jelenlegi patient_data
        tone (str): Hangnem
        language (str): Nyelv
        
    Returns:
        dict: {"system": "system_prompt", "user": "user_prompt"}
    """
    system_prompt = """Te egy tapasztalt egészségügyi asszisztens vagy, aki intelligens follow-up kérdéseket tesz fel a páciens tünetei alapján.

FELADATOD: A megadott reasoning kérdést természetes, empatikus módon megfogalmazni.

SZABÁLYOK:
1. Használd a megadott kérdést alapként, de tedd természetessé
2. Légy empatikus és támogató
3. Magyarázd meg röviden, miért fontos ez a kérdés
4. Magyar nyelven válaszolj
5. Kerüld a túl orvosi nyelvet
6. Magázódva beszélj"""

    tone_settings = TONE_SETTINGS.get(tone, TONE_SETTINGS["friendly"])
    
    symptoms = current_data.get("symptoms", [])
    symptoms_text = ", ".join(symptoms) if symptoms else "tünetei"
    
    user_prompt = f"""KONTEXTUS:
A páciens tünetei: {symptoms_text}

REASONING KÉRDÉS: {reasoning_question}

FELADAT: Fogalmazd át ezt a kérdést természetes, empatikus módon. Add hozzá egy rövid magyarázatot (1 mondatban), hogy miért fontos ez a kérdés az értékeléshez.

Használd ezt a hangnemet: {tone}"""
    
    return {
        "system": system_prompt,
        "user": user_prompt
    }

# Diagnosis, therapy és specialist advice promptok (meglévő funkciókhoz)
def build_diagnosis_prompt(symptoms):
    """Diagnózis prompt építése (kompatibilis a generate_diagnosis()-szel)."""
    return {
        "system": "Te egy egészségügyi asszisztens vagy, aki laikus tünetleírás alapján segít diagnózisban gondolkodni. Magázódva válaszolj!",
        "user": f"A következő tünetek alapján javasolj egy lehetséges laikus diagnózist röviden, magyarul, magázódva: {', '.join(symptoms)}"
    }

def build_alt_therapy_prompt(symptoms, diagnosis):
    """Alternatív terápia prompt építése (kompatibilis a generate_alt_therapy()-vel)."""
    return {
        "system": "Te egy egészségügyi asszisztens vagy, aki természetes enyhítő javaslatokat fogalmaz meg tünetek és diagnózis alapján. Magázódva válaszolj!",
        "user": f"A következő tünetek és laikus diagnózis alapján javasolj alternatív (otthoni vagy természetes) enyhítő megoldásokat magyarul, röviden:\nTünetek: {', '.join(symptoms)}\nDiagnózis: {diagnosis}"
    }

def build_specialist_advice_prompt(symptoms, diagnosis):
    """Szakorvos javaslat prompt építése (kompatibilis a generate_specialist_advice()-vel). Magázódva válaszolj!"""
    return {
        "system": "Te egy egészségügyi asszisztens vagy, aki megfelelő szakorvost javasol a tünetek és feltételezett diagnózis alapján. Magázódva válaszolj!",
        "user": f"A következő tünetek és laikus diagnózis alapján javasolj szakorvost magázódva, akihez érdemes fordulni: {', '.join(symptoms)} — Diagnózis: {diagnosis}"
    }