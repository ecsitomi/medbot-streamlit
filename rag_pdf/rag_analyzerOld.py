# =============================================================================
# rag_pdf/rag_analyzerOLD.py
# =============================================================================
"""
RAG alapú elemzés és válaszgenerálás
"""
import streamlit as st
from typing import Dict, Any, List, Optional
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import Document
from langchain.chains import LLMChain
import json
from pathlib import Path
import os

from .pdf_processor import PDFProcessor
from .vector_store import VectorStoreManager
from .config import RAG_CONFIG

def translate_text(text: str, openai_api_key: str) -> str:
    """Egyéni szöveg lefordítása angolra"""
    if not text:
        return ""
    llm = ChatOpenAI(openai_api_key=openai_api_key, temperature=0)
    return llm.predict(f"Translate the following Hungarian medical term or sentence to English: '{text}'").strip()

def translate_list(texts: List[str], openai_api_key: str) -> List[str]:
    """Lista fordítása angolra"""
    return [translate_text(t, openai_api_key) for t in texts if t]

def translate_patient_data(patient_data: Dict[str, Any], openai_api_key: str) -> Dict[str, Any]:
    """Betegadatok lefordítása angolra a RAG kereséshez"""
    translated = patient_data.copy()
    
    translated['symptoms'] = translate_list(patient_data.get('symptoms', []), openai_api_key)
    translated['diagnosis'] = translate_text(patient_data.get('diagnosis', ''), openai_api_key)
    translated['existing_conditions'] = translate_list(patient_data.get('existing_conditions', []), openai_api_key)
    translated['medications'] = translate_list(patient_data.get('medications', []), openai_api_key)
    
    return translated

