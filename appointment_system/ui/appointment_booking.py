# =============================================================================
# appointment_system/ui/appointment_booking.py - MINIMÁLIS JAVÍTÁS
# =============================================================================
"""
Időpont foglalás UI komponens - MINIMÁLIS JAVÍTÁS
"""
import streamlit as st
from datetime import datetime, timedelta, date, time
from typing import List, Optional
from ..models.doctor import Doctor
from ..models.appointment import Appointment, AppointmentStatus, PatientInfo
from ..logic.appointment_logic import AppointmentManager  # ← MEGTARTVA

class AppointmentBookingUI:
    """Időpont foglalás UI komponens - MINIMÁLIS JAVÍTÁS"""
    
    def __init__(self):
        self.appointment_manager = AppointmentManager()  # ← MEGTARTVA
    
    def display_appointment_booking(self, doctor: Doctor, 
                                  patient_data: dict) -> Optional[Appointment]:
        """
        Időpont foglalás UI megjelenítése - MINIMÁLIS JAVÍTÁS
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
        
        # ✅ JAVÍTOTT: Session state alapú foglalás megerősítése
        appointment = self._display_booking_confirmation_fixed(
            doctor, selected_datetime, patient_info
        )
        
        return appointment
    
    def _display_booking_confirmation_fixed(self, doctor: Doctor, 
                                          selected_datetime: datetime,
                                          patient_info: PatientInfo) -> Optional[Appointment]:
        """✅ JAVÍTOTT: Session state alapú foglalás megerősítése"""
        
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
        
        # ✅ JAVÍTÁS: Session state alapú gomb kezelés
        if 'booking_confirmed' not in st.session_state:
            st.session_state.booking_confirmed = False
        
        # Megerősítés gomb - EGYSZERŰSÍTETT
        if st.button("🎯 Időpont foglalása", type="primary", key="confirm_booking"):
            print("🎯 Időpont foglalása gomb megnyomva")
            
            # ✅ Session state inicializálás, ha nem létezik
            if 'appointment_data' not in st.session_state:
                st.session_state.appointment_data = {}
            
            with st.spinner("Foglalás feldolgozása..."):
                booking_result = self.appointment_manager.book_appointment(
                    doctor_id=doctor.id,
                    appointment_datetime=selected_datetime,
                    patient_info=patient_info,
                    notes=f"Automatikus foglalás a medical chatbot rendszerből."
                )
            
            if booking_result['success']:
                appointment = booking_result['appointment']
                
                # ✅ JAVÍTÁS: Konzisztens session state frissítés
                st.session_state.appointment_data = {
                    "selected_doctor": doctor,  # Doctor objektum
                    "selected_datetime": selected_datetime,
                    "appointment": appointment,  # Appointment objektum
                    "booking_status": "confirmed"
                }
                
                # ✅ JAVÍTOTT: st.rerun() helyett session state alapú megjelenítés
                st.session_state.booking_success = True
                st.session_state.successful_appointment = appointment
                
                # Azonnali sikeres foglalás üzenet
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
        
        # ✅ JAVÍTOTT: Sikeres foglalás megjelenítése session state alapján
        if st.session_state.get('booking_success', False):
            appointment = st.session_state.get('successful_appointment')
            if appointment:
                st.balloons()
                st.success(f"""
                # 🎉 FOGLALÁS SIKERESEN MENTVE!
                
                **Referencia:** {appointment.reference_number}
                **Státusz:** Megerősítve
                
                Az appointment sikeresen elmentésre került!
                """)
                
                # Új foglalás gomb
                if st.button("🔄 Új foglalás indítása"):
                    # Session state tisztítása
                    st.session_state.booking_confirmed = False
                    st.session_state.booking_success = False
                    if 'successful_appointment' in st.session_state:
                        del st.session_state.successful_appointment
                    # ✅ JAVÍTOTT: st.rerun() használata
                    st.rerun()
        
        return None
    
    # ✅ JAVÍTOTT: Session state alapú dátum kiválasztás
    def _display_date_selection(self, doctor: Doctor) -> Optional[date]:
        """Dátum kiválasztás - SESSION STATE JAVÍTÁSSAL"""
        st.markdown("#### 📆 Dátum kiválasztás")
        
        today = date.today()
        max_date = today + timedelta(days=30)
        
        available_days = [wh.day for wh in doctor.working_hours]
        
        # ✅ JAVÍTOTT: Session state kulcs használat
        selected_date = st.date_input(
            "Válasszon dátumot:",
            min_value=today,
            max_value=max_date,
            value=today,
            key=f"appointment_date_{doctor.id}"  # ✅ Egyedi kulcs
        )
        
        weekday = selected_date.strftime("%A").lower()
        
        if weekday not in available_days:
            st.error(f"Dr. {doctor.name} nem rendel ezen a napon. Válasszon másik dátumot.")
            return None
        
        return selected_date
    
    # ✅ JAVÍTOTT: Session state alapú idő kiválasztás
    def _display_time_selection(self, doctor: Doctor, selected_date: date) -> Optional[time]:
        """Időpont kiválasztás - SESSION STATE JAVÍTÁSSAL"""
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
        
        # ✅ JAVÍTOTT: Session state kulcs használat
        selected_time_str = st.selectbox(
            "Válasszon időpontot:",
            options=time_options,
            key=f"appointment_time_{doctor.id}_{selected_date}"  # ✅ Egyedi kulcs
        )
        
        hour, minute = map(int, selected_time_str.split(':'))
        selected_time = time(hour, minute)
        
        return selected_time
    
    # ✅ JAVÍTOTT: Form submit kezelés
    def _display_patient_info_form(self, patient_data: dict) -> Optional[PatientInfo]:
        """Páciens adatok kiegészítése - FORM SUBMIT JAVÍTÁSSAL"""
        st.markdown("#### 👤 Páciens Adatok")
        
        # ✅ JAVÍTOTT: Egyetlen form minden adattal
        with st.form("patient_info_form", clear_on_submit=False):
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
            
            # ✅ JAVÍTOTT: Egyetlen submit gomb
            submitted = st.form_submit_button("✅ Adatok megerősítése", type="primary")
        
        # ✅ JAVÍTOTT: Form submit kezelés session state-tel
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
            
            # ✅ Session state-be mentés
            st.session_state.patient_form_submitted = True
            st.session_state.patient_info_data = patient_info
            
            return patient_info
        
        # ✅ Session state alapú visszaadás
        if st.session_state.get('patient_form_submitted', False):
            return st.session_state.get('patient_info_data')
        
        return None
    
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