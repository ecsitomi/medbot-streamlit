# =============================================================================
# rag_pdf/rag_analyzer.py - JAVÍTOTT VERZIÓ
# =============================================================================
"""
RAG alapú PDF elemzés JAVÍTOTT VERZIÓ - deprecated függvények kijavítva
"""
import os
import streamlit as st
from typing import List, Dict, Any, Optional
from datetime import datetime
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
#from langchain_chroma import Chroma
import json
from pathlib import Path

# Streamlitre kell
try:
    import pysqlite3
    import sys
    sys.modules["sqlite3"] = pysqlite3
except ImportError:
    print("⚠️ pysqlite3-binary nem elérhető – SQLite override sikertelen")

# Fordítási segédfüggvények
def translate_text(text: str, openai_api_key: str) -> str:
    if not text:
        return ""
    llm = ChatOpenAI(openai_api_key=openai_api_key, temperature=0)
    return llm.predict(f"Translate this Hungarian medical phrase to English: {text}").strip()

def translate_list(items: List[str], openai_api_key: str) -> List[str]:
    return [translate_text(item, openai_api_key) for item in items if item]

def translate_patient_data(patient_data: Dict[str, Any], openai_api_key: str) -> Dict[str, Any]:
    translated = patient_data.copy()
    translated['symptoms'] = translate_list(patient_data.get('symptoms', []), openai_api_key)
    translated['diagnosis'] = translate_text(patient_data.get('diagnosis', ''), openai_api_key)
    translated['existing_conditions'] = translate_list(patient_data.get('existing_conditions', []), openai_api_key)
    translated['medications'] = translate_list(patient_data.get('medications', []), openai_api_key)
    return translated

###

