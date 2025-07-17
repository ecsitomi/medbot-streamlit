# =============================================================================
# medline_integration/api_client.py
# =============================================================================
"""
Medline Plus API kliens az egészségügyi információk lekérdezéséhez.
Rate limiting és hibakezelés támogatással.
"""
import time
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any
import requests
import streamlit as st
from urllib.parse import quote_plus
import re

class MedlineRateLimiter:
    """Rate limiter a Medline API-hoz (max 85 kérés/perc)."""
    
    def __init__(self, max_requests: int = 80, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
    
    def can_make_request(self) -> bool:
        """Ellenőrzi, hogy küldhetünk-e kérést."""
        now = time.time()
        # Régi kérések eltávolítása
        self.requests = [req_time for req_time in self.requests if now - req_time < self.time_window]
        return len(self.requests) < self.max_requests
    
    def add_request(self):
        """Rögzíti az új kérés időpontját."""
        self.requests.append(time.time())
    
    def wait_time(self) -> float:
        """Visszaadja, mennyi ideig kell várni a következő kérésig."""
        if self.can_make_request():
            return 0.0
        oldest_request = min(self.requests)
        return self.time_window - (time.time() - oldest_request)

class MedlineAPIClient:
    """
    Medline Plus API kliens osztály.
    Támogatja a keresést, XML feldolgozást és rate limiting-et.
    """
    
    BASE_URL = "https://wsearch.nlm.nih.gov/ws/query"
    
    def __init__(self, language: str = "en", tool_name: str = "medical_chatbot"):
        self.language = language
        self.db = "healthTopics" if language == "en" else "healthTopicsSpanish"
        self.tool_name = tool_name
        self.rate_limiter = MedlineRateLimiter()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': f'Medical Chatbot ({tool_name})',
            'Accept': 'application/xml'
        })
    
    def _normalize_search_term(self, term: str) -> str:
        """
        Keresési kifejezés normalizálása és optimalizálása.
        Magyar diagnózisból angol keresési kifejezést készít.
        """
        # Gyakori magyar-angol fordítások
        translations = {
            'fejfájás': 'headache',
            'torokfájás': 'sore throat',
            'láz': 'fever',
            'köhögés': 'cough',
            'hányás': 'nausea vomiting',
            'hasmenés': 'diarrhea',
            'fáradtság': 'fatigue',
            'szédülés': 'dizziness',
            'hasfájás': 'stomach pain abdominal pain',
            'hányinger': 'nausea',
            'megfázás': 'common cold',
            'influenza': 'flu influenza',
            'allergia': 'allergy',
            'asztma': 'asthma',
            'magas vérnyomás': 'high blood pressure hypertension',
            'cukorbetegség': 'diabetes',
            'gyomorfekély': 'stomach ulcer',
            'migrén': 'migraine',
            'depresszió': 'depression',
            'szorongás': 'anxiety'
        }
        
        # Kis betűssé alakítás és tisztítás
        term = term.lower().strip()
        
        # Felesleges szavak eltávolítása
        stop_words = ['lehetséges', 'valószínű', 'esetleg', 'talán', 'lehet', 'a', 'az', 'egy']
        for stop_word in stop_words:
            term = re.sub(rf'\b{stop_word}\b', '', term)
        
        # Fordítás keresése
        for hungarian, english in translations.items():
            if hungarian in term:
                return english
        
        # Ha nincs fordítás, akkor az eredeti term-et adjuk vissza
        return term.strip()
    
    def _build_search_params(self, term: str, retmax: int = 10, rettype: str = "brief") -> Dict[str, str]:
        """API kérés paramétereinek összeállítása."""
        normalized_term = self._normalize_search_term(term)
        
        params = {
            'db': self.db,
            'term': quote_plus(normalized_term),
            'retmax': str(retmax),
            'rettype': rettype,
            'tool': self.tool_name
        }
        
        return params
    
    def _make_request(self, params: Dict[str, str]) -> Optional[str]:
        """HTTP kérés küldése rate limiting-gel."""
        # Rate limiting ellenőrzés
        if not self.rate_limiter.can_make_request():
            wait_time = self.rate_limiter.wait_time()
            if wait_time > 0:
                time.sleep(wait_time)
        
        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            # Rate limiter frissítése
            self.rate_limiter.add_request()
            
            return response.text
            
        except requests.exceptions.RequestException as e:
            st.error(f"Medline API hiba: {e}")
            return None
    
    def search_health_topics(self, term: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Egészségügyi témák keresése.
        
        Args:
            term (str): Keresési kifejezés (magyar vagy angol)
            max_results (int): Maximális eredmények száma
            
        Returns:
            List[Dict]: Egészségügyi témák listája
        """
        params = self._build_search_params(term, max_results, "brief")
        
        xml_response = self._make_request(params)
        if not xml_response:
            return []
        
        return self._parse_search_results(xml_response)
    
    def get_detailed_topic(self, term: str) -> Optional[Dict[str, Any]]:
        """
        Részletes témainformációk lekérése.
        
        Args:
            term (str): Keresési kifejezés
            
        Returns:
            Dict: Részletes témainformációk
        """
        params = self._build_search_params(term, 1, "topic")
        
        xml_response = self._make_request(params)
        if not xml_response:
            return None
        
        results = self._parse_search_results(xml_response)
        return results[0] if results else None
    
    def _parse_search_results(self, xml_content: str) -> List[Dict[str, Any]]:
        """XML válasz feldolgozása strukturált adatokká."""
        try:
            root = ET.fromstring(xml_content)
            results = []
            
            # Alapinformációk
            search_info = {
                'term': root.find('term').text if root.find('term') is not None else '',
                'count': int(root.find('count').text) if root.find('count') is not None else 0
            }
            
            # Dokumentumok feldolgozása
            for doc in root.findall('.//document'):
                document_data = {
                    'url': doc.get('url', ''),
                    'rank': int(doc.get('rank', 0)),
                    'title': '',
                    'summary': '',
                    'organization': '',
                    'alt_titles': [],
                    'mesh_terms': [],
                    'groups': [],
                    'snippet': ''
                }
                
                # Tartalmi elemek feldolgozása
                for content in doc.findall('content'):
                    content_name = content.get('name', '')
                    content_text = self._clean_xml_content(content.text or '')
                    
                    if content_name == 'title':
                        document_data['title'] = content_text
                    elif content_name == 'organizationName':
                        document_data['organization'] = content_text
                    elif content_name == 'FullSummary':
                        document_data['summary'] = content_text
                    elif content_name == 'altTitle':
                        document_data['alt_titles'].append(content_text)
                    elif content_name == 'mesh':
                        document_data['mesh_terms'].append(content_text)
                    elif content_name == 'groupName':
                        document_data['groups'].append(content_text)
                    elif content_name == 'snippet':
                        document_data['snippet'] = content_text
                
                results.append(document_data)
            
            return results
            
        except ET.ParseError as e:
            st.error(f"XML feldolgozási hiba: {e}")
            return []
        except Exception as e:
            st.error(f"Váratlan hiba a Medline válasz feldolgozása során: {e}")
            return []
    
    def _clean_xml_content(self, content: str) -> str:
        """XML tartalomból HTML tagek eltávolítása."""
        if not content:
            return ''
        
        # HTML tagek eltávolítása
        content = re.sub(r'<[^>]+>', '', content)
        
        # Felesleges szóközök eltávolítása
        content = re.sub(r'\s+', ' ', content).strip()
        
        return content
    
    def search_multiple_terms(self, terms: List[str], max_results_per_term: int = 3) -> Dict[str, List[Dict[str, Any]]]:
        """
        Több kifejezés egyidejű keresése.
        
        Args:
            terms (List[str]): Keresési kifejezések listája
            max_results_per_term (int): Maximális eredmények száma kifejezésenként
            
        Returns:
            Dict: Kifejezések és eredményeik
        """
        results = {}
        
        for term in terms:
            if term.strip():
                topic_results = self.search_health_topics(term, max_results_per_term)
                if topic_results:
                    results[term] = topic_results
        
        return results

# =============================================================================
# Segédfüggvények
# =============================================================================

def create_medline_client(language: str = "en") -> MedlineAPIClient:
    """Medline API kliens gyártófüggvény."""
    return MedlineAPIClient(language=language)

def test_medline_connection() -> bool:
    """Medline API kapcsolat tesztelése."""
    try:
        client = create_medline_client()
        results = client.search_health_topics("headache", 1)
        return len(results) > 0
    except Exception:
        return False