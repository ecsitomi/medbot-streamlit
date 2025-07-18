# =============================================================================
# appointment_system/ui/appointment_booking.py - JAVÍTOTT VERZIÓ
# =============================================================================
"""
Időpont foglalás UI komponens - JAVÍTOTT VERZIÓ
"""
import streamlit as st
from datetime import datetime, timedelta, date, time
from typing import List, Optional
from ..models.doctor import Doctor
from ..models.appointment import Appointment, AppointmentStatus, PatientInfo
from ..logic.appointment_logic import AppointmentManager  # ← ÚJ IMPORT

class AppointmentBookingUI:
    """Időpont foglalás UI komponens - JAVÍTOTT VERZIÓ"""
    
    def __init__(self):
        self.appointment_manager = AppointmentManager()  # ← ÚJ MANAGER
    
    def display_appointment_booking(self, doctor: Doctor, 
                                  patient_data: dict) -> Optional[Appointment]:
        """
        Időpont foglalás UI megjelenítése - JAVÍTOTT VERZIÓ
        """
        st.markdown("### 📅 Időpont Foglalás")
        
        # Orvos emlékeztető
        st.info(f"**Kiválasztott orvos:** {doctor.get_display_name()} - {doctor.get_specialization_hu()}")
        
        # Dátum kiválasztás
        selected_date = self._display_date_selection(doctor)
        
        if not selected_date:
            return None
        
        # Időpont kiválasztás
        selected_time = self._display_time_selection(doctor, selected_date)
        
        if not selected_time:
            return None
        
        # Kombinált datetime
        selected_datetime = datetime.combine(selected_date, selected_time)
        
        # Páciens adatok kiegészítése
        patient_info = self._display_patient_info_form(patient_data)
        
        if not patient_info:
            return None
        
        # JAVÍTOTT: Foglalás megerősítése AppointmentManager-rel
        appointment = self._display_booking_confirmation_fixed(
            doctor, selected_datetime, patient_info
        )
        
        return appointment
    
    def _display_booking_confirmation_fixed(self, doctor: Doctor, 
                                          selected_datetime: datetime,
                                          patient_info: PatientInfo) -> Optional[Appointment]:
        """JAVÍTOTT: Foglalás megerősítése AppointmentManager használatával"""
        
        st.markdown("#### ✅ Foglalás Megerősítése")
        
        # Összegzés
        st.info(f"""
        **Foglalás részletei:**
        
        • **Orvos:** {doctor.get_display_name()} - {doctor.get_specialization_hu()}
        • **Dátum:** {selected_datetime.strftime('%Y. %m. %d. %H:%M')}
        • **Időtartam:** {doctor.appointment_duration} perc
        • **Páciens:** {patient_info.name}
        • **Telefon:** {patient_info.phone}
        • **Email:** {patient_info.email}
        """)
        
        # Megerősítés gomb
        if st.button("🎯 Időpont foglalása", type="primary"):
            
            # ✅ JAVÍTOTT: AppointmentManager használata
            with st.spinner("Foglalás feldolgozása..."):
                booking_result = self.appointment_manager.book_appointment(
                    doctor_id=doctor.id,
                    appointment_datetime=selected_datetime,
                    patient_info=patient_info,
                    notes=f"Automatikus foglalás a medical chatbot rendszerből."
                )
            
            if booking_result['success']:
                appointment = booking_result['appointment']
                
                # Session state frissítése
                st.session_state.appointment_data = {
                    "selected_doctor": doctor,
                    "selected_datetime": selected_datetime,
                    "appointment": appointment,
                    "booking_status": "confirmed"
                }
                
                # Sikeres foglalás üzenet
                st.success(f"""
                🎉 **Sikeres foglalás!**
                
                Referencia szám: **{appointment.reference_number}**
                
                Egy megerősítő emailt küldtünk a {patient_info.email} címre.
                """)
                
                # ✅ DEBUG INFORMÁCIÓ
                st.info(f"📁 **Debug:** Foglalás mentve a data/appointments.json fájlba!")
                
                return appointment
            else:
                # Hiba esetén
                st.error("❌ **Foglalás sikertelen!**")
                for error in booking_result['errors']:
                    st.error(f"• {error}")
                
                for warning in booking_result['warnings']:
                    st.warning(f"⚠️ {warning}")
                
                return None
        
        return None
    
    # ... (többi metódus változatlan)
    def _display_date_selection(self, doctor: Doctor) -> Optional[date]:
        """Dátum kiválasztás - VÁLTOZATLAN"""
        st.markdown("#### 📆 Dátum kiválasztás")
        
        today = date.today()
        max_date = today + timedelta(days=30)
        
        available_days = [wh.day for wh in doctor.working_hours]
        
        selected_date = st.date_input(
            "Válasszon dátumot:",
            min_value=today,
            max_value=max_date,
            value=today,
            key="appointment_date"
        )
        
        weekday = selected_date.strftime("%A").lower()
        
        if weekday not in available_days:
            st.error(f"Dr. {doctor.name} nem rendel ezen a napon. Válasszon másik dátumot.")
            return None
        
        return selected_date
    
    def _display_time_selection(self, doctor: Doctor, selected_date: date) -> Optional[time]:
        """Időpont kiválasztás - VÁLTOZATLAN"""
        st.markdown("#### 🕐 Időpont kiválasztás")
        
        weekday = selected_date.strftime("%A").lower()
        working_hours = doctor.get_working_hours_for_day(weekday)
        
        if not working_hours:
            st.error("Nincs munkaidő információ erre a napra.")
            return None
        
        available_times = self._generate_available_times(doctor, working_hours)
        
        if not available_times:
            st.error("Nincs elérhető időpont erre a napra.")
            return None
        
        time_options = [t.strftime("%H:%M") for t in available_times]
        
        selected_time_str = st.selectbox(
            "Válasszon időpontot:",
            options=time_options,
            key="appointment_time"
        )
        
        hour, minute = map(int, selected_time_str.split(':'))
        selected_time = time(hour, minute)
        
        return selected_time
    
    def _generate_available_times(self, doctor: Doctor, working_hours) -> List[time]:
        """Elérhető időpontok generálása - VÁLTOZATLAN"""
        times = []
        duration = doctor.appointment_duration
        
        start_time = working_hours.start_time
        end_time = working_hours.end_time
        break_start = working_hours.break_start
        break_end = working_hours.break_end
        
        current_time = start_time
        
        while current_time < end_time:
            appointment_end = datetime.combine(date.today(), current_time) + timedelta(minutes=duration)
            appointment_end_time = appointment_end.time()
            
            if appointment_end_time > end_time:
                break
            
            if break_start and break_end:
                if not (current_time >= break_start and current_time < break_end):
                    times.append(current_time)
            else:
                times.append(current_time)
            
            next_time = datetime.combine(date.today(), current_time) + timedelta(minutes=duration)
            current_time = next_time.time()
        
        return times
    
    def _display_patient_info_form(self, patient_data: dict) -> Optional[PatientInfo]:
        """Páciens adatok kiegészítése - VÁLTOZATLAN"""
        st.markdown("#### 👤 Páciens Adatok")
        
        with st.form("patient_info_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Teljes név *", key="patient_name")
                phone = st.text_input("Telefonszám *", key="patient_phone")
                email = st.text_input("Email cím *", key="patient_email")
            
            with col2:
                age = st.number_input("Életkor *", min_value=1, max_value=120, 
                                    value=patient_data.get('age', 30),
                                    key="patient_age")
                gender = st.selectbox("Nem *", ["férfi", "nő"], 
                                    index=0 if patient_data.get('gender') == 'férfi' else 1,
                                    key="patient_gender")
            
            symptoms = patient_data.get('symptoms', [])
            diagnosis = patient_data.get('diagnosis', '')
            existing_conditions = patient_data.get('existing_conditions', [])
            medications = patient_data.get('medications', [])
            
            st.write("**Automatikusan kitöltött adatok:**")
            st.write(f"• Tünetek: {', '.join(symptoms) if symptoms else 'Nincs'}")
            st.write(f"• Diagnózis: {diagnosis if diagnosis else 'Nincs'}")
            st.write(f"• Betegségek: {', '.join(existing_conditions) if existing_conditions else 'Nincs'}")
            st.write(f"• Gyógyszerek: {', '.join(medications) if medications else 'Nincs'}")
            
            submitted = st.form_submit_button("✅ Adatok megerősítése")
        
        if submitted:
            if not all([name, phone, email]):
                st.error("Kérjük töltse ki az összes kötelező mezőt!")
                return None
            
            patient_info = PatientInfo(
                name=name,
                age=age,
                gender=gender,
                phone=phone,
                email=email,
                symptoms=symptoms,
                diagnosis=diagnosis,
                medical_history=existing_conditions,
                medications=medications
            )
            
            return patient_info
        
        return None