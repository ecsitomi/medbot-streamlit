# =============================================================================
# appointment_system/logic/notification_handler.py
# =============================================================================
"""
Értesítések kezelése
"""
import streamlit as st
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from ..models.appointment import Appointment
from ..models.doctor import Doctor

class NotificationHandler:
    """Értesítések kezelése"""
    
    def __init__(self):
        self.notification_templates = {
            'email_confirmation': {
                'subject': 'Időpont foglalás megerősítése - {reference_number}',
                'body': """
Kedves {patient_name}!

Megerősítjük az időpont foglalását:

Orvos: {doctor_name} - {doctor_specialization}
Időpont: {appointment_datetime}
Helyszín: {doctor_address}
Referencia szám: {reference_number}

Kérjük, érkezzen 10 perccel korábban!

Üdvözlettel,
Medical Chatbot Team
                """
            },
            'sms_reminder': {
                'body': """
Időpont emlékeztető: {appointment_datetime}
{doctor_name} - {doctor_specialization}
{doctor_address}
Ref: {reference_number}
                """
            },
            'email_reminder': {
                'subject': 'Időpont emlékeztető - {reference_number}',
                'body': """
Kedves {patient_name}!

Emlékeztetjük, hogy holnap orvosi rendelése van:

Orvos: {doctor_name} - {doctor_specialization}
Időpont: {appointment_datetime}
Helyszín: {doctor_address}

Kérjük, érkezzen 10 perccel korábban!

Üdvözlettel,
Medical Chatbot Team
                """
            }
        }
    
    def send_booking_confirmation(self, appointment: Appointment, doctor: Doctor) -> bool:
        """
        Foglalás megerősítő értesítés küldése
        
        Args:
            appointment: Foglalás
            doctor: Orvos
            
        Returns:
            bool: Sikeres volt-e a küldés
        """
        try:
            # Email megerősítés
            email_sent = self._send_email_notification(
                appointment, doctor, 'email_confirmation'
            )
            
            # SMS megerősítés (opcionális)
            sms_sent = self._send_sms_notification(
                appointment, doctor, 'sms_reminder'
            )
            
            # Notification log
            self._log_notification(appointment, 'confirmation', email_sent and sms_sent)
            
            return email_sent
            
        except Exception as e:
            st.error(f"Hiba az értesítés küldésekor: {e}")
            return False
    
    def send_appointment_reminder(self, appointment: Appointment, doctor: Doctor) -> bool:
        """
        Időpont emlékeztető küldése
        
        Args:
            appointment: Foglalás
            doctor: Orvos
            
        Returns:
            bool: Sikeres volt-e a küldés
        """
        try:
            # Email emlékeztető
            email_sent = self._send_email_notification(
                appointment, doctor, 'email_reminder'
            )
            
            # SMS emlékeztető
            sms_sent = self._send_sms_notification(
                appointment, doctor, 'sms_reminder'
            )
            
            # Notification log
            self._log_notification(appointment, 'reminder', email_sent and sms_sent)
            
            return email_sent
            
        except Exception as e:
            st.error(f"Hiba az emlékeztető küldésekor: {e}")
            return False
    
    def _send_email_notification(self, appointment: Appointment, doctor: Doctor, 
                               template_name: str) -> bool:
        """Email értesítés küldése (szimuláció)"""
        
        template = self.notification_templates.get(template_name)
        if not template:
            return False
        
        # Template változók kitöltése
        variables = {
            'patient_name': appointment.patient_info.name,
            'doctor_name': doctor.get_display_name(),
            'doctor_specialization': doctor.get_specialization_hu(),
            'appointment_datetime': appointment.get_formatted_datetime(),
            'doctor_address': doctor.address,
            'reference_number': appointment.reference_number
        }
        
        # Email tartalom generálása
        subject = template['subject'].format(**variables)
        body = template['body'].format(**variables)
        
        # Szimuláció - valós implementációban itt küldenéd el az emailt
        st.success(f"📧 Email elküldve: {appointment.patient_info.email}")
        
        # Debug információ
        if st.checkbox("📧 Email részletek megtekintése", key=f"email_{appointment.id}"):
            st.code(f"To: {appointment.patient_info.email}\nSubject: {subject}\n\n{body}")
        
        return True
    
    def _send_sms_notification(self, appointment: Appointment, doctor: Doctor, 
                             template_name: str) -> bool:
        """SMS értesítés küldése (szimuláció)"""
        
        template = self.notification_templates.get(template_name)
        if not template:
            return False
        
        # Template változók kitöltése
        variables = {
            'patient_name': appointment.patient_info.name,
            'doctor_name': doctor.name,
            'doctor_specialization': doctor.get_specialization_hu(),
            'appointment_datetime': appointment.get_formatted_datetime(),
            'doctor_address': doctor.address,
            'reference_number': appointment.reference_number
        }
        
        # SMS tartalom generálása
        message = template['body'].format(**variables).strip()
        
        # Szimuláció - valós implementációban itt küldenéd el az SMS-t
        st.success(f"📱 SMS elküldve: {appointment.patient_info.phone}")
        
        # Debug információ
        if st.checkbox("📱 SMS részletek megtekintése", key=f"sms_{appointment.id}"):
            st.code(f"To: {appointment.patient_info.phone}\nMessage: {message}")
        
        return True
    
    def _log_notification(self, appointment: Appointment, notification_type: str, success: bool):
        """Értesítés logolása"""
        
        # Session state-be mentés
        if 'notification_log' not in st.session_state:
            st.session_state.notification_log = []
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'appointment_id': appointment.id,
            'reference_number': appointment.reference_number,
            'notification_type': notification_type,
            'success': success,
            'patient_email': appointment.patient_info.email,
            'patient_phone': appointment.patient_info.phone
        }
        
        st.session_state.notification_log.append(log_entry)
    
    def get_notification_history(self, appointment_id: str) -> List[Dict]:
        """
        Értesítési előzmények lekérése
        
        Args:
            appointment_id: Foglalás ID
            
        Returns:
            List[Dict]: Értesítések listája
        """
        if 'notification_log' not in st.session_state:
            return []
        
        return [
            log for log in st.session_state.notification_log 
            if log['appointment_id'] == appointment_id
        ]
    
    def schedule_reminders(self, appointment: Appointment, doctor: Doctor):
        """
        Automatikus emlékeztetők ütemezése
        
        Args:
            appointment: Foglalás
            doctor: Orvos
        """
        # Valós implementációban itt ütemezni a jövőbeli értesítéseket
        # Például: 24 órával előtte email, 2 órával előtte SMS
        
        reminder_times = [
            appointment.datetime - timedelta(hours=24),  # 1 nappal előtte
            appointment.datetime - timedelta(hours=2),   # 2 órával előtte
        ]
        
        st.info(f"""
        ⏰ **Automatikus emlékeztetők ütemezve:**
        • Email: {reminder_times[0].strftime('%Y. %m. %d. %H:%M')}
        • SMS: {reminder_times[1].strftime('%Y. %m. %d. %H:%M')}
        """)