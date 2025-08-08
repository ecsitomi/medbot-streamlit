# pubmed_integration/pubmed_analyzer.py
"""
PubMed alapú orvosi kutatás és elemzés
"""
import os
import re
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
from .advanced_search_strategy import AdvancedPubMedSearchStrategy

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
            model="gpt-5",
            temperature=0
        )
    
    # TOVÁBBFEJLESZTETT ADVANCED SEARCH STRATEGY
    def run_advanced_pubmed_search(self, patient_data: Dict[str, Any]) -> str:
        """Újratervezett stratégia alapú lekérdezés és keresés"""
        strategy = AdvancedPubMedSearchStrategy()
        
        # Debug információk megjelenítése fejlesztési módban
        if st.session_state.get('debug_mode', False):
            debug_info = strategy.debug_query_generation(patient_data)
            st.write("🔧 **Debug információk:**", debug_info)
        
        queries = strategy.build_comprehensive_search_queries(patient_data)
        
        if not queries:
            st.warning("⚠️ Nem sikerült keresési lekérdezéseket generálni")
            return ""
        
        # Lekérdezések végrehajtása
        all_results = ""
        successful_queries = 0
        
        for i, q in enumerate(queries):
            query_string = strategy.format_final_query(q)
            
            if not query_string:
                st.warning(f"❌ {i+1}. lekérdezés üres")
                continue
                
            #st.info(f"🔍 {i+1}. lekérdezés ({len(query_string)} karakter): {query_string[:100]}...")
            
            try:
                result = self.pubmed_tool.invoke(query_string)
                if result and len(result.strip()) > 50:  # Csak értelmes eredményeket fogadjuk el
                    all_results += f"\n--- QUERY {i+1} ---\n{query_string}\n--- RESULT ---\n{result}\n"
                    successful_queries += 1
                    #st.success(f"✅ {i+1}. lekérdezés sikeres")
                else:
                    st.warning(f"⚠️ {i+1}. lekérdezés üres eredményt adott")
                
                # Ha már van 2 sikeres lekérdezés, elég
                if successful_queries >= 2:
                    break
                    
            except Exception as e:
                st.error(f"❌ Hiba a {i+1}. lekérdezésnél: {e}")
                continue
        
        if successful_queries == 0:
            st.error("❌ Egyik lekérdezés sem volt sikeres")
            return ""
        
        #st.success(f"✅ Összesen {successful_queries} sikeres lekérdezés")
        return all_results.strip()
    
    def run_simple_pubmed_search(self, patient_data: Dict[str, Any]) -> str:
        """Egyszerű fallback keresés, ha a komplex keresés nem működik"""
        symptoms = patient_data.get('symptoms', [])
        diagnosis = patient_data.get('diagnosis', '')
        
        # Egyszerű query építése
        query_parts = []
        
        if symptoms:
            # Csak az első 2 tünet
            primary_symptoms = symptoms[:2]
            for symptom in primary_symptoms:
                # Egyszerű fordítás
                eng_symptom = self._simple_translate(symptom)
                if eng_symptom:
                    query_parts.append(eng_symptom)
        
        if diagnosis and diagnosis != "Nem sikerült diagnózist javasolni.":
            eng_diagnosis = self._simple_translate(diagnosis)
            if eng_diagnosis:
                query_parts.append(eng_diagnosis)
        
        if not query_parts:
            return ""
        
        # Egyszerű query összeállítása
        simple_query = " AND ".join(query_parts[:2])  # Max 2 elem
        final_query = f"({simple_query}) AND humans[MeSH]"
        
        #st.info(f"🔍 Egyszerű keresés: {final_query}")
        
        try:
            result = self.pubmed_tool.invoke(final_query)
            return result if result else ""
        except Exception as e:
            st.error(f"❌ Egyszerű keresés is sikertelen: {e}")
            return ""
    
    def _simple_translate(self, text: str) -> str:
        """Egyszerű magyar-angol fordítás alapvető kifejezésekhez"""
        simple_translations = {
            'fejfájás': 'headache',
            'láz': 'fever',
            'köhögés': 'cough',
            'hányás': 'vomiting',
            'hasmenés': 'diarrhea',
            'fáradtság': 'fatigue',
            'szédülés': 'dizziness',
            'hasfájás': 'abdominal pain',
            'torokfájás': 'sore throat',
            'légzési nehézség': 'dyspnea',
            'influenza': 'influenza',
            'megfázás': 'common cold',
            'gastritis': 'gastritis',
            'allergia': 'allergy',
            'asztma': 'asthma'
        }
        
        text_lower = text.lower().strip()
        
        # Tisztítás - bizonytalan kifejezések eltávolítása
        text_lower = re.sub(r'^(lehetséges|valószínű|esetleg|talán)\s+', '', text_lower)
        text_lower = re.sub(r'\s+(gyanúja|gyanú)$', '', text_lower)
        
        return simple_translations.get(text_lower, text_lower)  
    
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
            #st.info(f"🔍 PubMed keresés: {query[:100]}...")
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
        """AI válasz strukturált formába alakítása - REGEX ALAPÚ"""
        import re
        from datetime import datetime
        
        sections = {
            "research_findings": "",
            "treatment_methods": "",
            "clinical_guidelines": "",
            "prognosis": "",
            "further_tests": ""
        }
        
        if not response or len(response.strip()) < 10:
            return self._create_empty_result()
        
        # Regex pattern a számozott szekciók megtalálására
        # Támogatja: 1. **Cím** vagy 1. Cím formátumokat
        patterns = [
            # 1. Legfrissebb kutatási eredmények
            r"1\.\s*\*{0,2}(?:Legfrissebb kutatási eredmények|Kutatási eredmények)[:\*]*\s*(.*?)(?=2\.|$)",
            # 2. Ajánlott kezelési módszerek
            r"2\.\s*\*{0,2}(?:Ajánlott kezelési módszerek|Kezelési módszerek)[:\*]*\s*(.*?)(?=3\.|$)",
            # 3. Klinikai irányelvek
            r"3\.\s*\*{0,2}(?:Klinikai irányelvek|Irányelvek)[:\*]*\s*(.*?)(?=4\.|$)",
            # 4. Prognózis és kilátások
            r"4\.\s*\*{0,2}(?:Prognózis és kilátások|Prognózis)[:\*]*\s*(.*?)(?=5\.|$)",
            # 5. További vizsgálatok
            r"5\.\s*\*{0,2}(?:További vizsgálatok|További javasolt vizsgálatok|Vizsgálatok)[:\*]*\s*(.*?)(?=$)"
        ]
        
        # Kulcsok sorrendben
        keys = ["research_findings", "treatment_methods", "clinical_guidelines", "prognosis", "further_tests"]
        
        # Próbáljuk meg minden patternt
        for i, (pattern, key) in enumerate(zip(patterns, keys)):
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                # Tisztítjuk a tartalmat
                content = self._clean_content(content)
                if content:
                    sections[key] = content
        
        # Ha nem találtunk számozott listát, próbáljuk meg ** címek ** alapján
        if not any(sections.values()):
            sections = self._extract_by_headers(response)
        
        # Ha még mindig nincs eredmény, használjunk általános pattern-t
        if not any(sections.values()):
            sections = self._extract_general_numbered_list(response)
        
        # Fallback: teljes válasz mentése
        if not any(sections.values()):
            sections["full_response"] = response
            if st.session_state.get('debug_mode', False):
                st.warning("⚠️ Nem sikerült szekciókra bontani, teljes válasz mentve")
        
        return {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            **sections
        }

    def _extract_by_headers(self, response: str) -> Dict[str, str]:
        """Kivonat ** header ** formátum alapján"""
        import re
        
        sections = {
            "research_findings": "",
            "treatment_methods": "",
            "clinical_guidelines": "",
            "prognosis": "",
            "further_tests": ""
        }
        
        # Pattern a **cím** formátumú részek megtalálására
        header_patterns = {
            "research_findings": r"\*\*(Legfrissebb kutatási eredmények|Kutatási eredmények)\*\*:?\s*(.*?)(?=\*\*|$)",
            "treatment_methods": r"\*\*(Ajánlott kezelési módszerek|Kezelési módszerek)\*\*:?\s*(.*?)(?=\*\*|$)",
            "clinical_guidelines": r"\*\*(Klinikai irányelvek|Irányelvek)\*\*:?\s*(.*?)(?=\*\*|$)",
            "prognosis": r"\*\*(Prognózis és kilátások|Prognózis)\*\*:?\s*(.*?)(?=\*\*|$)",
            "further_tests": r"\*\*(További vizsgálatok|További javasolt vizsgálatok)\*\*:?\s*(.*?)(?=\*\*|$)"
        }
        
        for key, pattern in header_patterns.items():
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(2).strip()
                content = self._clean_content(content)
                if content:
                    sections[key] = content
        
        return sections

    def _extract_general_numbered_list(self, response: str) -> Dict[str, str]:
        """Általános számozott lista feldolgozása"""
        import re
        
        sections = {
            "research_findings": "",
            "treatment_methods": "",
            "clinical_guidelines": "",
            "prognosis": "",
            "further_tests": ""
        }
        
        # Általános pattern bármilyen számozott listához
        general_pattern = r"(\d+)\.\s*\*{0,2}(.*?)\*{0,2}:?\s*(.*?)(?=\d+\.|$)"
        
        matches = re.findall(general_pattern, response, re.DOTALL)
        
        for number, title, content in matches:
            title_lower = title.lower().strip()
            content = self._clean_content(content.strip())
            
            # Kulcsszavak alapján kategorizálás
            if any(kw in title_lower for kw in ['kutatás', 'eredmény', 'publikáció', 'tanulmány', 'evidencia']):
                sections["research_findings"] = content
            elif any(kw in title_lower for kw in ['kezelés', 'terápia', 'gyógyszer', 'módszer']):
                sections["treatment_methods"] = content
            elif any(kw in title_lower for kw in ['irányelv', 'protokoll', 'guideline', 'standard']):
                sections["clinical_guidelines"] = content
            elif any(kw in title_lower for kw in ['prognózis', 'kilátás', 'kimenetel', 'gyógyulás']):
                sections["prognosis"] = content
            elif any(kw in title_lower for kw in ['vizsgálat', 'diagnosztika', 'teszt', 'további']):
                sections["further_tests"] = content
        
        return sections

    def _clean_content(self, content: str) -> str:
        """Tartalom tisztítása"""
        if not content:
            return ""
        
        import re
        
        # Eltávolítjuk a felesleges whitespace-t
        content = content.strip()
        
        # Eltávolítjuk a többszörös üres sorokat
        content = re.sub(r'\n\s*\n+', '\n\n', content)
        
        # Eltávolítjuk a vezető számozást a sorok elejéről
        content = re.sub(r'^[\d\-\*\•]+\.\s*', '', content, flags=re.MULTILINE)
        
        # Eltávolítjuk a felesleges markdown jelöléseket
        content = re.sub(r'^\*+\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'\*+$', '', content, flags=re.MULTILINE)
        
        return content.strip()

    # TESZTELŐ FÜGGVÉNY
    def test_parse_response(self):
        """Tesztelés különböző válasz formátumokkal"""
        
        test_responses = [
            # Formátum 1: Számozott lista **címekkel**
            """
            1. **Legfrissebb kutatási eredmények**
            A legújabb meta-analízis szerint a betegség...
            
            2. **Ajánlott kezelési módszerek**
            Az elsővonalbeli kezelés magában foglalja...
            
            3. **Klinikai irányelvek**
            A WHO 2024-es ajánlása alapján...
            
            4. **Prognózis és kilátások**
            A betegek 80%-a teljes gyógyulást mutat...
            
            5. **További vizsgálatok**
            Javasolt laborvizsgálatok: CBC, CRP...
            """,
            
            # Formátum 2: Csak **címek**
            """
            **Legfrissebb kutatási eredmények**
            Új tanulmányok kimutatták...
            
            **Ajánlott kezelési módszerek**
            Gyógyszeres terápia: ...
            """,
            
            # Formátum 3: Egyszerű számozott lista
            """
            1. Kutatási eredmények: A vizsgálatok azt mutatják...
            2. Kezelési módszerek: Antibiotikum terápia...
            3. Irányelvek: EMA guideline szerint...
            4. Prognózis: Jó kilátások...
            5. További vizsgálatok: MRI javasolt...
            """
        ]
        
        for i, test_response in enumerate(test_responses):
            st.write(f"### Teszt {i+1}")
            result = self._parse_analysis_response(test_response)
            st.json(result)
    
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
        #st.info("🔬 PubMed mélykutatás indítása...")
        
        # Analyzer inicializálása
        analyzer = PubMedAnalyzer(openai_api_key)
        
        # 1. Magyar adatok fordítása angolra
        #st.info("🌐 Adatok előkészítése a kereséshez...")
        translated_data = analyzer.translate_patient_data(patient_data)
        
        # 2. Keresési query összeállítása
        search_query = analyzer.build_search_query(translated_data, rag_results)
        #st.info(f"🔍 Keresési kifejezés: {search_query}")
        
        # 3. PubMed keresés - TOVÁBBFEJLESZTETT STRATÉGIA
        #st.info("🔍 Optimalizált PubMed keresés indítása...")
        pubmed_results = analyzer.run_advanced_pubmed_search(translated_data)
        
        # Ha a fejlett keresés nem működött, próbáljuk az egyszerű keresést
        if not pubmed_results or len(pubmed_results.strip()) < 100:
            st.warning("⚠️ Fejlett keresés sikertelen, egyszerű keresés próbálása...")
            pubmed_results = analyzer.run_simple_pubmed_search(patient_data)
        
        if not pubmed_results:
            st.warning("⚠️ Nem találtunk releváns publikációkat egyik módszerrel sem")
            return analyzer._create_empty_result()
        
        # 4. Eredmények elemzése
        #with st.spinner("🤖 Publikációk elemzése..."):
        analysis_results = analyzer.analyze_pubmed_results(
            pubmed_results, 
            patient_data,
            rag_results
        )
        '''
        st.info("🤖 Publikációk elemzése és magyar nyelvű összefoglaló készítése...")
        analysis_results = analyzer.analyze_pubmed_results(
            pubmed_results, 
            patient_data,
            rag_results
        )
        '''

        # 5. Eredmények mentése
        save_path = analyzer.save_results(analysis_results, patient_data)
        #if save_path:
         #   st.success(f"💾 Eredmények elmentve: {Path(save_path).name}")
        
        # 6. Eredmények megjelenítése
        #display_pubmed_results(analysis_results, save_path)
        
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
            #with st.expander(title, expanded=(key == "research_findings")):
            #    st.markdown(content)

            st.success(f"👨‍⚕️ {title}: {content.strip()}")
    
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