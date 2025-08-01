# pubmed_integration/pubmed_analyzer.py
"""
PubMed alapú orvosi kutatás és elemzés
"""
import os
import streamlit as st
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from pathlib import Path

from langchain_community.tools.pubmed.tool import PubmedQueryRun
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from .config import PUBMED_CONFIG, PUBMED_DATA_DIR

class PubMedAnalyzer:
    """PubMed alapú orvosi elemző"""
    
    def __init__(self, openai_api_key: str = None):
        # API kulcs
        if not openai_api_key:
            openai_api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
        
        if not openai_api_key:
            raise ValueError("OpenAI API key nem található")
        
        self.api_key = openai_api_key
        
        # PubMed tool inicializálása
        self.pubmed_tool = PubmedQueryRun()
        
        # LLM inicializálása
        self.llm = ChatOpenAI(
            openai_api_key=self.api_key,
            model=PUBMED_CONFIG["llm"]["model"],
            temperature=PUBMED_CONFIG["llm"]["temperature"],
            max_tokens=PUBMED_CONFIG["llm"]["max_tokens"]
        )
        
        # Fordító LLM (kisebb modell a költséghatékonyság miatt)
        self.translator = ChatOpenAI(
            openai_api_key=self.api_key,
            model="gpt-3.5-turbo",
            temperature=0
        )
    
    def translate_to_english(self, text: str) -> str:
        """Magyar szöveg fordítása angolra"""
        if not text:
            return ""
        
        prompt = f"Translate this Hungarian medical text to English. Only return the translation, nothing else:\n{text}"
        return self.translator.predict(prompt).strip()
    
    def translate_patient_data(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Betegadatok fordítása angolra a PubMed kereséshez"""
        translated = {}
        
        # Tünetek fordítása
        symptoms = patient_data.get('symptoms', [])
        if symptoms:
            translated['symptoms'] = [self.translate_to_english(s) for s in symptoms if s]
        
        # Diagnózis fordítása
        diagnosis = patient_data.get('diagnosis', '')
        if diagnosis:
            translated['diagnosis'] = self.translate_to_english(diagnosis)
        
        # Egyéb mezők fordítása
        if patient_data.get('existing_conditions'):
            translated['existing_conditions'] = [
                self.translate_to_english(c) for c in patient_data['existing_conditions'] if c
            ]
        
        if patient_data.get('medications'):
            translated['medications'] = [
                self.translate_to_english(m) for m in patient_data['medications'] if m
            ]
        
        # Számértékek átvétele változtatás nélkül
        translated['age'] = patient_data.get('age')
        translated['gender'] = patient_data.get('gender')
        translated['severity'] = patient_data.get('severity')
        translated['duration'] = patient_data.get('duration')
        
        return translated
    
    def build_search_query(self, translated_data: Dict[str, Any], rag_results: Dict[str, Any] = None) -> str:
        """PubMed keresési query összeállítása"""
        query_parts = []
        
        # Fő tünetek
        if translated_data.get('symptoms'):
            symptoms_str = " AND ".join(f'"{s}"' for s in translated_data['symptoms'][:3])
            query_parts.append(f"({symptoms_str})")
        
        # Diagnózis
        if translated_data.get('diagnosis'):
            query_parts.append(f'"{translated_data["diagnosis"]}"')
        
        # Ha van RAG eredmény, használjuk azt is
        if rag_results and rag_results.get('patient_condition'):
            # Kivonjuk a kulcsszavakat a RAG eredményből
            condition_text = self.translate_to_english(rag_results['patient_condition'])
            # Csak az első mondatot használjuk
            if condition_text:
                first_sentence = condition_text.split('.')[0]
                query_parts.append(f"({first_sentence})")
        
        # Életkor és nem szűrők
        age = translated_data.get('age')
        if age:
            if age < 18:
                query_parts.append("pediatric OR children")
            elif age > 65:
                query_parts.append("elderly OR geriatric")
        
        # Query összeállítása
        final_query = " AND ".join(query_parts) if query_parts else "medical treatment"
        
        # Limitáljuk a query hosszát
        if len(final_query) > 200:
            final_query = final_query[:200]
        
        return final_query
    
    def search_pubmed(self, query: str) -> str:
        """PubMed keresés végrehajtása"""
        try:
            st.info(f"🔍 PubMed keresés: {query[:100]}...")
            results = self.pubmed_tool.invoke(query)
            return results
        except Exception as e:
            st.error(f"PubMed keresési hiba: {e}")
            return ""
    
    def analyze_pubmed_results(self, pubmed_results: str, patient_data: Dict[str, Any], 
                             rag_results: Dict[str, Any] = None) -> Dict[str, Any]:
        """PubMed eredmények elemzése és magyar nyelvű összefoglaló készítése"""
        
        if not pubmed_results:
            return self._create_empty_result()
        
        # Prompt template az elemzéshez
        analysis_prompt = PromptTemplate(
            input_variables=["pubmed_results", "patient_info", "rag_context"],
            template="""Te egy orvosi szakértő vagy, aki a legfrissebb PubMed publikációk alapján ad tanácsokat.

PubMed keresési eredmények:
{pubmed_results}

Beteg információk:
{patient_info}

Korábbi elemzés (ha van):
{rag_context}

Kérlek készíts MAGYAR nyelvű részletes elemzést a következő struktúrában:

1. **Legfrissebb kutatási eredmények** - Mit mondanak a legújabb publikációk a beteg állapotáról?
2. **Ajánlott kezelési módszerek** - Milyen evidencia-alapú kezeléseket javasolnak a cikkek?
3. **Klinikai irányelvek** - Vannak-e specifikus protokollok vagy guidelines?
4. **Prognózis és kilátások** - Mit mutatnak a kutatások a gyógyulási esélyekről?
5. **További vizsgálatok** - Milyen további vizsgálatokat javasolnak a publikációk?

FONTOS: A válaszod legyen MAGYAR nyelvű, közérthető és praktikus!
"""
        )
        
        # LLM chain
        chain = LLMChain(llm=self.llm, prompt=analysis_prompt)
        
        # Beteg info összefoglalása
        patient_info = self._format_patient_info(patient_data)
        
        # RAG kontextus
        rag_context = ""
        if rag_results:
            rag_context = f"""
            Állapot: {rag_results.get('patient_condition', 'N/A')}
            Javasolt kezelés: {rag_results.get('symptom_management', 'N/A')}
            """
        
        try:
            # Elemzés futtatása
            response = chain.run(
                pubmed_results=pubmed_results[:3000],  # Limitáljuk a hosszt
                patient_info=patient_info,
                rag_context=rag_context
            )
            
            # Válasz feldolgozása
            return self._parse_analysis_response(response)
            
        except Exception as e:
            st.error(f"PubMed elemzési hiba: {e}")
            return self._create_empty_result()
    
    def _format_patient_info(self, patient_data: Dict[str, Any]) -> str:
        """Beteg információk formázása"""
        info_parts = []
        
        if patient_data.get('age'):
            info_parts.append(f"Életkor: {patient_data['age']} év")
        
        if patient_data.get('gender'):
            info_parts.append(f"Nem: {patient_data['gender']}")
        
        if patient_data.get('symptoms'):
            info_parts.append(f"Tünetek: {', '.join(patient_data['symptoms'])}")
        
        if patient_data.get('diagnosis'):
            info_parts.append(f"Diagnózis: {patient_data['diagnosis']}")
        
        if patient_data.get('severity'):
            info_parts.append(f"Súlyosság: {patient_data['severity']}")
        
        return " | ".join(info_parts)
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """AI válasz strukturált formába alakítása"""
        sections = {
            "research_findings": "",
            "treatment_methods": "",
            "clinical_guidelines": "",
            "prognosis": "",
            "further_tests": ""
        }
        
        # Egyszerű szekció felismerés
        current_section = None
        lines = response.split('\n')
        
        section_keywords = {
            "research_findings": ["kutatási eredmények", "publikációk", "tanulmányok"],
            "treatment_methods": ["kezelési", "terápia", "gyógyszer"],
            "clinical_guidelines": ["irányelvek", "protokoll", "guidelines"],
            "prognosis": ["prognózis", "kilátások", "gyógyulás"],
            "further_tests": ["vizsgálatok", "diagnosztika", "tesztek"]
        }
        
        for line in lines:
            line_lower = line.lower()
            
            # Szekció azonosítása
            for section, keywords in section_keywords.items():
                if any(keyword in line_lower for keyword in keywords):
                    current_section = section
                    break
            
            # Tartalom hozzáadása
            if current_section and line.strip() and not line.startswith('*'):
                sections[current_section] += line + "\n"
        
        # Ha nem sikerült parseolni, az egész választ tároljuk
        if not any(sections.values()):
            sections["full_response"] = response
        
        return {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            **sections
        }
    
    def _create_empty_result(self) -> Dict[str, Any]:
        """Üres eredmény struktúra"""
        return {
            'success': False,
            'timestamp': datetime.now().isoformat(),
            'research_findings': "Nem találtunk releváns publikációkat.",
            'treatment_methods': "Nincs elérhető információ.",
            'clinical_guidelines': "Nincs elérhető információ.",
            'prognosis': "Nincs elérhető információ.",
            'further_tests': "Nincs elérhető információ."
        }
    
    def save_results(self, results: Dict[str, Any], patient_data: Dict[str, Any]) -> str:
        """Eredmények mentése"""
        try:
            # Export könyvtár
            export_dir = PUBMED_DATA_DIR / "exports"
            export_dir.mkdir(exist_ok=True)
            
            # Fájlnév
            case_id = patient_data.get('case_id', f"pubmed_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            json_path = export_dir / f"{case_id}_pubmed.json"
            
            # Teljes adat összeállítása
            export_data = {
                "pubmed_analysis": results,
                "patient_data": patient_data,
                "timestamp": results.get('timestamp', datetime.now().isoformat())
            }
            
            # Mentés
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            return str(json_path)
            
        except Exception as e:
            st.error(f"Mentési hiba: {e}")
            return ""

def run_pubmed_analysis(patient_data: Dict[str, Any], 
                    rag_results: Dict[str, Any] = None,
                    openai_api_key: str = None) -> Dict[str, Any]:
    """
    PubMed alapú orvosi elemzés futtatása
    
    Args:
        patient_data: Beteg adatok
        rag_results: RAG elemzés eredményei (opcionális)
        openai_api_key: OpenAI API kulcs
    
    Returns:
        Dict: PubMed elemzés eredménye
    """
    try:
        st.info("🔬 PubMed mélykutatás indítása...")
        
        # Analyzer inicializálása
        analyzer = PubMedAnalyzer(openai_api_key)
        
        # 1. Magyar adatok fordítása angolra
        st.info("🌐 Adatok előkészítése a kereséshez...")
        translated_data = analyzer.translate_patient_data(patient_data)
        
        # 2. Keresési query összeállítása
        search_query = analyzer.build_search_query(translated_data, rag_results)
        st.info(f"🔍 Keresési kifejezés: {search_query}")
        
        # 3. PubMed keresés
        pubmed_results = analyzer.search_pubmed(search_query)
        
        if not pubmed_results:
            st.warning("⚠️ Nem találtunk releváns publikációkat")
            return analyzer._create_empty_result()
        
        # 4. Eredmények elemzése
        st.info("🤖 Publikációk elemzése és magyar nyelvű összefoglaló készítése...")
        analysis_results = analyzer.analyze_pubmed_results(
            pubmed_results, 
            patient_data,
            rag_results
        )
        
        # 5. Eredmények mentése
        save_path = analyzer.save_results(analysis_results, patient_data)
        if save_path:
            st.success(f"💾 Eredmények elmentve: {Path(save_path).name}")
        
        # 6. Eredmények megjelenítése
        display_pubmed_results(analysis_results, save_path)
        
        return analysis_results
        
    except Exception as e:
        st.error(f"❌ PubMed elemzési hiba: {e}")
        return {'success': False, 'error': str(e)}

def display_pubmed_results(results: Dict[str, Any], save_path: str = None):
    """PubMed eredmények megjelenítése"""
    st.markdown("### 🔬 PubMed Kutatási Eredmények")
    
    if not results.get('success', False):
        st.error("Nem sikerült az elemzés")
        return
    
    # Szekciók megjelenítése
    sections = [
        ("📚 Legfrissebb kutatási eredmények", "research_findings"),
        ("💊 Ajánlott kezelési módszerek", "treatment_methods"),
        ("📋 Klinikai irányelvek", "clinical_guidelines"),
        ("📈 Prognózis és kilátások", "prognosis"),
        ("🔍 További javasolt vizsgálatok", "further_tests")
    ]
    
    for title, key in sections:
        content = results.get(key, "")
        if content and content.strip():
            with st.expander(title, expanded=(key == "research_findings")):
                st.markdown(content)
    
    # Ha van teljes válasz (fallback)
    if results.get('full_response'):
        with st.expander("📄 Teljes elemzés", expanded=True):
            st.markdown(results['full_response'])
    
    # Letöltési lehetőség
    if save_path and os.path.exists(save_path):
        with open(save_path, 'r', encoding='utf-8') as f:
            st.download_button(
                label="📥 PubMed elemzés letöltése (JSON)",
                data=f.read(),
                file_name=Path(save_path).name,
                mime="application/json",
                key="download_pubmed_json"
            )