# =============================================================================
# medline_integration/data_processor.py
# =============================================================================
"""
Medline adatok feldolgozása és strukturálása a medical chatbot számára.
"""
import re
from typing import Dict, List, Optional, Any, Tuple
import streamlit as st
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class MedlineTopicSummary:
    """Medline téma összefoglalója."""
    title: str
    url: str
    summary: str
    organization: str
    relevance_score: float
    snippet: str
    alt_titles: List[str]
    mesh_terms: List[str]
    groups: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Dictionary konverzió exporthoz."""
        return {
            'title': self.title,
            'url': self.url,
            'summary': self.summary[:500] + '...' if len(self.summary) > 500 else self.summary,
            'organization': self.organization,
            'relevance_score': self.relevance_score,
            'snippet': self.snippet,
            'alt_titles': self.alt_titles,
            'mesh_terms': self.mesh_terms,
            'groups': self.groups
        }

class MedlineDataProcessor:
    """
    Medline API válaszok feldolgozása és relevancia értékelése.
    """
    
    def __init__(self):
        self.symptom_keywords = {
            'headache': ['fejfájás', 'head pain', 'cephalgia', 'migraine'],
            'fever': ['láz', 'pyrexia', 'hyperthermia', 'high temperature'],
            'cough': ['köhögés', 'productive cough', 'dry cough'],
            'nausea': ['hányinger', 'nausea', 'vomiting', 'emesis'],
            'fatigue': ['fáradtság', 'tiredness', 'exhaustion', 'weakness'],
            'pain': ['fájdalom', 'ache', 'discomfort', 'soreness']
        }
    
    def process_search_results(self, search_results: List[Dict[str, Any]], 
                             patient_symptoms: List[str],
                             diagnosis: str) -> List[MedlineTopicSummary]:
        """
        Keresési eredmények feldolgozása és relevancia szerinti rendezése.
        
        Args:
            search_results (List[Dict]): Medline API válaszok
            patient_symptoms (List[str]): Páciens tünetei
            diagnosis (str): Diagnózis
            
        Returns:
            List[MedlineTopicSummary]: Feldolgozott és rangsorolt témák
        """
        processed_topics = []
        
        for result in search_results:
            # Relevancia számítása
            relevance_score = self._calculate_relevance_score(
                result, patient_symptoms, diagnosis
            )
            
            # MedlineTopicSummary létrehozása
            topic_summary = MedlineTopicSummary(
                title=result.get('title', ''),
                url=result.get('url', ''),
                summary=result.get('summary', ''),
                organization=result.get('organization', ''),
                relevance_score=relevance_score,
                snippet=result.get('snippet', ''),
                alt_titles=result.get('alt_titles', []),
                mesh_terms=result.get('mesh_terms', []),
                groups=result.get('groups', [])
            )
            
            processed_topics.append(topic_summary)
        
        # Relevancia szerint rendezés
        processed_topics.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return processed_topics
    
    def _calculate_relevance_score(self, result: Dict[str, Any], 
                                 patient_symptoms: List[str],
                                 diagnosis: str) -> float:
        """
        Relevancia pontszám számítása.
        
        Figyelembe veszi:
        - Tünet egyezések
        - Diagnózis egyezések
        - Medline rank
        - Szöveg relevanciája
        """
        score = 0.0
        
        # Alappontszám (Medline rank alapján)
        medline_rank = result.get('rank', 0)
        base_score = max(0, 10 - medline_rank)  # 0-10 skála
        score += base_score
        
        # Tünet egyezések
        symptom_matches = self._count_symptom_matches(result, patient_symptoms)
        score += symptom_matches * 5
        
        # Diagnózis egyezések
        diagnosis_matches = self._count_diagnosis_matches(result, diagnosis)
        score += diagnosis_matches * 3
        
        # Cím relevancia
        title_relevance = self._calculate_title_relevance(result, patient_symptoms, diagnosis)
        score += title_relevance * 2
        
        # Összefoglaló relevancia
        summary_relevance = self._calculate_summary_relevance(result, patient_symptoms, diagnosis)
        score += summary_relevance
        
        return min(score, 100.0)  # Max 100 pont
    
    def _count_symptom_matches(self, result: Dict[str, Any], symptoms: List[str]) -> int:
        """Tünet egyezések számlálása."""
        matches = 0
        text_content = (
            result.get('title', '') + ' ' + 
            result.get('summary', '') + ' ' + 
            result.get('snippet', '')
        ).lower()
        
        for symptom in symptoms:
            if symptom.lower() in text_content:
                matches += 1
            
            # Szinonimák keresése
            for keyword_group in self.symptom_keywords.values():
                if symptom.lower() in keyword_group:
                    for synonym in keyword_group:
                        if synonym.lower() in text_content:
                            matches += 0.5
                            break
        
        return int(matches)
    
    def _count_diagnosis_matches(self, result: Dict[str, Any], diagnosis: str) -> int:
        """Diagnózis egyezések számlálása."""
        if not diagnosis:
            return 0
        
        text_content = (
            result.get('title', '') + ' ' + 
            result.get('summary', '') + ' ' + 
            ' '.join(result.get('mesh_terms', []))
        ).lower()
        
        diagnosis_words = diagnosis.lower().split()
        matches = 0
        
        for word in diagnosis_words:
            if len(word) > 3 and word in text_content:  # Csak hosszabb szavak
                matches += 1
        
        return matches
    
    def _calculate_title_relevance(self, result: Dict[str, Any], 
                                 symptoms: List[str], diagnosis: str) -> float:
        """Cím relevanciájának számítása."""
        title = result.get('title', '').lower()
        if not title:
            return 0.0
        
        relevance = 0.0
        
        # Tünet említések a címben
        for symptom in symptoms:
            if symptom.lower() in title:
                relevance += 2.0
        
        # Diagnózis említés a címben
        if diagnosis:
            diagnosis_words = diagnosis.lower().split()
            for word in diagnosis_words:
                if len(word) > 3 and word in title:
                    relevance += 1.5
        
        return relevance
    
    def _calculate_summary_relevance(self, result: Dict[str, Any], 
                                   symptoms: List[str], diagnosis: str) -> float:
        """Összefoglaló relevanciájának számítása."""
        summary = result.get('summary', '').lower()
        if not summary:
            return 0.0
        
        relevance = 0.0
        
        # Tünet említések az összefoglalóban
        for symptom in symptoms:
            if symptom.lower() in summary:
                relevance += 1.0
        
        # Diagnózis említés az összefoglalóban
        if diagnosis:
            diagnosis_words = diagnosis.lower().split()
            for word in diagnosis_words:
                if len(word) > 3 and word in summary:
                    relevance += 0.5
        
        return relevance
    
    def filter_by_relevance_threshold(self, topics: List[MedlineTopicSummary], 
                                    threshold: float = 5.0) -> List[MedlineTopicSummary]:
        """Relevancia küszöb alapján szűrés."""
        return [topic for topic in topics if topic.relevance_score >= threshold]
    
    def group_by_categories(self, topics: List[MedlineTopicSummary]) -> Dict[str, List[MedlineTopicSummary]]:
        """Témák csoportosítása kategóriák szerint."""
        categories = {}
        
        for topic in topics:
            if topic.groups:
                for group in topic.groups:
                    if group not in categories:
                        categories[group] = []
                    categories[group].append(topic)
            else:
                if 'Egyéb' not in categories:
                    categories['Egyéb'] = []
                categories['Egyéb'].append(topic)
        
        return categories
    
    def extract_key_information(self, topic: MedlineTopicSummary) -> Dict[str, Any]:
        """
        Téma kulcsinformációinak kigyűjtése.
        
        Returns:
            Dict: Kulcsinformációk (tünetek, kezelések, okok, stb.)
        """
        summary = (topic.summary or '').lower()
        
        key_info = {
            'symptoms': self._extract_symptoms(summary),
            'causes': self._extract_causes(summary),
            'treatments': self._extract_treatments(summary),
            'prevention': self._extract_prevention(summary),
            'when_to_see_doctor': self._extract_when_to_see_doctor(summary)
        }
        
        return key_info
    
    def _extract_symptoms(self, text: str) -> List[str]:
        """Tünetek kigyűjtése a szövegből."""
        if not text:
            return []
            
        symptom_patterns = [
            r'symptoms?(?:\s+include)?:?\s*([^.]+)',
            r'signs?(?:\s+include)?:?\s*([^.]+)',
            r'may\s+(?:experience|have|feel):?\s*([^.]+)'
        ]
        
        symptoms = []
        for pattern in symptom_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if match and isinstance(match, str):
                    symptom_list = [s.strip() for s in match.split(',')]
                    symptoms.extend(symptom_list)
        
        return symptoms[:5]  # Max 5 tünet
    
    def _extract_causes(self, text: str) -> List[str]:
        """Okok kigyűjtése a szövegből."""
        if not text:
            return []
            
        cause_patterns = [
            r'caused?\s+by:?\s*([^.]+)',
            r'reasons?\s+(?:include)?:?\s*([^.]+)',
            r'due\s+to:?\s*([^.]+)'
        ]
        
        causes = []
        for pattern in cause_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if match and isinstance(match, str):
                    cause_list = [c.strip() for c in match.split(',')]
                    causes.extend(cause_list)
        
        return causes[:3]  # Max 3 ok
    
    def _extract_treatments(self, text: str) -> List[str]:
        """Kezelések kigyűjtése a szövegből."""
        if not text:
            return []
            
        treatment_patterns = [
            r'treatment(?:s)?:?\s*([^.]+)',
            r'therapy:?\s*([^.]+)',
            r'medications?:?\s*([^.]+)'
        ]
        
        treatments = []
        for pattern in treatment_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if match and isinstance(match, str):
                    treatment_list = [t.strip() for t in match.split(',')]
                    treatments.extend(treatment_list)
        
        return treatments[:4]  # Max 4 kezelés
    
    def _extract_prevention(self, text: str) -> List[str]:
        """Megelőzés kigyűjtése a szövegből."""
        if not text:
            return []
            
        prevention_patterns = [
            r'prevent(?:ion)?:?\s*([^.]+)',
            r'avoid:?\s*([^.]+)',
            r'prevention(?:\s+include)?:?\s*([^.]+)'
        ]
        
        prevention = []
        for pattern in prevention_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if match and isinstance(match, str):
                    prevention_list = [p.strip() for p in match.split(',')]
                    prevention.extend(prevention_list)
        
        return prevention[:3]  # Max 3 megelőzés
    
    def _extract_when_to_see_doctor(self, text: str) -> List[str]:
        """Mikor kell orvoshoz fordulni információk."""
        if not text:
            return []
            
        doctor_patterns = [
            r'see\s+(?:a\s+)?doctor:?\s*([^.]+)',
            r'seek\s+medical\s+(?:help|attention):?\s*([^.]+)',
            r'call\s+(?:a\s+)?doctor:?\s*([^.]+)'
        ]
        
        doctor_advice = []
        for pattern in doctor_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if match and isinstance(match, str):
                    advice_list = [a.strip() for a in match.split(',')]
                    doctor_advice.extend(advice_list)
        
        return doctor_advice[:2]  # Max 2 tanács

# =============================================================================
# Cache és optimalizálás
# =============================================================================

class MedlineCache:
    """
    Medline keresési eredmények cache-elése.
    Csökkenti az API hívások számát.
    """
    
    def __init__(self, cache_duration_hours: int = 24):
        self.cache_duration = timedelta(hours=cache_duration_hours)
        self.cache = {}
    
    def get(self, search_term: str) -> Optional[List[Dict[str, Any]]]:
        """Cache-ből adatok lekérése."""
        if search_term in self.cache:
            cached_data, timestamp = self.cache[search_term]
            if datetime.now() - timestamp < self.cache_duration:
                return cached_data
            else:
                del self.cache[search_term]
        return None
    
    def set(self, search_term: str, data: List[Dict[str, Any]]):
        """Adatok cache-be mentése."""
        self.cache[search_term] = (data, datetime.now())
    
    def clear(self):
        """Cache törlése."""
        self.cache.clear()

# Globális cache példány
medline_cache = MedlineCache()