import streamlit as st
from openai import OpenAI
import json
import re
import datetime
import hashlib
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import os

# OpenAI kliens inicializálása
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Streamlit konfiguráció
st.set_page_config(
    page_title="Egészségügyi Chatbot",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="auto"
)

# Session state inicializálás
def initialize_session_state():
    """Session state változók inicializálása."""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role": "assistant", "content": """Üdvözlöm! Én egy egészségügyi asszisztens vagyok. 

**Hogyan működik a konzultáció:**
1. 📝 Először összegyűjtöm az összes szükséges információt Önről
2. 🔍 Majd elkészítem a részletes orvosi értékelést  
3. 📄 Végül letöltheti az összefoglalót

**Kezdjük!** Kérem, írja le, mi a panasza vagy milyen tünetei vannak."""}
        ]
    
    if "patient_data" not in st.session_state:
        st.session_state.patient_data = {
            "age": None,
            "gender": None,
            "symptoms": [],
            "duration": None,
            "severity": None,
            "existing_conditions": [],
            "medications": []
        }

    if "triage_level" not in st.session_state:
        st.session_state.triage_level = ""

    if "alt_therapy" not in st.session_state:
        st.session_state.alt_therapy = ""

    if "diagnosis" not in st.session_state:
        st.session_state.diagnosis = ""

    if "gpt_alt_therapy" not in st.session_state:
        st.session_state.gpt_alt_therapy = ""

    if "gpt_specialist_advice" not in st.session_state:
        st.session_state.gpt_specialist_advice = ""

    if "asked_for_more_symptoms" not in st.session_state:
        st.session_state.asked_for_more_symptoms = False

    # Sidebar frissítés tracking
    if "sidebar_last_update" not in st.session_state:
        st.session_state.sidebar_last_update = ""
    
    if "sidebar_container" not in st.session_state:
        st.session_state.sidebar_container = None

# Tool schema az új OpenAI formátumban
tool_schema = {
    "type": "function",
    "function": {
        "name": "extract_medical_info",
        "description": "Páciens panaszának szöveges értelmezése strukturált egészségügyi mezőkké",
        "parameters": {
            "type": "object",
            "properties": {
                "age": {"type": "integer", "description": "A páciens életkora"},
                "gender": {"type": "string", "enum": ["férfi", "nő"], "description": "A páciens neme"},
                "symptoms": {"type": "array", "items": {"type": "string"}, "description": "A páciens tünetei"},
                "duration": {"type": "string", "description": "Tünetek időtartama (pl. 2 napja, 1 hete)"},
                "severity": {"type": "string", "enum": ["enyhe", "súlyos"], "description": "Tünetek súlyossága"},
                "existing_conditions": {"type": "array", "items": {"type": "string"}, "description": "Meglévő betegségek, allergiák"},
                "medications": {"type": "array", "items": {"type": "string"}, "description": "Szedett gyógyszerek, vitaminok"}
            },
            "required": []
        }
    }
}

def update_state_from_function_output(output):
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

def get_next_question_gpt():
    """GPT alapú következő kérdés generálás a hiányzó adatok alapján."""
    try:
        data = st.session_state.patient_data
        chat_history = st.session_state.chat_history
        
        # Hiányzó adatok azonosítása
        missing_data = []
        symptoms_count = len(data.get("symptoms", []))
        
        if symptoms_count == 0:
            missing_data.append("symptoms")
        elif symptoms_count == 1 and not st.session_state.asked_for_more_symptoms:
            missing_data.append("additional_symptoms")
        
        if not data.get("duration"):
            missing_data.append("duration")
        if not data.get("severity"):
            missing_data.append("severity")
        if not data.get("age"):
            missing_data.append("age")
        if not data.get("gender"):
            missing_data.append("gender")
        if not data.get("existing_conditions"):
            missing_data.append("existing_conditions")
        if not data.get("medications"):
            missing_data.append("medications")
        
        # Ha nincs hiányzó adat, akkor kész vagyunk
        if not missing_data:
            return "Köszönöm az összes információt! Most elkészítem az orvosi értékelést."
        
        # Kontextus építése a GPT számára
        current_data_summary = []
        if data.get("symptoms"):
            current_data_summary.append(f"Tünetek: {', '.join(data['symptoms'])}")
        if data.get("age"):
            current_data_summary.append(f"Életkor: {data['age']} év")
        if data.get("gender"):
            current_data_summary.append(f"Nem: {data['gender']}")
        if data.get("duration"):
            current_data_summary.append(f"Időtartam: {data['duration']}")
        if data.get("severity"):
            current_data_summary.append(f"Súlyosság: {data['severity']}")
        if data.get("existing_conditions"):
            current_data_summary.append(f"Betegségek: {', '.join(data['existing_conditions'])}")
        if data.get("medications"):
            current_data_summary.append(f"Gyógyszerek: {', '.join(data['medications'])}")
        
        # Utolsó 3 üzenet a kontextushoz
        recent_conversation = ""
        if len(chat_history) > 1:
            recent_messages = chat_history[-4:]  # Utolsó 4 üzenet (2 kör)
            for msg in recent_messages:
                role = "Asszisztens" if msg["role"] == "assistant" else "Páciens"
                recent_conversation += f"{role}: {msg['content']}\n"
        
        # Prioritás meghatározása
        priority_field = missing_data[0]
        
        # GPT prompt összeállítása
        system_prompt = """Te egy tapasztalt egészségügyi asszisztens vagy, aki empátiával és szakértelemmel tesz fel kérdéseket a pácienseknek.

