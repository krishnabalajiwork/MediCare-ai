import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
import random

# Page config
st.set_page_config(
    page_title="MediCare AI Scheduling Agent", 
    page_icon="🏥", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    body, .stApp { font-family: 'Inter', sans-serif; background-color: #f8fafc; }

    /* Header */
    .medical-header {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        padding: 2rem;
        margin: -2rem -2rem 2rem -2rem;
        border-radius: 0 0 16px 16px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .medical-header h1 { margin: 0; font-size: 2rem; font-weight: 700; }
    .medical-header p { opacity: 0.9; margin: 0.5rem 0 0; }

    /* Cards */
    .card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
        border: 1px solid #e2e8f0;
    }

    /* Messages */
    .ai-message { background: #eff6ff; border-left: 4px solid #2563eb; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; }
    .user-message { background: #ecfdf5; border-right: 4px solid #059669; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; text-align: right; }

    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
    }

    /* Hide branding */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- Session State ---
if 'conversation' not in st.session_state:
    st.session_state.conversation = []
if 'step' not in st.session_state:
    st.session_state.step = 'greeting'
if 'patient' not in st.session_state:
    st.session_state.patient = {}
if 'appointment' not in st.session_state:
    st.session_state.appointment = {}

# --- Data Loaders ---
@st.cache_data
def load_patients():
    try:
        return pd.read_csv("patients_database.csv")
    except:
        return pd.DataFrame()

@st.cache_data
def load_schedule():
    try:
        return pd.read_excel("doctor_schedules.xlsx", sheet_name="Full_Schedule")
    except:
        return pd.DataFrame()

# --- AI Agent ---
class AIScheduler:
    def __init__(self):
        self.patients = load_patients()
        self.schedule = load_schedule()

    def greet(self):
        return ("""
        🏥 **Welcome to MediCare Allergy & Wellness Center!**

        I’m your AI scheduling assistant. Let’s get your appointment booked.
        Please share your information to get started.
        """)

    def search_patient(self, first, last, dob, phone):
        df = self.patients
        if df.empty:
            return None, False
        match = df[(df.first_name.str.lower()==first.lower()) & (df.last_name.str.lower()==last.lower())]
        if not match.empty:
            return match.iloc[0].to_dict(), True
        return None, False

    def book(self, patient, doctor, date, time, duration):
        return {
            "appointment_id": f"APT{random.randint(10000,99999)}",
            "patient_name": patient.get("full_name"),
            "doctor": doctor,
            "date": date,
            "time": time,
            "duration": duration,
            "status": "Confirmed"
        }

agent = AIScheduler()

# --- Header ---
st.markdown("""
<div class="medical-header">
  <h1>🏥 MediCare AI Scheduling Agent</h1>
  <p>Smarter Appointments for Allergy & Wellness Care</p>
</div>
""", unsafe_allow_html=True)

# --- Sidebar Dashboard ---
with st.sidebar:
    st.subheader("📊 Dashboard")
    if st.session_state.patient:
        st.markdown(f"""
        <div class='card'>
            <b>Patient:</b> {st.session_state.patient.get('full_name')}<br>
            <b>ID:</b> {st.session_state.patient.get('patient_id','N/A')}
        </div>
        """, unsafe_allow_html=True)
    if st.session_state.appointment:
        st.markdown(f"""
        <div class='card'>
            <b>Appointment:</b> {st.session_state.appointment['appointment_id']}<br>
            <b>Date:</b> {st.session_state.appointment['date']} {st.session_state.appointment['time']}<br>
            <b>Doctor:</b> {st.session_state.appointment['doctor']}
        </div>
        """, unsafe_allow_html=True)

# --- Main Content ---
col1, col2 = st.columns([2,1])

with col1:
    st.subheader("💬 Patient Consultation")

    for msg in st.session_state.conversation:
        role_class = "ai-message" if msg['role']=="assistant" else "user-message"
        st.markdown(f"<div class='{role_class}'>{msg['content']}</div>", unsafe_allow_html=True)

    if st.session_state.step == 'greeting':
        greeting = agent.greet()
        if not any(m['content']==greeting for m in st.session_state.conversation):
            st.session_state.conversation.append({"role":"assistant","content":greeting})
        with st.form("patient_form"):
            first = st.text_input("First Name *")
            last = st.text_input("Last Name *")
            dob = st.date_input("Date of Birth *")
            phone = st.text_input("Phone *")
            email = st.text_input("Email *")
            submitted = st.form_submit_button("🔍 Search / Register")
            if submitted:
                data, found = agent.search_patient(first,last,dob.strftime('%m/%d/%Y'),phone)
                if found:
                    st.session_state.patient = data
                    reply = f"✅ Found your record, {first}. You're a returning patient."
                else:
                    st.session_state.patient = {
                        "patient_id": "NEW", "first_name": first, "last_name": last,
                        "full_name": f"{first} {last}", "date_of_birth": dob.strftime('%m/%d/%Y'),
                        "phone": phone, "email": email, "patient_type":"New"
                    }
                    reply = f"👋 Welcome {first}! You're registered as a new patient."
                st.session_state.conversation.append({"role":"assistant","content":reply})
                st.session_state.step = "scheduling"
                st.rerun()

    elif st.session_state.step == 'scheduling':
        patient_type = st.session_state.patient.get("patient_type","New")
        duration = 60 if patient_type=="New" else 30
        with st.form("appt_form"):
            doctor = st.selectbox("Preferred Doctor", ["Dr. Sarah Chen","Dr. Michael Rodriguez","Dr. Emily Johnson","Dr. Robert Kim"])
            date = st.selectbox("Select Date", [(datetime.now()+timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1,6)])
            time = st.selectbox("Time Slot", ["09:00","09:30","10:00","14:00","14:30"])
            confirm = st.form_submit_button("📅 Confirm Appointment")
            if confirm:
                appt = agent.book(st.session_state.patient, doctor, date, time, duration)
                st.session_state.appointment = appt
                st.session_state.step = "confirmation"
                st.session_state.conversation.append({"role":"assistant","content":f"✅ Appointment confirmed with {doctor} on {date} at {time}."})
                st.rerun()

    elif st.session_state.step == 'confirmation':
        appt = st.session_state.appointment
        st.success(f"Appointment {appt['appointment_id']} confirmed for {appt['date']} at {appt['time']} with {appt['doctor']}.")
        st.markdown("Thank you! You’ll receive reminders via email/phone.")