class RAGAnalyzer:
    """
    RAG alapú PDF elemzés JAVÍTOTT VERZIÓ
    """
    
    def __init__(self, vector_store_path: str = "rag_pdf/vectorstore"):
        self.vector_store_path = vector_store_path
        self.embeddings = None
        self.vectorstore = None
        self.llm = None
        self.retrieval_chain = None
        self._initialize_components()
    
    def _initialize_components(self):
        """Komponensek inicializálása JAVÍTOTT verzió"""
        try:
            # ✅ JAVÍTVA: OpenAI API key kezelés
            api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key not found")
            
            # ✅ JAVÍTVA: Modern LangChain komponensek
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=api_key,
                model="text-embedding-3-small"  # Legújabb embedding model
            )
            
            self.llm = ChatOpenAI(
                openai_api_key=api_key,
                model="gpt-4",
                temperature=0.1,
                max_tokens=1500
            )
            
            # Vector store betöltése vagy létrehozása
            self._load_or_create_vectorstore()
            
            # ✅ JAVÍTVA: Modern LCEL (LangChain Expression Language) chain
            self._create_retrieval_chain()
            
            print("✅ RAG Analyzer sikeresen inicializálva")
            
        except Exception as e:
            print(f"❌ RAG Analyzer inicializálási hiba: {e}")
            raise
    
    def _load_or_create_vectorstore(self):
        """Vector store betöltése vagy létrehozása"""
        try:
            if os.path.exists(self.vector_store_path):
                # ✅ JAVÍTVA: Betöltés ellenőrzése
                self.vectorstore = Chroma(
                    persist_directory=self.vector_store_path,
                    embedding_function=self.embeddings
                )
                
                # Ellenőrizzük, hogy van-e tartalom
                collection_count = self.vectorstore._collection.count()
                if collection_count > 0:
                    print(f"✅ Vector store betöltve: {collection_count} dokumentum")
                else:
                    print("⚠️ Vector store üres, PDF-ek betöltése szükséges")
                    self._load_pdfs_to_vectorstore()
            else:
                print("📁 Vector store nem létezik, létrehozás...")
                self._load_pdfs_to_vectorstore()
                
        except Exception as e:
            print(f"❌ Vector store hiba: {e}")
            # Fallback: új vector store létrehozása
            self._load_pdfs_to_vectorstore()
    
    def _load_pdfs_to_vectorstore(self):
        """PDF-ek betöltése a vector store-ba JAVÍTOTT verzió"""
        try:
            # ✅ JAVÍTVA: PDF könyvtár ellenőrzése
            pdf_directory = Path("medline_data/pdfs")
            if not pdf_directory.exists():
                print(f"❌ PDF könyvtár nem létezik: {pdf_directory}")
                return
            
            pdf_files = list(pdf_directory.glob("*.pdf"))
            if not pdf_files:
                print("❌ Nincsenek PDF fájlok a könyvtárban")
                return
            
            print(f"📚 PDF fájlok betöltése: {len(pdf_files)} fájl")
            
            # ✅ JAVÍTVA: Dokumentumok feldolgozása
            all_documents = []
            
            for pdf_file in pdf_files:
                try:
                    # PDF betöltése
                    loader = PyPDFLoader(str(pdf_file))
                    documents = loader.load()
                    
                    # Metadata hozzáadása
                    for doc in documents:
                        doc.metadata.update({
                            'source_file': pdf_file.name,
                            'file_type': 'medline_pdf',
                            'topic': self._extract_topic_from_filename(pdf_file.name)
                        })
                    
                    all_documents.extend(documents)
                    print(f"✅ Betöltve: {pdf_file.name} ({len(documents)} oldal)")
                    
                except Exception as e:
                    print(f"❌ Hiba PDF betöltésekor ({pdf_file.name}): {e}")
            
            if not all_documents:
                print("❌ Nincsenek betölthető dokumentumok")
                return
            
            # ✅ JAVÍTVA: Text splitting optimalizálása
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,      # Kisebb chunk-ok a pontosabb retrievalért
                chunk_overlap=200,    # Átfedés a kontextus megőrzésére
                length_function=len,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            
            split_documents = text_splitter.split_documents(all_documents)
            print(f"📄 Dokumentumok feldarabolva: {len(split_documents)} chunk")
            
            # ✅ JAVÍTVA: Vector store létrehozása
            os.makedirs(self.vector_store_path, exist_ok=True)
            
            self.vectorstore = Chroma.from_documents(
                documents=split_documents,
                embedding=self.embeddings,
                persist_directory=self.vector_store_path
            )
            
            print(f"✅ Vector store létrehozva: {len(split_documents)} dokumentum chunk")
            
        except Exception as e:
            print(f"❌ PDF betöltési hiba: {e}")
            raise
    
    def _extract_topic_from_filename(self, filename: str) -> str:
        """Topic kinyerése a fájlnévből"""
        # medline_01_headache_20250730_095014.pdf
        parts = filename.replace('.pdf', '').split('_')
        if len(parts) >= 3:
            return parts[2]  # headache rész
        return "unknown"
    
    def _create_retrieval_chain(self):
        """✅ JAVÍTVA: Modern LCEL chain létrehozása"""
        if not self.vectorstore:
            raise ValueError("Vector store nincs inicializálva")
        
        # ✅ JAVÍTVA: Magyar nyelvű prompt template
        prompt_template = PromptTemplate.from_template("""
Te egy egészségügyi szakértő vagy, aki Medline Plus információk alapján ad tanácsokat.

KONTEXTUS (Medline Plus dokumentumok):
{context}

BETEG ADATOK ÉS KÉRDÉS: {question}

FELADAT:
Válaszolj MAGYARUL a következő kérdésekre a Medline dokumentumok alapján:

1. **Mi lehet a beteg problémája?** - Diagnózis és magyarázat
2. **Mit tehet a tünetek ellen?** - Kezelési lehetőségek és otthoni praktikák  
3. **Milyen orvoshoz forduljon?** - Specializáció és sürgősség
4. **További tanácsok** - Megelőzés és hasznos információk

Ha nincs releváns információ, írd: "Nincs megfelelő információ a dokumentumokban"

VÁLASZ MAGYARUL:
""")

        # ✅ JAVÍTVA: Retriever konfigurálása
        retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": 5,  # Top 5 legrelvánsabb chunk
                #"score_threshold": 0.3  # Minimum hasonlósági küszöb
            }
        )
        
        # ✅ JAVÍTVA: Modern LCEL chain (LangChain Expression Language)
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        self.retrieval_chain = (
            {
                "context": retriever | format_docs,
                "question": RunnablePassthrough()
            }
            | prompt_template
            | self.llm
            | StrOutputParser()
        )
        
        print("✅ Modern LCEL retrieval chain létrehozva")
    
    def analyze_medical_case(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orvosi eset elemzése JAVÍTOTT verzió
        
        Args:
            case_data: Orvosi eset adatok (JSON)
            
        Returns:
            Dict: Elemzési eredmények
        """
        try:
            if not self.retrieval_chain:
                raise ValueError("RAG chain nincs inicializálva")
            
            # ✅ JAVÍTVA: Query összeállítása
            translated_data = translate_patient_data(case_data, os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY"))
            query = self._build_medical_query(translated_data)
            #query = self._build_medical_query(case_data)
            print(f"🔍 RAG Query: {query}")
            
            # ✅ JAVÍTVA: Modern invoke használata predict helyett
            with st.spinner("RAG elemzés folyamatban..."):
                rag_response = self.retrieval_chain.invoke(query)
            
            print(f"📄 RAG Response: {rag_response[:200]}...")
            
            # ✅ JAVÍTVA: Válasz feldolgozása
            analysis_result = self._parse_rag_response(rag_response, case_data)
            
            return analysis_result
            
        except Exception as e:
            print(f"❌ RAG elemzési hiba: {e}")
            return {
                'success': False,
                'error': str(e),
                'rag_response': None,
                'medical_insights': []
            }
    
    def _build_medical_query(self, case_data: Dict[str, Any]) -> str:
        """✅ JAVÍTVA: Orvosi query összeállítása"""
        # Alapadatok kinyerése
        symptoms = case_data.get('symptoms', [])
        age = case_data.get('age', 'ismeretlen')
        gender = case_data.get('gender', 'ismeretlen')
        duration = case_data.get('duration', 'ismeretlen')
        diagnosis = case_data.get('diagnosis', '')
        existing_conditions = case_data.get('existing_conditions', [])
        medications = case_data.get('medications', [])
        
        # Query összeállítása magyar nyelven
        query_parts = []
        
        query_parts.append(f"Páciens: {age} éves {gender}")
        
        if symptoms:
            symptoms_text = ', '.join(symptoms)
            query_parts.append(f"Tünetek: {symptoms_text}")
        
        if duration and duration != 'ismeretlen':
            query_parts.append(f"Időtartam: {duration}")
        
        if diagnosis and diagnosis != "Nem sikerült diagnózist javasolni.":
            query_parts.append(f"Lehetséges diagnózis: {diagnosis}")
            
        if existing_conditions:
            query_parts.append(f"Meglévő betegségek: {', '.join(existing_conditions)}")
            
        if medications:
            query_parts.append(f"Gyógyszerek: {', '.join(medications)}")
        
        main_query = " | ".join(query_parts)
        
        full_query = f"""
{main_query}

Kérlek adj részletes egészségügyi tanácsokat a Medline dokumentumok alapján!
"""
        
        return full_query.strip()
    
    def _parse_rag_response(self, rag_response: str, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """✅ JAVÍTVA: RAG válasz feldolgozása strukturált formába"""
        
        # ✅ JAVÍTVA: Üres válasz ellenőrzés
        if not rag_response or rag_response.strip() == "":
            return {
                'success': False,
                'error': 'Üres RAG válasz',
                'patient_condition': 'Nincs információ',
                'symptom_management': 'Nincs információ', 
                'recommended_specialist': 'Nincs információ',
                'additional_info': 'Nincs információ',
                'timestamp': datetime.now().isoformat(),
                'sources': []
            }
        
        # ✅ JAVÍTVA: "Nincs releváns információ" ellenőrzés
        if "nincs megfelelő információ" in rag_response.lower() or "nincs releváns információ" in rag_response.lower():
            return {
                'success': False,
                'error': 'Nincs releváns információ a dokumentumokban',
                'patient_condition': 'Nincs megfelelő információ a dokumentumokban',
                'symptom_management': 'Nincs megfelelő információ a dokumentumokban',
                'recommended_specialist': 'Nincs megfelelő információ a dokumentumokban', 
                'additional_info': 'Nincs megfelelő információ a dokumentumokban',
                'timestamp': datetime.now().isoformat(),
                'sources': []
            }
        
        # ✅ JAVÍTVA: Strukturált válasz kinyerése
        parsed_result = self._extract_structured_response(rag_response)
        
        # ✅ JAVÍTVA: Eredmény struktúra
        result = {
            'success': True,
            'patient_condition': parsed_result.get('patient_condition', 'Nem sikerült kinyerni'),
            'symptom_management': parsed_result.get('symptom_management', 'Nem sikerült kinyerni'),
            'recommended_specialist': parsed_result.get('recommended_specialist', 'Nem sikerült kinyerni'),
            'additional_info': parsed_result.get('additional_info', 'Nem sikerült kinyerni'),
            'timestamp': datetime.now().isoformat(),
            'sources': ['medline_pdf'],  # Általános forrás
            'full_response': rag_response  # Teljes válasz megőrzése
        }
        
        return result
    
    def _extract_structured_response(self, response: str) -> Dict[str, str]:
        #Strukturált válasz kinyerése a RAG response-ból sorszám alapján

        sections = {
            "patient_condition": "",
            "symptom_management": "",
            "recommended_specialist": "",
            "additional_info": ""
        }

        import re

        # Regex a 4 szekció címének megtalálására
        pattern = r"(1\.\s\*\*.*?\*\*.*?)(?=2\.|\Z)|" \
                r"(2\.\s\*\*.*?\*\*.*?)(?=3\.|\Z)|" \
                r"(3\.\s\*\*.*?\*\*.*?)(?=4\.|\Z)|" \
                r"(4\.\s\*\*.*?\*\*.*)"

        matches = re.findall(pattern, response, flags=re.DOTALL)

        for i, match_group in enumerate(matches):
            for match in match_group:
                if match:
                    if i == 0:
                        sections["patient_condition"] = match.strip()
                    elif i == 1:
                        sections["symptom_management"] = match.strip()
                    elif i == 2:
                        sections["recommended_specialist"] = match.strip()
                    elif i == 3:
                        sections["additional_info"] = match.strip()

        # Fallback üzenet, ha valami kimarad
        for key in sections:
            if not sections[key]:
                sections[key] = "Nem sikerült releváns információt találni"

        return sections

    
    def get_vectorstore_stats(self) -> Dict[str, Any]:
        """Vector store statisztikák"""
        try:
            if not self.vectorstore:
                return {'error': 'Vector store nincs inicializálva'}
            
            collection_count = self.vectorstore._collection.count()
            
            # Metadatok összegyűjtése
            if collection_count > 0:
                # Példa dokumentumok lekérése
                sample_docs = self.vectorstore.similarity_search("medline", k=3)
                topics = set()
                sources = set()
                
                for doc in sample_docs:
                    if 'topic' in doc.metadata:
                        topics.add(doc.metadata['topic'])
                    if 'source_file' in doc.metadata:
                        sources.add(doc.metadata['source_file'])
                
                return {
                    'total_documents': collection_count,
                    'topics_found': list(topics),
                    'source_files': list(sources),
                    'sample_content': sample_docs[0].page_content[:200] if sample_docs else None
                }
            else:
                return {
                    'total_documents': 0,
                    'topics_found': [],
                    'source_files': [],
                    'sample_content': None
                }
                
        except Exception as e:
            return {'error': f'Stats lekérési hiba: {e}'}
    
    def test_retrieval(self, query: str, k: int = 3) -> Dict[str, Any]:
        """✅ JAVÍTVA: Retrieval tesztelése"""
        try:
            if not self.vectorstore:
                return {'error': 'Vector store nincs inicializálva'}
            
            # Similarity search
            docs = self.vectorstore.similarity_search(query, k=k)
            
            results = []
            for i, doc in enumerate(docs):
                results.append({
                    'rank': i + 1,
                    'content': doc.page_content[:300],
                    'metadata': doc.metadata,
                    'content_length': len(doc.page_content)
                })
            
            return {
                'query': query,
                'results_count': len(results),
                'results': results
            }
            
        except Exception as e:
            return {'error': f'Retrieval teszt hiba: {e}'}

# =============================================================================
# HIÁNYZÓ FÜGGVÉNY HOZZÁADÁSA - kompatibilitáshoz
# =============================================================================

def run_rag_analysis(patient_data: Dict[str, Any], openai_api_key: str = None) -> Dict[str, Any]:
    """
    ✅ JAVÍTVA: RAG elemzés futtatása - kompatibilitás függvény
    
    Args:
        patient_data: Beteg adatok (a session state-ből)
        openai_api_key: OpenAI API kulcs (opcionális)
        
    Returns:
        Dict: RAG elemzés eredménye
    """
    try:
        st.info("🔍 RAG alapú elemzés indítása...")
        
        # API kulcs ellenőrzése
        if not openai_api_key:
            openai_api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
        
        if not openai_api_key:
            st.error("❌ OpenAI API kulcs nem található!")
            return _create_empty_result()
        
        # RAG Analyzer inicializálása
        analyzer = RAGAnalyzer()
        
        # Elemzés futtatása
        st.info("🤖 AI elemzés futtatása...")
        results = analyzer.analyze_medical_case(patient_data)
        
        # Eredmények ellenőrzése
        if not results.get('success', False):
            st.warning(f"⚠️ RAG elemzés problémába ütközött: {results.get('error', 'Ismeretlen hiba')}")
            return _create_empty_result()
        
        # Eredmények mentése
        save_paths = _save_rag_results(results, patient_data)
        
        # UI megjelenítés
        _display_rag_results(results, save_paths)
        
        st.success("✅ RAG elemzés sikeresen befejezve!")
        return results
        
    except Exception as e:
        st.error(f"❌ RAG elemzési hiba: {e}")
        print(f"RAG hiba részletei: {e}")
        return _create_empty_result()

def _create_empty_result() -> Dict[str, Any]:
    """Üres eredmény struktúra"""
    return {
        'success': False,
        'patient_condition': "Nem áll rendelkezésre információ",
        'symptom_management': "Nem áll rendelkezésre információ", 
        'recommended_specialist': "Nem áll rendelkezésre információ",
        'additional_info': "Nem áll rendelkezésre információ",
        'timestamp': datetime.now().isoformat(),
        'sources': []
    }

def _save_rag_results(results: Dict[str, Any], patient_data: Dict[str, Any]) -> Dict[str, str]:
    """RAG eredmények mentése"""
    try:
        export_path = Path("rag_data/exports")
        export_path.mkdir(parents=True, exist_ok=True)
        
        # Export adat összeállítása
        case_id = patient_data.get('case_id', f"rag_{datetime.now().strftime('%Y%m%d%H%M%S')}")
        export_data = {
            "rag_analysis": results,
            "patient_data": patient_data,
            "analysis_timestamp": results.get('timestamp', datetime.now().isoformat()),
            "case_id": case_id
        }
        
        # JSON mentés
        json_path = export_path / f"{case_id}_rag.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        return {
            "json_path": str(json_path),
            "pdf_path": None  # PDF generálás opcionális
        }
        
    except Exception as e:
        print(f"RAG eredmény mentési hiba: {e}")
        return {"json_path": None, "pdf_path": None}

def _display_rag_results(results: Dict[str, Any], save_paths: Dict[str, str]):
    """RAG eredmények megjelenítése"""
    st.markdown("### 🧠 RAG Elemzés Eredménye")
    
    # Eredmények megjelenítése expander-ekben
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
    
    # Letöltési lehetőségek
    if save_paths.get('json_path'):
        st.markdown("### 📥 Letöltés")
        try:
            with open(save_paths['json_path'], 'r', encoding='utf-8') as f:
                st.download_button(
                    label="📄 RAG JSON letöltése",
                    data=f.read(),
                    file_name=Path(save_paths['json_path']).name,
                    mime="application/json"
                )
        except Exception as e:
            st.error(f"Letöltési hiba: {e}")