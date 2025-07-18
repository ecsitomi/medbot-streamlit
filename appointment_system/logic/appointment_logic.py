# =============================================================================
# appointment_system/logic/appointment_logic.py - JAVÍTOTT VERZIÓ
# =============================================================================
"""
Foglalási logika és workflow kezelés
"""
import streamlit as st
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple, Any
import sys
import os

# Lokális importok javítása
try:
    from ..models.appointment import Appointment, AppointmentStatus, PatientInfo
    from ..models.doctor import Doctor
    from ..database.appointments_db import get_appointments_db
    from ..database.doctors_db import get_doctors_db
    from .availability_checker import AvailabilityChecker
    from .notification_handler import NotificationHandler
except ImportError:
    # Fallback import path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from models.appointment import Appointment, AppointmentStatus, PatientInfo
    from models.doctor import Doctor
    from database.appointments_db import get_appointments_db
    from database.doctors_db import get_doctors_db
    from logic.availability_checker import AvailabilityChecker
    from logic.notification_handler import NotificationHandler

class BookingValidator:
    """Foglalási validáció"""
    
    def __init__(self):
        self.appointments_db = get_appointments_db()
        self.doctors_db = get_doctors_db()
        self.availability_checker = AvailabilityChecker()
    
    def validate_booking_request(self, doctor_id: str, appointment_datetime: datetime, 
                                patient_info: PatientInfo) -> Dict[str, Any]:
        """Foglalási kérés validálása"""
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Orvos létezik?
        doctor = self.doctors_db.get_doctor_by_id(doctor_id)
        if not doctor:
            result['valid'] = False
            result['errors'].append("Nem létező orvos")
            return result
        
        # Múltbeli időpont?
        if appointment_datetime < datetime.now():
            result['valid'] = False
            result['errors'].append("Múltbeli időpontra nem lehet foglalni")
        
        # Túl közeli időpont?
        if appointment_datetime < datetime.now() + timedelta(hours=2):
            result['valid'] = False
            result['errors'].append("Legalább 2 órával előre kell foglalni")
        
        # Túl távoli időpont?
        if appointment_datetime > datetime.now() + timedelta(days=60):
            result['valid'] = False
            result['errors'].append("Maximum 60 nappal előre lehet foglalni")
        
        # Munkaidő ellenőrzés
        if not self._is_within_working_hours(doctor, appointment_datetime):
            result['valid'] = False
            result['errors'].append("Az orvos nem rendel ekkor")
        
        # Szabad időpont?
        if not self._is_slot_available(doctor_id, appointment_datetime):
            result['valid'] = False
            result['errors'].append("Ez az időpont már foglalt")
        
        # Páciens adatok validálása
        patient_validation = self._validate_patient_info(patient_info)
        if not patient_validation['valid']:
            result['valid'] = False
            result['errors'].extend(patient_validation['errors'])
        
        # Figyelmeztetések
        if self._has_recent_appointment(patient_info.email, doctor_id):
            result['warnings'].append("Nemrég volt már foglalása ennél az orvosnál")
        
        return result
    
    def _is_within_working_hours(self, doctor: Doctor, appointment_datetime: datetime) -> bool:
        """Munkaidő ellenőrzés"""
        weekday = appointment_datetime.strftime("%A").lower()
        working_hours = doctor.get_working_hours_for_day(weekday)
        
        if not working_hours:
            return False
        
        appointment_time = appointment_datetime.time()
        
        # Munkaidő ellenőrzés
        if appointment_time < working_hours.start_time or appointment_time >= working_hours.end_time:
            return False
        
        # Szünet ellenőrzés
        if working_hours.break_start and working_hours.break_end:
            if working_hours.break_start <= appointment_time < working_hours.break_end:
                return False
        
        return True
    
    def _is_slot_available(self, doctor_id: str, appointment_datetime: datetime) -> bool:
        """Szabad időpont ellenőrzés"""
        available_slots = self.availability_checker.get_available_slots(
            self.doctors_db.get_doctor_by_id(doctor_id),
            appointment_datetime.date()
        )
        
        return appointment_datetime.time() in available_slots
    
    def _validate_patient_info(self, patient_info: PatientInfo) -> Dict[str, Any]:
        """Páciens adatok validálása"""
        result = {
            'valid': True,
            'errors': []
        }
        
        # Kötelező mezők
        if not patient_info.name or len(patient_info.name.strip()) < 2:
            result['valid'] = False
            result['errors'].append("Érvényes név szükséges")
        
        if not patient_info.phone or len(patient_info.phone.strip()) < 10:
            result['valid'] = False
            result['errors'].append("Érvényes telefonszám szükséges")
        
        if not patient_info.email or '@' not in patient_info.email:
            result['valid'] = False
            result['errors'].append("Érvényes email cím szükséges")
        
        if not (0 < patient_info.age < 120):
            result['valid'] = False
            result['errors'].append("Érvényes életkor szükséges")
        
        if patient_info.gender not in ['férfi', 'nő']:
            result['valid'] = False
            result['errors'].append("Nem megadása szükséges")
        
        return result
    
    def _has_recent_appointment(self, patient_email: str, doctor_id: str) -> bool:
        """Nemrég volt-e foglalása"""
        patient_appointments = self.appointments_db.get_appointments_by_patient(patient_email)
        recent_threshold = datetime.now() - timedelta(days=7)
        
        for appointment in patient_appointments:
            if (appointment.doctor_id == doctor_id and 
                appointment.datetime > recent_threshold and
                appointment.status != AppointmentStatus.CANCELLED):
                return True
        
        return False

