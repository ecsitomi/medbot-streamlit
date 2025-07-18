# =============================================================================
# appointment_system/models/doctor.py
# =============================================================================
"""
Orvos adatmodellek
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime, time
from enum import Enum

class DoctorSpecialization(Enum):
    """Orvosi szakspecializációk"""
    GENERAL_PRACTITIONER = "háziorvos"
    INTERNAL_MEDICINE = "belgyógyász"
    NEUROLOGY = "neurológus"
    CARDIOLOGY = "kardiológus"
    DERMATOLOGY = "bőrgyógyász"
    GASTROENTEROLOGY = "gasztroenterológus"
    ORTHOPEDICS = "ortopéd"
    PEDIATRICS = "gyermekorvos"
    PSYCHIATRY = "pszichiáter"
    SURGERY = "sebész"
    GYNECOLOGY = "nőgyógyász"
    UROLOGY = "urológus"
    OPHTHALMOLOGY = "szemész"
    ENT = "fül-orr-gégész"
    EMERGENCY = "sürgősségi orvos"

@dataclass
class WorkingHours:
    """Munkaidő adatok"""
    day: str  # "monday", "tuesday", etc.
    start_time: time
    end_time: time
    break_start: Optional[time] = None
    break_end: Optional[time] = None

@dataclass
class Doctor:
    """Orvos adatmodell"""
    id: str
    name: str
    specialization: DoctorSpecialization
    location: str
    address: str
    phone: str
    email: str
    working_hours: List[WorkingHours]
    rating: float = 4.5
    description: str = ""
    appointment_duration: int = 30  # percek
    available_from: datetime = field(default_factory=datetime.now)
    languages: List[str] = field(default_factory=lambda: ["magyar"])
    
    def __post_init__(self):
        """Post-init validáció"""
        if not (0 <= self.rating <= 5):
            raise ValueError("Rating must be between 0 and 5")
        if self.appointment_duration <= 0:
            raise ValueError("Appointment duration must be positive")
    
    def get_display_name(self) -> str:
        """Megjelenítési név"""
        return f"Dr. {self.name}"
    
    def get_specialization_hu(self) -> str:
        """Magyar szakspecializáció"""
        return self.specialization.value
    
    def is_available_on_day(self, day: str) -> bool:
        """Ellenőrzi, hogy dolgozik-e az adott napon"""
        return any(wh.day.lower() == day.lower() for wh in self.working_hours)
    
    def get_working_hours_for_day(self, day: str) -> Optional[WorkingHours]:
        """Munkaidő lekérése adott napra"""
        for wh in self.working_hours:
            if wh.day.lower() == day.lower():
                return wh
        return None