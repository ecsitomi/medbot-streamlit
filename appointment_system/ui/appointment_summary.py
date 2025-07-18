# =============================================================================
# appointment_system/ui/appointment_summary.py - JAVÍTOTT VERZIÓ
# =============================================================================
"""
Foglalás összegző komponens - JAVÍTOTT ICS generálással
"""
import streamlit as st
from datetime import datetime
from typing import Optional
from ..models.doctor import Doctor
from ..models.appointment import Appointment

class AppointmentSummaryUI:
    """Foglalás összegző UI komponens - JAVÍTOTT VERZIÓ"""
    
    def display_appointment_summary(self, appointment: Appointment, doctor: Doctor):
        """Foglalás összegzőjének megjelenítése - JAVÍTOTT VERZIÓ"""
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
        
        # Akciógombok - JAVÍTOTT VERZIÓ
        self._display_action_buttons_fixed(appointment, doctor)
    
    def _display_important_info(self, appointment: Appointment, doctor: Doctor):
        """Fontos információk megjelenítése - VÁLTOZATLAN"""
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
    
    def _display_action_buttons_fixed(self, appointment: Appointment, doctor: Doctor):
        """JAVÍTOTT akciógombok ICS letöltéssel"""
        st.markdown("#### 🎯 Műveletek")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📧 Email megerősítés", type="secondary"):
                self._send_email_confirmation(appointment, doctor)
        
        with col2:
            if st.button("📱 SMS emlékeztető", type="secondary"):
                self._send_sms_reminder(appointment, doctor)
        
        with col3:
            # ✅ JAVÍTOTT ICS letöltés
            ics_content = self._generate_ics_content_fixed(appointment, doctor)
            
            st.download_button(
                label="🗓️ Naptárba (.ics)",
                data=ics_content.encode('utf-8'),
                file_name=f"appointment_{appointment.reference_number}.ics",
                mime="text/calendar",
                type="secondary"
            )
    
    def _generate_ics_content_fixed(self, appointment: Appointment, doctor: Doctor) -> str:
        """JAVÍTOTT ICS naptár fájl generálása"""
        
        # ✅ Időzóna kezelés és proper formátum
        import uuid
        from datetime import timezone
        
        # UTC időpontra konvertálás (Budapest = UTC+1/+2)
        start_dt = appointment.datetime
        end_dt = appointment.get_end_datetime()
        
        # YYYYMMDDTHHMMSS formátum
        start_time = start_dt.strftime("%Y%m%dT%H%M%S")
        end_time = end_dt.strftime("%Y%m%dT%H%M%S")
        
        # Egyedi UID generálása
        uid = str(uuid.uuid4())
        
        # ✅ Proper ICS formátum
        ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Medical Chatbot//Appointment System//HU
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VEVENT
UID:{uid}@medicalchatbot.hu
DTSTART:{start_time}
DTEND:{end_time}
DTSTAMP:{datetime.now().strftime("%Y%m%dT%H%M%S")}
SUMMARY:Orvosi rendelés - {doctor.get_display_name()}
DESCRIPTION:Orvosi rendelés\\n\\nOrvos: {doctor.get_display_name()}\\nSzakorvos: {doctor.get_specialization_hu()}\\nPáciens: {appointment.patient_info.name}\\nReferencia: {appointment.reference_number}\\n\\nTünetek: {', '.join(appointment.patient_info.symptoms) if appointment.patient_info.symptoms else 'Nincs'}\\n\\nMegjegyzés: {appointment.notes}
LOCATION:{doctor.address}
ORGANIZER;CN={doctor.get_display_name()}:MAILTO:{doctor.email}
ATTENDEE;CN={appointment.patient_info.name}:MAILTO:{appointment.patient_info.email}
STATUS:CONFIRMED
SEQUENCE:0
PRIORITY:5
CLASS:PRIVATE
TRANSP:OPAQUE
BEGIN:VALARM
TRIGGER:-PT15M
ACTION:DISPLAY
DESCRIPTION:Emlékeztető: Orvosi rendelés 15 perc múlva
END:VALARM
END:VEVENT
END:VCALENDAR"""
        
        return ics_content
    
    # Többi metódus változatlan...
    def _send_email_confirmation(self, appointment: Appointment, doctor: Doctor):
        """Email megerősítés küldése (szimuláció) - VÁLTOZATLAN"""
        st.success(f"✅ Email megerősítés elküldve a {appointment.patient_info.email} címre!")
        
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
        """SMS emlékeztető küldése (szimuláció) - VÁLTOZATLAN"""
        st.success(f"✅ SMS emlékeztető elküldve a {appointment.patient_info.phone} számra!")
        
        with st.expander("📱 SMS előnézet"):
            st.markdown(f"""
            **SMS tartalom:**
            
            Időpont emlékeztető: {appointment.get_formatted_datetime()}
            Dr. {doctor.name} - {doctor.get_specialization_hu()}
            {doctor.address}
            Ref: {appointment.reference_number}
            """)
    
    def _add_to_calendar(self, appointment: Appointment, doctor: Doctor):
        """DEPRECATED - használd a _display_action_buttons_fixed-et"""
        pass