class AppointmentManager:
    """Foglalások kezelése"""
    
    def __init__(self):
        self.appointments_db = get_appointments_db()
        self.doctors_db = get_doctors_db()
        self.validator = BookingValidator()
        self.notification_handler = NotificationHandler()
    
    def book_appointment(self, doctor_id: str, appointment_datetime: datetime, 
                        patient_info: PatientInfo, notes: str = "") -> Dict[str, Any]:
        """Időpont foglalása"""
        result = {
            'success': False,
            'appointment': None,
            'reference_number': None,
            'errors': [],
            'warnings': []
        }
        
        # Validáció
        validation = self.validator.validate_booking_request(
            doctor_id, appointment_datetime, patient_info
        )
        
        if not validation['valid']:
            result['errors'] = validation['errors']
            return result
        
        result['warnings'] = validation['warnings']
        
        # Orvos lekérése
        doctor = self.doctors_db.get_doctor_by_id(doctor_id)
        if not doctor:
            result['errors'].append("Orvos nem található")
            return result
        
        # Appointment létrehozása
        appointment = Appointment(
            id=f"apt_{datetime.now().strftime('%Y%m%d%H%M%S')}_{doctor_id}",
            doctor_id=doctor_id,
            patient_info=patient_info,
            datetime=appointment_datetime,
            duration_minutes=doctor.appointment_duration,
            status=AppointmentStatus.PENDING,
            notes=notes
        )
        
        # Adatbázisba mentés
        if self.appointments_db.add_appointment(appointment):
            result['success'] = True
            result['appointment'] = appointment
            result['reference_number'] = appointment.reference_number
            
            # Automatikus megerősítés
            appointment.status = AppointmentStatus.CONFIRMED
            self.appointments_db.update_appointment(appointment)
            
            # Értesítés küldése
            try:
                self.notification_handler.send_booking_confirmation(appointment, doctor)
            except Exception as e:
                result['warnings'].append(f"Értesítés küldése sikertelen: {e}")
        else:
            result['errors'].append("Foglalás mentése sikertelen")
        
        return result
    
    def cancel_appointment(self, appointment_id: str, reason: str = "") -> Dict[str, Any]:
        """Időpont lemondása"""
        result = {
            'success': False,
            'appointment': None,
            'errors': [],
            'warnings': []
        }
        
        # Appointment lekérése
        appointment = self.appointments_db.get_appointment_by_id(appointment_id)
        if not appointment:
            result['errors'].append("Foglalás nem található")
            return result
        
        # Státusz ellenőrzés
        if appointment.status == AppointmentStatus.CANCELLED:
            result['errors'].append("Foglalás már le van mondva")
            return result
        
        # Lemondási határidő ellenőrzés
        if appointment.datetime < datetime.now() + timedelta(hours=24):
            result['warnings'].append("24 órán belüli lemondás")
        
        # Lemondás
        if reason:
            appointment.notes += f"\nLemondás oka: {reason}"
        
        if self.appointments_db.cancel_appointment(appointment_id):
            result['success'] = True
            result['appointment'] = self.appointments_db.get_appointment_by_id(appointment_id)
        else:
            result['errors'].append("Lemondás sikertelen")
        
        return result
    
    def get_patient_appointments(self, patient_email: str) -> List[Appointment]:
        """Páciens foglalásainak lekérése"""
        return self.appointments_db.get_appointments_by_patient(patient_email)
    
    def get_doctor_appointments(self, doctor_id: str, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[Appointment]:
        """Orvos foglalásainak lekérése"""
        appointments = self.appointments_db.get_appointments_by_doctor(doctor_id)
        
        if start_date and end_date:
            appointments = [
                apt for apt in appointments
                if start_date <= apt.datetime.date() <= end_date
            ]
        
        return appointments

class AppointmentWorkflow:
    """Foglalási workflow kezelő"""
    
    def __init__(self):
        self.appointment_manager = AppointmentManager()
        self.doctors_db = get_doctors_db()
    
    def execute_full_booking_workflow(self, doctor_id: str, appointment_datetime: datetime, 
                                    patient_data: Dict[str, Any], medical_context: Dict[str, Any]) -> Dict[str, Any]:
        """Teljes foglalási workflow végrehajtása"""
        result = {
            'success': False,
            'appointment': None,
            'steps_completed': [],
            'errors': [],
            'warnings': []
        }
        
        try:
            # 1. Páciens adatok konvertálása
            patient_info = self._convert_patient_data(patient_data, medical_context)
            result['steps_completed'].append("patient_data_conversion")
            
            # 2. Orvos elérhetőségének ellenőrzése
            doctor = self.doctors_db.get_doctor_by_id(doctor_id)
            if not doctor:
                result['errors'].append("Orvos nem található")
                return result
            
            result['steps_completed'].append("doctor_verification")
            
            # 3. Időpont foglalása
            booking_result = self.appointment_manager.book_appointment(
                doctor_id, appointment_datetime, patient_info, 
                notes=f"Foglalás a Medical Chatbot rendszerből. Diagnózis: {medical_context.get('diagnosis', 'N/A')}"
            )
            
            if booking_result['success']:
                result['success'] = True
                result['appointment'] = booking_result['appointment']
                result['steps_completed'].append("appointment_booking")
                
                # 4. Session state frissítése
                self._update_session_state(booking_result['appointment'], doctor)
                result['steps_completed'].append("session_state_update")
                
                # 5. Workflow információk hozzáadása
                result['workflow_info'] = {
                    'booking_source': 'medical_chatbot',
                    'medical_context': medical_context,
                    'reference_number': booking_result['reference_number'],
                    'doctor_info': {
                        'name': doctor.get_display_name(),
                        'specialization': doctor.get_specialization_hu(),
                        'phone': doctor.phone,
                        'address': doctor.address
                    }
                }
                
                result['steps_completed'].append("workflow_completion")
            else:
                result['errors'] = booking_result['errors']
                result['warnings'] = booking_result['warnings']
        
        except Exception as e:
            result['errors'].append(f"Workflow hiba: {str(e)}")
        
        return result
    
    def _convert_patient_data(self, patient_data: Dict[str, Any], medical_context: Dict[str, Any]) -> PatientInfo:
        """Páciens adatok konvertálása PatientInfo objektummá"""
        
        # Alapértelmezett értékek
        name = patient_data.get('name', 'Ismeretlen Páciens')
        age = patient_data.get('age', 30)
        gender = patient_data.get('gender', 'férfi')
        phone = patient_data.get('phone', '+36 30 000 0000')
        email = patient_data.get('email', 'patient@example.com')
        
        # Orvosi adatok
        symptoms = patient_data.get('symptoms', [])
        diagnosis = medical_context.get('diagnosis', '')
        medical_history = patient_data.get('existing_conditions', [])
        medications = patient_data.get('medications', [])
        
        return PatientInfo(
            name=name,
            age=age,
            gender=gender,
            phone=phone,
            email=email,
            symptoms=symptoms,
            diagnosis=diagnosis,
            medical_history=medical_history,
            medications=medications
        )
    
    def _update_session_state(self, appointment: Appointment, doctor: Doctor):
        """Session state frissítése a sikeres foglalás után"""
        st.session_state.appointment_data = {
            "selected_doctor": doctor,
            "selected_datetime": appointment.datetime,
            "appointment": appointment,
            "booking_status": "confirmed"
        }