FELADATOD: Természetes, barátságos kérdést generálni, ami pontosan EGY hiányzó adatot gyűjt be.

SZABÁLYOK:
1. Csak EGY adatot kérdezz meg egyszerre
2. Légy empatikus és természetes
3. Használd a kontextust és a korábbi beszélgetést
4. Rövid, érthető kérdést tégy fel
5. Ha szükséges, adj példákat a válaszhoz
6. Magyar nyelven válaszolj

ADATMEZŐK MAGYARÁZATA:
- symptoms: Tünetek (fájdalom, diszkomfort, stb.)
- additional_symptoms: További tünetek keresése az első után
- duration: Tünetek időtartama (mióta tart)
- severity: Súlyosság (enyhe/súlyos)
- age: Életkor
- gender: Nem (férfi/nő)
- existing_conditions: Krónikus betegségek, allergiák
- medications: Szedett gyógyszerek, vitaminok"""

        user_prompt = f"""KONTEXTUS:
Jelenlegi adataim a páciensről:
{chr(10).join(current_data_summary) if current_data_summary else "Még nincsenek adatok"}

Legutóbbi beszélgetés:
{recent_conversation if recent_conversation else "Ez az első interakció"}

KÖVETKEZŐ HIÁNYZÓ ADAT: {priority_field}

