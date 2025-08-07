# =============================================================================
# core/config.py
# =============================================================================
"""
Konfigurációs beállítások és konstansok a medical chatbot számára.
JAVÍTOTT VERZIÓ - "közepes" súlyosság hozzáadásával.
"""
import os
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  # Környezeti változók betöltése .env fájlból

# OpenAI kliens inicializálása
def get_openai_client():
    """OpenAI kliens létrehozása."""
    #client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    return client

# Streamlit konfiguráció
STREAMLIT_CONFIG = {
    "page_title": "Egészségügyi Chatbot",
    "page_icon": "🩺",
    "layout": "wide",
    "initial_sidebar_state": "auto"
}

# Tool schema az új OpenAI formátumban - JAVÍTOTT VERZIÓ
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "extract_medical_info",
        "description": "Páciens panaszának szöveges értelmezése strukturált egészségügyi mezőkké",
        "parameters": {
            "type": "object",
            "properties": {
                "age": {"type": "integer", "description": "A páciens életkora"},
                "gender": {"type": "string", "enum": ["férfi", "nő"], "description": "A páciens biológiai neme"},
                "symptoms": {"type": "array", "items": {"type": "string"}, "description": "A páciens tünetei"},
                "duration": {"type": "string", "description": "Tünetek időtartama (pl. 2 napja, 1 hete)"},
                "severity": {"type": "string", "enum": ["enyhe", "közepes", "súlyos"], "description": "Tünetek súlyossága"},  
                "existing_conditions": {"type": "array", "items": {"type": "string"}, "description": "Meglévő betegségek, allergiák"},
                "medications": {"type": "array", "items": {"type": "string"}, "description": "Szedett gyógyszerek, vitaminok"}
            },
            "required": []
        }
    }
}

# Alternatív terápiás tippek
ALTERNATIVE_TIPS = {
    "fejfájás": "Igyál több vizet, kerüld az erős fényt, és próbálj meg relaxálni.",
    "torokfájás": "Langyos sós vizes gargalizálás és kamillatea enyhítheti a panaszokat.",
    "köhögés": "Mézes tea és párás levegő segíthet a köhögés csillapításában.",
    "hasfájás": "Borsmentatea vagy meleg borogatás nyugtathatja a hasat.",
    "hányinger": "Gyömbéres tea vagy lassú, mély légzés csökkentheti a hányingert.",
    "szédülés": "Lassú mozgás, ülő vagy fekvő helyzet, és folyadékpótlás segíthet." 
}

# Alapértelmezett üdvözlő üzenet
WELCOME_MESSAGE = {
    "role": "assistant", 
    "content": """Üdvözlöm! Én egy egészségügyi asszisztens vagyok. 

**Hogyan működik a konzultáció:**
1. 📝 Először összegyűjtöm az összes szükséges információt Önről
2. 🔍 Majd elkészítem a részletes értékelést  
3. 📄 Végül letöltheti az összefoglalót

**Kezdjük!** Kérem, írja le, mi a panasza vagy milyen tünetei vannak."""
}

# Alapértelmezett patient data struktúra
DEFAULT_PATIENT_DATA = {
    "age": None,
    "gender": None,
    "symptoms": [],
    "duration": None,
    "severity": None,
    "existing_conditions": [],
    "medications": []
}