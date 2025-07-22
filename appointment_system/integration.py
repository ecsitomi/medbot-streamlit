# =============================================================================
# appointment_system/integration.py - ELLENŐRZÉS ÉS JAVÍTÁS
# =============================================================================
"""
Appointment System integráció a meglévő medical chatbot rendszerrel
JAVÍTOTT VERZIÓ - Export függvények hozzáadása
"""
import streamlit as st
from typing import List, Dict, Any, Optional
from .ui.doctor_selection import DoctorSelectionUI
from .ui.appointment_booking import AppointmentBookingUI
from .models.doctor import Doctor
from .models.appointment import Appointment

class AppointmentSystemIntegration:
    """Appointment System integráció központi osztálya."""
    
    def __init__(self):
        self.doctor_selection_ui = DoctorSelectionUI()
        self.appointment_booking_ui = AppointmentBookingUI()
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Medline-specifikus session state inicializálása."""
        if 'appointment_data' not in st.session_state:
            st.session_state.appointment_data = {
                "selected_doctor": None,
                "selected_datetime": None,
                "appointment": None,
                "booking_status": None
            }
    
    def display_appointment_section(self, gpt_specialist_advice: str, 
                                  patient_data: Dict[str, Any], 
                                  diagnosis: str):
        """Appointment szekció megjelenítése a medical summary után"""
        if not gpt_specialist_advice:
            return
        
        st.markdown("---")
        st.markdown("### 🏥 Időpont Foglalás")
        
        # Ellenőrizzük, hogy van-e már foglalás
        if st.session_state.appointment_data.get("booking_status") == "confirmed":
            self._display_existing_appointment()
            return
        
        # Orvos kiválasztás
        selected_doctor = self.doctor_selection_ui.display_doctor_selection(
            gpt_specialist_advice, 
            diagnosis, 
            patient_data.get('symptoms', [])
        )
        
        if selected_doctor:
            # Időpont foglalás
            appointment = self.appointment_booking_ui.display_appointment_booking(
                selected_doctor, 
                patient_data
            )
            
            if appointment:
                # Sikeres foglalás esetén
                st.balloons()
    
    def _display_existing_appointment(self):
        """Meglévő foglalás megjelenítése"""
        appointment_data = st.session_state.appointment_data
        appointment = appointment_data.get("appointment")
        
        if not appointment:
            return
        
        st.success(f"""
        ✅ **Már van aktív foglalása!**
        
        **Referencia szám:** {appointment.reference_number}
        **Orvos:** {appointment_data['selected_doctor'].get_display_name()}
        **Időpont:** {appointment.get_formatted_datetime()}
        **Státusz:** {appointment.get_status_hu()}
        """)
        
        # Új foglalás gomb
        if st.button("🔄 Új foglalás"):
            st.session_state.appointment_data = {
                "selected_doctor": None,
                "selected_datetime": None,
                "appointment": None,
                "booking_status": None
            }
            st.rerun()
    
    def add_to_export_data(self, export_data: Dict[str, Any]) -> Dict[str, Any]:
        """Appointment adatok hozzáadása az export adatokhoz"""
        appointment_data = st.session_state.appointment_data
        
        if appointment_data.get("booking_status") == "confirmed":
            appointment = appointment_data.get("appointment")
            doctor = appointment_data.get("selected_doctor")
            
            if appointment and doctor:
                export_data["appointment"] = {
                    "reference_number": appointment.reference_number,
                    "doctor_name": doctor.get_display_name(),
                    "doctor_specialization": doctor.get_specialization_hu(),
                    "doctor_phone": doctor.phone,
                    "doctor_email": doctor.email,
                    "doctor_address": doctor.address,
                    "appointment_datetime": appointment.get_formatted_datetime(),
                    "appointment_duration": appointment.duration_minutes,
                    "appointment_status": appointment.get_status_hu(),
                    "patient_name": appointment.patient_info.name,
                    "patient_phone": appointment.patient_info.phone,
                    "patient_email": appointment.patient_info.email,
                    "created_at": appointment.created_at.isoformat(),
                    "notes": appointment.notes
                }
        
        return export_data
    
    def get_appointment_status(self) -> Dict[str, Any]:
        """Appointment rendszer státuszának lekérése"""
        appointment_data = st.session_state.appointment_data

        # DEBUG
        print(f"🔍 DEBUG appointment_data keys: {appointment_data.keys()}")
        print(f"🔍 DEBUG appointment type: {type(appointment_data.get('appointment'))}")
        print(f"🔍 DEBUG doctor type: {type(appointment_data.get('selected_doctor'))}")
        
        # Kivonjuk az objektumokat
        appointment = appointment_data.get("appointment")
        selected_doctor = appointment_data.get("selected_doctor")
        
        return {
            "has_appointment": appointment_data.get("booking_status") == "confirmed",
            "selected_doctor": selected_doctor is not None,
            "appointment_details": {
                # ✅ JAVÍTVA: objektum attribútumok helyes elérése
                "reference_number": appointment.reference_number if appointment else None,
                "doctor_name": selected_doctor.name if selected_doctor else None,
                "datetime": appointment_data.get("selected_datetime")
            }
        }

# Globális integráció példány
appointment_integration = AppointmentSystemIntegration()

# =============================================================================
# EXPORTÁLT FÜGGVÉNYEK - ezek hiányoztak!
# =============================================================================

def integrate_appointment_booking(gpt_specialist_advice: str, 
                                patient_data: Dict[str, Any], 
                                diagnosis: str):
    """
    Wrapper függvény az appointment booking integrálásához
    Hívd meg ezt a ui/medical_summary.py display_medical_summary() végén
    """
    global appointment_integration
    
    try:
        appointment_integration.display_appointment_section(
            gpt_specialist_advice, 
            patient_data, 
            diagnosis
        )
    except Exception as e:
        st.error(f"Appointment rendszer hiba: {e}")

def add_appointment_to_export_data(export_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Appointment adatok hozzáadása az export adatokhoz
    Hívd meg ezt a export/data_formatter.py create_export_data() végén
    """
    global appointment_integration
    
    try:
        return appointment_integration.add_to_export_data(export_data)
    except Exception as e:
        st.error(f"Appointment export hiba: {e}")
        return export_data