Kérlek, tegyél fel EGY természetes kérdést, ami ezt az adatot gyűjti be. A kérdés legyen empatikus és a kontextushoz illő."""

        # GPT hívás
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )
        
        generated_question = response.choices[0].message.content.strip()
        
        # Speciális tracking beállítása
        if priority_field == "additional_symptoms":
            st.session_state.asked_for_more_symptoms = True
        
        return generated_question
        
    except Exception as e:
        st.error(f"Hiba a kérdés generálásában: {e}")
        # Fallback az eredeti statikus kérdésre
        return get_next_question_static()

def get_next_question_static():
    """Eredeti statikus kérdésgenerálás fallback-ként."""
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
        return "Kérem, adja meg a nemét (férfi/nő). Ez is fontos az értékeléshez."
    elif not data.get("existing_conditions"):
        return "Vannak-e ismert krónikus betegségei, allergiái vagy egyéb egészségügyi problémái? Ha nincs, írja be: 'nincs'."
    elif not data.get("medications"):
        return "Szed-e rendszeresen gyógyszereket vagy vitaminokat? Ha nem, írja be: 'nincs'."
    else:
        return "Köszönöm az összes információt! Most elkészítem az orvosi értékelést."

def process_chat_input_enhanced(user_input):
    """Továbbfejlesztett chat input feldolgozás GPT kérdésekkel."""
    try:
        # OpenAI function call próbálkozás (megtartjuk)
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Te egy egészségügyi asszisztens vagy. Kinyered az egészségügyi adatokat a szövegből."},
                    {"role": "user", "content": user_input}
                ],
                tools=[tool_schema],
                tool_choice="auto"
            )
            
            reply = response.choices[0].message
            if hasattr(reply, 'tool_calls') and reply.tool_calls:
                for tool_call in reply.tool_calls:
                    if tool_call.function.name == "extract_medical_info":
                        update_state_from_function_output(tool_call.function.arguments)
        except:
            pass
        
        # Manual extraction (megtartjuk)
        manual_extract_info(user_input)
        
        # Speciális esetek kezelése
        lower_input = user_input.lower()
        if any(phrase in lower_input for phrase in ['nincs több', 'más nincs', 'semmi más', 'csak ennyi', 'nincs']):
            st.session_state.asked_for_more_symptoms = True
        
        # Ellenőrizzük az állapotot
        if has_sufficient_data():
            if not st.session_state.triage_level:
                # Értékelés indítása
                data = st.session_state.patient_data
                assistant_reply = "✅ Köszönöm! Összegyűjtöttem az adatokat:\n\n"
                assistant_reply += f"• **Tünetek:** {', '.join(data.get('symptoms', []))}\n"
                if data.get('duration'): assistant_reply += f"• **Időtartam:** {data['duration']}\n"
                if data.get('severity'): assistant_reply += f"• **Súlyosság:** {data['severity']}\n"
                if data.get('age'): assistant_reply += f"• **Életkor:** {data['age']} év\n"
                if data.get('gender'): assistant_reply += f"• **Nem:** {data['gender']}\n"
                
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
            # GPT alapú következő kérdés - EZ AZ ÚJ RÉSZ!
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

def get_next_question():
    """Meghatározza a következő kérdést a hiányzó adatok alapján."""
    data = st.session_state.patient_data
    symptoms_count = len(data.get("symptoms", []))
    
    # Prioritás szerint ellenőrzés
    if symptoms_count == 0:
        return "Kérem, írja le részletesen, milyen tünetei vannak. Mi fáj, vagy mit tapasztal?"
    
    elif symptoms_count == 1 and not st.session_state.asked_for_more_symptoms:
        # Megjelöljük, hogy megkérdeztük
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
        return "Kérem, adja meg a nemét (férfi/nő). Ez is fontos az értékeléshez."
    
    elif not data.get("existing_conditions"):
        return "Vannak-e ismert krónikus betegségei, allergiái vagy egyéb egészségügyi problémái? Ha nincs, írja be: 'nincs'."
    
    elif not data.get("medications"):
        return "Szed-e rendszeresen gyógyszereket vagy vitaminokat? Ha nem, írja be: 'nincs'."
    
    else:
        return "Köszönöm az összes információt! Most elkészítem az orvosi értékelést."

def get_data_hash():
    """Patient data hash a változások követéséhez."""
    data_str = json.dumps(st.session_state.patient_data, sort_keys=True)
    return hashlib.md5(data_str.encode()).hexdigest()

def create_dynamic_sidebar():
    """Dinamikusan frissülő sidebar."""
    # Sidebar
    with st.sidebar:
        st.markdown("### ℹ️ Információk")
        
        # Jogi nyilatkozat
        with st.expander("📄 Jogi nyilatkozat", expanded=False):
            st.markdown("""
            **Fontos:** Ez az alkalmazás nem minősül orvosi tanácsadásnak. 
            Az itt megjelenített információk kizárólag tájékoztató jellegűek. 
            Tünetei alapján mindig konzultáljon egészségügyi szakemberrel.
            """)
        
        # GDPR nyilatkozat
        with st.expander("🔒 Adatvédelem (GDPR)", expanded=False):
            st.markdown("""
            A megadott adatokat nem tároljuk és nem továbbítjuk harmadik fél számára. 
            Az alkalmazás célja kizárólag a felhasználó önálló tájékozódásának támogatása. 
            Az adatokat kizárólag az aktuális munkamenet során, ideiglenesen használjuk fel.
            """)
        
        # Adatgyűjtés container - MINDIG frissül
        status_container = st.empty()
        
        # Adatok hash ellenőrzése
        current_hash = get_data_hash()
        
        # Ha van adat, akkor megjelenítjük a státuszt
        if any(v for v in st.session_state.patient_data.values() if v):
            with status_container.container():
                st.markdown("### 📊 Adatgyűjtés állapota")
                data = st.session_state.patient_data
                
                # Progress tracking
                total_fields = 7
                completed_fields = 0
                
                status_map = {
                    "age": "👤 Életkor",
                    "gender": "👤 Nem", 
                    "symptoms": "🩺 Tünetek",
                    "duration": "⏰ Időtartam",
                    "severity": "⚠️ Súlyosság",
                    "existing_conditions": "🏥 Betegségek",
                    "medications": "💊 Gyógyszerek"
                }
                
                for key, label in status_map.items():
                    value = data.get(key)
                    if key == "symptoms":
                        symptoms_count = len(value) if value else 0
                        if symptoms_count >= 2:
                            st.success(f"✅ {label}: {symptoms_count} tünet")
                            completed_fields += 1
                        elif symptoms_count == 1 and st.session_state.asked_for_more_symptoms:
                            st.success(f"✅ {label}: {symptoms_count} tünet (elegendő)")
                            completed_fields += 1
                        elif symptoms_count == 1:
                            st.warning(f"⏳ {label}: {symptoms_count} tünet (folyamatban)")
                        else:
                            st.error(f"❌ {label}: Hiányzik")
                    else:
                        if value and value != "nincs":
                            st.success(f"✅ {label}")
                            completed_fields += 1
                        else:
                            st.error(f"❌ {label}: Hiányzik")
                
                # Progress bar
                progress = completed_fields / total_fields
                st.progress(progress, text=f"Adatgyűjtés: {completed_fields}/{total_fields}")
                
                if completed_fields == total_fields:
                    st.success("🎉 Minden adat összegyűlt! Az orvosi értékelés elkészülhet.")
        
        # Hash mentése
        st.session_state.sidebar_last_update = current_hash
        
        # Exportálás gomb - CSAK ha van értékelés
        if st.session_state.triage_level:  # Ez jelzi, hogy megtörtént az értékelés
            st.markdown("### 📄 Exportálás")
            
            export_data = create_export_data()
            
            # JSON export
            st.download_button(
                label="📄 JSON letöltése",
                data=json.dumps(export_data, indent=2, ensure_ascii=False),
                file_name=f"{export_data['case_id']}.json",
                mime="application/json"
            )
            
            # PDF export
            pdf_data = generate_pdf(export_data)
            if pdf_data:
                st.download_button(
                    label="📑 PDF letöltése",
                    data=pdf_data,
                    file_name=f"{export_data['case_id']}.pdf",
                    mime="application/pdf"
                )
        
        # Reset gomb
        if st.button("🔄 Új konzultáció"):
            # Reset all session state including tracking variables
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

def triage_decision(data):
    symptoms = data.get("symptoms", [])
    severity = data.get("severity", "")
    duration = data.get("duration", "")
    
    # Biztonságosabb regex kezelés
    duration_days = 0
    if duration:
        match = re.search(r"\d+", duration)
        if match:
            try:
                duration_days = int(match.group())
            except ValueError:
                duration_days = 0

    if "mellkasi fájdalom" in symptoms or "légszomj" in symptoms:
        return "🔴 A tünetei alapján azonnali orvosi ellátás javasolt."
    elif severity == "súlyos" or ("láz" in symptoms and "torokfájás" in symptoms and duration_days > 3):
        return "🟡 Javasolt orvossal konzultálni."
    else:
        return "🔵 A tünetei alapján valószínűleg elegendő lehet az otthoni megfigyelés."

ALTERNATIVE_TIPS = {
    "fejfájás": "Igyál több vizet, kerüld az erős fényt, és próbálj meg relaxálni.",
    "torokfájás": "Langyos sós vizes gargalizálás és kamillatea enyhítheti a panaszokat.",
    "köhögés": "Mézes tea és párás levegő segíthet a köhögés csillapításában.",
    "hasfájás": "Borsmentatea vagy meleg borogatás nyugtathatja a hasat.",
    "hányinger": "Gyömbéres tea vagy lassú, mély légzés csökkentheti a hányingert."
}

def alternative_recommendations(symptoms):
    tips = [ALTERNATIVE_TIPS[s] for s in symptoms if s in ALTERNATIVE_TIPS]
    return "\n".join(tips)

def generate_diagnosis(symptoms):
    prompt = f"A következő tünetek alapján javasolj egy lehetséges laikus diagnózist röviden, magyarul: {', '.join(symptoms)}"
    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Te egy egészségügyi asszisztens vagy, aki laikus tünetleírás alapján segít diagnózisban gondolkodni."},
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Hiba a diagnózis generálásában: {e}")
        return "Nem sikerült diagnózist javasolni."

def generate_alt_therapy(symptoms, diagnosis):
    prompt = f"A következő tünetek és laikus diagnózis alapján javasolj alternatív (otthoni vagy természetes) enyhítő megoldásokat magyarul, röviden:\nTünetek: {', '.join(symptoms)}\nDiagnózis: {diagnosis}"
    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Te egy egészségügyi asszisztens vagy, aki természetes enyhítő javaslatokat fogalmaz meg tünetek és diagnózis alapján."},
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Hiba az alternatív terápia generálásában: {e}")
        return "Nem sikerült alternatív javaslatot generálni."

def generate_specialist_advice(symptoms, diagnosis):
    prompt = f"A következő tünetek és laikus diagnózis alapján javasolj szakorvost, akihez érdemes fordulni: {', '.join(symptoms)} — Diagnózis: {diagnosis}"
    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Te egy egészségügyi asszisztens vagy, aki megfelelő szakorvost javasol a tünetek és feltételezett diagnózis alapján."},
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Hiba a szakorvos javaslat generálásában: {e}")
        return "Nem sikerült szakorvost javasolni."

def process_chat_input(user_input):
    """Feldolgozza a felhasználói inputot és generálja a választ."""
    try:
        # OpenAI function call próbálkozás
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Te egy egészségügyi asszisztens vagy. Kinyered az egészségügyi adatokat a szövegből."},
                    {"role": "user", "content": user_input}
                ],
                tools=[tool_schema],
                tool_choice="auto"
            )
            
            reply = response.choices[0].message
            if hasattr(reply, 'tool_calls') and reply.tool_calls:
                for tool_call in reply.tool_calls:
                    if tool_call.function.name == "extract_medical_info":
                        update_state_from_function_output(tool_call.function.arguments)
        except:
            pass  # Ha a function call nem működik, legalább a manual extraction van
        
        # Speciális esetek kezelése
        lower_input = user_input.lower()
        if any(phrase in lower_input for phrase in ['nincs több', 'más nincs', 'semmi más', 'csak ennyi']):
            st.session_state.asked_for_more_symptoms = True
        
        # Ellenőrizzük az állapotot
        if has_sufficient_data():
            if not st.session_state.triage_level:
                # Értékelés indítása
                data = st.session_state.patient_data
                assistant_reply = "✅ Köszönöm! Összegyűjtöttem az adatokat:\n\n"
                assistant_reply += f"• **Tünetek:** {', '.join(data.get('symptoms', []))}\n"
                if data.get('duration'): assistant_reply += f"• **Időtartam:** {data['duration']}\n"
                if data.get('severity'): assistant_reply += f"• **Súlyosság:** {data['severity']}\n"
                if data.get('age'): assistant_reply += f"• **Életkor:** {data['age']} év\n"
                if data.get('gender'): assistant_reply += f"• **Nem:** {data['gender']}\n"
                
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
            # Következő kérdés kérése
            next_question = get_next_question()
            
            # Ha sikerült adatot kinyerni, megerősítjük
            if st.session_state.patient_data.get('symptoms'):
                symptoms = ', '.join(st.session_state.patient_data['symptoms'])
                if "Köszönöm! Rögzítettem" not in next_question:
                    next_question = f"Köszönöm! Rögzítettem: {symptoms}.\n\n{next_question}"
            
            return next_question

    except Exception as e:
        return f"Hiba történt: {str(e)}. Próbálja újra!"

def display_medical_summary():
    """Megjeleníti az orvosi összefoglalót."""
    if st.session_state.triage_level:
        st.info(f"**🏥 Elsődleges orvosi értékelés:**\n{st.session_state.triage_level}")

    if st.session_state.diagnosis:
        st.info(f"**🔬 Lehetséges diagnózis:**\n{st.session_state.diagnosis}")

    if st.session_state.alt_therapy:
        st.success(f"**🌿 Kézi alternatív enyhítő javaslatok:**\n{st.session_state.alt_therapy}")

    if st.session_state.gpt_alt_therapy:
        st.success(f"**🧠 AI által javasolt alternatív enyhítés:**\n{st.session_state.gpt_alt_therapy}")

    if st.session_state.gpt_specialist_advice:
        st.warning(f"**👨‍⚕️ Javasolt szakorvos:**\n{st.session_state.gpt_specialist_advice}")

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
    return export_data

def generate_pdf(export_data):
    """PDF generálása."""
    try:
        pdf_output = BytesIO()
        c = canvas.Canvas(pdf_output, pagesize=A4)
        width, height = A4
        y = height - 20 * mm

        c.setFont("Helvetica-Bold", 16)
        c.drawString(20 * mm, y, "Egészségügyi Összefoglaló")
        y -= 15 * mm

        c.setFont("Helvetica", 10)
        for key, value in export_data.items():
            if isinstance(value, list):
                value = ", ".join(value) if value else "Nincs adat"
            elif value is None:
                value = "Nincs adat"
            
            text = f"{key.replace('_', ' ').title()}: {value}"
            
            # Szöveg tördelése
            max_width = width - 40 * mm
            words = text.split(' ')
            lines = []
            current_line = ""
            
            for word in words:
                test_line = current_line + " " + word if current_line else word
                if c.stringWidth(test_line, "Helvetica", 10) < max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            
            if current_line:
                lines.append(current_line)
            
            for line in lines:
                c.drawString(20 * mm, y, line)
                y -= 5 * mm
                if y < 20 * mm:
                    c.showPage()
                    y = height - 20 * mm
                    c.setFont("Helvetica", 10)

        c.save()
        pdf_output.seek(0)
        return pdf_output
    except Exception as e:
        st.error(f"Hiba a PDF generálásában: {e}")
        return None

def main():
    """Fő alkalmazás."""
    initialize_session_state()
    
    # Címsor
    st.title("🩺 Egészségügyi Chatbot Asszisztens")
    
    # Dinamikus sidebar létrehozása
    create_dynamic_sidebar()

    # Chat történet megjelenítése
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Írja le a tüneteit vagy tegyen fel kérdést..."):
        # Data hash mentése MIELŐTT feldolgozzuk
        old_hash = get_data_hash()
        
        # Ellenőrizzük, hogy volt-e már értékelés
        had_evaluation = bool(st.session_state.triage_level)
        
        # Felhasználói üzenet hozzáadása
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # Felhasználói üzenet megjelenítése
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Adatok kinyerése KÖZVETLENÜL
        manual_extract_info(prompt)
        
        # Ellenőrizzük, változott-e az adat
        new_hash = get_data_hash()
        data_changed = old_hash != new_hash
        
        # AI válasz generálása
        with st.chat_message("assistant"):
            with st.spinner("Elemzés folyamatban..."):
                response = process_chat_input_enhanced(prompt)
                st.markdown(response)
        
        # AI válasz hozzáadása a történethez
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        
        # Ha most lett kész az értékelés, frissítjük az oldalt
        evaluation_just_completed = not had_evaluation and bool(st.session_state.triage_level)
        
        # Ha adat változott VAGY az értékelés most fejeződött be
        if data_changed or evaluation_just_completed:
            st.rerun()
        
        # Orvosi összefoglaló megjelenítése - CSAK ha van értékelés
    if st.session_state.triage_level:  # Ez jelzi, hogy megtörtént az értékelés
        st.markdown("---")
        st.markdown("### 📋 Orvosi Összefoglaló")
        display_medical_summary()

if __name__ == "__main__":
    main()