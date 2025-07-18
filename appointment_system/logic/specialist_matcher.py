# =============================================================================
# appointment_system/logic/specialist_matcher.py - JAVÍTOTT VERZIÓ
# =============================================================================
"""
Szakorvos matching logika GPT diagnózis alapján
"""
import re
from typing import List, Dict, Tuple, Optional
import sys
import os

# Lokális importok javítása
try:
    from ..models.doctor import Doctor, DoctorSpecialization
    from ..database.doctors_db import get_doctors_db
except ImportError:
    # Fallback import path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from models.doctor import Doctor, DoctorSpecialization
    from database.doctors_db import get_doctors_db

class SpecialistMatcher:
    """Szakorvos matching algoritmus"""
    
    def __init__(self):
        self.db = get_doctors_db()
        self.specialization_keywords = {
            DoctorSpecialization.INTERNAL_MEDICINE: [
                'belgyógyász', 'internal medicine', 'általános', 'láz', 'fáradtság',
                'általános betegségek', 'krónikus betegségek', 'diabetes', 'vérnyomás'
            ],
            DoctorSpecialization.NEUROLOGY: [
                'neurológus', 'neurology', 'fejfájás', 'migraine', 'szédülés',
                'headache', 'nervous system', 'idegrendszer', 'stroke'
            ],
            DoctorSpecialization.CARDIOLOGY: [
                'kardiológus', 'cardiology', 'szív', 'heart', 'mellkasi fájdalom',
                'chest pain', 'szívritmus', 'vérnyomás', 'kardiovaszkuláris'
            ],
            DoctorSpecialization.DERMATOLOGY: [
                'bőrgyógyász', 'dermatology', 'bőr', 'skin', 'allergia',
                'allergy', 'kiütés', 'rash', 'ekcéma'
            ],
            DoctorSpecialization.GASTROENTEROLOGY: [
                'gasztroenterológus', 'gastroenterology', 'has', 'stomach',
                'emésztés', 'digestion', 'hasfájás', 'hányás', 'hasmenés'
            ],
            DoctorSpecialization.ORTHOPEDICS: [
                'ortopéd', 'orthopedics', 'csont', 'bone', 'ízület', 'joint',
                'fájdalom', 'mozgás', 'gerinc', 'törés'
            ],
            DoctorSpecialization.PSYCHIATRY: [
                'pszichiáter', 'psychiatry', 'depresszió', 'depression',
                'szorongás', 'anxiety', 'mentális', 'mental health'
            ],
            DoctorSpecialization.EMERGENCY: [
                'sürgősségi', 'emergency', 'sürgős', 'urgent', 'azonnal',
                'immediately', 'vészhelyzet', 'akut'
            ]
        }
    
    def match_specialists(self, gpt_specialist_advice: str, 
                         diagnosis: str, 
                         symptoms: List[str]) -> List[Tuple[Doctor, float]]:
        """Szakorvosok matching-je a GPT tanács alapján"""
        matches = []
        
        # Összes szöveg összegyűjtése az elemzéshez
        all_text = f"{gpt_specialist_advice} {diagnosis} {' '.join(symptoms)}".lower()
        
        # Minden orvosra kiszámítjuk a relevancia pontszámot
        for doctor in self.db.get_all_doctors():
            score = self._calculate_relevance_score(doctor, all_text)
            if score > 0:
                matches.append((doctor, score))
        
        # Rendezés relevancia alapján
        matches.sort(key=lambda x: x[1], reverse=True)
        
        return matches[:5]  # Top 5 match
    
    def _calculate_relevance_score(self, doctor: Doctor, text: str) -> float:
        """Relevancia pontszám számítás"""
        score = 0.0
        
        # Alappontszám a szakspecializációs kulcsszavak alapján
        keywords = self.specialization_keywords.get(doctor.specialization, [])
        
        for keyword in keywords:
            if keyword in text:
                score += 10.0
        
        # Bonus pontok
        
        # Orvos neve említve
        if doctor.name.lower() in text or doctor.get_display_name().lower() in text:
            score += 20.0
        
        # Szakspecializáció direct mention
        if doctor.specialization.value in text:
            score += 15.0
        
        # Értékelés alapú bonus
        rating_bonus = (doctor.rating - 4.0) * 5.0  # 4.0 felett 5 pont per 0.1 pont
        score += max(0, rating_bonus)
        
        # Általános orvos esetén minden esetben van valami alap pontszám
        if doctor.specialization == DoctorSpecialization.GENERAL_PRACTITIONER:
            score += 5.0
        
        return min(score, 100.0)  # Max 100 pont
    
    def get_emergency_recommendations(self) -> List[Doctor]:
        """Sürgősségi esetek esetén javasolt orvosok"""
        return self.db.get_doctors_by_specialization(DoctorSpecialization.EMERGENCY)
    
    def get_general_practitioners(self) -> List[Doctor]:
        """Háziorvosok lekérése"""
        return self.db.get_doctors_by_specialization(DoctorSpecialization.GENERAL_PRACTITIONER)
