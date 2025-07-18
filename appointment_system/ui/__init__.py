# =============================================================================
# appointment_system/ui/__init__.py - JAVÍTOTT VERZIÓ
# =============================================================================
"""
UI modul - felhasználói felület komponensek az appointment system számára
"""
from typing import Dict, Optional

# Főbb UI komponensek
from .doctor_selection import DoctorSelectionUI
from .appointment_booking import AppointmentBookingUI
from .appointment_summary import AppointmentSummaryUI
from .calendar_widget import CalendarWidget

# Publikus API
__all__ = [
    # UI komponensek
    'DoctorSelectionUI',
    'AppointmentBookingUI', 
    'AppointmentSummaryUI',
    'CalendarWidget'
]

# UI Helper funkciók
def create_appointment_ui_suite() -> Dict[str, object]:
    """Teljes appointment UI suite létrehozása"""
    return {
        'doctor_selection': DoctorSelectionUI(),
        'appointment_booking': AppointmentBookingUI(),
        'appointment_summary': AppointmentSummaryUI(),
        'calendar_widget': CalendarWidget()
    }

def get_ui_component(component_name: str) -> Optional[object]:
    """Specifikus UI komponens lekérése"""
    components = {
        'doctor_selection': DoctorSelectionUI,
        'appointment_booking': AppointmentBookingUI,
        'appointment_summary': AppointmentSummaryUI,
        'calendar_widget': CalendarWidget
    }
    
    component_class = components.get(component_name)
    return component_class() if component_class else None

# UI konfigurációk
UI_CONSTANTS = {
    'COLORS': {
        'primary': '#1f77b4',
        'success': '#2ca02c',
        'warning': '#ff7f0e',
        'error': '#d62728',
        'info': '#17becf'
    },
    'ICONS': {
        'doctor': '👨‍⚕️',
        'appointment': '📅',
        'calendar': '🗓️',
        'time': '🕐',
        'phone': '📞',
        'email': '📧',
        'location': '📍',
        'rating': '⭐'
    },
    'MESSAGES': {
        'success': '✅ Sikeres foglalás!',
        'error': '❌ Hiba történt!',
        'warning': '⚠️ Figyelem!',
        'info': 'ℹ️ Információ'
    }
}

# CSS stílusok
APPOINTMENT_UI_STYLES = """
<style>
.appointment-card {
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 16px;
    margin: 8px 0;
    background-color: #f9f9f9;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.appointment-card:hover {
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    transform: translateY(-2px);
    transition: all 0.3s ease;
}

.doctor-info {
    display: flex;
    align-items: center;
    gap: 12px;
}

.doctor-rating {
    color: #ffd700;
    font-weight: bold;
}

.appointment-time {
    background-color: #e8f4f8;
    padding: 8px 16px;
    border-radius: 20px;
    display: inline-block;
    margin: 4px;
    cursor: pointer;
    border: 2px solid transparent;
}

.appointment-time:hover {
    background-color: #d4edda;
    border-color: #28a745;
}

.appointment-time.selected {
    background-color: #28a745;
    color: white;
    border-color: #1e7e34;
}

.calendar-day {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 2px;
    cursor: pointer;
    border: 1px solid #ddd;
}

.calendar-day.available {
    background-color: #d4edda;
    border-color: #28a745;
}

.calendar-day.unavailable {
    background-color: #f8d7da;
    border-color: #dc3545;
    cursor: not-allowed;
}

.calendar-day.selected {
    background-color: #007bff;
    color: white;
    border-color: #0056b3;
}
</style>
"""

def inject_appointment_ui_styles():
    """Appointment UI stílusok injektálása"""
    import streamlit as st
    st.markdown(APPOINTMENT_UI_STYLES, unsafe_allow_html=True)