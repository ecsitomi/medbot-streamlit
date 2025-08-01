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
        # MeSH terms mapping - magyar tünet -> MeSH hierarchy (JAVÍTOTT)
        self.mesh_mapping = {
            'fejfájás': ['Headache', 'Cephalgia', 'Head Pain', 'Migraine Disorders'],
            'láz': ['Fever', 'Hyperthermia', 'Pyrexia'],
            'köhögés': ['Cough', 'Respiratory Sounds', 'Bronchial Diseases'],
            'torokfájás': ['Pharyngitis', 'Throat Diseases', 'Sore Throat'],
            'hányás': ['Vomiting', 'Nausea'],
            'hasmenés': ['Diarrhea', 'Gastrointestinal Diseases'],
            'fáradtság': ['Fatigue', 'Asthenia', 'Muscle Weakness'],
            'szédülés': ['Dizziness', 'Vertigo', 'Balance Disorders'],
            'hasfájás': ['Abdominal Pain', 'Stomach Pain'],
            'légzési nehézség': ['Dyspnea', 'Respiratory Distress'],
            'hányinger': ['Nausea'],
            'étvágytalanság': ['Anorexia', 'Appetite Loss'],
            'gyengeség': ['Muscle Weakness', 'Asthenia'],
            'ízületi fájdalom': ['Arthralgia', 'Joint Pain'],
            'hasi felfúvódás': ['Abdominal Distension', 'Bloating'],
            'bőrkiütés': ['Rash', 'Dermatitis', 'Skin Eruptions'],
            'viszketés': ['Pruritus', 'Itching'],
            'alvászavar': ['Sleep Disorders', 'Insomnia'],
            'koncentrációs problémák': ['Attention Disorders', 'Cognitive Dysfunction']
        }
        
        # Szinonimák és alternatív kifejezések (BŐVÍTETT)
        self.synonyms = {
            'headache': ['cephalgia', 'head pain', 'cranial pain', 'cranialgia'],
            'fever': ['pyrexia', 'hyperthermia', 'elevated temperature', 'febrile'],
            'cough': ['tussis', 'coughing', 'productive cough', 'dry cough', 'persistent cough'],
            'fatigue': ['exhaustion', 'tiredness', 'weakness', 'lethargy', 'asthenia'],
            'nausea': ['queasiness', 'sick feeling', 'stomach upset'],
            'vomiting': ['emesis', 'throwing up', 'retching'],
            'diarrhea': ['loose stools', 'frequent bowel movements', 'gastroenteritis'],
            'abdominal pain': ['stomach pain', 'belly pain', 'gastric pain', 'epigastric pain'],
            'dizziness': ['lightheadedness', 'unsteadiness', 'vertigo'],
            'dyspnea': ['shortness of breath', 'breathing difficulty', 'respiratory distress'],
            'rash': ['skin eruption', 'dermatitis', 'skin lesions'],
            'joint pain': ['arthralgia', 'joint ache', 'joint stiffness']
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
        Optimalizált keresési stratégia - kevesebb, de hatékonyabb query-k
        """
        queries = []
        
        # 1. Elsődleges tünet-alapú keresés (legfontosabb)
        primary_query = self._build_primary_symptom_query(patient_data)
        if primary_query:
            queries.append(SearchQuery(
                primary_query=primary_query,
                mesh_terms=self._get_relevant_mesh_terms(patient_data),
                study_types=[StudyType.SYSTEMATIC_REVIEW, StudyType.META_ANALYSIS],
                date_range=(2020, 2024),  # Csak a legfrissebb
                demographics=self._extract_demographics(patient_data),
                max_results=15
            ))
        
        # 2. Diagnózis-specifikus keresés (ha van diagnózis)
        diagnosis_query = self._build_diagnosis_query(patient_data)
        if diagnosis_query:
            queries.append(SearchQuery(
                primary_query=diagnosis_query,
                mesh_terms=[],
                study_types=[StudyType.RCT, StudyType.CLINICAL_TRIAL],
                date_range=(2018, 2024),
                demographics=self._extract_demographics(patient_data),
                max_results=10
            ))
        
        # 3. Fallback - egyszerű keresés (ha az előzőek nem működnek)
        fallback_query = self._build_simple_fallback_query(patient_data)
        if fallback_query:
            queries.append(SearchQuery(
                primary_query=fallback_query,
                mesh_terms=[],
                study_types=[StudyType.SYSTEMATIC_REVIEW],
                date_range=(2015, 2024),
                demographics={},
                max_results=8
            ))
        
        return queries
    
    def _build_simple_fallback_query(self, patient_data: Dict[str, Any]) -> str:
        """Egyszerű fallback keresés alapvető kulcsszavakkal"""
        symptoms = patient_data.get('symptoms', [])
        if not symptoms:
            return ""
        
        # Csak az első tünet angol fordítása
        primary_symptom = self._translate_symptom(symptoms[0])
        if not primary_symptom:
            return ""
        
        # Egyszerű query: tünet + humans szűrő
        return f"{primary_symptom}[Title/Abstract] AND humans[MeSH]"
    
    def _build_primary_symptom_query(self, patient_data: Dict[str, Any]) -> str:
        """Optimalizált tünet-alapú query építése"""
        symptoms = patient_data.get('symptoms', [])
        if not symptoms:
            return ""
        
        # Csak a 2 legfontosabb tünetet használjuk a túl összetett query elkerülésére
        primary_symptoms = symptoms[:2]
        query_parts = []
        
        for symptom in primary_symptoms:
            symptom_terms = []
            
            # 1. Közvetlen angol fordítás
            eng_symptom = self._translate_symptom(symptom)
            if eng_symptom:
                symptom_terms.append(f'{eng_symptom}[Title/Abstract]')
            
            # 2. MeSH terms (csak a legfontosabbakat)
            mesh_terms = self.mesh_mapping.get(symptom.lower(), [])
            for mesh in mesh_terms[:2]:  # Maximum 2 MeSH term per symptom
                symptom_terms.append(f'{mesh}[MeSH Terms]')
            
            # 3. Egy szinonima hozzáadása
            synonyms = self.synonyms.get(eng_symptom.lower(), [])
            if synonyms:
                symptom_terms.append(f'{synonyms[0]}[Title/Abstract]')
            
            if symptom_terms:
                # OR kapcsolat a szinonimák között (max 4 term per symptom)
                symptom_query = "(" + " OR ".join(symptom_terms[:4]) + ")"
                query_parts.append(symptom_query)
        
        if not query_parts:
            return ""
        
        # AND kapcsolat a tünetek között
        main_query = " AND ".join(query_parts)
        
        # Alapvető szűrők hozzáadása
        base_filters = ['humans[MeSH]']
        
        # Final query összeállítása
        if main_query:
            final_query = f"({main_query}) AND {' AND '.join(base_filters)}"
            # Query hosszának ellenőrzése és levágása ha szükséges
            if len(final_query) > 300:
                # Fallback: csak az első tünet + egy MeSH term
                first_symptom = self._translate_symptom(primary_symptoms[0])
                mesh_term = self.mesh_mapping.get(primary_symptoms[0].lower(), [''])[0]
                if mesh_term:
                    final_query = f"({first_symptom}[Title/Abstract] OR {mesh_term}[MeSH Terms]) AND humans[MeSH]"
                else:
                    final_query = f"{first_symptom}[Title/Abstract] AND humans[MeSH]"
            
            return final_query
        
        return ""
    
    def _build_diagnosis_query(self, patient_data: Dict[str, Any]) -> str:
        """Optimalizált diagnózis-specifikus keresés"""
        diagnosis = patient_data.get('diagnosis', '')
        if not diagnosis or diagnosis == "Nem sikerült diagnózist javasolni.":
            return ""

        clean_diagnosis = self._clean_diagnosis(diagnosis)
        if not clean_diagnosis:
            return ""

        # Egyszerűsített diagnosis query
        diagnosis_parts = [
            f'{clean_diagnosis}[Title/Abstract]',
            f'{clean_diagnosis}[MeSH Terms]'
        ]

        # Ha van treatment context, hozzáadjuk
        if len(clean_diagnosis.split()) <= 3:  # Csak rövid diagnózisoknál
            diagnosis_parts.append(f'({clean_diagnosis}) AND (therapy[MeSH Terms] OR treatment[Title/Abstract])')

        diagnosis_query = "(" + " OR ".join(diagnosis_parts) + ")"
        final_query = f'{diagnosis_query} AND humans[MeSH]'
        
        # Hosszúság ellenőrzése
        if len(final_query) > 200:
            # Fallback: csak alapvető keresés
            final_query = f'{clean_diagnosis}[Title/Abstract] AND humans[MeSH]'
        
        return final_query
    
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
        """Optimalizált PubMed query formázása"""
        base_query = search_query.primary_query
        
        if not base_query:
            return ""
        
        query_parts = [base_query]
        
        # Tanulmány típus szűrők - csak a legfontosabbakat
        if search_query.study_types:
            # Csak 2-3 tanulmány típust használunk
            priority_studies = sorted(
                search_query.study_types, 
                key=lambda x: self.study_priority.get(x, 0), 
                reverse=True
            )[:3]
            
            study_filters = []
            for study_type in priority_studies:
                study_filters.append(f'"{study_type.value}"[Publication Type]')
            
            if study_filters:
                study_query = "(" + " OR ".join(study_filters) + ")"
                query_parts.append(study_query)
        
        # Dátum szűrő - csak ha szükséges
        start_year, end_year = search_query.date_range
        if end_year - start_year <= 10:  # Csak ha nem túl széles az időtartam
            date_filter = f'"{start_year}"[PDAT]:"{end_year}"[PDAT]'
            query_parts.append(date_filter)
        
        final_query = " AND ".join(query_parts)
        
        # Query hosszának szigorú limitálása
        if len(final_query) > 250:
            # Fallback: csak az alapquery + humans szűrő
            final_query = f"{base_query} AND humans[MeSH]"
            
            # Ha még mindig túl hosszú, radikális egyszerűsítés
            if len(final_query) > 150:
                # Kivonunk egy egyszerű kulcsszót az eredeti query-ből
                words = base_query.split()
                if len(words) > 3:
                    simple_term = ' '.join(words[:2])
                    final_query = f"{simple_term} AND humans[MeSH]"
                else:
                    final_query = f"{base_query[:100]} AND humans[MeSH]"
        
        return final_query
    
    # Helper metódusok
    def _translate_symptom(self, symptom: str) -> str:
        """Tünet fordítása angolra - BŐVÍTETT"""
        translations = {
            'fejfájás': 'headache',
            'láz': 'fever', 
            'köhögés': 'cough',
            'torokfájás': 'sore throat',
            'hányás': 'vomiting',
            'hasmenés': 'diarrhea',
            'fáradtság': 'fatigue',
            'szédülés': 'dizziness',
            'hasfájás': 'abdominal pain',
            'hányinger': 'nausea',
            'légzési nehézség': 'dyspnea',
            'nehéz légzés': 'dyspnea',
            'fulladás': 'dyspnea',
            'mellkasi fájdalom': 'chest pain',
            'étvágytalanság': 'anorexia',
            'fogyás': 'weight loss',
            'hízás': 'weight gain',
            'gyengeség': 'weakness',
            'izomfájdalom': 'muscle pain',
            'ízületi fájdalom': 'joint pain',
            'hátfájás': 'back pain',
            'nyakfájás': 'neck pain',
            'bőrkiütés': 'rash',
            'viszketés': 'pruritus',
            'alvászavar': 'sleep disorder',
            'álmatlanság': 'insomnia',
            'nyugtalanság': 'restlessness',
            'idegesség': 'nervousness',
            'koncentrációs problémák': 'concentration problems',
            'memóriaproblémák': 'memory problems',
            'vizeletürítési problémák': 'urination problems',
            'gyakori vizelés': 'frequent urination',
            'szomjúság': 'thirst',
            'szárazság': 'dryness',
            'izzadás': 'sweating',
            'hidegrázás': 'chills',
            'fázékonyság': 'chills',
            'hőhullámok': 'hot flashes',
            'vérzés': 'bleeding',
            'zúzódás': 'bruising',
            'duzzanat': 'swelling',
            'fájdalom': 'pain',
            'égő érzés': 'burning sensation',
            'zsibbadás': 'numbness',
            'bizsergés': 'tingling'
        }
        
        symptom_lower = symptom.lower().strip()
        return translations.get(symptom_lower, symptom_lower)
    
    def _translate_condition(self, condition: str) -> str:
        """Betegség fordítása - BŐVÍTETT"""
        translations = {
            'magas vérnyomás': 'hypertension',
            'cukorbetegség': 'diabetes mellitus',
            'asztma': 'asthma',
            'allergia': 'allergy',
            'szívbetegség': 'heart disease',
            'szívinfarktus': 'myocardial infarction',
            'stroke': 'stroke',
            'rák': 'cancer',
            'tumor': 'tumor',
            'epilepszia': 'epilepsy',
            'migrén': 'migraine',
            'depresszió': 'depression',
            'szorongás': 'anxiety',
            'arthritis': 'arthritis',
            'osteoporosis': 'osteoporosis',
            'hypothyroidism': 'hypothyroidism',
            'hyperthyroidism': 'hyperthyroidism',
            'veseproblémák': 'kidney disease',
            'májproblémák': 'liver disease',
            'tüdőproblémák': 'lung disease',
            'gastritis': 'gastritis',
            'reflux': 'gastroesophageal reflux',
            'colitis': 'colitis',
            'irritábilis bél': 'irritable bowel syndrome',
            'krónikus fájdalom': 'chronic pain',
            'fibromyalgia': 'fibromyalgia',
            'autoimmun betegség': 'autoimmune disease',
            'immunhiány': 'immunodeficiency',
            'obesitas': 'obesity',
            'anorexia': 'anorexia',
            'bulimia': 'bulimia',
            'szkizofrénia': 'schizophrenia',
            'bipoláris zavar': 'bipolar disorder',
            'adhd': 'attention deficit hyperactivity disorder',
            'autizmus': 'autism',
            'alzheimer': 'alzheimer disease',
            'parkinson': 'parkinson disease',
            'multiple sclerosis': 'multiple sclerosis',
            'lupus': 'systemic lupus erythematosus'
        }
        
        condition_lower = condition.lower().strip()
        return translations.get(condition_lower, condition_lower)
    
    def _clean_diagnosis(self, diagnosis: str) -> str:
        """Diagnózis tisztítása és normalizálása"""
        if not diagnosis:
            return ""
        
        # Alapvető tisztítás
        clean_diag = diagnosis.lower().strip()
        
        # Bizonytalan kifejezések eltávolítása
        uncertainty_patterns = [
            r'^(lehetséges|valószínű|esetleg|talán|lehet hogy|feltehető|gyanú)\s+',
            r'\s+(gyanúja|gyanú|valószínű|lehetséges)$',
            r'^\s*(a|az|egy)\s+',
            r'\s+(betegség|szindróma|tünetegyüttes)$'
        ]
        
        for pattern in uncertainty_patterns:
            clean_diag = re.sub(pattern, '', clean_diag)
        
        # Magyar→angol orvosi kifejezések fordítása
        medical_translations = {
            'felső légúti fertőzés': 'upper respiratory infection',
            'vírusos fertőzés': 'viral infection',
            'bakteriális fertőzés': 'bacterial infection',
            'gyomor-bél fertőzés': 'gastroenteritis',
            'influenza': 'influenza',
            'megfázás': 'common cold',
            'tonsillitis': 'tonsillitis',
            'pharyngitis': 'pharyngitis',
            'bronchitis': 'bronchitis',
            'pneumonia': 'pneumonia',
            'sinusitis': 'sinusitis',
            'otitis': 'otitis',
            'conjunctivitis': 'conjunctivitis',
            'dermatitis': 'dermatitis',
            'allergiás reakció': 'allergic reaction',
            'étel allergia': 'food allergy',
            'asztma': 'asthma',
            'migrén': 'migraine',
            'tenziós fejfájás': 'tension headache',
            'gastritis': 'gastritis',
            'reflux': 'gastroesophageal reflux',
            'irritábilis bél szindróma': 'irritable bowel syndrome',
            'húgyúti fertőzés': 'urinary tract infection',
            'cystitis': 'cystitis',
            'veseköves': 'nephrolithiasis kidney stones',
            'magas vérnyomás': 'hypertension',
            'diabetes': 'diabetes mellitus',
            'hypothyroidism': 'hypothyroidism',
            'hyperthyroidism': 'hyperthyroidism',
            'anémia': 'anemia',
            'depresszió': 'depression',
            'szorongás': 'anxiety disorder',
            'fibromyalgia': 'fibromyalgia',
            'arthritis': 'arthritis',
            'osteoarthritis': 'osteoarthritis',
            'rheumatoid arthritis': 'rheumatoid arthritis'
        }
        
        # Keresés a fordítási szótárban
        for hu_term, en_term in medical_translations.items():
            if hu_term in clean_diag:
                return en_term
        
        # Ha nincs közvetlen fordítás, akkor alapvető tisztítás
        clean_diag = re.sub(r'[^\w\s]', ' ', clean_diag)  # Speciális karakterek eltávolítása
        clean_diag = ' '.join(clean_diag.split())  # Többszörös szóközök eltávolítása
        
        return clean_diag if len(clean_diag) > 2 else ""
    
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
    
    def debug_query_generation(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Debug információk a query generálásról"""
        debug_info = {
            'original_data': patient_data,
            'translated_symptoms': {},
            'mesh_terms': {},
            'generated_queries': [],
            'query_lengths': [],
            'recommendations': []
        }
        
        # Tünetek fordítása debug
        symptoms = patient_data.get('symptoms', [])
        for symptom in symptoms:
            translated = self._translate_symptom(symptom)
            debug_info['translated_symptoms'][symptom] = translated
            
            mesh = self.mesh_mapping.get(symptom.lower(), [])
            debug_info['mesh_terms'][symptom] = mesh
        
        # Query generálás debug
        queries = self.build_comprehensive_search_queries(patient_data)
        for i, query in enumerate(queries):
            formatted_query = self.format_final_query(query)
            debug_info['generated_queries'].append({
                'index': i,
                'raw_query': query.primary_query,
                'formatted_query': formatted_query,
                'length': len(formatted_query),
                'study_types': [st.value for st in query.study_types],
                'date_range': query.date_range
            })
            debug_info['query_lengths'].append(len(formatted_query))
        
        # Javaslatok
        if not queries:
            debug_info['recommendations'].append("❌ Nem sikerült query-t generálni!")
        
        avg_length = sum(debug_info['query_lengths']) / len(debug_info['query_lengths']) if debug_info['query_lengths'] else 0
        if avg_length > 200:
            debug_info['recommendations'].append("⚠️ Query-k túl hosszúak, egyszerűsítés szükséges")
        
        if len(queries) > 3:
            debug_info['recommendations'].append("⚠️ Túl sok query, csökkenteni kellene")
        
        return debug_info