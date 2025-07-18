# =============================================================================
# appointment_system/__init__.py - JAVÍTOTT VERZIÓ
# =============================================================================
"""
Időpont Foglaló Rendszer - Medical Chatbot integráció
"""

__version__ = "1.0.0"
__author__ = "Medical Chatbot Team"
__description__ = "Időpont foglaló rendszer orvosi chatbot integrációval"

# Főbb komponensek importálása
from .models.doctor import Doctor, DoctorSpecialization
from .models.appointment import Appointment, AppointmentStatus
from .database.doctors_db import DoctorsDatabase, get_doctors_db
from .database.appointments_db import AppointmentsDatabase, get_appointments_db
from .logic.specialist_matcher import SpecialistMatcher
from .logic.appointment_logic import AppointmentManager, BookingValidator, AppointmentWorkflow
from .ui.doctor_selection import DoctorSelectionUI
from .ui.appointment_booking import AppointmentBookingUI
from .integration import AppointmentSystemIntegration, appointment_integration

# Publikus API
__all__ = [
    'Doctor', 'DoctorSpecialization',
    'Appointment', 'AppointmentStatus', 
    'DoctorsDatabase', 'get_doctors_db',
    'AppointmentsDatabase', 'get_appointments_db',
    'SpecialistMatcher',
    'AppointmentManager', 'BookingValidator', 'AppointmentWorkflow',
    'DoctorSelectionUI', 'AppointmentBookingUI',
    'AppointmentSystemIntegration', 'appointment_integration'
]
