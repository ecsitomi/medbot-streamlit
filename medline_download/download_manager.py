# =============================================================================
# medline_download/download_manager.py
# =============================================================================
"""
Fő koordinátor osztály a letöltési folyamathoz
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import json
import streamlit as st
from concurrent.futures import ThreadPoolExecutor
import hashlib

from .api_client import MedlineFullContentClient
from .xml_parser import MedlineXMLParser, MedlineTopicContent
from .pdf_generator import MedlinePDFGenerator
from .config import MEDLINE_DOWNLOAD_CONFIG, PDF_DIR, CACHE_DIR

class MedlineDownloadManager:
    """
    Medline letöltések koordinálása
    """
    
    def __init__(self):
        self.api_client = MedlineFullContentClient()
        self.xml_parser = MedlineXMLParser()
        self.pdf_generator = MedlinePDFGenerator()
        self.config = MEDLINE_DOWNLOAD_CONFIG
        self._init_session_state()
    
    def _init_session_state(self):
        """Session state inicializálás"""
        if 'medline_download_status' not in st.session_state:
            st.session_state.medline_download_status = {
                'state': 'idle',  # idle, downloading, completed, error
                'progress': 0.0,
                'current_topic': '',
                'total_topics': 0,
                'completed_topics': 0,
                'pdf_files': [],
                'errors': []
            }
    
    async def download_topics_to_pdf(self, topics: List[Any], 
                                   patient_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Medline témák letöltése PDF-be
        
        Args:
            topics: MedlineTopicSummary objektumok listája
            patient_data: Beteg adatok a PDF-hez
            
        Returns:
            Dict: Eredmény státusz
        """
        # Státusz inicializálás
        self._update_status('downloading', 0, len(topics))
        
        result = {
            'success': False,
            'pdf_files': [],
            'errors': []
        }
        
        try:
            # NULL/üres ellenőrzések
            if not topics:
                raise ValueError("Nincsenek témák megadva")
            
            # 1. Keresési kifejezések előkészítése
            search_terms = self._prepare_search_terms(topics)
            
            if not search_terms:
                raise ValueError("Nem sikerült keresési kifejezéseket előkészíteni")
            
            # 2. API tartalmak letöltése
            topic_contents = await self._download_all_topics(search_terms)
            
            if not topic_contents:
                raise ValueError("Nem sikerült tartalmat letölteni")
            
            # 3. PDF generálás
            pdf_files = await self._generate_pdfs(topic_contents, patient_data)
            
            # 4. Eredmény összeállítása
            result['success'] = len(pdf_files) > 0
            result['pdf_files'] = pdf_files
            
            # Státusz frissítés
            self._update_status('completed', len(topics), len(topics))
            st.session_state.medline_download_status['pdf_files'] = pdf_files
            
        except Exception as e:
            error_msg = f"Letöltési hiba: {str(e)}"
            result['errors'].append(error_msg)
            self._update_status('error', errors=[error_msg])
            print(f"HIBA DEBUG: {e}")  # Debug info
            import traceback
            traceback.print_exc()
        
        return result
    
    def _prepare_search_terms(self, topics: List[Any]) -> Dict[str, str]:
        """Keresési kifejezések előkészítése"""
        search_terms = {}
        
        if not topics:
            return search_terms
        
        print(f"DEBUG: Feldolgozandó témák száma: {len(topics)}")
        
        for i, topic in enumerate(topics):
            try:
                # MedlineTopicSummary objektumból
                if hasattr(topic, 'title') and topic.title:
                    # Tisztítás és normalizálás + egyedi index
                    clean_title = str(topic.title).lower().strip()
                    if clean_title:  # Nem üres
                        # Egyedi kulcs létrehozása index hozzáadásával
                        unique_key = f"{clean_title}_{i}"
                        search_terms[unique_key] = str(topic.title)
                        print(f"DEBUG: Hozzáadva topic {i}: '{topic.title}' -> key: '{unique_key}'")
                elif hasattr(topic, 'name') and topic.name:
                    # Alternatív név mező
                    clean_name = str(topic.name).lower().strip()
                    if clean_name:
                        unique_key = f"{clean_name}_{i}"
                        search_terms[unique_key] = str(topic.name)
                        print(f"DEBUG: Hozzáadva topic {i} (name): '{topic.name}' -> key: '{unique_key}'")
                elif isinstance(topic, str):
                    # Ha string-et kaptunk
                    clean_topic = topic.lower().strip()
                    if clean_topic:
                        unique_key = f"{clean_topic}_{i}"
                        search_terms[unique_key] = topic
                        print(f"DEBUG: Hozzáadva topic {i} (string): '{topic}' -> key: '{unique_key}'")
                else:
                    print(f"FIGYELEM: Ismeretlen topic típus: {type(topic)} - {topic}")
            except Exception as e:
                print(f"Hiba topic feldolgozásnál: {e}")
                continue
        
        print(f"DEBUG: Végső search_terms: {search_terms}")
        return search_terms
    
    async def _download_all_topics(self, search_terms: Dict[str, str]) -> List[MedlineTopicContent]:
        """Összes topic letöltése és parse-olása"""
        contents = []
        
        if not search_terms:
            return contents
        
        total = len(search_terms)
        completed = 0
        
        try:
            # Cache ellenőrzés - a valódi címeket használjuk
            cached_contents = self._load_from_cache(list(search_terms.values()))
            if cached_contents is None:
                cached_contents = {}
            
            # Csak a nem cachelt elemek letöltése
            to_download = {
                term: title for term, title in search_terms.items() 
                if title not in cached_contents
            }
            
            if to_download:
                # Párhuzamos letöltés
                self._update_status(current_topic="Tartalmak letöltése...")
                
                # API hívások - a values() értékeket küldjük (valódi címek)
                api_results = await self.api_client.fetch_multiple_topics(
                    list(to_download.values())
                )
                
                if api_results is None:
                    api_results = {}
                
                # XML parse - most újra össze kell párosítani a kulcsokat és értékeket
                term_to_key_map = {title: key for key, title in to_download.items()}
                for title, xml_content in api_results.items():
                    if xml_content and title in term_to_key_map:
                        key = term_to_key_map[title]
                        completed += 1
                        self._update_status(
                            progress=completed/total,
                            current_topic=f"Feldolgozás: {title}",
                            completed_topics=completed
                        )
                        
                        parsed = self.xml_parser.parse_topic_xml(xml_content)
                        if parsed:
                            contents.append(parsed)
                            # Cache mentés - a címet használjuk kulcsként, nem az egyedi azonosítót
                            self._save_to_cache(title, parsed)
                        else:
                            error_msg = f"Parse hiba: {title}"
                            st.session_state.medline_download_status['errors'].append(error_msg)
                            print(f"DEBUG: {error_msg}")
            
            # Cachelt tartalmak hozzáadása
            if cached_contents:
                contents.extend(cached_contents.values())
        
        except Exception as e:
            print(f"Download all topics hiba: {e}")
            import traceback
            traceback.print_exc()
        
        return contents
    
    async def _generate_pdfs(self, contents: List[MedlineTopicContent], 
                           patient_data: Optional[Dict]) -> List[str]:
        """PDF-ek generálása"""
        pdf_files = []
        
        if not contents:
            return pdf_files
        
        total = len(contents)
        
        try:
            # Egyedi PDF-ek generálása
            for i, content in enumerate(contents):
                if content is None:
                    continue
                    
                # FIX: Biztonságos title kinyerése
                content_title = self._safe_get_title(content)
                
                self._update_status(
                    progress=(i+1)/total,
                    current_topic=f"PDF generálás: {content_title}"
                )
                
                # Fájlnév generálás - sorszámmal
                filename = self._generate_filename(content_title, i + 1)
                filepath = PDF_DIR / filename
                
                # PDF generálás
                success = await self._generate_single_pdf(content, str(filepath), patient_data)
                
                if success:
                    pdf_files.append(filename)
                else:
                    error_msg = f"PDF generálási hiba: {content_title}"
                    st.session_state.medline_download_status['errors'].append(error_msg)
            
            # Opcionális: Kombinált PDF
            if len(contents) > 1 and st.session_state.get('medline_combined_pdf', False):
                combined_filename = f"medline_combined_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                combined_path = PDF_DIR / combined_filename
                
                success = self.pdf_generator.generate_combined_pdf(
                    contents, str(combined_path), patient_data
                )
                
                if success:
                    pdf_files.append(combined_filename)
        
        except Exception as e:
            print(f"PDF generálási hiba: {e}")
            import traceback
            traceback.print_exc()
        
        return pdf_files
    
    def _safe_get_title(self, content: MedlineTopicContent) -> str:
        """Biztonságos title kinyerés"""
        if content is None:
            return "Unknown Topic"
        
        # Próbáljuk meg a title mezőt
        if hasattr(content, 'title') and content.title:
            title = content.title
            # Ellenőrizzük, hogy string-e és nem None
            if title is not None and str(title).strip():
                return str(title).strip()
        
        # Alternatívák
        if hasattr(content, 'name') and content.name:
            name = content.name
            if name is not None and str(name).strip():
                return str(name).strip()
        
        # Fallback
        return "Unknown Topic"
    
    async def _generate_single_pdf(self, content: MedlineTopicContent, 
                                 filepath: str, patient_data: Optional[Dict]) -> bool:
        """Egyetlen PDF generálása (async wrapper)"""
        try:
            if content is None:
                return False
                
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                return await loop.run_in_executor(
                    executor,
                    self.pdf_generator.generate_pdf,
                    content,
                    filepath,
                    patient_data
                )
        except Exception as e:
            print(f"Single PDF generálási hiba: {e}")
            return False
    
    def _generate_filename(self, title: str, index: int = 1) -> str:
        """Biztonságos fájlnév generálás"""
        try:
            # FIX: None ellenőrzés és alapértelmezett érték
            if title is None or not str(title).strip():
                title = f"medline_topic_{index}"
            else:
                title = str(title).strip()  # Biztosítjuk, hogy string legyen
            
            # Tisztítás - csak akkor, ha van mit tisztítani
            if title:
                # Csak ASCII karakterek, számok, szóközök, kötőjelek, aláhúzások
                safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_'))
                safe_title = safe_title.replace(' ', '_')[:50]  # Max 50 karakter
            else:
                safe_title = ""
            
            if not safe_title:  # Ha teljesen üres lett
                safe_title = f"medline_topic_{index}"
            
            # Sorszám és dátum egyedi azonosító
            date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            return f"medline_{index:02d}_{safe_title}_{date_str}.pdf"
            
        except Exception as e:
            print(f"Filename generálási hiba: {e}")
            # Fallback: mindig működő fájlnév
            return f"medline_topic_{index:02d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    def _update_status(self, state: Optional[str] = None, 
                      progress: Optional[float] = None,
                      total_topics: Optional[int] = None,
                      current_topic: Optional[str] = None,
                      completed_topics: Optional[int] = None,
                      errors: Optional[List[str]] = None):
        """Státusz frissítése"""
        try:
            status = st.session_state.medline_download_status
            
            if state is not None:
                status['state'] = state
            if progress is not None:
                status['progress'] = progress
            if total_topics is not None:
                status['total_topics'] = total_topics
            if current_topic is not None:
                status['current_topic'] = current_topic
            if completed_topics is not None:
                status['completed_topics'] = completed_topics
            if errors is not None:
                status['errors'].extend(errors)
        except Exception as e:
            print(f"Státusz frissítési hiba: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Aktuális státusz lekérése"""
        try:
            return st.session_state.medline_download_status
        except Exception as e:
            print(f"Státusz lekérési hiba: {e}")
            return {
                'state': 'error',
                'progress': 0.0,
                'current_topic': '',
                'total_topics': 0,
                'completed_topics': 0,
                'pdf_files': [],
                'errors': [str(e)]
            }
    
    # Cache kezelés
    def _load_from_cache(self, terms: List[str]) -> Dict[str, MedlineTopicContent]:
        """Cache-ből betöltés"""
        cached = {}
        
        try:
            if not self.config["cache"]["enabled"] or not terms:
                return cached
            
            for term in terms:
                if not term:
                    continue
                    
                cache_file = self._get_cache_path(term)
                if cache_file and cache_file.exists():
                    try:
                        # Ellenőrizzük a cache érvényességét
                        age_hours = (datetime.now().timestamp() - 
                                   cache_file.stat().st_mtime) / 3600
                        
                        if age_hours < self.config["cache"]["ttl_hours"]:
                            with open(cache_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                # Rekonstrukció
                                content = MedlineTopicContent(**data)
                                cached[term] = content
                    except Exception as e:
                        print(f"Cache betöltési hiba ({term}): {e}")
        except Exception as e:
            print(f"Cache load hiba: {e}")
        
        return cached
    
    def _save_to_cache(self, term: str, content: MedlineTopicContent):
        """Cache-be mentés"""
        try:
            if not self.config["cache"]["enabled"] or not term or not content:
                return
            
            cache_file = self._get_cache_path(term)
            if cache_file:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(content.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Cache mentési hiba ({term}): {e}")
    
    def _get_cache_path(self, term: str) -> Optional[Path]:
        """Cache fájl útvonal generálás"""
        try:
            if not term:
                return None
            # Hash a fájlnévhez
            term_hash = hashlib.md5(str(term).encode()).hexdigest()[:16]
            return CACHE_DIR / f"medline_{term_hash}.json"
        except Exception as e:
            print(f"Cache path hiba: {e}")
            return None
    
    def clear_cache(self):
        """Cache törlése"""
        try:
            for cache_file in CACHE_DIR.glob("medline_*.json"):
                cache_file.unlink()
            return True
        except Exception as e:
            print(f"Cache törlési hiba: {e}")
            return False