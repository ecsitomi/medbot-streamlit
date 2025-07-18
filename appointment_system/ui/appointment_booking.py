# =============================================================================
# appointment_system/ui/appointment_booking.py
# =============================================================================
"""
Időpont foglalás UI komponens
"""
import streamlit as st
from datetime import datetime, timedelta, date, time
from typing import List, Optional
from ..models.doctor import Doctor
from ..models.appointment import Appointment, AppointmentStatus, PatientInfo

class AppointmentBookingUI:
    """Időpont foglalás UI komponens"""
    
    def display_appointment_booking(self, doctor: Doctor, 
                                  patient_data: dict) -> Optional[Appointment]:
        """
        Időpont foglalás UI megjelenítése
        
        Args:
            doctor: Kiválasztott orvos
            patient_data: Páciens adatok
            
        Returns:
            Optional[Appointment]: Létrehozott időpont
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
        
        # Foglalás megerősítése
        appointment = self._display_booking_confirmation(
            doctor, selected_datetime, patient_info
        )
        
        return appointment
    
    def _display_date_selection(self, doctor: Doctor) -> Optional[date]:
        """Dátum kiválasztás"""
        
        st.markdown("#### 📆 Dátum kiválasztás")
        
        # Következő 30 nap
        today = date.today()
        max_date = today + timedelta(days=30)
        
        # Elérhető napok az orvos munkaideje alapján
        available_days = [wh.day for wh in doctor.working_hours]
        
        # Dátum input
        selected_date = st.date_input(
            "Válasszon dátumot:",
            min_value=today,
            max_value=max_date,
            value=today,
            key="appointment_date"
        )
        
        # Ellenőrzés, hogy dolgozik-e az orvos aznap
        weekday = selected_date.strftime("%A").lower()
        
        if weekday not in available_days:
            st.error(f"Dr. {doctor.name} nem rendel ezen a napon. Válasszon másik dátumot.")
            return None
        
        return selected_date
    
    def _display_time_selection(self, doctor: Doctor, selected_date: date) -> Optional[time]:
        """Időpont kiválasztás"""
        
        st.markdown("#### 🕐 Időpont kiválasztás")
        
        # Munkaidő lekérése
        weekday = selected_date.strftime("%A").lower()
        working_hours = doctor.get_working_hours_for_day(weekday)
        
        if not working_hours:
            st.error("Nincs munkaidő információ erre a napra.")
            return None
        
        # Elérhető időpontok generálása
        available_times = self._generate_available_times(doctor, working_hours)
        
        if not available_times:
            st.error("Nincs elérhető időpont erre a napra.")
            return None
        
        # Időpont kiválasztás
        time_options = [t.strftime("%H:%M") for t in available_times]
        
        selected_time_str = st.selectbox(
            "Válasszon időpontot:",
            options=time_options,
            key="appointment_time"
        )
        
        # String to time konverzió
        hour, minute = map(int, selected_time_str.split(':'))
        selected_time = time(hour, minute)
        
        return selected_time
    
    def _generate_available_times(self, doctor: Doctor, working_hours) -> List[time]:
        """Elérhető időpontok generálása"""
        
        times = []
        duration = doctor.appointment_duration
        
        # Kezdő és befejező idő
        start_time = working_hours.start_time
        end_time = working_hours.end_time
        
        # Szünet ideje
        break_start = working_hours.break_start
        break_end = working_hours.break_end
        
        # Időpontok generálása
        current_time = start_time
        
        while current_time < end_time:
            # Ellenőrzés, hogy van-e elég idő a rendelésre
            appointment_end = datetime.combine(date.today(), current_time) + timedelta(minutes=duration)
            appointment_end_time = appointment_end.time()
            
            if appointment_end_time > end_time:
                break
            
            # Szünet ellenőrzése
            if break_start and break_end:
                if not (current_time >= break_start and current_time < break_end):
                    times.append(current_time)
            else:
                times.append(current_time)
            
            # Következő időpont
            next_time = datetime.combine(date.today(), current_time) + timedelta(minutes=duration)
            current_time = next_time.time()
        
        return times
    
    def _display_patient_info_form(self, patient_data: dict) -> Optional[PatientInfo]:
        """Páciens adatok kiegészítése"""
        
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
            
            # Automatikusan kitöltött mezők
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
            # Validáció
            if not all([name, phone, email]):
                st.error("Kérjük töltse ki az összes kötelező mezőt!")
                return None
            
            # PatientInfo objektum létrehozása
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
    
    def _display_booking_confirmation(self, doctor: Doctor, 
                                    selected_datetime: datetime,
                                    patient_info: PatientInfo) -> Optional[Appointment]:
        """Foglalás megerősítése"""
        
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
            # Appointment létrehozása
            appointment = Appointment(
                id=f"apt_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                doctor_id=doctor.id,
                patient_info=patient_info,
                datetime=selected_datetime,
                duration_minutes=doctor.appointment_duration,
                status=AppointmentStatus.PENDING,
                notes=f"Automatikus foglalás a medical chatbot rendszerből."
            )
            
            # Session state-be mentés
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
            
            return appointment
        
        return None