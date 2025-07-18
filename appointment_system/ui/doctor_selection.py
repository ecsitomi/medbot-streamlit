# =============================================================================
# appointment_system/ui/doctor_selection.py
# =============================================================================
"""
Orvos kiválasztás UI komponens
"""
import streamlit as st
from typing import List, Optional, Tuple
from ..models.doctor import Doctor
from ..logic.specialist_matcher import SpecialistMatcher

class DoctorSelectionUI:
    """Orvos kiválasztás UI komponens"""
    
    def __init__(self):
        self.matcher = SpecialistMatcher()
    
    def display_doctor_selection(self, gpt_specialist_advice: str, 
                               diagnosis: str, 
                               symptoms: List[str]) -> Optional[Doctor]:
        """
        Orvos kiválasztás UI megjelenítése
        
        Args:
            gpt_specialist_advice: GPT által javasolt szakorvos
            diagnosis: Diagnózis
            symptoms: Tünetek listája
            
        Returns:
            Optional[Doctor]: Kiválasztott orvos
        """
        st.markdown("### 👨‍⚕️ Ajánlott Orvosok")
        
        # Orvos matching
        with st.spinner("Ajánlott orvosok keresése..."):
            matches = self.matcher.match_specialists(gpt_specialist_advice, diagnosis, symptoms)
        
        if not matches:
            st.warning("Nem találtunk megfelelő orvost a tünetek alapján.")
            return None
        
        # GPT tanács megjelenítése
        if gpt_specialist_advice:
            st.info(f"**AI javaslat:** {gpt_specialist_advice}")
        
        # Orvos kiválasztás
        selected_doctor = self._display_doctor_cards(matches)
        
        return selected_doctor
    
    def _display_doctor_cards(self, matches: List[Tuple[Doctor, float]]) -> Optional[Doctor]:
        """Orvos kártyák megjelenítése"""
        
        # Kiválasztás rádió gombokkal
        doctor_options = []
        for doctor, score in matches:
            display_text = f"**{doctor.get_display_name()}** - {doctor.get_specialization_hu()}"
            doctor_options.append((display_text, doctor, score))
        
        if not doctor_options:
            return None
        
        # Rádió gomb választás
        selected_option = st.radio(
            "Válasszon orvost:",
            options=range(len(doctor_options)),
            format_func=lambda i: doctor_options[i][0],
            key="doctor_selection"
        )
        
        selected_doctor = doctor_options[selected_option][1]
        
        # Kiválasztott orvos részletes információi
        self._display_doctor_details(selected_doctor)
        
        return selected_doctor
    
    def _display_doctor_details(self, doctor: Doctor):
        """Orvos részletes információinak megjelenítése"""
        
        with st.expander(f"📋 {doctor.get_display_name()} részletes adatai", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Szakspecializáció:** {doctor.get_specialization_hu()}")
                st.write(f"**Cím:** {doctor.address}")
                st.write(f"**Telefon:** {doctor.phone}")
                st.write(f"**Email:** {doctor.email}")
                
                # Értékelés csillagokkal
                stars = "⭐" * int(doctor.rating)
                st.write(f"**Értékelés:** {stars} ({doctor.rating}/5)")
            
            with col2:
                st.write(f"**Helyszín:** {doctor.location}")
                st.write(f"**Rendelési idő:** {doctor.appointment_duration} perc")
                st.write(f"**Nyelvek:** {', '.join(doctor.languages)}")
                
                # Munkaidő
                if doctor.working_hours:
                    st.write("**Munkaidő:**")
                    for wh in doctor.working_hours:
                        day_hu = self._get_day_name_hu(wh.day)
                        time_str = f"{wh.start_time.strftime('%H:%M')} - {wh.end_time.strftime('%H:%M')}"
                        st.write(f"• {day_hu}: {time_str}")
            
            # Leírás
            if doctor.description:
                st.write("**Leírás:**")
                st.write(doctor.description)
    
    def _get_day_name_hu(self, day: str) -> str:
        """Napnév fordítása magyarra"""
        day_names = {
            'monday': 'Hétfő',
            'tuesday': 'Kedd',
            'wednesday': 'Szerda',
            'thursday': 'Csütörtök', 
            'friday': 'Péntek',
            'saturday': 'Szombat',
            'sunday': 'Vasárnap'
        }
        return day_names.get(day.lower(), day)