class RAGAnalyzer:
    """RAG alapú Medline PDF elemző"""
    
    def __init__(self, openai_api_key: str):
        self.pdf_processor = PDFProcessor()
        self.vector_store_manager = VectorStoreManager(openai_api_key)
        
        # LLM inicializálása
        self.llm = ChatOpenAI(
            openai_api_key=openai_api_key,
            model_name=RAG_CONFIG["llm"]["model"],
            temperature=RAG_CONFIG["llm"]["temperature"],
            max_tokens=RAG_CONFIG["llm"]["max_tokens"]
        )
        
        # Prompt template
        '''
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """Te egy egészségügyi szakértő vagy, aki a Medline Plus információk alapján 
            személyre szabott tanácsokat ad. A következő releváns információk állnak rendelkezésedre 
            a beteg állapotával kapcsolatban.
            
            Kontextus a Medline dokumentumokból:
            {context}
            
            A beteg adatai:
            - Életkor: {age} év
            - Nem: {gender}
            - Tünetek: {symptoms}
            - Időtartam: {duration}
            - Súlyosság: {severity}
            - Diagnózis: {diagnosis}
            - Meglévő betegségek: {existing_conditions}
            - Gyógyszerek: {medications}
            """),
            ("human", """A fenti információk alapján kérlek adj részletes választ a következő kérdésekre:

            1. **Milyen beteg a páciens?** - Mi lehet a probléma a Medline információk alapján?
            2. **Mit tehet a tünetek ellen?** - Milyen otthoni kezelések, életmódbeli változtatások segíthetnek?
            3. **Milyen orvoshoz forduljon?** - Melyik szakorvost ajánlod és miért?
            4. **További hasznos információk** - Ami fontos lehet a beteg számára

            Kérlek strukturált, könnyen érthető választ adj magyarul!""")
        ])
        '''
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are a healthcare expert providing personalized advice based on Medline Plus information. 
            The following relevant information is available about the patient's condition.

            Context from Medline documents:
            {context}

            Patient data:
            - Age: {age} years
            - Gender: {gender}
            - Symptoms: {symptoms}
            - Duration: {duration}
            - Severity: {severity}
            - Diagnosis: {diagnosis}
            - Pre-existing conditions: {existing_conditions}
            - Medications: {medications}
            """),
                ("human", """Based on the above information, please provide a detailed answer to the following questions:

            1. **What might be the patient's condition?** – What could be the issue based on the Medline information?
            2. **What can the patient do about the symptoms?** – What home treatments or lifestyle changes could help?
            3. **Which doctor should the patient consult?** – What kind of specialist do you recommend and why?
            4. **Additional useful information** – Anything else that could be important for the patient

            Please give a clear, structured, and easy-to-understand answer in **Hungarian**!""")
        ])

        
        # LLM Chain
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt_template)
    
    def prepare_context(self, relevant_docs: List[Document]) -> str:
        """Releváns dokumentumok kontextussá alakítása"""
        if not relevant_docs:
            return "Nincs releváns Medline információ."
        
        context_parts = []
        for i, doc in enumerate(relevant_docs, 1):
            source = doc.metadata.get('source', 'Unknown')
            content = doc.page_content[:500]  # Max 500 karakter dokumentumonként
            context_parts.append(f"[{i}. Forrás: {source}]\n{content}...")
        
        return "\n\n".join(context_parts)
    
    def analyze_patient_with_rag(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Beteg elemzése RAG használatával"""
        st.info("🔍 RAG alapú elemzés indítása...")

        try:
            # PDF-ek feldolgozása
            if not hasattr(self.vector_store_manager, 'vectorstore') or self.vector_store_manager.vectorstore is None:
                st.info("📄 PDF-ek feldolgozása és indexelése...")
                chunks = self.pdf_processor.process_pdfs()
                if chunks:
                    self.vector_store_manager.create_or_load_vectorstore(chunks)
                else:
                    st.warning("Nincsenek feldolgozható PDF-ek")
                    return self._create_empty_result()
            else:
                self.vector_store_manager.create_or_load_vectorstore()

            # 🔄 Betegadatok fordítása angolra
            st.info("🌐 Betegadatok fordítása angolra a dokumentumkereséshez...")
            translated_data = translate_patient_data(patient_data, self.llm.openai_api_key)

            # 🔎 Releváns információk keresése
            st.info("🔎 Releváns információk keresése...")
            symptoms = translated_data.get('symptoms', [])
            diagnosis = translated_data.get('diagnosis', '')

            relevant_docs = self.vector_store_manager.search_by_symptoms(
                symptoms=symptoms,
                diagnosis=diagnosis
            )

            if not relevant_docs:
                st.warning("Nem találtam releváns információkat a Medline dokumentumokban")
                return self._create_empty_result()

            # Kontextus
            context = self.prepare_context(relevant_docs)

            # 🤖 AI válasz generálása magyar nyelven (magyar adatokkal)
            st.info("🤖 AI válasz generálása...")

            input_data = {
                "context": context,
                "age": patient_data.get('age', 'ismeretlen'),
                "gender": patient_data.get('gender', 'ismeretlen'),
                "symptoms": ', '.join(patient_data.get('symptoms', [])) or 'nincs megadva',
                "duration": patient_data.get('duration', 'ismeretlen'),
                "severity": patient_data.get('severity', 'ismeretlen'),
                "diagnosis": patient_data.get('diagnosis', 'nincs megadva'),
                "existing_conditions": ', '.join(patient_data.get('existing_conditions', [])) or 'nincs',
                "medications": ', '.join(patient_data.get('medications', [])) or 'nincs'
            }

            response = self.chain.run(**input_data)

            result = self._parse_ai_response(response)
            result['timestamp'] = datetime.now().isoformat()
            result['sources'] = [doc.metadata.get('source', 'Unknown') for doc in relevant_docs]

            st.success("✅ RAG elemzés sikeres!")
            return result

        except Exception as e:
            st.error(f"RAG elemzési hiba: {e}")
            return self._create_empty_result()

    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """AI válasz strukturált formába alakítása"""
        # Egyszerű parsing - később lehet sophisticatedebb
        sections = {
            "patient_condition": "",
            "symptom_management": "",
            "recommended_specialist": "",
            "additional_info": ""
        }
        
        # Szekciók keresése a válaszban
        current_section = None
        lines = response.split('\n')
        
        for line in lines:
            if "Milyen beteg" in line or "probléma" in line:
                current_section = "patient_condition"
            elif "Mit tehet" in line or "tünetek ellen" in line:
                current_section = "symptom_management"
            elif "orvoshoz" in line or "szakorvos" in line:
                current_section = "recommended_specialist"
            elif "További" in line or "hasznos" in line:
                current_section = "additional_info"
            elif current_section and line.strip():
                sections[current_section] += line + "\n"
        
        # Tisztítás
        for key in sections:
            sections[key] = sections[key].strip()
        
        # Ha nem sikerült parseolni, akkor az egész választ visszaadjuk
        if not any(sections.values()):
            sections["full_response"] = response
        
        return sections
    
    def _create_empty_result(self) -> Dict[str, Any]:
        """Üres eredmény struktúra"""
        return {
            "patient_condition": "Nem áll rendelkezésre információ",
            "symptom_management": "Nem áll rendelkezésre információ",
            "recommended_specialist": "Nem áll rendelkezésre információ",
            "additional_info": "Nem áll rendelkezésre információ",
            "timestamp": datetime.now().isoformat(),
            "sources": []
        }
    
    def save_results(self, results: Dict[str, Any], patient_data: Dict[str, Any], 
                    export_path: Path = None) -> Dict[str, str]:
        """Eredmények mentése JSON és PDF formátumban"""
        if export_path is None:
            export_path = Path("rag_data/exports")
        
        export_path.mkdir(parents=True, exist_ok=True)
        
        # Teljes export adat összeállítása
        export_data = {
            "rag_analysis": results,
            "patient_data": patient_data,
            "analysis_timestamp": results.get('timestamp', datetime.now().isoformat()),
            "case_id": patient_data.get('case_id', f"rag_{datetime.now().strftime('%Y%m%d%H%M%S')}")
        }
        
        # JSON mentés
        json_path = export_path / f"{export_data['case_id']}_rag.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        # PDF generálás (a meglévő PDF generator használatával)
        try:
            from export.pdf_generator import generate_pdf
            
            # RAG eredmények hozzáadása az export adatokhoz
            export_data_for_pdf = patient_data.copy()
            export_data_for_pdf['rag_analysis'] = results
            
            pdf_data = generate_pdf(export_data_for_pdf)
            if pdf_data:
                pdf_path = export_path / f"{export_data['case_id']}_rag.pdf"
                with open(pdf_path, 'wb') as f:
                    f.write(pdf_data.getvalue())
            else:
                pdf_path = None
                
        except Exception as e:
            st.error(f"PDF generálási hiba: {e}")
            pdf_path = None
        
        return {
            "json_path": str(json_path),
            "pdf_path": str(pdf_path) if pdf_path else None
        }

