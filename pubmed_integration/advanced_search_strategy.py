# =============================================================================
# pubmed_integration/advanced_search_strategy.py
# =============================================================================
"""
Fejlett PubMed keresési stratégia - Pontosabb és szélesebb körű eredményekért
"""
import re
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum
import streamlit as st

class StudyType(Enum):
    META_ANALYSIS = "meta-analysis"
    SYSTEMATIC_REVIEW = "systematic review"
    RCT = "randomized controlled trial"
    CLINICAL_TRIAL = "clinical trial"
    COHORT_STUDY = "cohort study"
    CASE_CONTROL = "case-control study"
    CASE_SERIES = "case series"
    CASE_REPORT = "case report"

@dataclass
class SearchQuery:
    primary_query: str
    mesh_terms: List[str]
    study_types: List[StudyType]
    date_range: Tuple[int, int]  # (start_year, end_year)
    demographics: Dict[str, Any]
    max_results: int = 50

class AdvancedPubMedSearchStrategy:
    """
    Fejlett PubMed keresési stratégia orvosi kutatásokhoz
    """
    
    def __init__(self):
        # MeSH terms mapping - magyar tünet -> MeSH hierarchy
        self.mesh_mapping = {
            'fejfájás': ['Headache', 'Migraine Disorders', 'Tension-Type Headache', 'Cluster Headache'],
            'láz': ['Fever', 'Hyperthermia', 'Body Temperature Changes'],
            'köhögés': ['Cough', 'Respiratory Tract Diseases', 'Bronchitis'],
            'torokfájás': ['Pharyngitis', 'Sore Throat', 'Throat Diseases'],
            'hányás': ['Vomiting', 'Nausea', 'Gastrointestinal Diseases'],
            'hasmenés': ['Diarrhea', 'Gastrointestinal Diseases', 'Intestinal Diseases'],
            'fáradtság': ['Fatigue', 'Asthenia', 'Chronic Fatigue Syndrome'],
            'szédülés': ['Dizziness', 'Vertigo', 'Vestibular Diseases'],
            'hasfájás': ['Abdominal Pain', 'Gastrointestinal Diseases'],
            'légzési nehézség': ['Dyspnea', 'Respiratory Insufficiency', 'Lung Diseases']
        }
        
        # Szinonimák és alternatív kifejezések
        self.synonyms = {
            'headache': ['cephalgia', 'head pain', 'cranial pain'],
            'fever': ['pyrexia', 'hyperthermia', 'elevated temperature'],
            'cough': ['tussis', 'expectoration', 'productive cough', 'dry cough'],
            'fatigue': ['exhaustion', 'tiredness', 'weakness', 'lethargy']
        }
        
        # Demográfiai szűrők
        self.age_filters = {
            'infant': 'infant[MeSH] OR newborn[MeSH]',
            'child': 'child[MeSH] OR pediatric[Title/Abstract]',
            'adolescent': 'adolescent[MeSH] OR teenage*[Title/Abstract]',
            'adult': 'adult[MeSH]',
            'elderly': 'aged[MeSH] OR elderly[Title/Abstract] OR geriatric[Title/Abstract]'
        }
        
        # Tanulmány típus prioritás (magasabb = fontosabb)
        self.study_priority = {
            StudyType.META_ANALYSIS: 10,
            StudyType.SYSTEMATIC_REVIEW: 9,
            StudyType.RCT: 8,
            StudyType.CLINICAL_TRIAL: 7,
            StudyType.COHORT_STUDY: 6,
            StudyType.CASE_CONTROL: 5,
            StudyType.CASE_SERIES: 3,
            StudyType.CASE_REPORT: 2
        }
    
    def build_comprehensive_search_queries(self, patient_data: Dict[str, Any]) -> List[SearchQuery]:
        """
        Komplex keresési stratégia építése több query-vel
        
        Stratégia:
        1. Fő tünetek + MeSH terms (széles keresés)
        2. Diagnózis-specifikus keresés  
        3. Demográfia-specifikus keresés
        4. Komorbiditás keresés
        5. Kezelés-specifikus keresés
        """
        queries = []
        
        # 1. Fő tünetek alapú keresés (széles)
        primary_query = self._build_primary_symptom_query(patient_data)
        if primary_query:
            queries.append(SearchQuery(
                primary_query=primary_query,
                mesh_terms=self._get_relevant_mesh_terms(patient_data),
                study_types=[StudyType.META_ANALYSIS, StudyType.SYSTEMATIC_REVIEW, StudyType.RCT],
                date_range=(2019, 2024),  # Utolsó 5 év
                demographics=self._extract_demographics(patient_data),
                max_results=20
            ))
        
        # 2. Diagnózis-specifikus keresés
        diagnosis_query = self._build_diagnosis_query(patient_data)
        if diagnosis_query:
            queries.append(SearchQuery(
                primary_query=diagnosis_query,
                mesh_terms=[],
                study_types=[StudyType.SYSTEMATIC_REVIEW, StudyType.RCT, StudyType.CLINICAL_TRIAL],
                date_range=(2015, 2024),  # Utolsó 9 év
                demographics=self._extract_demographics(patient_data),
                max_results=15
            ))
        
        # 3. Demográfia-specifikus keresés
        demo_query = self._build_demographic_query(patient_data)
        if demo_query:
            queries.append(SearchQuery(
                primary_query=demo_query,
                mesh_terms=self._get_relevant_mesh_terms(patient_data),
                study_types=[StudyType.COHORT_STUDY, StudyType.CASE_CONTROL],
                date_range=(2010, 2024),  # Szélesebb időtartam
                demographics=self._extract_demographics(patient_data),
                max_results=10
            ))
        
        # 4. Komorbiditás és gyógyszer interakció keresés
        comorbidity_query = self._build_comorbidity_query(patient_data)
        if comorbidity_query:
            queries.append(SearchQuery(
                primary_query=comorbidity_query,
                mesh_terms=[],
                study_types=[StudyType.SYSTEMATIC_REVIEW, StudyType.META_ANALYSIS],
                date_range=(2015, 2024),
                demographics={},
                max_results=10
            ))
        
        # 5. Kezelési protokoll keresés
        treatment_query = self._build_treatment_protocol_query(patient_data)
        if treatment_query:
            queries.append(SearchQuery(
                primary_query=treatment_query,
                mesh_terms=[],
                study_types=[StudyType.RCT, StudyType.CLINICAL_TRIAL],
                date_range=(2018, 2024),
                demographics=self._extract_demographics(patient_data),
                max_results=15
            ))
        
        return queries
    
    def _build_primary_symptom_query(self, patient_data: Dict[str, Any]) -> str:
        """Fő tünetek alapú query építése MeSH terms-el"""
        symptoms = patient_data.get('symptoms', [])
        if not symptoms:
            return ""
        
        query_parts = []
        
        # Minden tünetre MeSH + szinonimák
        for symptom in symptoms[:4]:  # Max 4 tünet
            symptom_terms = []
            
            # MeSH terms
            mesh_terms = self.mesh_mapping.get(symptom.lower(), [])
            for mesh in mesh_terms:
                symptom_terms.append(f'"{mesh}"[MeSH]')
            
            # Szinonimák
            eng_symptom = self._translate_symptom(symptom)
            synonyms = self.synonyms.get(eng_symptom.lower(), [])
            for synonym in synonyms:
                symptom_terms.append(f'"{synonym}"[Title/Abstract]')
            
            # Alapvető angol kifejezés
            symptom_terms.append(f'"{eng_symptom}"[Title/Abstract]')
            
            if symptom_terms:
                # OR kapcsolat a szinonimák között
                symptom_query = "(" + " OR ".join(symptom_terms) + ")"
                query_parts.append(symptom_query)
        
        # AND kapcsolat a tünetek között
        main_query = " AND ".join(query_parts) if query_parts else ""
        
        # Minőség szűrők hozzáadása
        quality_filters = [
            'humans[MeSH]',  # Csak humán tanulmányok
            'english[Language]'  # Csak angol nyelű publikációk
        ]
        
        if main_query:
            return f"({main_query}) AND " + " AND ".join(quality_filters)
        
        return ""
    
    def _build_diagnosis_query(self, patient_data: Dict[str, Any]) -> str:
        """Diagnózis-specifikus keresés"""
        diagnosis = patient_data.get('diagnosis', '')
        if not diagnosis or diagnosis == "Nem sikerült diagnózist javasolni.":
            return ""
        
        # Diagnózis tisztítása és angol fordítása
        clean_diagnosis = self._clean_diagnosis(diagnosis)
        
        # Diagnózis alapú keresés több szempontból
        diagnosis_parts = [
            f'"{clean_diagnosis}"[Title/Abstract]',
            f'"{clean_diagnosis}"[MeSH]',
            f'"{clean_diagnosis}" AND therapy[MeSH]',
            f'"{clean_diagnosis}" AND treatment[Title/Abstract]'
        ]
        
        diagnosis_query = "(" + " OR ".join(diagnosis_parts) + ")"
        
        # Minőségi szű
        return f'{diagnosis_query} AND humans[MeSH] AND english[Language]'
    
    def _build_demographic_query(self, patient_data: Dict[str, Any]) -> str:
        """Demográfia-specifikus keresés"""
        age = patient_data.get('age')
        gender = patient_data.get('gender')
        symptoms = patient_data.get('symptoms', [])
        
        if not age or not symptoms:
            return ""
        
        # Életkor kategória meghatározása
        age_category = self._get_age_category(age)
        age_filter = self.age_filters.get(age_category, '')
        
        # Gender szűrő
        gender_filter = ""
        if gender:
            if gender.lower() == 'nő':
                gender_filter = 'female[MeSH]'
            elif gender.lower() == 'férfi':
                gender_filter = 'male[MeSH]'
        
        # Fő tünetek
        main_symptoms = symptoms[:2]  # Csak 2 fő tünet
        symptom_terms = []
        for symptom in main_symptoms:
            eng_symptom = self._translate_symptom(symptom)
            symptom_terms.append(f'"{eng_symptom}"[Title/Abstract]')
        
        symptom_query = " AND ".join(symptom_terms)
        
        # Query összeállítás
        query_parts = []
        if symptom_query:
            query_parts.append(f"({symptom_query})")
        if age_filter:
            query_parts.append(age_filter)
        if gender_filter:
            query_parts.append(gender_filter)
        
        query_parts.extend(['humans[MeSH]', 'english[Language]'])
        
        return " AND ".join(query_parts) if query_parts else ""
    
    def _build_comorbidity_query(self, patient_data: Dict[str, Any]) -> str:
        """Komorbiditás és gyógyszer interakció keresés"""
        existing_conditions = patient_data.get('existing_conditions', [])
        medications = patient_data.get('medications', [])
        symptoms = patient_data.get('symptoms', [])[:2]  # Max 2 tünet
        
        if not existing_conditions and not medications:
            return ""
        
        query_parts = []
        
        # Komorbiditások
        if existing_conditions and existing_conditions != ['nincs']:
            conditions = [self._translate_condition(cond) for cond in existing_conditions]
            condition_terms = [f'"{cond}"[MeSH] OR "{cond}"[Title/Abstract]' for cond in conditions]
            if condition_terms:
                query_parts.append("(" + " OR ".join(condition_terms) + ")")
        
        # Gyógyszerek
        if medications and medications != ['nincs']:
            med_terms = [f'"{med}"[Substance Name] OR "{med}"[Title/Abstract]' 
                        for med in medications]
            if med_terms:
                query_parts.append("(" + " OR ".join(med_terms) + ")")
        
        # Tünetek hozzáadása kontextushoz
        if symptoms and query_parts:
            symptom_terms = [f'"{self._translate_symptom(s)}"[Title/Abstract]' for s in symptoms]
            if symptom_terms:
                query_parts.append("(" + " OR ".join(symptom_terms) + ")")
        
        if query_parts:
            main_query = " AND ".join(query_parts)
            return f"({main_query}) AND humans[MeSH] AND english[Language]"
        
        return ""
    
    def _build_treatment_protocol_query(self, patient_data: Dict[str, Any]) -> str:
        """Kezelési protokoll és guideline keresés"""
        diagnosis = patient_data.get('diagnosis', '')
        symptoms = patient_data.get('symptoms', [])
        
        if not diagnosis and not symptoms:
            return ""
        
        # Kezelési kifejezések
        treatment_terms = [
            'therapy[MeSH]',
            'treatment[Title/Abstract]',
            'management[Title/Abstract]',
            'guidelines[Title/Abstract]',
            'protocol[Title/Abstract]',
            'clinical practice[Title/Abstract]'
        ]
        
        query_parts = []
        
        # Diagnózis alapú kezelés
        if diagnosis and diagnosis != "Nem sikerült diagnózist javasolni.":
            clean_diagnosis = self._clean_diagnosis(diagnosis)
            diagnosis_treatment = f'"{clean_diagnosis}" AND (' + " OR ".join(treatment_terms) + ')'
            query_parts.append(f"({diagnosis_treatment})")
        
        # Tünet alapú kezelés
        if symptoms:
            main_symptoms = symptoms[:2]
            for symptom in main_symptoms:
                eng_symptom = self._translate_symptom(symptom)
                symptom_treatment = f'"{eng_symptom}" AND (' + " OR ".join(treatment_terms) + ')'
                query_parts.append(f"({symptom_treatment})")
        
        if query_parts:
            main_query = " OR ".join(query_parts)
            return f"({main_query}) AND humans[MeSH] AND english[Language]"
        
        return ""
    
    def format_final_query(self, search_query: SearchQuery) -> str:
        """Végleges PubMed query formázása"""
        query_parts = [search_query.primary_query]
        
        # Tanulmány típus szűrők
        if search_query.study_types:
            study_filters = []
            for study_type in search_query.study_types:
                study_filters.append(f'"{study_type.value}"[Publication Type]')
            
            if study_filters:
                query_parts.append("(" + " OR ".join(study_filters) + ")")
        
        # Dátum szűrő
        start_year, end_year = search_query.date_range
        date_filter = f'"{start_year}"[Date - Publication] : "{end_year}"[Date - Publication]'
        query_parts.append(date_filter)
        
        final_query = " AND ".join(query_parts)
        
        # Query hosszának limitálása (PubMed API limit)
        if len(final_query) > 400:
            final_query = final_query[:400]
        
        return final_query
    
    # Helper metódusok
    def _translate_symptom(self, symptom: str) -> str:
        """Tünet fordítása angolra - egyszerűsített"""
        translations = {
            'fejfájás': 'headache',
            'láz': 'fever', 
            'köhögés': 'cough',
            'torokfájás': 'sore throat',
            'hányás': 'vomiting',
            'hasmenés': 'diarrhea',
            'fáradtság': 'fatigue',
            'szédülés': 'dizziness',
            'hasfájás': 'abdominal pain'
        }
        return translations.get(symptom.lower(), symptom)
    
    def _translate_condition(self, condition: str) -> str:
        """Betegség fordítása"""
        translations = {
            'magas vérnyomás': 'hypertension',
            'cukorbetegség': 'diabetes',
            'asztma': 'asthma',
            'allergia': 'allergy'
        }
        return translations.get(condition.lower(), condition)
    
    def _clean_diagnosis(self, diagnosis: str) -> str:
        """Diagnózis tisztítása"""
        # Remove common prefixes
        diagnosis = re.sub(r'^(lehetséges|valószínű|esetleg)\s+', '', diagnosis.lower())
        return diagnosis.strip()
    
    def _get_age_category(self, age: int) -> str:
        """Életkor kategória meghatározása"""
        if age < 2:
            return 'infant'
        elif age < 18:
            return 'child'
        elif age < 25:
            return 'adolescent'
        elif age < 65:
            return 'adult'
        else:
            return 'elderly'
    
    def _extract_demographics(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Demográfiai adatok kinyerése"""
        return {
            'age': patient_data.get('age'),
            'gender': patient_data.get('gender'),
            'age_category': self._get_age_category(patient_data.get('age', 30))
        }
    
    def _get_relevant_mesh_terms(self, patient_data: Dict[str, Any]) -> List[str]:
        """Releváns MeSH terms gyűjtése"""
        symptoms = patient_data.get('symptoms', [])
        all_mesh = []
        
        for symptom in symptoms:
            mesh_terms = self.mesh_mapping.get(symptom.lower(), [])
            all_mesh.extend(mesh_terms)
        
        return list(set(all_mesh))  # Duplikátumok eltávolítása