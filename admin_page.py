# =============================================================================
# admin_page.py - KÜLÖN FÁJL A PROJEKT GYÖKERÉBEN
# =============================================================================
"""
Admin oldal az appointment system adatok kezeléséhez
Használat: streamlit run admin_page.py
"""
import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime
import sys

# Projekt modulok importálása
try:
    from appointment_system.database.appointments_db import get_appointments_db, get_data_statistics
    from appointment_system.models.appointment import AppointmentStatus
except ImportError:
    st.error("❌ Appointment system modulok nem elérhetőek!")
    st.stop()

def configure_page():
    """Oldal konfiguráció"""
    st.set_page_config(
        page_title="Medical Chatbot - Admin",
        page_icon="🔧",
        layout="wide"
    )

def display_data_overview():
    """Adatok áttekintése"""
    st.title("🔧 Medical Chatbot - Admin Panel")
    
    # Adatstatisztikák
    stats = get_data_statistics()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📅 Összes Foglalás", stats['total_appointments'])
    
    with col2:
        st.metric("👨‍⚕️ Orvosok", stats['unique_doctors'])
    
    with col3:
        st.metric("👤 Páciensek", stats['unique_patients'])
    
    with col4:
        st.metric("📁 Fájl Méret", f"{stats['file_size_kb']} KB")

def display_file_information():
    """Fájl információk megjelenítése"""
    st.markdown("### 📁 Adatfájl Információk")
    
    stats = get_data_statistics()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"""
        **📄 Adatfájl Helye:**
        `{stats['data_file']}`
        
        **💾 Fájl Méret:**
        {stats['file_size_bytes']} bytes ({stats['file_size_kb']} KB)
        
        **📊 Stato:**
        {'✅ Létezik' if stats['file_exists'] else '❌ Nem létezik'}
        """)
    
    with col2:
        # Fájl tartalom előnézet
        if stats['file_exists']:
            st.markdown("**📋 Fájl Tartalom Előnézet:**")
            try:
                with open(stats['data_file'], 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # JSON formázott megjelenítés
                parsed_json = json.loads(content)
                st.json(list(parsed_json.keys())[:5])  # Csak az első 5 kulcs
                
                if len(parsed_json) > 5:
                    st.caption(f"... és még {len(parsed_json) - 5} appointment")
                    
            except Exception as e:
                st.error(f"Hiba a fájl olvasásában: {e}")
        else:
            st.warning("📂 Az adatfájl még nem létezik. Készítsd el az első foglalást!")

def display_appointments_table():
    """Appointments táblázat megjelenítése"""
    st.markdown("### 📅 Foglalások Táblázata")
    
    db = get_appointments_db()
    appointments = list(db.appointments.values())
    
    if not appointments:
        st.info("📭 Még nincsenek foglalások az adatbázisban.")
        return
    
    # DataFrame készítése
    data = []
    for apt in appointments:
        data.append({
            'Referencia': apt.reference_number,
            'Orvos ID': apt.doctor_id,
            'Páciens': apt.patient_info.name,
            'Email': apt.patient_info.email,
            'Telefon': apt.patient_info.phone,
            'Időpont': apt.datetime.strftime('%Y-%m-%d %H:%M'),
            'Időtartam': f"{apt.duration_minutes} perc",
            'Státusz': apt.status.value,
            'Létrehozva': apt.created_at.strftime('%Y-%m-%d %H:%M')
        })
    
    df = pd.DataFrame(data)
    
    # Interaktív táblázat
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )
    
    # Statisztikák
    status_counts = df['Státusz'].value_counts()
    
    st.markdown("### 📊 Státusz Megoszlás")
    col1, col2 = st.columns(2)
    
    with col1:
        st.bar_chart(status_counts)
    
    with col2:
        for status, count in status_counts.items():
            st.metric(status, count)