# =============================================================================
# Főfüggvény a könnyű használathoz
# =============================================================================

def run_rag_analysis(patient_data: Dict[str, Any], openai_api_key: str = None) -> Dict[str, Any]:
    """
    RAG elemzés futtatása
    
    Args:
        patient_data: Beteg adatok (a session state-ből)
        openai_api_key: OpenAI API kulcs
        
    Returns:
        Dict: RAG elemzés eredménye
    """
    # API kulcs lekérése
    if not openai_api_key:
        #openai_api_key = st.secrets.get("OPENAI_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not openai_api_key:
        st.error("OpenAI API kulcs nem található!")
        return {}
    
    # RAG Analyzer inicializálása
    analyzer = RAGAnalyzer(openai_api_key)
    
    # Elemzés futtatása
    results = analyzer.analyze_patient_with_rag(patient_data)
    
    # Eredmények mentése
    save_paths = analyzer.save_results(results, patient_data)
    
    # Eredmények megjelenítése
    st.markdown("### 🧠 RAG Elemzés Eredménye")
    
    with st.expander("📋 Beteg állapota", expanded=True):
        st.markdown(results.get('patient_condition', 'Nincs információ'))
    
    with st.expander("💊 Mit tehet a tünetek ellen", expanded=True):
        st.markdown(results.get('symptom_management', 'Nincs információ'))
    
    with st.expander("👨‍⚕️ Ajánlott szakorvos", expanded=True):
        st.markdown(results.get('recommended_specialist', 'Nincs információ'))
    
    with st.expander("ℹ️ További információk", expanded=True):
        st.markdown(results.get('additional_info', 'Nincs információ'))
    
    # Források megjelenítése
    if results.get('sources'):
        st.info(f"📚 Felhasznált források: {', '.join(results['sources'])}")
    
    # Export linkek
    st.markdown("### 📥 Letöltés")
    col1, col2 = st.columns(2)
    
    with col1:
        if save_paths.get('json_path'):
            with open(save_paths['json_path'], 'r', encoding='utf-8') as f:
                st.download_button(
                    label="📄 RAG JSON letöltése",
                    data=f.read(),
                    file_name=Path(save_paths['json_path']).name,
                    mime="application/json"
                )
    
    with col2:
        if save_paths.get('pdf_path'):
            with open(save_paths['pdf_path'], 'rb') as f:
                st.download_button(
                    label="📑 RAG PDF letöltése",
                    data=f.read(),
                    file_name=Path(save_paths['pdf_path']).name,
                    mime="application/pdf"
                )
    
    return results