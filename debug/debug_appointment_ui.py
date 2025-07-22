# debug_appointment_ui.py
"""
Debug az appointment booking UI folyamathoz
"""
import streamlit as st
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Monkey patch the appointment booking UI
from appointment_system.ui.appointment_booking import AppointmentBookingUI

# Save original method
original_booking_confirmation = AppointmentBookingUI._display_booking_confirmation_fixed

def debug_booking_confirmation(self, doctor, selected_datetime, patient_info):
    """Debug verzió a booking confirmation metódushoz"""
    print(f"🎯 DEBUG: _display_booking_confirmation_fixed called")
    print(f"🎯 DEBUG: Doctor: {doctor.name} (ID: {doctor.id})")
    print(f"🎯 DEBUG: DateTime: {selected_datetime}")
    print(f"🎯 DEBUG: Patient: {patient_info.name}")
    
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
    
    # Debug info box
    with st.expander("🔍 Debug Info", expanded=True):
        st.write("**Session State Before:**")
        st.json({
            "appointment_data": st.session_state.get('appointment_data', 'NOT SET'),
            "appointments_db": len(st.session_state.get('appointments_db', {}))
        })
    
    # Megerősítés gomb
    if st.button("🎯 Időpont foglalása", type="primary"):
        print(f"🔴 DEBUG: Booking button clicked!")
        
        with st.spinner("Foglalás feldolgozása..."):
            booking_result = self.appointment_manager.book_appointment(
                doctor_id=doctor.id,
                appointment_datetime=selected_datetime,
                patient_info=patient_info,
                notes=f"Automatikus foglalás a medical chatbot rendszerből."
            )
        
        print(f"🔴 DEBUG: Booking result: {booking_result}")
        
        if booking_result['success']:
            appointment = booking_result['appointment']
            print(f"🟢 DEBUG: Appointment created: {appointment.reference_number}")
            
            # Session state frissítése
            st.session_state.appointment_data = {
                "selected_doctor": doctor,
                "selected_datetime": selected_datetime,
                "appointment": appointment,
                "booking_status": "confirmed"
            }
            
            # Sikeres foglalás üzenet
            st.success(f"""
            🎉 **Sikeres foglalás!**
            
            Referencia szám: **{appointment.reference_number}**
            
            Egy megerősítő emailt küldtünk a {patient_info.email} címre.
            """)
            
            st.info(f"📁 **Debug:** Foglalás mentve a data/appointments.json fájlba!")
            
            # Debug info after
            with st.expander("🔍 Debug Info After", expanded=True):
                st.write("**Session State After:**")
                st.json({
                    "appointment_data": {
                        "booking_status": st.session_state.appointment_data.get("booking_status"),
                        "reference": appointment.reference_number
                    },
                    "appointments_db": len(st.session_state.get('appointments_db', {}))
                })
                
                # Check file
                appointments_file = "data/appointments.json"
                if os.path.exists(appointments_file):
                    st.success(f"✅ File exists: {appointments_file}")
                    file_size = os.path.getsize(appointments_file)
                    st.write(f"File size: {file_size} bytes")
                else:
                    st.error(f"❌ File NOT found: {appointments_file}")
            
            return appointment
        else:
            # Hiba esetén
            st.error("❌ **Foglalás sikertelen!**")
            for error in booking_result['errors']:
                st.error(f"• {error}")
            
            for warning in booking_result['warnings']:
                st.warning(f"⚠️ {warning}")
            
            return None
    
    return None

# Apply patch
AppointmentBookingUI._display_booking_confirmation_fixed = debug_booking_confirmation

# Import and run main app
from main import main

if __name__ == "__main__":
    print("🚀 DEBUG: Starting debug version of main app")
    main()