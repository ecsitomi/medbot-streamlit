# =============================================================================
# appointment_system/models/appointment.py - LAMBDA VERZIÓ
# =============================================================================
"""
Időpont adatmodellek - Lambda verzió
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum

class AppointmentStatus(Enum):
    """Időpont státuszok"""
    PENDING = "függőben"
    CONFIRMED = "megerősítve"
    CANCELLED = "törölve"
    COMPLETED = "befejezve"
    NO_SHOW = "meg nem jelent"

@dataclass
class PatientInfo:
    """Páciens információk az időponthoz"""
    name: str
    age: int
    gender: str
    phone: str
    email: str
    symptoms: List[str] = field(default_factory=list)
    diagnosis: str = ""
    medical_history: List[str] = field(default_factory=list)
    medications: List[str] = field(default_factory=list)

@dataclass
class Appointment:
    id: str
    doctor_id: str
    patient_info: PatientInfo
    start_time: datetime  # <-- új név, nem ütközik a datetime típussal
    duration_minutes: int
    status: AppointmentStatus
    notes: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now())
    updated_at: datetime = field(default_factory=lambda: datetime.now())
    reference_number: str = ""
    
    def __post_init__(self):
        if not self.reference_number:
            self.reference_number = self.generate_reference_number()
    
    def generate_reference_number(self) -> str:
        import hashlib
        import random
        hash_input = f"{self.doctor_id}{self.start_time.isoformat()}{random.randint(1000, 9999)}"
        hash_obj = hashlib.md5(hash_input.encode())
        return f"APT-{hash_obj.hexdigest()[:8].upper()}"
    
    def get_status_hu(self) -> str:
        return self.status.value
    
    def get_formatted_datetime(self) -> str:
        return self.start_time.strftime("%Y. %m. %d. %H:%M")
    
    def get_end_datetime(self) -> datetime:
        return self.start_time + timedelta(minutes=self.duration_minutes)
