# =============================================================================
# appointment_system/config.py
# =============================================================================
"""
Appointment system konfigurációs beállítások
"""
from datetime import time
from typing import Dict, List

# Általános beállítások
APPOINTMENT_SYSTEM_CONFIG = {
    "default_appointment_duration": 30,  # percek
    "booking_advance_days": 60,          # hány nappal előre lehet foglalni
    "min_advance_hours": 2,              # minimum hány órával előre kell foglalni
    "max_appointments_per_day": 20,      # maximum foglalások naponta
    "reminder_hours": [24, 2],           # mikor küldjön emlékeztetőt (órában)
    "working_days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
    "emergency_phone": "+36 1 104",      # sürgősségi telefonszám
}

# Munkaidő sablonok
WORKING_HOURS_TEMPLATES = {
    "standard": {
        "monday": (time(8, 0), time(16, 0)),
        "tuesday": (time(8, 0), time(16, 0)),
        "wednesday": (time(8, 0), time(16, 0)),
        "thursday": (time(8, 0), time(16, 0)),
        "friday": (time(8, 0), time(14, 0))
    },
    "extended": {
        "monday": (time(7, 0), time(19, 0)),
        "tuesday": (time(7, 0), time(19, 0)),
        "wednesday": (time(7, 0), time(19, 0)),
        "thursday": (time(7, 0), time(19, 0)),
        "friday": (time(7, 0), time(17, 0))
    }
}

# Értesítési beállítások
NOTIFICATION_CONFIG = {
    "email_enabled": True,
    "sms_enabled": True,
    "automatic_reminders": True,
    "confirmation_required": True,
    "sender_email": "noreply@medicalchatbot.com",
    "sender_name": "Medical Chatbot",
    "sms_sender": "MedChat"
}

# UI beállítások
UI_CONFIG = {
    "calendar_weeks_ahead": 8,
    "max_doctors_display": 10,
    "time_slot_interval": 30,  # percek
    "show_doctor_photos": False,
    "show_doctor_ratings": True,
    "show_availability_count": True
}

# Matching algoritmus beállítások
MATCHING_CONFIG = {
    "max_suggestions": 5,
    "min_relevance_score": 3.0,
    "boost_high_rating": True,
    "boost_availability": True,
    "prefer_same_location": True
}