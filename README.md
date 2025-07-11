# Medical Chatbot - Egészségügyi Asszisztens

Egy intelligens egészségügyi chatbot, amely GPT-4 alapon gyűjt orvosi adatokat, elemez és értékel.

## Funkcionalitások

- 🩺 Interaktív tünet-adatgyűjtés
- 🤖 GPT-4 alapú intelligens kérdésgenerálás
- 🏥 Automatikus triage döntések
- 💊 Alternatív terápiás javaslatok
- 👨‍⚕️ Szakorvos javaslatok
- 📄 JSON és PDF export

## Projekt struktúra

```
medical_chatbot/
├── main.py                    # Fő alkalmazás
├── core/                      # Alapvető funkcionalitások
│   ├── __init__.py
│   ├── config.py             # Konfigurációk és konstansok
│   ├── session.py            # Session state kezelés
│   └── utils.py              # Segédfunkciók
├── logic/                     # Üzleti logika
│   ├── __init__.py
│   ├── data_extraction.py    # Orvosi adatok kinyerése
│   ├── gpt_communication.py  # GPT kommunikáció
│   ├── medical_analysis.py   # Orvosi elemzések
│   └── chat_processor.py     # Chat feldolgozás
├── ui/                        # Felhasználói felület
│   ├── __init__.py
│   ├── sidebar.py            # Sidebar komponensek
│   ├── chat_interface.py     # Chat felület
│   └── medical_summary.py    # Orvosi összefoglaló UI
├── export/                    # Export funkcionalitások
│   ├── __init__.py
│   ├── data_formatter.py     # Adat formázás
│   └── pdf_generator.py      # PDF generálás
├── requirements.txt
└── README.md
```

## Telepítés

1. Klónozd a repository-t
2. Telepítsd a függőségeket:
```bash
pip install -r requirements.txt
```

3. Állítsd be az OpenAI API kulcsot a Streamlit secrets-ben vagy környezeti változóban

## Futtatás

```bash
streamlit run main.py
```

## Használat

1. **Adatgyűjtés**: Az asszisztens interaktívan gyűjti össze a szükséges orvosi adatokat
2. **Értékelés**: A rendszer automatikusan elkészíti az orvosi értékelést
3. **Export**: Letölthető JSON vagy PDF formátumban az összefoglaló

## Modulok

### Core
- **config.py**: OpenAI konfiguráció, tool schema, konstansok
- **session.py**: Streamlit session state kezelés
- **utils.py**: Hash generálás, adatvalidáció

### Logic
- **data_extraction.py**: GPT és manuális adatkinyerés
- **gpt_communication.py**: AI kommunikáció és kérdésgenerálás
- **medical_analysis.py**: Triage döntések és orvosi elemzés
- **chat_processor.py**: Chat folyamat vezérlés

### UI
- **sidebar.py**: Dinamikus sidebar és státusz
- **chat_interface.py**: Chat felhasználói felület
- **medical_summary.py**: Eredmények megjelenítése

### Export
- **data_formatter.py**: Export adatok formázása
- **pdf_generator.py**: PDF dokumentum generálás

## Biztonsági megjegyzések

- Az alkalmazás nem minősül orvosi tanácsadásnak
- Az adatokat nem tároljuk permanensen
- GDPR kompatibilis adatkezelés
- Csak tájékoztató célú használatra alkalmas

## Fejlesztői információk

- Python 3.8+
- Streamlit framework
- OpenAI GPT-4 API
- ReportLab PDF generálás

## Licenc

MIT License