import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="MediCare AI Scheduling Agent",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS FOR A MODERN UI ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');

    /* --- Theme Variables --- */
    :root {
        --primary-color: #007bff;
        --primary-light: #e6f2ff;
        --success-color: #28a745;
        --success-light: #eaf6ec;
        --warning-color: #ffc107;
        --warning-light: #fff9e6;
        --info-color: #17a2b8;
        --info-light: #e8f6f8;
        --background-color: #f8f9fa;
        --surface-color: #ffffff;
        --text-color: #343a40;
        --text-secondary-color: #6c757d;
        --border-color: #dee2e6;
        --font-family: 'Roboto', sans-serif;
    }

    /* --- General Styles --- */
    body {
        font-family: var(--font-family);
        color: var(--text-color);
    }
    .main > div {
        background-color: var(--background-color);
    }
    h1, h2, h3, h4, h5, h6 {
        font-weight: 700;
        color: var(--text-color);
    }

    /* --- Header --- */
    .app-header {
        background-color: var(--surface-color);
        color: var(--text-color);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        border: 1px solid var(--border-color);
    }
    .app-header h1 {
        font-size: 2.2rem;
        margin: 0;
        color: var(--primary-color);
    }
    .app-header p {
        font-size: 1.1rem;
        color: var(--text-secondary-color);
        margin: 0.25rem 0 0 0;
    }

    /* --- Sidebar --- */
    .css-1d391kg {
        background-color: var(--surface-color);
        border-right: 1px solid var(--border-color);
    }
    .sidebar-header {
        font-size: 1.25rem;
        font-weight: 700;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid var(--primary-color);
    }
    .metric-card {
        background-color: var(--primary-light);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        text-align: center;
        border-left: 5px solid var(--primary-color);
    }
    .metric-number {
        font-size: 2rem;
        font-weight: 700;
        color: var(--primary-color);
    }
    .metric-label {
        font-size: 0.9rem;
        color: var(--text-secondary-color);
        font-weight: 500;
    }

    /* --- Content Cards & Forms --- */
    .content-card {
        background-color: var(--surface-color);
        border-radius: 10px;
        padding: 2rem;
        border: 1px solid var(--border-color);
        margin-bottom: 1.5rem;
    }
    .content-card h3 {
        color: var(--primary-color);
        border-bottom: 1px solid var(--border-color);
        padding-bottom: 0.75rem;
        margin-bottom: 1.5rem;
    }
    
    /* --- Buttons --- */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
        background-color: var(--primary-color);
        color: white;
        border: none;
        transition: background-color 0.2s ease, transform 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #0056b3;
        transform: translateY(-2px);
    }
    .stButton > button:active {
        background-color: #004494;
    }

    /* --- AI Chat Messages --- */
    .ai-message {
        background-color: var(--primary-light);
        padding: 1rem 1.5rem;
        border-radius: 15px 15px 15px 5px;
        margin-bottom: 1rem;
        border-left: 4px solid var(--primary-color);
    }

    /* --- Information Boxes --- */
    .info-box {
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left-width: 5px;
        border-left-style: solid;
    }
    .info-box-warning {
        background-color: var(--warning-light);
        border-left-color: var(--warning-color);
    }
    .info-box-info {
        background-color: var(--info-light);
        border-left-color: var(--info-color);
    }
    .info-box-success {
        background-color: var(--success-light);
        border-left-color: var(--success-color);
    }

    /* --- Progress Stepper --- */
    .stepper-container {
        display: flex;
        justify-content: space-between;
        margin-bottom: 2rem;
        position: relative;
    }
    .step {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        width: 100px; /* Fixed width for each step */
    }
    .step-circle {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        background-color: #ccc;
        color: white;
        display: flex;
        justify-content: center;
        align-items: center;
        font-weight: bold;
        margin-bottom: 0.5rem;
        border: 2px solid #ccc;
        transition: all 0.3s ease;
    }
    .step-label {
        font-size: 0.8rem;
        color: #ccc;
        transition: all 0.3s ease;
    }
    .step.active .step-circle {
        background-color: var(--primary-color);
        border-color: var(--primary-color);
    }
    .step.active .step-label {
        color: var(--primary-color);
        font-weight: bold;
    }
    .step.completed .step-circle {
        background-color: var(--success-color);
        border-color: var(--success-color);
    }
    .step.completed .step-label {
        color: var(--success-color);
    }
    
    /* --- Confirmation Page --- */
    .confirmation-card {
        background: var(--surface-color);
        border: 2px solid var(--success-color);
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
    }
    .confirmation-card h2 { color: var(--success-color); }
    .appointment-details p { 
        font-size: 1.1rem;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

</style>
""", unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if 'step' not in st.session_state:
    st.session_state.step = 'greeting'
if 'current_patient' not in st.session_state:
    st.session_state.current_patient = {}
if 'appointment_data' not in st.session_state:
    st.session_state.appointment_data = {}

# --- DATA LOADING (CACHED) ---
@st.cache_data
def load_data():
    try:
        patients_df = pd.read_csv('patients_database.csv')
    except FileNotFoundError:
        st.error("`patients_database.csv` not found.")
        return pd.DataFrame()
    return patients_df

# --- AI AGENT LOGIC ---
class AISchedulingAgent:
    def __init__(self):
        self.patients_df = load_data()

    def greet_patient(self):
        return """
        🏥 **Welcome to MediCare Allergy & Wellness Center!**
        
        I'm your AI scheduling assistant. To get started, please provide your information below.
        """

    def search_patient(self, first_name, last_name, dob, phone):
        if self.patients_df.empty:
            return None
        
        match = self.patients_df[
            (self.patients_df['first_name'].str.lower() == first_name.lower()) &
            (self.patients_df['last_name'].str.lower() == last_name.lower()) &
            (self.patients_df['date_of_birth'] == dob)
        ]
        return match.iloc[0].to_dict() if not match.empty else None

    def book_appointment(self, patient_data, doctor, date, time, duration):
        appointment_id = f"APT{random.randint(10000, 99999)}"
        location_map = {
            'Dr. Sarah Chen': 'Main Clinic - Downtown',
            'Dr. Michael Rodriguez': 'North Branch',
            'Dr. Emily Johnson': 'South Branch',
        }
        return {
            'appointment_id': appointment_id,
            'patient_name': f"{patient_data['first_name']} {patient_data['last_name']}",
            'doctor': doctor,
            'date': date,
            'time': time,
            'duration': duration,
            'location': location_map.get(doctor, 'Main Clinic'),
            'patient_type': patient_data['patient_type'],
            'status': 'Confirmed',
            'email': patient_data['email'],
        }

# --- UI RENDERING FUNCTIONS ---

def render_header():
    st.markdown("""
    <div class="app-header">
        <h1>🏥 MediCare AI Scheduling Agent</h1>
        <p>Intelligent Appointment Scheduling for Allergy & Wellness Care</p>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar(agent):
    with st.sidebar:
        st.markdown('<p class="sidebar-header">📊 Medical Dashboard</p>', unsafe_allow_html=True)
        
        # Dynamic Metrics
        if not agent.patients_df.empty:
            total_patients = len(agent.patients_df)
            new_patients = len(agent.patients_df[agent.patients_df['patient_type'] == 'New'])
            returning_patients = total_patients - new_patients
        else:
            total_patients, new_patients, returning_patients = 0, 0, 0

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'<div class="metric-card"><div class="metric-number">{total_patients}</div><div class="metric-label">👥 Total Patients</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-card"><div class="metric-number">{new_patients}</div><div class="metric-label">➕ New Patients</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="metric-card"><div class="metric-number">918</div><div class="metric-label">🗓️ Available Slots</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-card"><div class="metric-number">{returning_patients}</div><div class="metric-label">🔄 Returning Patients</div></div>', unsafe_allow_html=True)
        
        st.markdown('<p class="sidebar-header" style="margin-top: 2rem;">ℹ️ Important Info</p>', unsafe_allow_html=True)
        st.markdown("""
        <div class="info-box info-box-warning"><strong>Medication Alert:</strong> Stop antihistamines 7 days before testing.</div>
        <div class="info-box info-box-info"><strong>Forms:</strong> Complete intake forms 24 hours before your visit.</div>
        <div class="info-box info-box-success"><strong>Reminders:</strong> You'll receive 3 automated reminders.</div>
        """, unsafe_allow_html=True)