def display_raw_data():
    """Nyers adatok megjelenítése"""
    st.markdown("### 📄 Nyers JSON Adatok")
    
    stats = get_data_statistics()
    
    if stats['file_exists']:
        with st.expander("🔍 JSON Fájl Tartalom", expanded=False):
            try:
                with open(stats['data_file'], 'r', encoding='utf-8') as f:
                    content = f.read()
                
                st.code(content, language='json')
                
            except Exception as e:
                st.error(f"Hiba a fájl olvasásában: {e}")
    else:
        st.warning("📂 Az adatfájl még nem létezik.")

def display_backup_tools():
    """Backup és export eszközök"""
    st.markdown("### 🛠️ Adatkezelő Eszközök")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📦 Backup Készítése"):
            db = get_appointments_db()
            backup_path = db.backup_data()
            if backup_path:
                st.success(f"✅ Backup készítve: `{backup_path}`")
            else:
                st.error("❌ Backup készítése sikertelen!")
    
    with col2:
        if st.button("📊 CSV Export"):
            db = get_appointments_db()
            csv_path = db.export_csv()
            if csv_path:
                st.success(f"✅ CSV exportálva: `{csv_path}`")
                
                # CSV letöltés
                with open(csv_path, 'rb') as f:
                    st.download_button(
                        label="📥 CSV Letöltése",
                        data=f.read(),
                        file_name=os.path.basename(csv_path),
                        mime='text/csv',
                        key="admin_csv_download"
                    )
            else:
                st.error("❌ CSV export sikertelen!")
    
    with col3:
        if st.button("🗑️ Adatok Törlése", type="secondary"):
            st.warning("⚠️ Ez törölni fogja az összes appointment adatot!")
            
            confirm = st.checkbox("Igen, törölni akarom az adatokat")
            if confirm:
                if st.button("🗑️ Végleges Törlés", type="primary"):
                    stats = get_data_statistics()
                    if os.path.exists(stats['data_file']):
                        os.remove(stats['data_file'])
                        st.success("✅ Adatok törölve!")
                        st.rerun()

def display_system_info():
    """Rendszer információk"""
    st.markdown("### 💻 Rendszer Információk")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"""
        **🐍 Python Verzió:**
        {sys.version}
        
        **📁 Munkakönyvtár:**
        `{os.getcwd()}`
        
        **⏰ Jelenlegi Idő:**
        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """)
    
    with col2:
        # Könyvtár struktúra
        st.markdown("**📂 Projekt Struktúra:**")
        
        project_files = []
        for root, dirs, files in os.walk('.'):
            level = root.replace('.', '').count(os.sep)
            indent = ' ' * 2 * level
            project_files.append(f"{indent}{os.path.basename(root)}/")
            
            subindent = ' ' * 2 * (level + 1)
            for file in files[:3]:  # Csak az első 3 fájl
                project_files.append(f"{subindent}{file}")
            
            if len(files) > 3:
                project_files.append(f"{subindent}... és {len(files)-3} további fájl")
            
            if level > 2:  # Mélység korlátozás
                break
        
        st.code('\n'.join(project_files[:20]))

def main():
    """Fő admin funkció"""
    configure_page()
    
    # Sidebar navigáció
    with st.sidebar:
        st.title("🔧 Admin Menü")
        
        page = st.selectbox(
            "Válassz funkciót:",
            [
                "📊 Áttekintés",
                "📅 Foglalások",
                "📁 Fájl Info",
                "📄 Nyers Adatok",
                "🛠️ Eszközök",
                "💻 Rendszer Info"
            ]
        )
        
        st.markdown("---")
        
        # Gyors statisztikák
        stats = get_data_statistics()
        st.metric("📅 Foglalások", stats['total_appointments'])
        st.metric("📁 Fájl Méret", f"{stats['file_size_kb']} KB")
        
        if st.button("🔄 Frissítés"):
            st.rerun()
    
    # Fő tartalom
    if page == "📊 Áttekintés":
        display_data_overview()
        display_file_information()
    
    elif page == "📅 Foglalások":
        display_appointments_table()
    
    elif page == "📁 Fájl Info":
        display_file_information()
    
    elif page == "📄 Nyers Adatok":
        display_raw_data()
    
    elif page == "🛠️ Eszközök":
        display_backup_tools()
    
    elif page == "💻 Rendszer Info":
        display_system_info()

if __name__ == "__main__":
    main()