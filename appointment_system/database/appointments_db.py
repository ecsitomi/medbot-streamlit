# =============================================================================
# appointment_system/database/appointments_db.py - PERZISZTENS VERZIÓ
# =============================================================================
"""
Foglalások adatbázis kezelése PERZISZTENS TÁROLÁSSAL
"""
import streamlit as st
import json
import os
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
import sys

# Lokális importok javítása
try:
    from ..models.appointment import Appointment, AppointmentStatus, PatientInfo
    from ..models.doctor import Doctor
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from models.appointment import Appointment, AppointmentStatus, PatientInfo
    from models.doctor import Doctor

class AppointmentsDatabase:
    """Foglalások adatbázis kezelő PERZISZTENS TÁROLÁSSAL"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.appointments_file = os.path.join(data_dir, "appointments.json")
        self.appointments: Dict[str, Appointment] = {}
        self.appointments_by_doctor: Dict[str, List[str]] = {}
        self.appointments_by_patient: Dict[str, List[str]] = {}
        
        # Adatok betöltése
        self._ensure_data_directory()
        self._load_from_file()
        self._initialize_session_state()
    
    def _ensure_data_directory(self):
        """Data könyvtár létrehozása ha nem létezik"""
        os.makedirs(self.data_dir, exist_ok=True)
    
    def _load_from_file(self):
        """Adatok betöltése JSON fájlból"""
        if os.path.exists(self.appointments_file):
            try:
                with open(self.appointments_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # JSON-ból Appointment objektumok rekonstruálása
                for apt_id, apt_data in data.items():
                    try:
                        appointment = self._json_to_appointment(apt_data)
                        self.appointments[apt_id] = appointment
                        
                        # Indexek frissítése
                        self._update_doctor_index(appointment)
                        self._update_patient_index(appointment)
                        
                    except Exception as e:
                        print(f"Hiba az appointment betöltésében ({apt_id}): {e}")
                
                print(f"✅ Betöltve {len(self.appointments)} appointment a fájlból")
                
            except Exception as e:
                print(f"Hiba a JSON fájl betöltésében: {e}")
        else:
            print("📁 Új appointments.json fájl lesz létrehozva")
    
    def _json_to_appointment(self, data: Dict[str, Any]) -> Appointment:
        """JSON adat konvertálása Appointment objektummá - JAVÍTOTT VÉGLEGESEN"""
        
        # PatientInfo rekonstruálás
        patient_data = data.get('patient_info', {})
        patient_info = PatientInfo(
            name=patient_data.get('name', ''),
            age=patient_data.get('age', 0),
            gender=patient_data.get('gender', ''),
            phone=patient_data.get('phone', ''),
            email=patient_data.get('email', ''),
            symptoms=patient_data.get('symptoms', []),
            diagnosis=patient_data.get('diagnosis', ''),
            medical_history=patient_data.get('medical_history', []),
            medications=patient_data.get('medications', [])
        )
        
        # ✅ JAVÍTVA: datetime field név konzisztensen
        appointment = Appointment(
            id=data['id'],
            doctor_id=data['doctor_id'],
            patient_info=patient_info,
            datetime=datetime.fromisoformat(data['datetime']),  # ✅ datetime field
            duration_minutes=data['duration_minutes'],
            status=AppointmentStatus(data['status']),
            notes=data.get('notes', ''),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            reference_number=data.get('reference_number', '')
        )
    
        return appointment
    
    def _appointment_to_json(self, appointment: Appointment) -> Dict[str, Any]:
        """Appointment objektum konvertálása JSON-ba - JAVÍTOTT VÉGLEGESEN"""
        return {
            'id': appointment.id,
            'doctor_id': appointment.doctor_id,
            'patient_info': {
                'name': appointment.patient_info.name,
                'age': appointment.patient_info.age,
                'gender': appointment.patient_info.gender,
                'phone': appointment.patient_info.phone,
                'email': appointment.patient_info.email,
                'symptoms': appointment.patient_info.symptoms,
                'diagnosis': appointment.patient_info.diagnosis,
                'medical_history': appointment.patient_info.medical_history,
                'medications': appointment.patient_info.medications
            },
            'datetime': appointment.datetime.isoformat(),  # ✅ datetime field
            'duration_minutes': appointment.duration_minutes,
            'status': appointment.status.value,
            'notes': appointment.notes,
            'created_at': appointment.created_at.isoformat(),
            'updated_at': appointment.updated_at.isoformat(),
            'reference_number': appointment.reference_number
        }
    
    def _save_to_file(self):
        """Adatok mentése JSON fájlba"""
        try:
            # Appointments konvertálása JSON-ba
            appointments_data = {}
            for apt_id, appointment in self.appointments.items():
                appointments_data[apt_id] = self._appointment_to_json(appointment)
            
            # Fájlba írás
            with open(self.appointments_file, 'w', encoding='utf-8') as f:
                json.dump(appointments_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Elmentve {len(appointments_data)} appointment")
            
        except Exception as e:
            print(f"❌ Hiba a mentésben: {e}")
    
    def _initialize_session_state(self):
        """Session state inicializálása"""
        if 'appointments_db' not in st.session_state:
            st.session_state.appointments_db = {}
        
        # Session state szinkronizálása
        for apt_id, appointment in self.appointments.items():
            st.session_state.appointments_db[apt_id] = appointment
    
    def add_appointment(self, appointment: Appointment) -> bool:
        """Új foglalás hozzáadása AUTOMATIKUS MENTÉSSEL"""
        if appointment.id in self.appointments:
            return False
        
        # Időpont ütközés ellenőrzése
        if self._has_time_conflict(appointment):
            return False
        
        # Foglalás hozzáadása
        self.appointments[appointment.id] = appointment
        
        # Indexek frissítése
        self._update_doctor_index(appointment)
        self._update_patient_index(appointment)
        
        # Session state frissítése
        #st.session_state.appointments_db.add_appointment(appointment)

        
        # 🚀 AUTOMATIKUS MENTÉS
        self._save_to_file()
        
        print(f"✅ Új appointment hozzáadva és elmentve: {appointment.reference_number}")
        
        return True
    
    def update_appointment(self, appointment: Appointment) -> bool:
        """Foglalás frissítése AUTOMATIKUS MENTÉSSEL"""
        if appointment.id not in self.appointments:
            return False
        
        # Időpont ütközés ellenőrzése (csak ha változott az idő)
        old_appointment = self.appointments[appointment.id]
        if old_appointment.datetime != appointment.datetime:
            if self._has_time_conflict(appointment, exclude_id=appointment.id):
                return False
        
        # Frissítés
        self.appointments[appointment.id] = appointment
        appointment.updated_at = datetime.now()
        
        # Session state frissítése
        st.session_state.appointments_db.add_appointment(appointment)

        
        # 🚀 AUTOMATIKUS MENTÉS
        self._save_to_file()
        
        print(f"✅ Appointment frissítve és elmentve: {appointment.reference_number}")
        
        return True
    
    def cancel_appointment(self, appointment_id: str) -> bool:
        """Foglalás lemondása AUTOMATIKUS MENTÉSSEL"""
        if appointment_id not in self.appointments:
            return False
        
        appointment = self.appointments[appointment_id]
        appointment.status = AppointmentStatus.CANCELLED
        appointment.updated_at = datetime.now()
        
        # Session state frissítése
        st.session_state.appointments_db[appointment_id] = appointment
        
        # 🚀 AUTOMATIKUS MENTÉS
        self._save_to_file()
        
        print(f"✅ Appointment lemondva és elmentve: {appointment.reference_number}")
        
        return True
    
    def delete_appointment(self, appointment_id: str) -> bool:
        """Foglalás törlése AUTOMATIKUS MENTÉSSEL"""
        if appointment_id not in self.appointments:
            return False
        
        appointment = self.appointments[appointment_id]
        
        # Indexek frissítése
        self._remove_from_doctor_index(appointment)
        self._remove_from_patient_index(appointment)
        
        # Törlés
        del self.appointments[appointment_id]
        
        # Session state frissítése
        if appointment_id in st.session_state.appointments_db:
            del st.session_state.appointments_db[appointment_id]
        
        # 🚀 AUTOMATIKUS MENTÉS
        self._save_to_file()
        
        print(f"✅ Appointment törölve és elmentve: {appointment.reference_number}")
        
        return True
    
    # =============================================================================
    # MEGLÉVŐ FÜGGVÉNYEK (változtatás nélkül)
    # =============================================================================
    
    def get_appointment_by_id(self, appointment_id: str) -> Optional[Appointment]:
        """Foglalás lekérése ID alapján"""
        return self.appointments.get(appointment_id)
    
    def get_appointments_by_doctor(self, doctor_id: str) -> List[Appointment]:
        """Orvos összes foglalásának lekérése"""
        appointment_ids = self.appointments_by_doctor.get(doctor_id, [])
        return [self.appointments[aid] for aid in appointment_ids if aid in self.appointments]
    
    def get_appointments_by_patient(self, patient_email: str) -> List[Appointment]:
        """Páciens összes foglalásának lekérése"""
        appointment_ids = self.appointments_by_patient.get(patient_email, [])
        return [self.appointments[aid] for aid in appointment_ids if aid in self.appointments]
    
    def get_appointments_by_date(self, target_date: date) -> List[Appointment]:
        """Adott napon lévő foglalások lekérése"""
        return [
            appointment for appointment in self.appointments.values()
            if appointment.datetime.date() == target_date
        ]
    
    def get_appointments_by_date_range(self, start_date: date, end_date: date) -> List[Appointment]:
        """Dátum tartomány alapján foglalások lekérése"""
        return [
            appointment for appointment in self.appointments.values()
            if start_date <= appointment.datetime.date() <= end_date
        ]
    
    def get_doctor_schedule(self, doctor_id: str, start_date: date, end_date: date) -> Dict[str, List[Appointment]]:
        """Orvos menetrendje egy időszakra"""
        doctor_appointments = self.get_appointments_by_doctor(doctor_id)
        schedule = {}
        
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.isoformat()
            schedule[date_str] = [
                appointment for appointment in doctor_appointments
                if appointment.datetime.date() == current_date
            ]
            current_date += timedelta(days=1)
        
        return schedule
    
    def get_available_slots(self, doctor_id: str, target_date: date, duration_minutes: int = 30) -> List[datetime]:
        """Szabad időpontok lekérése"""
        doctor_appointments = [
            app for app in self.get_appointments_by_doctor(doctor_id)
            if app.datetime.date() == target_date and app.status != AppointmentStatus.CANCELLED
        ]
        
        booked_times = [app.datetime.time() for app in doctor_appointments]
        
        # Egyszerű logika - 9:00-17:00 között 30 perces slotok
        available_slots = []
        current_time = datetime.combine(target_date, datetime.min.time().replace(hour=9))
        end_time = datetime.combine(target_date, datetime.min.time().replace(hour=17))
        
        while current_time < end_time:
            if current_time.time() not in booked_times:
                available_slots.append(current_time)
            current_time += timedelta(minutes=duration_minutes)
        
        return available_slots
    
    def _has_time_conflict(self, appointment: Appointment, exclude_id: Optional[str] = None) -> bool:
        """Időpont ütközés ellenőrzése - JAVÍTOTT VÉGLEGESEN"""
        doctor_appointments = self.get_appointments_by_doctor(appointment.doctor_id)
        
        for existing_appointment in doctor_appointments:
            if exclude_id and existing_appointment.id == exclude_id:
                continue
            
            if existing_appointment.status == AppointmentStatus.CANCELLED:
                continue
            
            # ✅ JAVÍTVA: datetime field név használata
            if existing_appointment.datetime == appointment.datetime:
                return True
        
        return False
    
    def _update_doctor_index(self, appointment: Appointment):
        """Orvos index frissítése"""
        if appointment.doctor_id not in self.appointments_by_doctor:
            self.appointments_by_doctor[appointment.doctor_id] = []
        if appointment.id not in self.appointments_by_doctor[appointment.doctor_id]:
            self.appointments_by_doctor[appointment.doctor_id].append(appointment.id)
    
    def _update_patient_index(self, appointment: Appointment):
        """Páciens index frissítése"""
        patient_email = appointment.patient_info.email
        if patient_email not in self.appointments_by_patient:
            self.appointments_by_patient[patient_email] = []
        if appointment.id not in self.appointments_by_patient[patient_email]:
            self.appointments_by_patient[patient_email].append(appointment.id)
    
    def _remove_from_doctor_index(self, appointment: Appointment):
        """Orvos indexből eltávolítás"""
        if appointment.doctor_id in self.appointments_by_doctor:
            if appointment.id in self.appointments_by_doctor[appointment.doctor_id]:
                self.appointments_by_doctor[appointment.doctor_id].remove(appointment.id)
    
    def _remove_from_patient_index(self, appointment: Appointment):
        """Páciens indexből eltávolítás"""
        patient_email = appointment.patient_info.email
        if patient_email in self.appointments_by_patient:
            if appointment.id in self.appointments_by_patient[patient_email]:
                self.appointments_by_patient[patient_email].remove(appointment.id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Statisztikák lekérése"""
        total_appointments = len(self.appointments)
        
        # Státusz szerint csoportosítás
        status_counts = {}
        for status in AppointmentStatus:
            status_counts[status.value] = len([
                app for app in self.appointments.values()
                if app.status == status
            ])
        
        # Mai foglalások
        today = date.today()
        today_appointments = len(self.get_appointments_by_date(today))
        
        # Következő hét foglalások
        next_week = today + timedelta(days=7)
        next_week_appointments = len(self.get_appointments_by_date_range(today, next_week))
        
        return {
            'total_appointments': total_appointments,
            'status_breakdown': status_counts,
            'today_appointments': today_appointments,
            'next_week_appointments': next_week_appointments,
            'unique_doctors': len(self.appointments_by_doctor),
            'unique_patients': len(self.appointments_by_patient),
            'data_file': self.appointments_file,
            'file_exists': os.path.exists(self.appointments_file)
        }
    
    # =============================================================================
    # KIEGÉSZÍTŐ FUNKCIÓK
    # =============================================================================
    
    def backup_data(self, backup_name: str = None):
        """Adatok biztonsági mentése"""
        if backup_name is None:
            backup_name = f"appointments_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        backup_path = os.path.join(self.data_dir, backup_name)
        
        try:
            import shutil
            shutil.copy2(self.appointments_file, backup_path)
            print(f"📦 Backup készítve: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"❌ Backup hiba: {e}")
            return None
    
    def export_csv(self) -> str:
        """Appointments exportálása CSV fájlba"""
        try:
            import pandas as pd
            
            appointments_list = []
            for appointment in self.appointments.values():
                appointments_list.append({
                    'Reference': appointment.reference_number,
                    'Doctor_ID': appointment.doctor_id,
                    'Patient_Name': appointment.patient_info.name,
                    'Patient_Email': appointment.patient_info.email,
                    'Patient_Phone': appointment.patient_info.phone,
                    'DateTime': appointment.datetime.strftime('%Y-%m-%d %H:%M'),
                    'Duration': appointment.duration_minutes,
                    'Status': appointment.status.value,
                    'Symptoms': ', '.join(appointment.patient_info.symptoms),
                    'Diagnosis': appointment.patient_info.diagnosis,
                    'Notes': appointment.notes,
                    'Created': appointment.created_at.strftime('%Y-%m-%d %H:%M')
                })
            
            df = pd.DataFrame(appointments_list)
            csv_path = os.path.join(self.data_dir, f"appointments_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            df.to_csv(csv_path, index=False, encoding='utf-8')
            
            print(f"📊 CSV exportálva: {csv_path}")
            return csv_path
            
        except Exception as e:
            print(f"❌ CSV export hiba: {e}")
            return None

# Globális appointments database példány PERZISZTENS TÁROLÁSSAL
_appointments_db = None

def get_appointments_db() -> AppointmentsDatabase:
    if "appointments_db" not in st.session_state:
        st.session_state.appointments_db = AppointmentsDatabase()
    return st.session_state.appointments_db


# =============================================================================
# ADATKEZELŐ SEGÉDFÜGGVÉNYEK
# =============================================================================

def get_data_file_path() -> str:
    """Adatfájl útvonalának lekérése"""
    db = get_appointments_db()
    return db.appointments_file

def get_data_statistics() -> Dict[str, Any]:
    """Adattárolási statisztikák"""
    db = get_appointments_db()
    stats = db.get_statistics()
    
    # Fájl méret hozzáadása
    if os.path.exists(stats['data_file']):
        file_size = os.path.getsize(stats['data_file'])
        stats['file_size_bytes'] = file_size
        stats['file_size_kb'] = round(file_size / 1024, 2)
    else:
        stats['file_size_bytes'] = 0
        stats['file_size_kb'] = 0
    
    return stats

def backup_all_data() -> str:
    """Összes adat biztonsági mentése"""
    db = get_appointments_db()
    return db.backup_data()

def export_appointments_csv() -> str:
    """Appointments CSV exportálása"""
    db = get_appointments_db()
    return db.export_csv()