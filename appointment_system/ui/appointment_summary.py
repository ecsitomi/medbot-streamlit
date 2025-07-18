# =============================================================================
# appointment_system/ui/appointment_summary.py
# =============================================================================
"""
Foglalás összegző komponens
"""
import streamlit as st
from datetime import datetime
from typing import Optional
from ..models.doctor import Doctor
from ..models.appointment import Appointment

class AppointmentSummaryUI:
    """Foglalás összegző UI komponens"""
    
    def display_appointment_summary(self, appointment: Appointment, doctor: Doctor):
        """
        Foglalás összegzőjének megjelenítése
        
        Args:
            appointment: Foglalás
            doctor: Orvos
        """
        st.markdown("### 📋 Foglalás Összegzője")
        
        # Sikeres foglalás banner
        st.success("🎉 Sikeres időpont foglalás!")
        
        # Foglalás részletei
        with st.container():
            st.markdown("#### 📝 Foglalás Részletei")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Alapadatok:**")
                st.write(f"🆔 **Referencia szám:** {appointment.reference_number}")
                st.write(f"📅 **Dátum:** {appointment.datetime.strftime('%Y. %m. %d.')}")
                st.write(f"🕐 **Időpont:** {appointment.datetime.strftime('%H:%M')}")
                st.write(f"⏱️ **Időtartam:** {appointment.duration_minutes} perc")
                st.write(f"📊 **Státusz:** {appointment.get_status_hu()}")
            
            with col2:
                st.markdown("**Orvos adatai:**")
                st.write(f"👨‍⚕️ **Orvos:** {doctor.get_display_name()}")
                st.write(f"🏥 **Szakorvos:** {doctor.get_specialization_hu()}")
                st.write(f"📞 **Telefon:** {doctor.phone}")
                st.write(f"📧 **Email:** {doctor.email}")
                st.write(f"📍 **Cím:** {doctor.address}")
        
        # Páciens adatok
        with st.expander("👤 Páciens Adatok", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Név:** {appointment.patient_info.name}")
                st.write(f"**Életkor:** {appointment.patient_info.age} év")
                st.write(f"**Nem:** {appointment.patient_info.gender}")
            
            with col2:
                st.write(f"**Telefon:** {appointment.patient_info.phone}")
                st.write(f"**Email:** {appointment.patient_info.email}")
            
            # Orvosi adatok
            if appointment.patient_info.symptoms:
                st.write(f"**Tünetek:** {', '.join(appointment.patient_info.symptoms)}")
            
            if appointment.patient_info.diagnosis:
                st.write(f"**Diagnózis:** {appointment.patient_info.diagnosis}")
            
            if appointment.patient_info.medical_history:
                st.write(f"**Kórtörténet:** {', '.join(appointment.patient_info.medical_history)}")
            
            if appointment.patient_info.medications:
                st.write(f"**Gyógyszerek:** {', '.join(appointment.patient_info.medications)}")
        
        # Fontos információk
        self._display_important_info(appointment, doctor)
        
        # Akciógombok
        self._display_action_buttons(appointment, doctor)
    
    def _display_important_info(self, appointment: Appointment, doctor: Doctor):
        """Fontos információk megjelenítése"""
        st.markdown("#### ⚠️ Fontos Információk")
        
        st.info(f"""
        **Rendelés előtt:**
        • Érkezzen 10 perccel korábban
        • Hozza magával a személyi igazolványát
        • Hozza magával a TAJ kártyáját
        • Hozza magával a korábbi leleteit (ha vannak)
        
        **Kapcsolat:**
        • Rendelő telefon: {doctor.phone}
        • Email: {doctor.email}
        • Cím: {doctor.address}
        
        **Lemondás/Módosítás:**
        • Legalább 24 órával a rendelés előtt
        • Referencia szám: {appointment.reference_number}
        """)
    
    def _display_action_buttons(self, appointment: Appointment, doctor: Doctor):
        """Akciógombok megjelenítése"""
        st.markdown("#### 🎯 Műveletek")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📧 Email megerősítés", type="secondary"):
                self._send_email_confirmation(appointment, doctor)
        
        with col2:
            if st.button("📱 SMS emlékeztető", type="secondary"):
                self._send_sms_reminder(appointment, doctor)
        
        with col3:
            if st.button("🗓️ Naptárba", type="secondary"):
                self._add_to_calendar(appointment, doctor)
    
    def _send_email_confirmation(self, appointment: Appointment, doctor: Doctor):
        """Email megerősítés küldése (szimuláció)"""
        st.success(f"✅ Email megerősítés elküldve a {appointment.patient_info.email} címre!")
        
        # Email tartalom preview
        with st.expander("📧 Email előnézet"):
            st.markdown(f"""
            **Tárgy:** Időpont foglalás megerősítése - {appointment.reference_number}
            
            Kedves {appointment.patient_info.name}!
            
            Megerősítjük az időpont foglalását:
            
            **Orvos:** {doctor.get_display_name()} - {doctor.get_specialization_hu()}
            **Időpont:** {appointment.get_formatted_datetime()}
            **Helyszín:** {doctor.address}
            **Referencia:** {appointment.reference_number}
            
            Kérjük, érkezzen 10 perccel korábban!
            
            Üdvözlettel,
            Medical Chatbot Team
            """)
    
    def _send_sms_reminder(self, appointment: Appointment, doctor: Doctor):
        """SMS emlékeztető küldése (szimuláció)"""
        st.success(f"✅ SMS emlékeztető elküldve a {appointment.patient_info.phone} számra!")
        
        # SMS tartalom preview
        with st.expander("📱 SMS előnézet"):
            st.markdown(f"""
            **SMS tartalom:**
            
            Időpont emlékeztető: {appointment.get_formatted_datetime()}
            Dr. {doctor.name} - {doctor.get_specialization_hu()}
            {doctor.address}
            Ref: {appointment.reference_number}
            """)
    
    def _add_to_calendar(self, appointment: Appointment, doctor: Doctor):
        """Naptár esemény létrehozása"""
        st.success("✅ Naptár esemény létrehozva!")
        
        # ICS file generálás (egyszerűsített)
        ics_content = self._generate_ics_content(appointment, doctor)
        
        st.download_button(
            label="📥 .ics fájl letöltése",
            data=ics_content,
            file_name=f"appointment_{appointment.reference_number}.ics",
            mime="text/calendar"
        )
    
    def _generate_ics_content(self, appointment: Appointment, doctor: Doctor) -> str:
        """ICS naptár fájl generálása"""
        start_time = appointment.datetime.strftime("%Y%m%dT%H%M%S")
        end_time = appointment.get_end_datetime().strftime("%Y%m%dT%H%M%S")
        
        ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Medical Chatbot//Appointment//EN
BEGIN:VEVENT
UID:{appointment.reference_number}@medicalchatbot.com
DTSTART:{start_time}
DTEND:{end_time}
SUMMARY:Orvosi rendelés - {doctor.get_display_name()}
DESCRIPTION:Orvosi rendelés\\n{doctor.get_specialization_hu()}\\nReferencia: {appointment.reference_number}
LOCATION:{doctor.address}
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR"""
        
        return ics_content