def render_progress_stepper():
    steps = ["Patient Info", "Schedule", "Confirmation"]
    current_step_name = st.session_state.step
    step_indices = {"greeting": 0, "scheduling": 1, "confirmation": 2}
    current_idx = step_indices.get(current_step_name, -1)

    stepper_html = '<div class="stepper-container">'
    for i, step in enumerate(steps):
        status = "active" if i == current_idx else "completed" if i < current_idx else ""
        icon = "✔️" if i < current_idx else str(i + 1)
        stepper_html += f"""
        <div class="step {status}">
            <div class="step-circle">{icon}</div>
            <div class="step-label">{step}</div>
        </div>
        """
    stepper_html += '</div>'
    st.markdown(stepper_html, unsafe_allow_html=True)

def render_patient_info_form(agent):
    with st.container():
        st.markdown('<div class="ai-message">🤖 <strong>AI Assistant:</strong><br>' + agent.greet_patient() + '</div>', unsafe_allow_html=True)
        
        with st.form("patient_info_form"):
            st.markdown("<h3>📝 Patient Information</h3>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("First Name *", placeholder="Enter your first name")
                dob = st.date_input("Date of Birth *", min_value=datetime(1920, 1, 1))
            with col2:
                last_name = st.text_input("Last Name *", placeholder="Enter your last name")
                phone = st.text_input("Phone Number *", placeholder="(555) 123-4567")
            
            email = st.text_input("Email Address *", placeholder="your.email@example.com")
            
            submitted = st.form_submit_button("🔍 Find My Information", use_container_width=True)

            if submitted:
                if not all([first_name, last_name, phone, email]):
                    st.warning("Please fill out all required fields.")
                else:
                    patient_data = agent.search_patient(first_name, last_name, dob.strftime('%m/%d/%Y'), phone)
                    
                    if patient_data:
                        st.session_state.current_patient = patient_data
                        st.success(f"✅ Welcome back, {first_name}! We've found your information as a returning patient.")
                    else:
                        st.session_state.current_patient = {
                            'first_name': first_name, 'last_name': last_name,
                            'date_of_birth': dob.strftime('%m/%d/%Y'),
                            'phone': phone, 'email': email, 'patient_type': 'New'
                        }
                        st.info(f"👋 Welcome, {first_name}! Let's get you set up as a new patient.")
                    
                    st.session_state.step = 'scheduling'
                    st.rerun()

def render_scheduling_form(agent):
    patient = st.session_state.current_patient
    patient_type = patient.get('patient_type', 'New')
    duration = 60 if patient_type == 'New' else 30

    st.info(f"As a **{patient_type} Patient**, your appointment will be **{duration} minutes** long.")

    with st.form("scheduling_form"):
        st.markdown("<h3>📅 Schedule Your Appointment</h3>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            doctor = st.selectbox("Preferred Doctor 👨‍⚕️", ['Dr. Sarah Chen', 'Dr. Michael Rodriguez', 'Dr. Emily Johnson'])
        with col2:
            date = st.date_input("Preferred Date 🗓️", min_value=datetime.now() + timedelta(days=1))
        with col3:
            time = st.selectbox("Available Time ⏰", ['09:00', '09:30', '10:00', '11:00', '14:00', '15:00'])
            
        st.markdown("<h4 style='margin-top: 2rem; font-weight: 500;'>💳 Insurance Information (Optional)</h4>", unsafe_allow_html=True)
        col_ins1, col_ins2 = st.columns(2)
        with col_ins1:
            st.text_input("Insurance Company", placeholder="Blue Cross Blue Shield")
        with col_ins2:
            st.text_input("Member ID", placeholder="ABC123456")

        book_appointment = st.form_submit_button("✅ Confirm Appointment", use_container_width=True)

        if book_appointment:
            appointment = agent.book_appointment(patient, doctor, date.strftime('%Y-%m-%d'), time, duration)
            st.session_state.appointment_data = appointment
            st.session_state.step = 'confirmation'
            st.rerun()

def render_confirmation_page():
    appointment = st.session_state.appointment_data
    st.balloons()
    st.markdown(f"""
    <div class="confirmation-card">
        <h2>🎉 Appointment Confirmed!</h2>
        <p>Your appointment with <strong>{appointment['doctor']}</strong> has been successfully scheduled.</p>
        <hr>
        <div class="appointment-details">
            <div style="text-align: left; max-width: 400px; margin: auto;">
                <p>👤 <strong>Patient:</strong> {appointment['patient_name']}</p>
                <p>🗓️ <strong>Date:</strong> {appointment['date']}</p>
                <p>⏰ <strong>Time:</strong> {appointment['time']} ({appointment['duration']} min)</p>
                <p>🏥 <strong>Location:</strong> {appointment['location']}</p>
            </div>
        </div>
        <br>
        <p>A confirmation email with important instructions has been sent to <strong>{appointment['email']}</strong>.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🔄 Schedule Another Appointment", use_container_width=True):
        # Reset state for a new booking
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# --- MAIN APPLICATION LOGIC ---
def main():
    agent = AISchedulingAgent()
    
    render_header()
    render_sidebar(agent)

    main_col, _ = st.columns([2, 1]) # Keep right column for potential future use or remove
    with main_col:
        with st.container():
            st.markdown('<div class="content-card">', unsafe_allow_html=True)
            
            # Render the progress stepper unless it's the final confirmation
            if st.session_state.step != 'confirmation':
                render_progress_stepper()

            # State-based UI Rendering
            if st.session_state.step == 'greeting':
                render_patient_info_form(agent)
            elif st.session_state.step == 'scheduling':
                render_scheduling_form(agent)
            elif st.session_state.step == 'confirmation':
                render_confirmation_page()
            
            st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
