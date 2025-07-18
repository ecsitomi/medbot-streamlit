# =============================================================================
# appointment_system/logic/__init__.py - JAVÍTOTT VERZIÓ
# =============================================================================
"""
Logic modul - üzleti logika az appointment system számára
"""

# Matching és keresés
from .specialist_matcher import SpecialistMatcher

# Szabad időpontok kezelése
from .availability_checker import AvailabilityChecker

# Foglalási logika
from .appointment_logic import (
    AppointmentManager,
    BookingValidator,
    AppointmentWorkflow
)

# Értesítések
from .notification_handler import NotificationHandler

# Publikus API
__all__ = [
    # Matching
    'SpecialistMatcher',
    
    # Availability
    'AvailabilityChecker',
    
    # Appointment logic
    'AppointmentManager',
    'BookingValidator',
    'AppointmentWorkflow',
    
    # Notifications
    'NotificationHandler'
]
