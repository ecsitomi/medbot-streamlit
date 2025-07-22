# debug_appointment_system.py
"""
Debug eszköz az appointment system hibakereséséhez
Futtasd ezt a main.py helyett: streamlit run debug_appointment_system.py
"""
import streamlit as st
import os
import sys
import json
from datetime import datetime

# Importáljuk a szükséges modulokat
from appointment_system.database.appointments_db import AppointmentsDatabase, get_appointments_db
from appointment_system.logic.appointment_logic import AppointmentManager
from appointment_system.models.appointment import Appointment, PatientInfo, AppointmentStatus

def debug_file_system():
    """Fájlrendszer debug információk"""
    st.markdown("### 🔍 Fájlrendszer Debug")
    
    # Munkakönyvtár
    st.write(f"**Munkakönyvtár:** `{os.getcwd()}`")
    
    # Data könyvtár ellenőrzése
    data_dir = "data"
    data_exists = os.path.exists(data_dir)
    st.write(f"**Data könyvtár létezik:** {data_exists}")
    
    if data_exists:
        st.write(f"**Data könyvtár írható:** {os.access(data_dir, os.W_OK)}")
        files = os.listdir(data_dir)
        st.write(f"**Fájlok a data könyvtárban:** {files}")
    
    # Appointments.json ellenőrzése
    appointments_file = os.path.join(data_dir, "appointments.json")
    file_exists = os.path.exists(appointments_file)
    st.write(f"**appointments.json létezik:** {file_exists}")
    
    if file_exists:
        file_size = os.path.getsize(appointments_file)
        st.write(f"**Fájl méret:** {file_size} bytes")
        
        # Fájl tartalom
        try:
            with open(appointments_file, 'r', encoding='utf-8') as f:
                content = f.read()
                st.write(f"**Fájl tartalom (első 200 karakter):** {content[:200]}...")
        except Exception as e:
            st.error(f"Hiba a fájl olvasásakor: {e}")

def debug_database_operations():
    """Adatbázis műveletek debug"""
    st.markdown("### 🗄️ Adatbázis Debug")
    
    # Monkey patch az AppointmentsDatabase osztályba
    original_init = AppointmentsDatabase.__init__
    original_save = AppointmentsDatabase._save_to_file
    original_add = AppointmentsDatabase.add_appointment
    
    def debug_init(self, data_dir="data"):
        print(f"🟦 DEBUG: AppointmentsDatabase.__init__ called with data_dir={data_dir}")
        original_init(self, data_dir)
        print(f"🟦 DEBUG: appointments_file path: {self.appointments_file}")
        print(f"🟦 DEBUG: Loaded {len(self.appointments)} appointments from file")
    
    def debug_save(self):
        print(f"🟨 DEBUG: _save_to_file() called")
        print(f"🟨 DEBUG: Saving {len(self.appointments)} appointments")
        try:
            result = original_save(self)
            print(f"🟨 DEBUG: Save completed successfully")
            return result
        except Exception as e:
            print(f"🔴 DEBUG: Save failed with error: {e}")
            raise
    
    def debug_add(self, appointment):
        print(f"🟩 DEBUG: add_appointment() called")
        print(f"🟩 DEBUG: Appointment ID: {appointment.id}")
        print(f"🟩 DEBUG: Reference: {appointment.reference_number}")
        print(f"🟩 DEBUG: Doctor ID: {appointment.doctor_id}")
        print(f"🟩 DEBUG: Patient: {appointment.patient_info.name}")
        
        result = original_add(self, appointment)
        
        print(f"🟩 DEBUG: add_appointment() result: {result}")
        print(f"🟩 DEBUG: Current appointments count: {len(self.appointments)}")
        
        return result
    
    # Apply monkey patches
    AppointmentsDatabase.__init__ = debug_init
    AppointmentsDatabase._save_to_file = debug_save
    AppointmentsDatabase.add_appointment = debug_add
    
    # Get database instance
    db = get_appointments_db()
    st.write(f"**Appointments in memory:** {len(db.appointments)}")

def debug_booking_process():
    """Foglalási folyamat tesztelése"""
    st.markdown("### 🎯 Foglalási Folyamat Debug Test")
    
    if st.button("🧪 Test Appointment Booking"):
        # Test appointment létrehozása
        test_patient = PatientInfo(
            name="Test Patient",
            age=30,
            gender="férfi",
            phone="+36 30 123 4567",
            email="test@example.com",
            symptoms=["fejfájás"],
            diagnosis="Test diagnosis"
        )
        
        test_appointment = Appointment(
            id=f"test_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            doctor_id="doc_001",
            patient_info=test_patient,
            datetime=datetime.now(),
            duration_minutes=30,
            status=AppointmentStatus.CONFIRMED,
            notes="Debug test appointment"
        )
        
        # Próbáljuk hozzáadni
        db = get_appointments_db()
        
        st.write("**Hozzáadás előtt:**")
        st.write(f"- Appointments in memory: {len(db.appointments)}")
        
        # Add appointment with debug
        success = db.add_appointment(test_appointment)
        
        st.write("**Hozzáadás után:**")
        st.write(f"- Success: {success}")
        st.write(f"- Appointments in memory: {len(db.appointments)}")
        
        # Ellenőrizzük a fájlt
        if os.path.exists(db.appointments_file):
            with open(db.appointments_file, 'r', encoding='utf-8') as f:
                file_content = json.load(f)
                st.write(f"- Appointments in file: {len(file_content)}")

def main():
    st.set_page_config(page_title="Appointment System Debug", page_icon="🔍", layout="wide")
    
    st.title("🔍 Appointment System Debug Tool")
    
    # Debug tabs
    tab1, tab2, tab3 = st.tabs(["Fájlrendszer", "Adatbázis", "Foglalás Test"])
    
    with tab1:
        debug_file_system()
    
    with tab2:
        debug_database_operations()
    
    with tab3:
        debug_booking_process()
    
    # Console output
    st.markdown("### 📝 Console Output")
    st.info("Nézd meg a terminált a print() debug üzenetekért!")

if __name__ == "__main__":
    main()