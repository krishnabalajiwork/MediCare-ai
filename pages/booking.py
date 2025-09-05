import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random

# You can move the Agent and load_data to a utils.py file for even cleaner code
# For simplicity, we'll keep them here for now.
# Assume patients_database.csv is in the root folder.
@st.cache_data
def load_data():
    try:
        return pd.read_csv('patients_database.csv')
    except FileNotFoundError:
        return None

class AISchedulingAgent:
    def __init__(self):
        self.patients_df = load_data()
    # ... (rest of the agent logic from previous code)
    
    def book_appointment(self, patient_data, doctor, date, time):
        # Your booking logic here
        return {
            'appointment_id': f"APT{random.randint(10000, 99999)}",
            'patient_name': f"{patient_data['first_name']} {patient_data['last_name']}",
            'doctor': doctor,
            'date': date,
            'time': time,
        }

def render():
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    agent = AISchedulingAgent()

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
                # Add validation here
                patient_data = {'first_name': first_name, 'last_name': last_name}
                final_doctor = random.choice(['Dr. Sarah Chen', 'Dr. Michael Rodriguez']) if doctor == 'Any Available' else doctor
                details = agent.book_appointment(patient_data, final_doctor, req_date.strftime('%Y-%m-%d'), req_time)
                
                st.session_state.appointment_confirmed = True
                st.session_state.appointment_details = details
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
