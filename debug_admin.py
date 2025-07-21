# debug_admin.py
"""
Debug az admin oldalhoz
"""
import streamlit as st
import os
import json
from datetime import datetime

def debug_admin_page():
    st.set_page_config(page_title="Debug Admin", page_icon="🔍", layout="wide")
    
    st.title("🔍 Debug Admin Page")
    
    # Check appointments file
    st.markdown("### 📁 Appointments File Check")
    
    appointments_file = "data/appointments.json"
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**File path:** `{appointments_file}`")
        st.write(f"**Absolute path:** `{os.path.abspath(appointments_file)}`")
        st.write(f"**File exists:** {os.path.exists(appointments_file)}")
        
        if os.path.exists(appointments_file):
            file_stats = os.stat(appointments_file)
            st.write(f"**File size:** {file_stats.st_size} bytes")
            st.write(f"**Modified:** {datetime.fromtimestamp(file_stats.st_mtime)}")
    
    with col2:
        if os.path.exists(appointments_file):
            try:
                with open(appointments_file, 'r', encoding='utf-8') as f:
                    appointments_data = json.load(f)
                
                st.success(f"✅ Successfully loaded {len(appointments_data)} appointments")
                
                # Show appointments
                for apt_id, apt_data in appointments_data.items():
                    st.write(f"**ID:** {apt_id}")
                    st.write(f"**Reference:** {apt_data.get('reference_number')}")
                    st.write(f"**Doctor:** {apt_data.get('doctor_id')}")
                    st.write(f"**Patient:** {apt_data.get('patient_info', {}).get('name')}")
                    st.write("---")
                    
            except Exception as e:
                st.error(f"Error loading file: {e}")
        else:
            st.error("❌ appointments.json not found!")
    
    # Test get_appointments_db
    st.markdown("### 🗄️ Database Instance Test")
    
    try:
        from appointment_system.database.appointments_db import get_appointments_db
        
        db = get_appointments_db()
        st.write(f"**Appointments in memory:** {len(db.appointments)}")
        st.write(f"**Database file path:** {db.appointments_file}")
        
        # List appointments
        if db.appointments:
            st.write("**Appointments:**")
            for apt_id, apt in db.appointments.items():
                st.write(f"- {apt_id}: {apt.reference_number} - {apt.patient_info.name}")
        else:
            st.warning("No appointments in database instance")
            
    except Exception as e:
        st.error(f"Error getting database: {e}")
        import traceback
        st.code(traceback.format_exc())

if __name__ == "__main__":
    debug_admin_page()