# =============================================================================
# appointment_system/models/__init__.py - JAVÍTOTT VERZIÓ
# =============================================================================
"""
Models modul - adatmodellek az appointment system számára
"""

# Alapvető adatmodellek
from .doctor import (
    Doctor, 
    DoctorSpecialization, 
    WorkingHours
)

from .appointment import (
    Appointment, 
    AppointmentStatus, 
    PatientInfo
)

from .patient import (
    PatientMedicalHistory,
    PatientPreferences
)

# Publikus API
__all__ = [
    # Doctor modellek
    'Doctor',
    'DoctorSpecialization', 
    'WorkingHours',
    
    # Appointment modellek
    'Appointment',
    'AppointmentStatus',
    'PatientInfo',
    
    # Patient modellek
    'PatientMedicalHistory',
    'PatientPreferences'
]