# =============================================================================
# appointment_system/models/patient.py
# =============================================================================
"""
Páciens adatmodellek (kiegészítő)
"""
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class PatientMedicalHistory:
    """Páciens orvosi előzmények"""
    patient_id: str
    chronic_conditions: List[str]
    allergies: List[str]
    medications: List[str]
    past_surgeries: List[str]
    family_history: List[str]
    last_updated: datetime

@dataclass
class PatientPreferences:
    """Páciens preferenciák"""
    patient_id: str
    preferred_language: str
    preferred_communication: str  # email, sms, phone
    preferred_appointment_time: str  # morning, afternoon, evening
    accessibility_needs: List[str]
    emergency_contact: str
    emergency_contact_phone: str