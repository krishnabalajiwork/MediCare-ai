import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random
import io

@st.cache_data
def load_data():
    # Using a self-contained data snippet to ensure it runs correctly.
    # For your live app, you can switch this to: pd.read_csv('patients_database.csv')
    try:
        csv_text_data = """patient_id,first_name,last_name,date_of_birth,patient_type
PAT1000,Kenneth,Davis,12/09/1945,New
PAT1001,James,Johnson,04/08/1949,Returning
PAT1002,John,Carter,03/23/1995,New
"""
        return pd.read_csv(io.StringIO(csv_text_data))
    except FileNotFoundError:
        st.error("patients_database.csv not found!")
        return None

def render():
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    
    if 'appointment_confirmed' not in st.session_state:
        st.session_state.appointment_confirmed = False

    if st.session_state.appointment_confirmed:
        st.balloons()
        st.header("✅ Appointment Confirmed!")
        details = st.session_state.appointment_details
        st.success(f"Thank you, {details['patient_name']}! Your appointment is booked.")
        st.markdown(f"""
            - **Doctor:** {details['doctor']}
            - **Date:** {details['date']}
            - **Time:** {details['time']}
            - **Appointment ID:** {details['appointment_id']}
        """)
        if st.button("Book Another Appointment"):
            del st.session_state.appointment_confirmed
            del st.session_state.appointment_details
            st.rerun()
    else:
        st.header("🗓️ Request an Appointment")
        with st.form("appointment_form"):
            st.subheader("Patient Details")
            c1, c2 = st.columns(2)
            first_name = c1.text_input("First Name")
            last_name = c2.text_input("Last Name")
            dob = st.date_input("Date of Birth", min_value=datetime(1920, 1, 1))
            
            st.divider()
            
            st.subheader("Appointment Details")
            c3, c4 = st.columns(2)
            req_date = c3.date_input("Preferred Date", min_value=datetime.now() + timedelta(days=1))
            req_time = c4.selectbox("Preferred Time", ['09:00 AM', '11:00 AM', '02:00 PM'])
            doctor = st.selectbox("Preferred Doctor", ['Any Available', 'Dr. Sarah Chen', 'Dr. Michael Rodriguez', 'Dr. Emily Johnson', 'Dr. Robert Kim'])
            
            submitted = st.form_submit_button("Confirm My Appointment")
            if submitted:
                # Basic validation
                if not first_name or not last_name:
                    st.warning("Please enter your first and last name.")
                else:
                    patient_data = {'first_name': first_name, 'last_name': last_name}
                    final_doctor = random.choice(['Dr. Sarah Chen', 'Dr. Michael Rodriguez']) if doctor == 'Any Available' else doctor
                    
                    st.session_state.appointment_details = {
                        'appointment_id': f"APT{random.randint(10000, 99999)}",
                        'patient_name': f"{first_name} {last_name}",
                        'doctor': final_doctor,
                        'date': req_date.strftime('%Y-%m-%d'),
                        'time': req_time,
                    }
                    st.session_state.appointment_confirmed = True
                    st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
