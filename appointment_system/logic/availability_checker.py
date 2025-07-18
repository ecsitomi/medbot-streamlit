# =============================================================================
# appointment_system/logic/availability_checker.py - JAVÍTOTT VERZIÓ
# =============================================================================
"""
Szabad időpontok ellenőrzése és generálása - JAVÍTOTT VERZIÓ
"""
import streamlit as st
from datetime import datetime, timedelta, date, time
from typing import List, Dict, Optional
from ..models.doctor import Doctor
from ..models.appointment import Appointment

class AvailabilityChecker:
    """Szabad időpontok ellenőrzése - JAVÍTOTT VERZIÓ"""
    
    def __init__(self):
        self.booked_appointments: Dict[str, List[Appointment]] = {}
        self._initialize_sample_bookings()
    
    def _initialize_sample_bookings(self):
        """JAVÍTOTT: Minta foglalások létrehozása (szimuláció)"""
        # Néhány random foglalás létrehozása a realisztikusság érdekében
        from ..models.appointment import PatientInfo, AppointmentStatus
        
        sample_bookings = [
            # Dr. Kovács János foglalásai
            {
                "doctor_id": "doc_001",
                "appointment_datetime": datetime(2024, 1, 15, 10, 0),  # ✅ JAVÍTVA: datetime-ról appointment_datetime-ra
                "patient_name": "Minta Páciens"
            },
            {
                "doctor_id": "doc_001", 
                "appointment_datetime": datetime(2024, 1, 15, 14, 30),  # ✅ JAVÍTVA
                "patient_name": "Teszt Páciens"
            },
            # Dr. Nagy Éva foglalásai
            {
                "doctor_id": "doc_002",
                "appointment_datetime": datetime(2024, 1, 16, 11, 0),  # ✅ JAVÍTVA
                "patient_name": "Próba Páciens"
            }
        ]
        
        for booking in sample_bookings:
            patient_info = PatientInfo(
                name=booking["patient_name"],
                age=35,
                gender="férfi",
                phone="+36 30 123 4567",
                email="test@example.com"
            )
            
            # ✅ JAVÍTVA: datetime field név használata
            appointment = Appointment(
                id=f"sample_{booking['doctor_id']}_{booking['appointment_datetime'].strftime('%Y%m%d%H%M')}",
                doctor_id=booking["doctor_id"],
                patient_info=patient_info,
                datetime=booking["appointment_datetime"],  # ✅ JAVÍTVA: datetime field név
                duration_minutes=30,
                status=AppointmentStatus.CONFIRMED
            )
            
            if booking["doctor_id"] not in self.booked_appointments:
                self.booked_appointments[booking["doctor_id"]] = []
            self.booked_appointments[booking["doctor_id"]].append(appointment)
    
    def get_available_slots(self, doctor: Doctor, selected_date: date) -> List[time]:
        """
        Szabad időpontok lekérése egy adott napra - VÁLTOZATLAN
        """
        # Munkaidő lekérése
        weekday = selected_date.strftime("%A").lower()
        working_hours = doctor.get_working_hours_for_day(weekday)
        
        if not working_hours:
            return []
        
        # Összes lehetséges időpont generálása
        all_slots = self._generate_all_slots(doctor, working_hours)
        
        # Foglalt időpontok lekérése
        booked_slots = self._get_booked_slots(doctor.id, selected_date)
        
        # Szabad időpontok szűrése
        available_slots = [
            slot for slot in all_slots 
            if slot not in booked_slots and self._is_slot_available(slot, selected_date)
        ]
        
        return available_slots
    
    def _generate_all_slots(self, doctor: Doctor, working_hours) -> List[time]:
        """Összes lehetséges időpont generálása - VÁLTOZATLAN"""
        slots = []
        duration = doctor.appointment_duration
        
        start_time = working_hours.start_time
        end_time = working_hours.end_time
        break_start = working_hours.break_start
        break_end = working_hours.break_end
        
        current_time = start_time
        
        while current_time < end_time:
            # Ellenőrizzük, hogy van-e elég idő
            appointment_end = datetime.combine(date.today(), current_time) + timedelta(minutes=duration)
            if appointment_end.time() > end_time:
                break
            
            # Szünet ellenőrzése
            if break_start and break_end:
                if not (current_time >= break_start and current_time < break_end):
                    slots.append(current_time)
            else:
                slots.append(current_time)
            
            # Következő slot
            next_slot = datetime.combine(date.today(), current_time) + timedelta(minutes=duration)
            current_time = next_slot.time()
        
        return slots
    
    def _get_booked_slots(self, doctor_id: str, selected_date: date) -> List[time]:
        """Foglalt időpontok lekérése - VÁLTOZATLAN"""
        booked_slots = []
        
        if doctor_id in self.booked_appointments:
            for appointment in self.booked_appointments[doctor_id]:
                if appointment.datetime.date() == selected_date:
                    booked_slots.append(appointment.datetime.time())
        
        return booked_slots
    
    def _is_slot_available(self, slot: time, selected_date: date) -> bool:
        """Időpont elérhetőségének ellenőrzése - VÁLTOZATLAN"""
        slot_datetime = datetime.combine(selected_date, slot)
        
        # Múltbeli időpontok nem elérhetők
        if slot_datetime < datetime.now():
            return False
        
        # Túl közeli időpontok (pl. 2 órán belül)
        if slot_datetime < datetime.now() + timedelta(hours=2):
            return False
        
        return True
    
    def book_appointment(self, appointment: Appointment) -> bool:
        """
        Időpont foglalása - VÁLTOZATLAN
        """
        doctor_id = appointment.doctor_id
        
        # Ellenőrizzük, hogy elérhető-e az időpont
        if not self._is_appointment_available(appointment):
            return False
        
        # Foglalás hozzáadása
        if doctor_id not in self.booked_appointments:
            self.booked_appointments[doctor_id] = []
        
        self.booked_appointments[doctor_id].append(appointment)
        return True
    
    def _is_appointment_available(self, appointment: Appointment) -> bool:
        """Foglalás elérhetőségének ellenőrzése - VÁLTOZATLAN"""
        doctor_id = appointment.doctor_id
        appointment_time = appointment.datetime.time()
        appointment_date = appointment.datetime.date()
        
        # Ellenőrizzük, hogy már foglalt-e
        if doctor_id in self.booked_appointments:
            for existing_appointment in self.booked_appointments[doctor_id]:
                if (existing_appointment.datetime.date() == appointment_date and 
                    existing_appointment.datetime.time() == appointment_time):
                    return False
        
        return True
    
    def get_doctor_schedule(self, doctor_id: str, start_date: date, end_date: date) -> Dict[str, List[Dict]]:
        """
        Orvos teljes programjának lekérése - VÁLTOZATLAN
        """
        schedule = {}
        
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.isoformat()
            schedule[date_str] = []
            
            # Foglalt időpontok
            if doctor_id in self.booked_appointments:
                for appointment in self.booked_appointments[doctor_id]:
                    if appointment.datetime.date() == current_date:
                        schedule[date_str].append({
                            "time": appointment.datetime.strftime("%H:%M"),
                            "type": "booked",
                            "patient": appointment.patient_info.name,
                            "status": appointment.status.value
                        })
            
            current_date += timedelta(days=1)
        
        return schedule