# =============================================================================
# appointment_system/ui/calendar_widget.py
# =============================================================================
"""
Naptár widget az időpont kiválasztáshoz
"""
import streamlit as st
from datetime import datetime, date, timedelta
from typing import List, Optional
from ..models.doctor import Doctor
from ..logic.availability_checker import AvailabilityChecker

class CalendarWidget:
    """Naptár widget az időpont foglaláshoz"""
    
    def __init__(self):
        self.availability_checker = AvailabilityChecker()
    
    def display_calendar(self, doctor: Doctor, selected_date: Optional[date] = None) -> Optional[date]:
        """
        Naptár megjelenítése
        
        Args:
            doctor: Orvos
            selected_date: Előre kiválasztott dátum
            
        Returns:
            Optional[date]: Kiválasztott dátum
        """
        st.markdown("#### 📅 Dátum Kiválasztás")
        
        # Dátum tartomány
        today = date.today()
        max_date = today + timedelta(days=60)  # 2 hónap előre
        
        # Dátum picker
        if selected_date is None:
            selected_date = today
        
        # Hét napok generálása
        week_days = self._get_week_days(selected_date)
        
        # Hetek megjelenítése
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if st.button("⬅️ Előző hét"):
                selected_date = selected_date - timedelta(days=7)
                st.rerun()
        
        with col2:
            st.markdown(f"**{selected_date.strftime('%Y. %B')}**")
        
        with col3:
            if st.button("➡️ Következő hét"):
                selected_date = selected_date + timedelta(days=7)
                st.rerun()
        
        # Naptár rács
        final_date = self._display_calendar_grid(doctor, week_days)
        
        return final_date
    
    def _get_week_days(self, selected_date: date) -> List[date]:
        """Hét napjainak generálása"""
        # Hét kezdete (hétfő)
        days_since_monday = selected_date.weekday()
        week_start = selected_date - timedelta(days=days_since_monday)
        
        return [week_start + timedelta(days=i) for i in range(7)]
    
    def _display_calendar_grid(self, doctor: Doctor, week_days: List[date]) -> Optional[date]:
        """Naptár rács megjelenítése"""
        
        # Fejléc
        day_names = ["Hétfő", "Kedd", "Szerda", "Csütörtök", "Péntek", "Szombat", "Vasárnap"]
        cols = st.columns(7)
        
        for i, day_name in enumerate(day_names):
            with cols[i]:
                st.markdown(f"**{day_name}**")
        
        # Dátumok
        cols = st.columns(7)
        selected_date = None
        
        for i, day_date in enumerate(week_days):
            with cols[i]:
                # Elérhetőség ellenőrzése
                is_available = self._is_date_available(doctor, day_date)
                available_slots = self.availability_checker.get_available_slots(doctor, day_date)
                
                # Gomb stílusa
                if day_date < date.today():
                    # Múltbeli dátum
                    st.markdown(f"~~{day_date.day}~~")
                elif is_available and available_slots:
                    # Elérhető dátum
                    if st.button(f"✅ {day_date.day}", key=f"date_{day_date.isoformat()}"):
                        selected_date = day_date
                    st.caption(f"{len(available_slots)} szabad")
                elif is_available:
                    # Munkanap, de nincs szabad időpont
                    st.markdown(f"🚫 {day_date.day}")
                    st.caption("Betelt")
                else:
                    # Nem munkanap
                    st.markdown(f"⭕ {day_date.day}")
                    st.caption("Zárva")
        
        return selected_date
    
    def _is_date_available(self, doctor: Doctor, check_date: date) -> bool:
        """Dátum elérhetőségének ellenőrzése"""
        # Múltbeli dátum
        if check_date < date.today():
            return False
        
        # Munkaidő ellenőrzése
        weekday = check_date.strftime("%A").lower()
        working_hours = doctor.get_working_hours_for_day(weekday)
        
        return working_hours is not None
    
    def display_time_slots(self, doctor: Doctor, selected_date: date) -> Optional[str]:
        """
        Időpontok megjelenítése egy adott napra
        
        Args:
            doctor: Orvos
            selected_date: Kiválasztott dátum
            
        Returns:
            Optional[str]: Kiválasztott időpont string formátumban
        """
        st.markdown(f"#### 🕐 Elérhető Időpontok - {selected_date.strftime('%Y. %m. %d.')}")
        
        # Szabad időpontok lekérése
        available_slots = self.availability_checker.get_available_slots(doctor, selected_date)
        
        if not available_slots:
            st.warning("Nincs elérhető időpont erre a napra.")
            return None
        
        # Időpontok csoportosítása (délelőtt/délután)
        morning_slots = [slot for slot in available_slots if slot.hour < 12]
        afternoon_slots = [slot for slot in available_slots if slot.hour >= 12]
        
        selected_time = None
        
        if morning_slots:
            st.markdown("**🌅 Délelőtti időpontok:**")
            cols = st.columns(min(len(morning_slots), 4))
            for i, slot in enumerate(morning_slots):
                with cols[i % 4]:
                    if st.button(slot.strftime("%H:%M"), key=f"morning_{slot}"):
                        selected_time = slot.strftime("%H:%M")
        
        if afternoon_slots:
            st.markdown("**🌇 Délutáni időpontok:**")
            cols = st.columns(min(len(afternoon_slots), 4))
            for i, slot in enumerate(afternoon_slots):
                with cols[i % 4]:
                    if st.button(slot.strftime("%H:%M"), key=f"afternoon_{slot}"):
                        selected_time = slot.strftime("%H:%M")
        
        return selected_time