def get_appointment_integration_status() -> Dict[str, Any]:
    """
    Appointment integráció státuszának lekérése
    """
    global appointment_integration
    return appointment_integration.get_appointment_status()

# =============================================================================
# TOVÁBBI SEGÉDFÜGGVÉNYEK
# =============================================================================

def initialize_appointment_system():
    """Appointment system inicializálása"""
    global appointment_integration
    
    # Appointment system inicializálás
    if 'appointment_system_initialized' not in st.session_state:
        st.session_state.appointment_system_initialized = True
        appointment_integration._initialize_session_state()

def reset_appointment_system():
    """Appointment system reset"""
    if 'appointment_data' in st.session_state:
        st.session_state.appointment_data = {
            "selected_doctor": None,
            "selected_datetime": None,
            "appointment": None,
            "booking_status": None
        }

def debug_appointment_system():
    """Debug információk megjelenítése"""
    global appointment_integration
    
    st.markdown("### 🔍 Appointment System Debug")
    
    status = appointment_integration.get_appointment_status()
    st.json(status)
    
    if 'appointment_data' in st.session_state:
        st.markdown("### 📊 Session State")
        st.json(st.session_state.appointment_data)

# =============================================================================
# __all__ EXPORT LISTA
# =============================================================================

__all__ = [
    'AppointmentSystemIntegration',
    'appointment_integration',
    'integrate_appointment_booking',
    'add_appointment_to_export_data', 
    'get_appointment_integration_status',
    'initialize_appointment_system',
    'reset_appointment_system',
    'debug_appointment_system'
]