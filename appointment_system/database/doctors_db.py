# =============================================================================
# appointment_system/database/doctors_db.py
# =============================================================================
"""
Orvosok adatbázis kezelése
"""
import streamlit as st
from typing import List, Optional, Dict, Any
from datetime import time
from ..models.doctor import Doctor, DoctorSpecialization, WorkingHours

class DoctorsDatabase:
    """Orvosok adatbázis kezelő"""
    
    def __init__(self):
        self.doctors: Dict[str, Doctor] = {}
        self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        """Minta orvosok létrehozása"""
        sample_doctors = [
            Doctor(
                id="doc_001",
                name="Kovács János",
                specialization=DoctorSpecialization.INTERNAL_MEDICINE,
                location="Budapest",
                address="1052 Budapest, Petőfi Sándor u. 12.",
                phone="+36 1 234 5678",
                email="kovacs.janos@medcenter.hu",
                working_hours=[
                    WorkingHours("monday", time(8, 0), time(16, 0), time(12, 0), time(13, 0)),
                    WorkingHours("tuesday", time(8, 0), time(16, 0), time(12, 0), time(13, 0)),
                    WorkingHours("wednesday", time(8, 0), time(16, 0), time(12, 0), time(13, 0)),
                    WorkingHours("thursday", time(8, 0), time(16, 0), time(12, 0), time(13, 0)),
                    WorkingHours("friday", time(8, 0), time(14, 0)),
                ],
                rating=4.8,
                description="Tapasztalt belgyógyász, 15 éves szakmai gyakorlattal. Szívbetegségek és diabetes specialista."
            ),
            Doctor(
                id="doc_002",
                name="Nagy Éva",
                specialization=DoctorSpecialization.NEUROLOGY,
                location="Budapest",
                address="1051 Budapest, Arany János u. 8.",
                phone="+36 1 345 6789",
                email="nagy.eva@neurocenter.hu",
                working_hours=[
                    WorkingHours("monday", time(9, 0), time(17, 0), time(13, 0), time(14, 0)),
                    WorkingHours("tuesday", time(9, 0), time(17, 0), time(13, 0), time(14, 0)),
                    WorkingHours("wednesday", time(9, 0), time(17, 0), time(13, 0), time(14, 0)),
                    WorkingHours("thursday", time(9, 0), time(17, 0), time(13, 0), time(14, 0)),
                ],
                rating=4.9,
                description="Neurológus specialista, fejfájás és migrén kezelésben jártas."
            ),
            Doctor(
                id="doc_003",
                name="Szabó Péter",
                specialization=DoctorSpecialization.CARDIOLOGY,
                location="Budapest",
                address="1065 Budapest, Bajcsy-Zsilinszky út 25.",
                phone="+36 1 456 7890",
                email="szabo.peter@cardio.hu",
                working_hours=[
                    WorkingHours("monday", time(8, 0), time(16, 0)),
                    WorkingHours("tuesday", time(8, 0), time(16, 0)),
                    WorkingHours("wednesday", time(8, 0), time(16, 0)),
                    WorkingHours("thursday", time(8, 0), time(16, 0)),
                    WorkingHours("friday", time(8, 0), time(12, 0)),
                ],
                rating=4.7,
                description="Kardiológus, szívritmus zavarok és magas vérnyomás kezelésében specialista."
            ),
            Doctor(
                id="doc_004",
                name="Takács Anna",
                specialization=DoctorSpecialization.DERMATOLOGY,
                location="Budapest",
                address="1064 Budapest, Váci út 45.",
                phone="+36 1 567 8901",
                email="takacs.anna@derma.hu",
                working_hours=[
                    WorkingHours("tuesday", time(10, 0), time(18, 0), time(14, 0), time(15, 0)),
                    WorkingHours("wednesday", time(10, 0), time(18, 0), time(14, 0), time(15, 0)),
                    WorkingHours("thursday", time(10, 0), time(18, 0), time(14, 0), time(15, 0)),
                    WorkingHours("friday", time(10, 0), time(16, 0)),
                ],
                rating=4.6,
                description="Bőrgyógyász, allergiák és bőrbetegségek kezelésében jártas."
            ),
            Doctor(
                id="doc_005",
                name="Horváth Zoltán",
                specialization=DoctorSpecialization.GENERAL_PRACTITIONER,
                location="Budapest",
                address="1053 Budapest, Kecskeméti u. 14.",
                phone="+36 1 678 9012",
                email="horvath.zoltan@haziorvos.hu",
                working_hours=[
                    WorkingHours("monday", time(7, 0), time(15, 0), time(11, 0), time(12, 0)),
                    WorkingHours("tuesday", time(7, 0), time(15, 0), time(11, 0), time(12, 0)),
                    WorkingHours("wednesday", time(7, 0), time(15, 0), time(11, 0), time(12, 0)),
                    WorkingHours("thursday", time(7, 0), time(15, 0), time(11, 0), time(12, 0)),
                    WorkingHours("friday", time(7, 0), time(13, 0)),
                ],
                rating=4.5,
                description="Háziorvos, általános orvosi problémák kezelésében tapasztalt."
            )
        ]
        
        for doctor in sample_doctors:
            self.doctors[doctor.id] = doctor
    
    def get_all_doctors(self) -> List[Doctor]:
        """Összes orvos lekérése"""
        return list(self.doctors.values())
    
    def get_doctor_by_id(self, doctor_id: str) -> Optional[Doctor]:
        """Orvos lekérése ID alapján"""
        return self.doctors.get(doctor_id)
    
    def get_doctors_by_specialization(self, specialization: DoctorSpecialization) -> List[Doctor]:
        """Orvosok lekérése szakspecializáció alapján"""
        return [doc for doc in self.doctors.values() if doc.specialization == specialization]
    
    def search_doctors(self, query: str) -> List[Doctor]:
        """Orvosok keresése név vagy szakma alapján"""
        query = query.lower()
        results = []
        
        for doctor in self.doctors.values():
            if (query in doctor.name.lower() or 
                query in doctor.specialization.value.lower() or
                query in doctor.location.lower()):
                results.append(doctor)
        
        return results
    
    def get_doctors_by_rating(self, min_rating: float = 4.0) -> List[Doctor]:
        """Orvosok lekérése értékelés alapján"""
        return [doc for doc in self.doctors.values() if doc.rating >= min_rating]
    
    def add_doctor(self, doctor: Doctor) -> bool:
        """Új orvos hozzáadása"""
        if doctor.id in self.doctors:
            return False
        self.doctors[doctor.id] = doctor
        return True
    
    def update_doctor(self, doctor: Doctor) -> bool:
        """Orvos adatainak frissítése"""
        if doctor.id not in self.doctors:
            return False
        self.doctors[doctor.id] = doctor
        return True
    
    def delete_doctor(self, doctor_id: str) -> bool:
        """Orvos törlése"""
        if doctor_id not in self.doctors:
            return False
        del self.doctors[doctor_id]
        return True

# Globális adatbázis példány
_doctors_db = None

def get_doctors_db() -> DoctorsDatabase:
    """Globális orvosok adatbázis lekérése"""
    global _doctors_db
    if _doctors_db is None:
        _doctors_db = DoctorsDatabase()
    return _doctors_db