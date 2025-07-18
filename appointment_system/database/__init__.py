# =============================================================================
# appointment_system/database/__init__.py - JAVÍTOTT VERZIÓ
# =============================================================================
"""
Database modul - adatbázis kezelés az appointment system számára
"""

# Fő adatbázis osztályok
from .doctors_db import (
    DoctorsDatabase, 
    get_doctors_db
)

from .appointments_db import (
    AppointmentsDatabase,
    get_appointments_db
)

# Minta adatok
from .sample_data import (
    generate_sample_doctors,
    generate_sample_appointments
)

# Publikus API
__all__ = [
    # Adatbázis osztályok
    'DoctorsDatabase',
    'get_doctors_db',
    'AppointmentsDatabase', 
    'get_appointments_db',
    
    # Sample data
    'generate_sample_doctors',
    'generate_sample_appointments'
]