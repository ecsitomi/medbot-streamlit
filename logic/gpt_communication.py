# =============================================================================
# logic/gpt_communication.py
# =============================================================================
"""
GPT alapú kommunikáció és intelligens kérdésgenerálás.
"""
import streamlit as st
from core import get_openai_client

def generate_diagnosis(symptoms):
    """GPT alapú diagnózis generálás."""
    if not symptoms:
        return "Nincs elegendő tünet a diagnózishoz."
    
    prompt = f"A következő tünetek alapján javasolj egy lehetséges laikus diagnózist röviden, magyarul: {', '.join(symptoms)}"
    try:
        client = get_openai_client()
        completion = client.chat.completions.create(
            model="gpt-5",
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
    """GPT alapú alternatív terápia javaslatok."""
    if not symptoms:
        return "Nincs elegendő információ a terápiás javaslatokhoz."
    
    prompt = f"A következő tünetek és laikus diagnózis alapján javasolj alternatív (otthoni vagy természetes) enyhítő megoldásokat magyarul, röviden:\nTünetek: {', '.join(symptoms)}\nDiagnózis: {diagnosis}"
    try:
        client = get_openai_client()
        completion = client.chat.completions.create(
            model="gpt-5",
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
    """GPT alapú szakorvos javaslat."""
    if not symptoms:
        return "Nincs elegendő információ a szakorvos javaslathoz."
    
    prompt = f"A következő tünetek és laikus diagnózis alapján javasolj szakorvost, akihez érdemes fordulni: {', '.join(symptoms)} — Diagnózis: {diagnosis}"
    try:
        client = get_openai_client()
        completion = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "Te egy egészségügyi asszisztens vagy, aki megfelelő szakorvost javasol a tünetek és feltételezett diagnózis alapján."},
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Hiba a szakorvos javaslat generálásában: {e}")
        return "Nem sikerült szakorvost javasolni."

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
        system_prompt = """Te egy tapasztalt egészségügyi asszisztens vagy, aki magázódva, de empátiával és szakértelemmel tesz fel kérdéseket a pácienseknek.

FELADATOD: Természetes, barátságos kérdést generálni, ami pontosan EGY hiányzó adatot gyűjt be. Magázódj a pácienssel, és használd a kontextust a kérdéshez.

SZABÁLYOK:
1. Csak EGY adatot kérdezz meg egyszerre
2. Légy empatikus és természetes
3. Használd a kontextust és a korábbi beszélgetést
4. Rövid, érthető kérdést tégy fel
5. Ha szükséges, adj példákat a válaszhoz
6. Magyar nyelven válaszolj magázódva

ADATMEZŐK MAGYARÁZATA:
- symptoms: Tünetek (fájdalom, diszkomfort, stb.)
- additional_symptoms: További tünetek keresése az első után
- duration: Tünetek időtartama (mióta tart)
- severity: Súlyosság (enyhe/súlyos)
- age: Életkor
- gender: Biológiai nem (férfi/nő)
- existing_conditions: Krónikus betegségek, allergiák
- medications: Szedett gyógyszerek, vitaminok"""

        user_prompt = f"""KONTEXTUS:
Jelenlegi adataim a páciensről:
{chr(10).join(current_data_summary) if current_data_summary else "Még nincsenek adatok"}

Legutóbbi beszélgetés:
{recent_conversation if recent_conversation else "Ez az első interakció"}

KÖVETKEZŐ HIÁNYZÓ ADAT: {priority_field}

Kérlek, tegyél fel EGY természetes kérdést, ami ezt az adatot gyűjti be. A kérdés legyen empatikus és a kontextushoz illő. Magázódj!"""

        # GPT hívás
        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.8,
            max_tokens=300
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
        return "Kérem, adja meg a biológia nemét (férfi/nő). Ez is fontos az értékeléshez."
    elif not data.get("existing_conditions"):
        return "Vannak-e ismert krónikus betegségei, allergiái vagy egyéb egészségügyi problémái? Ha nincs, írja be: 'nincs'."
    elif not data.get("medications"):
        return "Szed-e rendszeresen gyógyszereket vagy vitaminokat? Ha nem, írja be: 'nincs'."
    else:
        return "Köszönöm az összes információt! Most elkészítem az orvosi értékelést."