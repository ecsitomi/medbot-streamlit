# Medical Chatbot - Egészségügyi Asszisztens

Egy intelligens egészségügyi chatbot, amely GPT-4 alapon képes strukturált orvosi adatgyűjtésre, triage döntések meghozatalára és személyre szabott tanácsadásra.

## Funkcionalitások

🩺 Interaktív tünet-adatgyűjtés
🧩 Kontextusérzékeny adatkinyerés (GPT + regex)
🔄 Dinamikus kérdésgenerálás reasoning logikával
🤖 GPT-4 alapú diagnózis, terápia és szakorvos javaslat
🏥 Triage döntés a tünetek súlyossága alapján
📄 Eredmények exportja JSON és PDF formátumban

📁 Projekt Struktúra

medical_chatbot/
├── main.py                         # Fő alkalmazás (Streamlit)
├── core/                           # Alapvető funkcionalitások
│   ├── __init__.py
│   ├── config.py                   # Konfigurációk és konstansok
│   ├── session.py                  # Session state kezelés
│   └── utils.py                    # Segédfunkciók (pl. adatellenőrzés)
├── logic/                          # Üzleti logika
│   ├── __init__.py
│   ├── data_extraction.py          # Orvosi adatok kinyerése (GPT + kézi)
│   ├── gpt_communication.py        # GPT diagnózis, terápia, kérdésgenerálás
│   ├── medical_analysis.py         # Triage, alternatív javaslatok
│   └── chat_processor.py           # Chat folyamatkezelés reasoning logikával
├── ui/                             # Felhasználói felület
│   ├── __init__.py
│   ├── sidebar.py                  # Dinamikus állapot és navigáció
│   ├── chat_interface.py           # Interaktív chat UI
│   └── medical_summary.py          # Összegző megjelenítése
├── export/                         # Export funkcionalitások
│   ├── __init__.py
│   ├── data_formatter.py           # Export adatstruktúra formázás
│   └── pdf_generator.py            # PDF generálás (egyszerű és strukturált)
├── medline_integration/            # Egészségügyi edukációs modul
│   ├── __init__.py
│   ├── integration.py              # Export bővítése Medline tartalommal
│   ├── api_client.py               # Külső Medline cikkek lekérése
│   ├── ui_components.py            # Streamlit megjelenítés a felületen
│   └── data_processor.py           # Lokális adatbázis feldolgozása
├──rag_pdf/
│    ├── __init__.py
│    ├── pdf_processor.py            # PDF feldolgozás és chunking
│    ├── vector_store.py             # Chroma vector DB kezelés
│    ├── rag_analyzer.py             # RAG alapú elemzés
│    └── config.py                   # RAG konfiguráció
├── medline_db.json                 # Lokális Medline tartalmak (opcionális)
├── requirements.txt                # Függőségek telepítése
└── README.md                       # Ezt olvasod

🚀 Telepítés
- Klónozd a repót:
git clone https://github.com/felhasznalo/medical-chatbot.git
cd medical-chatbot

- Függőségek telepítése:
pip install -r requirements.txt

- Állítsd be az OpenAI API kulcsot .env fájlban vagy secrets.toml fájlban.
# core/config.py #
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

▶️ Futtatás
streamlit run main.py

🧪 Használati folyamat
1. Tünetek megadása – A chatbot kérdések segítségével begyűjti az életkort, nemet, tüneteket, időtartamot, stb.

2. Értékelés – Az adatok alapján automatikusan történik:

- Triage besorolás
- Laikus diagnózis generálása
- Alternatív terápiás javaslatok (kézi és AI alapú)
- Szakorvosi ajánlás
- Értékelés a Medline Plus külső integrációból

3. Összefoglalás letöltése – JSON és PDF formában.

🔹 Külső integrációk
- Medline Plus:
Az export funkció automatikusan integrálja a Medline-ból származó hitelesített egészségügyi ismeretterjesztő leírásokat a tünetekhez és betegségekhez. Ezáltal a PDF vagy JSON export nemcsak diagnózist és javaslatokat tartalmaz, hanem további megbízható forrásokat is az önálló tájékozódáshoz.

🧱 Modulok részletesen

🔹 Core
config.py: OpenAI konfiguráció, tool schema, konstansek, üdvözlő üzenet
session.py: Streamlit session state inicializálás és visszaállítás
utils.py: Hash, adatellenőrzés, session state frissítés

🔹 Logic
data_extraction.py: GPT + kézi adatkinyerés kontextus alapján (age, gender, symptoms stb.)
chat_processor.py: Reasoning kérdéslogika, kontextusérzékeny párbeszédkezelés
gpt_communication.py: Diagnózis, terápia, szakorvos javaslat generálása GPT-4 segítségével
medical_analysis.py: Triage szintek meghatározása, alternatív ajánlások

🔹 Medline Integration
integration.py: Vezérli az adatok feldúsítását, feldolgozást és a modul elemeit
api_client.py: A külső egészségügyi források elérését biztosítja
ui_components.py: Összegyűjtött eü. tartalom megjelenítése
data_processor.py: Lokális Medline adatbázis feldolgozó logika

🔹 UI
chat_interface.py: Chat felület
sidebar.py: Dinamikus státuszkijelzés, kérdésfolyamat vezérlés
medical_summary.py: Vizsgálati eredmények megjelenítése

🔹 Export
data_formatter.py: Eredmények formázása emberi olvashatóságra és export struktúrára
pdf_generator.py: Egyszerű és szekcionált PDF generálás ReportLab-bal

📤 Export formátumok
JSON: Strukturált export orvosi és metaadatokkal
PDF: Hagyományos vagy fejlettebb szekciós PDF

🛡️ Biztonság és Etika
Nem nyújt hivatalos orvosi tanácsot
Adatokat nem tárol véglegesen
GDPR kompatibilis működés
Csak tájékoztató célra használható

⚙️ Technológiák
Python 3.8+
Streamlit – webes frontend
OpenAI GPT-4 API
Reportlab – PDF generálás
dotenv – konfiguráció

📄 Licenc
MIT License
