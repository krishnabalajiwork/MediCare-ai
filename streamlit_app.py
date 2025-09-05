import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta, date
import random
import os
import io

# Configure page with medical theme
st.set_page_config(
    page_title="MediCare AI Scheduling Agent", 
    page_icon="🏥", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for medical/hospital theme with PROPER SPACING
st.markdown("""
<style>
    /* Import medical fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Main theme colors */
    :root {
        --primary-blue: #1e40af;
        --light-blue: #dbeafe;
        --success-green: #059669;
        --light-green: #d1fae5;
        --warning-orange: #d97706;
        --light-orange: #fed7aa;
        --medical-gray: #f8fafc;
        --border-gray: #e2e8f0;
        --text-primary: #1e293b;
        --text-secondary: #64748b;
        --dark-text: #0f172a;
    }

    /* Main app styling */
    .main > div {
        padding-top: 2rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }

    /* Header styling */
    .medical-header {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        padding: 2rem;
        margin: -2rem -2rem 2rem -2rem;
        border-radius: 0 0 20px 20px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 20px rgba(30, 64, 175, 0.3);
    }

    .medical-header h1 {
        font-family: 'Inter', sans-serif;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        color: white !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }

    .medical-header p {
        font-family: 'Inter', sans-serif;
        font-size: 1.2rem;
        margin: 0.5rem 0 0 0;
        color: rgba(255,255,255,0.95) !important;
    }

    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8fafc;
        border-right: 2px solid #e2e8f0;
    }

    /* Dashboard cards */
    .status-card {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%);
        color: white !important;
        padding: 1.25rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        box-shadow: 0 4px 12px rgba(5, 150, 105, 0.25);
    }

    .status-card h4 {
        margin: 0 0 0.75rem 0;
        font-weight: 600;
        font-size: 1rem;
        color: white !important;
    }

    .status-card p {
        margin: 0.5rem 0 0 0;
        font-size: 0.9rem;
        color: rgba(255,255,255,0.95) !important;
        line-height: 1.4;
    }

    /* Conversation styling */
    .chat-container {
        background: white;
        border-radius: 16px;
        padding: 2.5rem;
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
        margin-bottom: 2rem;
    }

    .ai-message {
        background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
        padding: 1.25rem 1.75rem;
        border-radius: 16px 16px 16px 6px;
        margin: 1.5rem 0;
        border-left: 4px solid #1e40af;
        font-family: 'Inter', sans-serif;
        color: #0f172a !important;
        font-weight: 500;
        box-shadow: 0 2px 8px rgba(30, 64, 175, 0.1);
    }

    .ai-message strong {
        color: #1e40af !important;
    }

    .user-message {
        background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
        padding: 1.25rem 1.75rem;
        border-radius: 16px 16px 6px 16px;
        margin: 1.5rem 0;
        border-right: 4px solid #059669;
        font-family: 'Inter', sans-serif;
        text-align: right;
        color: #0f172a !important;
        font-weight: 500;
        box-shadow: 0 2px 8px rgba(5, 150, 105, 0.1);
    }

    .user-message strong {
        color: #059669 !important;
    }

    /* Form styling */
    .medical-form {
        background: white;
        padding: 2.5rem;
        border-radius: 16px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
        margin: 2rem 0;
    }

    .form-section {
        margin-bottom: 2.5rem;
        padding-bottom: 1.5rem;
        border-bottom: 2px solid #e2e8f0;
    }

    .form-section:last-child {
        border-bottom: none;
        margin-bottom: 0;
    }

    .form-section h3 {
        color: #1e40af !important;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 1.25rem;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    /* Alert boxes with proper spacing */
    .success-alert {
        background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
        border-left: 6px solid #059669;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin: 2rem 0;
        color: #0f172a !important;
        font-weight: 500;
        box-shadow: 0 4px 12px rgba(5, 150, 105, 0.15);
    }

    .success-alert strong {
        color: #059669 !important;
    }

    .info-alert {
        background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
        border-left: 6px solid #1e40af;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin: 2rem 0;
        color: #0f172a !important;
        font-weight: 500;
        box-shadow: 0 4px 12px rgba(30, 64, 175, 0.15);
    }

    .info-alert strong {
        color: #1e40af !important;
    }

    .warning-alert {
        background: linear-gradient(135deg, #fef3c7 0%, #fed7aa 100%);
        border-left: 6px solid #d97706;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin: 2rem 0;
        color: #0f172a !important;
        font-weight: 500;
        box-shadow: 0 4px 12px rgba(217, 119, 6, 0.15);
    }

    .warning-alert strong {
        color: #d97706 !important;
    }

    /* Appointment Card with Perfect Spacing */
    .appointment-card {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border: 3px solid #0ea5e9;
        border-radius: 20px;
        padding: 2.5rem;
        margin: 3rem 0;
        box-shadow: 0 8px 24px rgba(14, 165, 233, 0.2);
        color: #0f172a !important;
    }

    .appointment-header {
        text-align: center;
        margin-bottom: 2.5rem;
        padding-bottom: 2rem;
        border-bottom: 2px solid #0ea5e9;
    }

    .appointment-id {
        background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
        color: white !important;
        padding: 1rem 2rem;
        border-radius: 30px;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 1.5rem;
        font-family: 'Inter', sans-serif;
        font-size: 1.1rem;
        box-shadow: 0 4px 12px rgba(14, 165, 233, 0.3);
    }

    .appointment-title {
        color: #0ea5e9 !important;
        margin: 0;
        font-size: 1.75rem;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
    }

    .appointment-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 4rem;
        margin-top: 2.5rem;
    }

    .appointment-item {
        display: flex;
        align-items: center;
        margin: 1.25rem 0;
        padding: 1.25rem 1.5rem;
        background: rgba(255, 255, 255, 0.8);
        border-radius: 12px;
        border-left: 4px solid #0ea5e9;
        box-shadow: 0 2px 8px rgba(14, 165, 233, 0.1);
        transition: all 0.2s ease;
    }

    .appointment-item:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(14, 165, 233, 0.2);
    }

    .appointment-icon {
        font-size: 1.4rem;
        margin-right: 1rem;
        width: 2rem;
        text-align: center;
    }

    .appointment-label {
        font-weight: 600;
        color: #1e40af !important;
        margin-right: 0.75rem;
        min-width: 5rem;
    }

    .appointment-value {
        color: #0f172a !important;
        font-weight: 500;
        flex: 1;
    }

    /* Reminder System with Perfect Spacing */
    .reminder-system {
        background: white;
        border-radius: 20px;
        padding: 3rem;
        box-shadow: 0 8px 24px rgba(0,0,0,0.1);
        border: 2px solid #e2e8f0;
        margin: 3rem 0;
    }

    .reminder-header {
        text-align: center;
        margin-bottom: 3rem;
        padding-bottom: 2rem;
        border-bottom: 2px solid #e2e8f0;
    }

    .reminder-title {
        color: #d97706 !important;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 2rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1rem;
    }

    .reminder-subtitle {
        color: #64748b !important;
        font-size: 1.1rem;
        margin: 0;
        font-weight: 400;
    }

    .reminder-cards-container {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 2rem;
        margin-top: 2rem;
    }

    .reminder-card {
        background: linear-gradient(135deg, #fefce8 0%, #fef3c7 100%);
        border: 2px solid #d97706;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 6px 20px rgba(217, 119, 6, 0.15);
        color: #0f172a !important;
        transition: all 0.3s ease;
        height: auto;
        min-height: 300px;
    }

    .reminder-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 32px rgba(217, 119, 6, 0.25);
    }

    .reminder-card h4 {
        color: #d97706 !important;
        margin: 0 0 1.5rem 0;
        font-size: 1.25rem;
        font-weight: 600;
        text-align: center;
        padding-bottom: 1rem;
        border-bottom: 1px solid #d97706;
    }

    .reminder-card p {
        color: #0f172a !important;
        margin: 1rem 0;
        line-height: 1.6;
        font-weight: 500;
    }

    .reminder-card strong {
        color: #d97706 !important;
    }

    .reminder-card ul {
        margin: 1rem 0;
        padding-left: 1.5rem;
    }

    .reminder-card li {
        color: #0f172a !important;
        margin: 0.5rem 0;
        line-height: 1.5;
    }

    /* Info Panel with Proper Spacing */
    .info-panel {
        background: white;
        border-radius: 16px;
        padding: 2.5rem;
        box-shadow: 0 6px 20px rgba(0,0,0,0.1);
        border: 2px solid #e2e8f0;
        margin-top: 2rem;
    }

    .info-panel h3 {
        color: #1e40af !important;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 1.5rem;
        margin-bottom: 2rem;
        text-align: center;
        padding-bottom: 1.5rem;
        border-bottom: 2px solid #e2e8f0;
    }

    .info-panel .alert-item {
        margin: 1.5rem 0;
        padding: 1.25rem;
        border-radius: 10px;
    }

    .info-panel .warning-alert {
        margin: 1.5rem 0;
    }

    .info-panel .info-alert {
        margin: 1.5rem 0;
    }

    .info-panel .success-alert {
        margin: 1.5rem 0;
    }

    /* Metrics styling */
    .metric-card {
        background: white;
        padding: 2rem;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        border: 2px solid #e2e8f0;
        margin-bottom: 1.5rem;
        transition: all 0.2s ease;
    }

    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    }

    .metric-number {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1e40af !important;
        font-family: 'Inter', sans-serif;
        margin-bottom: 0.5rem;
    }

    .metric-label {
        color: #64748b !important;
        font-size: 1rem;
        font-weight: 500;
        margin-top: 0.5rem;
    }

    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        color: white !important;
        border: none;
        border-radius: 12px;
        padding: 1rem 2.5rem;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        font-size: 1rem;
        box-shadow: 0 4px 16px rgba(30, 64, 175, 0.3);
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(30, 64, 175, 0.4);
    }

    .success-button > button {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%);
        box-shadow: 0 4px 16px rgba(5, 150, 105, 0.3);
        color: white !important;
    }

    /* Email preview */
    .email-preview {
        background: #f8fafc;
        border: 2px solid #e2e8f0;
        border-radius: 16px;
        padding: 2.5rem;
        margin: 2rem 0;
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
    }

    .email-preview h4 {
        color: #1e40af !important;
        margin-top: 0;
        font-size: 1.25rem;
    }

    .email-preview p {
        color: #0f172a !important;
        line-height: 1.6;
    }

    .email-content {
        background: white;
        border-left: 6px solid #1e40af;
        padding: 2rem;
        margin: 2rem 0;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(30, 64, 175, 0.1);
    }

    .email-content p {
        color: #0f172a !important;
        margin: 1rem 0;
        line-height: 1.6;
    }

    .email-content strong {
        color: #1e40af !important;
    }

    .critical-instructions {
        background: #fef2f2;
        border: 2px solid #fecaca;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 2rem 0;
    }

    .critical-instructions p {
        color: #991b1b !important;
        margin: 0.75rem 0;
        font-weight: 500;
    }

    .critical-instructions strong {
        color: #dc2626 !important;
    }

    /* Completion card */
    .completion-card {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        color: white !important;
        border-radius: 20px;
        padding: 4rem;
        margin: 3rem 0;
        text-align: center;
        box-shadow: 0 12px 32px rgba(30, 64, 175, 0.3);
    }

    .completion-card h2 {
        margin-top: 0;
        font-size: 2.5rem;
        color: white !important;
        margin-bottom: 1.5rem;
    }

    .completion-card p {
        color: rgba(255,255,255,0.95) !important;
        font-size: 1.3rem;
        margin-bottom: 2.5rem;
        line-height: 1.6;
    }

    .next-steps {
        background: rgba(255,255,255,0.2);
        border-radius: 12px;
        padding: 2rem;
        margin: 2rem 0;
    }

    .next-steps p {
        color: white !important;
        margin: 0.75rem 0;
        font-size: 1.1rem;
    }

    .next-steps strong {
        color: white !important;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Mobile responsive */
    @media (max-width: 768px) {
        .medical-header h1 {
            font-size: 2rem;
        }
        .main > div {
            padding-left: 1rem;
            padding-right: 1rem;
        }
        .appointment-grid {
            grid-template-columns: 1fr;
            gap: 2rem;
        }
        .reminder-cards-container {
            grid-template-columns: 1fr;
            gap: 1.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'current_patient' not in st.session_state:
    st.session_state.current_patient = {}
if 'appointment_data' not in st.session_state:
    st.session_state.appointment_data = {}
if 'step' not in st.session_state:
    st.session_state.step = 'greeting'

# Load data functions
@st.cache_data
def load_patient_data():
    try:
        return pd.read_csv('patients_database.csv')
    except FileNotFoundError:
        st.error("Patient database not found. Please ensure patients_database.csv is available.")
        return pd.DataFrame()

@st.cache_data
def load_schedule_data():
    try:
        return pd.read_excel('doctor_schedules.xlsx', sheet_name='Full_Schedule')
    except FileNotFoundError:
        st.error("Doctor schedule not found. Please ensure doctor_schedules.xlsx is available.")
        return pd.DataFrame()

# AI Agent Class
class AISchedulingAgent:
    def __init__(self):
        self.patients_df = load_patient_data()
        self.schedule_df = load_schedule_data()

    def greet_patient(self):
        return """🏥 **Welcome to MediCare Allergy & Wellness Center!**

I'm your AI scheduling assistant. I'll help you book an appointment with one of our specialists.

To get started, I'll need some basic information:"""

    def search_patient(self, first_name, last_name, dob=None, phone=None):
        """Search for existing patient in database"""
        if self.patients_df.empty:
            return None, False

        name_matches = self.patients_df[
            (self.patients_df['first_name'].str.lower() == first_name.lower()) & 
            (self.patients_df['last_name'].str.lower() == last_name.lower())
        ]

        if len(name_matches) == 1:
            return name_matches.iloc[0].to_dict(), True
        elif len(name_matches) > 1:
            if dob:
                dob_match = name_matches[name_matches['date_of_birth'] == dob]
                if len(dob_match) == 1:
                    return dob_match.iloc[0].to_dict(), True
            if phone:
                phone_match = name_matches[name_matches['phone'] == phone]
                if len(phone_match) == 1:
                    return phone_match.iloc[0].to_dict(), True
            return name_matches.iloc[0].to_dict(), False
        else:
            return None, False

    def book_appointment(self, patient_data, doctor, date, time, duration):
        """Book an appointment and return confirmation details"""
        appointment_id = f"APT{random.randint(10000, 99999)}"

        location_map = {
            'Dr. Sarah Chen': 'Main Clinic - Downtown',
            'Dr. Michael Rodriguez': 'North Branch',
            'Dr. Emily Johnson': 'South Branch',
            'Dr. Robert Kim': 'West Side Clinic'
        }

        booking_data = {
            'appointment_id': appointment_id,
            'patient_name': patient_data.get('full_name', f"{patient_data.get('first_name', '')} {patient_data.get('last_name', '')}"),
            'patient_id': patient_data.get('patient_id', 'NEW'),
            'doctor': doctor,
            'date': date,
            'time': time,
            'duration': duration,
            'location': location_map.get(doctor, 'Main Clinic - Downtown'),
            'patient_type': 'New Patient' if duration == 60 else 'Follow-up',
            'status': 'Confirmed',
            'booking_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'phone': patient_data.get('phone', ''),
            'email': patient_data.get('email', ''),
            'insurance': patient_data.get('insurance_company', 'Not provided')
        }

        return booking_data

def display_appointment_card(appointment):
    """Display appointment details with perfect spacing"""
    appointment_html = f"""
<div class="appointment-card">
    <div class="appointment-header">
        <div class="appointment-id">Appointment ID: {appointment['appointment_id']}</div>
        <h3 class="appointment-title">Your Appointment Details</h3>
    </div>
    <div class="appointment-grid">
        <div>
            <div class="appointment-item">
                <span class="appointment-icon">👤</span>
                <span class="appointment-label">Patient:</span>
                <span class="appointment-value">{appointment['patient_name']}</span>
            </div>
            <div class="appointment-item">
                <span class="appointment-icon">👨‍⚕️</span>
                <span class="appointment-label">Doctor:</span>
                <span class="appointment-value">{appointment['doctor']}</span>
            </div>
            <div class="appointment-item">
                <span class="appointment-icon">📅</span>
                <span class="appointment-label">Date:</span>
                <span class="appointment-value">{appointment['date']}</span>
            </div>
            <div class="appointment-item">
                <span class="appointment-icon">⏰</span>
                <span class="appointment-label">Time:</span>
                <span class="appointment-value">{appointment['time']}</span>
            </div>
        </div>
        <div>
            <div class="appointment-item">
                <span class="appointment-icon">⏱️</span>
                <span class="appointment-label">Duration:</span>
                <span class="appointment-value">{appointment['duration']} minutes</span>
            </div>
            <div class="appointment-item">
                <span class="appointment-icon">🏥</span>
                <span class="appointment-label">Location:</span>
                <span class="appointment-value">{appointment['location']}</span>
            </div>
            <div class="appointment-item">
                <span class="appointment-icon">📋</span>
                <span class="appointment-label">Type:</span>
                <span class="appointment-value">{appointment['patient_type']}</span>
            </div>
            <div class="appointment-item">
                <span class="appointment-icon">✅</span>
                <span class="appointment-label">Status:</span>
                <span class="appointment-value">{appointment['status']}</span>
            </div>
        </div>
    </div>
</div>
"""
    st.markdown(appointment_html, unsafe_allow_html=True)

def display_reminder_system(appointment):
    """Display reminder system with perfect spacing and formatting"""
    appointment_date = datetime.strptime(appointment['date'], '%Y-%m-%d')
    reminder1_date = appointment_date - timedelta(days=3)
    reminder2_date = appointment_date - timedelta(days=1)
    reminder3_date = appointment_date - timedelta(hours=4)

    reminder_html = f"""
<div class="reminder-system">
    <div class="reminder-header">
        <h2 class="reminder-title">🔔 Automated Reminder System</h2>
        <p class="reminder-subtitle">Our intelligent reminder system will keep you informed and ensure you don't miss your appointment.</p>
    </div>
    <div class="reminder-cards-container">
        <div class="reminder-card">
            <h4>📅 Reminder 1</h4>
            <p><strong>When:</strong> {reminder1_date.strftime('%Y-%m-%d')}</p>
            <p><strong>Time:</strong> 72 hours before</p>
            <p><strong>Type:</strong> Standard reminder</p>
            <p><strong>Message:</strong> Please complete your intake form</p>
            <p><strong>Channels:</strong> Email + SMS</p>
        </div>
        <div class="reminder-card">
            <h4>⚠️ Reminder 2</h4>
            <p><strong>When:</strong> {reminder2_date.strftime('%Y-%m-%d')}</p>
            <p><strong>Time:</strong> 24 hours before</p>
            <p><strong>Type:</strong> Interactive check</p>
            <p><strong>Questions:</strong></p>
            <ul>
                <li>Form completed?</li>
                <li>Visit confirmed?</li>
            </ul>
        </div>
        <div class="reminder-card">
            <h4>🚨 Final Reminder</h4>
            <p><strong>When:</strong> {reminder3_date.strftime('%Y-%m-%d %H:%M')}</p>
            <p><strong>Time:</strong> 4 hours before</p>
            <p><strong>Type:</strong> Final confirmation</p>
            <p><strong>Actions:</strong></p>
            <ul>
                <li>Confirm attendance</li>
                <li>Cancel if needed</li>
            </ul>
        </div>
    </div>
</div>
"""
    st.markdown(reminder_html, unsafe_allow_html=True)

def generate_ics_file(appointment):
    """Generates an .ics calendar file content from appointment details."""
    start_time_str = f"{appointment['date']} {appointment['time']}"
    start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M')
    end_time = start_time + timedelta(minutes=appointment['duration'])

    # Format for ICS file
    start_utc = start_time.strftime('%Y%m%dT%H%M%S')
    end_utc = end_time.strftime('%Y%m%dT%H%M%S')

    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
SUMMARY:Medical Appointment: {appointment['patient_name']}
DTSTART:{start_utc}
DTEND:{end_utc}
LOCATION:{appointment['location']}
DESCRIPTION:Appointment with {appointment['doctor']}. Appointment ID: {appointment['appointment_id']}.
END:VEVENT
END:VCALENDAR
""".strip()
    return ics_content

def main():
    # Medical Header
    st.markdown("""
    <div class="medical-header">
        <h1>🏥 MediCare AI Scheduling Agent</h1>
        <p>Intelligent Appointment Scheduling for Allergy & Wellness Care</p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize AI agent
    agent = AISchedulingAgent()

    # Sidebar with medical dashboard
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1.5rem 0; border-bottom: 2px solid #e2e8f0; margin-bottom: 1.5rem;">
            <h2 style="color: #1e40af; font-family: 'Inter', sans-serif; font-weight: 600; margin: 0; font-size: 1.5rem;">
                📊 Medical Dashboard
            </h2>
        </div>
        """, unsafe_allow_html=True)

        # Patient Status
        if st.session_state.current_patient:
            st.markdown(f"""
            <div class="status-card">
                <h4>✅ Patient Information</h4>
                <p><strong>Name:</strong> {st.session_state.current_patient.get('full_name', 'Unknown')}</p>
                <p><strong>Type:</strong> {st.session_state.current_patient.get('patient_type', 'Unknown')}</p>
                <p><strong>ID:</strong> {st.session_state.current_patient.get('patient_id', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)

        # Appointment Status
        if st.session_state.appointment_data:
            st.markdown(f"""
            <div class="status-card">
                <h4>✅ Appointment Scheduled</h4>
                <p><strong>Date:</strong> {st.session_state.appointment_data.get('date', 'Unknown')}</p>
                <p><strong>Time:</strong> {st.session_state.appointment_data.get('time', 'Unknown')}</p>
                <p><strong>Doctor:</strong> {st.session_state.appointment_data.get('doctor', 'Unknown')}</p>
                <p><strong>Duration:</strong> {st.session_state.appointment_data.get('duration', 'Unknown')} min</p>
            </div>
            """, unsafe_allow_html=True)

        # System Statistics
        st.markdown("""
        <div style="margin-top: 2.5rem;">
            <h3 style="color: #1e40af; font-family: 'Inter', sans-serif; font-weight: 600; margin-bottom: 1.5rem; font-size: 1.25rem;">
                📈 System Statistics
            </h3>
        </div>
        """, unsafe_allow_html=True)

        # Metrics
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-number">50</div>
                <div class="metric-label">Total Patients</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class="metric-card">
                <div class="metric-number">28</div>
                <div class="metric-label">New Patients</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-number">918</div>
                <div class="metric-label">Available Slots</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class="metric-card">
                <div class="metric-number">22</div>
                <div class="metric-label">Returning Patients</div>
            </div>
            """, unsafe_allow_html=True)

        # Quick Actions
        st.markdown("""
        <div style="margin-top: 2.5rem; padding-top: 1.5rem; border-top: 2px solid #e2e8f0;">
            <h3 style="color: #1e40af; font-family: 'Inter', sans-serif; font-weight: 600; margin-bottom: 1.5rem; font-size: 1.25rem;">
                ⚡ Quick Actions
            </h3>
        </div>
        """, unsafe_allow_html=True)

        if st.button("👥 View Sample Patients", use_container_width=True):
            sample_patients = pd.DataFrame([
                {'Name': 'Kenneth Davis', 'Type': 'New', 'Phone': '(450) 428-3286'},
                {'Name': 'Joseph Lewis', 'Type': 'New', 'Phone': '(206) 977-3615'},
                {'Name': 'Betty Moore', 'Type': 'Returning', 'Phone': '(935) 522-4483'}
            ])
            st.dataframe(sample_patients, use_container_width=True)

        if st.button("📅 View Today's Schedule", use_container_width=True):
            today_schedule = pd.DataFrame([
                {'Doctor': 'Dr. Sarah Chen', 'Time': '09:00', 'Available': '✅'},
                {'Doctor': 'Dr. Sarah Chen', 'Time': '09:30', 'Available': '✅'},
                {'Doctor': 'Dr. Sarah Chen', 'Time': '10:00', 'Available': '❌'},
                {'Doctor': 'Dr. Michael Rodriguez', 'Time': '14:00', 'Available': '✅'}
            ])
            st.dataframe(today_schedule, use_container_width=True)

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        # Conversation Container
        st.markdown("""
        <div class="chat-container">
            <h2 style="color: #1e40af; font-family: 'Inter', sans-serif; font-weight: 600; margin-bottom: 2rem; display: flex; align-items: center; gap: 1rem; font-size: 1.75rem;">
                💬 Patient Consultation
            </h2>
        """, unsafe_allow_html=True)

        # Display conversation history
        for message in st.session_state.conversation_history:
            if message['role'] == 'assistant':
                st.markdown(f"""
                <div class="ai-message">
                    <strong>🤖 AI Medical Assistant:</strong><br>
                    {message['content']}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="user-message">
                    <strong>👤 You:</strong><br>
                    {message['content']}
                </div>
                """, unsafe_allow_html=True)

        # Handle different conversation steps
        if st.session_state.step == 'greeting':
            greeting = agent.greet_patient()
            if not any(msg['content'] == greeting for msg in st.session_state.conversation_history):
                st.session_state.conversation_history.append({'role': 'assistant', 'content': greeting})
                st.markdown(f"""
                <div class="ai-message">
                    <strong>🤖 AI Medical Assistant:</strong><br>
                    {greeting}
                </div>
                """, unsafe_allow_html=True)

            # Patient Information Form
            st.markdown("""
            <div class="medical-form">
                <div class="form-section">
                    <h3>📝 Patient Information</h3>
                </div>
            """, unsafe_allow_html=True)

            with st.form("patient_info_form"):
                col_a, col_b = st.columns(2)
                with col_a:
                    first_name = st.text_input("First Name *", key="first_name", placeholder="Enter your first name")
                    dob = st.date_input(
                        "Date of Birth *", 
                        key="dob", 
                        min_value=date(1960, 1, 1),
                        max_value=date.today(),
                        value=date(1990, 1, 1)
                    )
                with col_b:
                    last_name = st.text_input("Last Name *", key="last_name", placeholder="Enter your last name")
                    phone = st.text_input("Phone Number *", placeholder="(555) 123-4567", key="phone")

                email = st.text_input("Email Address *", key="email", placeholder="your.email@example.com")

                st.markdown('<div class="success-button">', unsafe_allow_html=True)
                submitted = st.form_submit_button("🔍 Find My Information", use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

                if submitted and first_name and last_name and phone and email:
                    # Search for patient
                    patient_data, found = agent.search_patient(first_name, last_name, dob.strftime('%m/%d/%Y'), phone)

                    if patient_data:
                        st.session_state.current_patient = patient_data
                        patient_type = patient_data['patient_type']

                        st.markdown(f"""
                        <div class="success-alert">
                            <strong>✅ Patient Found:</strong> {patient_data['full_name']} ({patient_type})
                        </div>
                        """, unsafe_allow_html=True)

                        response = f"Great! I found your information, {first_name}. You're a {patient_type.lower()} patient."
                        if patient_type == 'Returning':
                            response += f" Your last visit was on {patient_data.get('last_visit', 'N/A')}."

                        st.session_state.conversation_history.append({'role': 'user', 'content': f"My name is {first_name} {last_name}"})
                        st.session_state.conversation_history.append({'role': 'assistant', 'content': response})

                    else:
                        # New patient
                        new_patient_data = {
                            'patient_id': 'NEW',
                            'first_name': first_name,
                            'last_name': last_name,
                            'full_name': f"{first_name} {last_name}",
                            'date_of_birth': dob.strftime('%m/%d/%Y'),
                            'phone': phone,
                            'email': email,
                            'patient_type': 'New',
                            'last_visit': None
                        }
                        st.session_state.current_patient = new_patient_data

                        st.markdown(f"""
                        <div class="info-alert">
                            <strong>👋 Welcome New Patient!</strong> We'll schedule a 60-minute comprehensive consultation.
                        </div>
                        """, unsafe_allow_html=True)

                        response = f"Welcome to MediCare, {first_name}! I see you're a new patient. We'll schedule a 60-minute appointment for your initial consultation."
                        st.session_state.conversation_history.append({'role': 'user', 'content': f"My name is {first_name} {last_name}"})
                        st.session_state.conversation_history.append({'role': 'assistant', 'content': response})

                    st.session_state.step = 'scheduling'
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

        elif st.session_state.step == 'scheduling':
            st.markdown("""
            <div class="medical-form">
                <div class="form-section">
                    <h3>📅 Schedule Your Appointment</h3>
                </div>
            """, unsafe_allow_html=True)

            patient_type = st.session_state.current_patient.get('patient_type', 'New')
            duration = 60 if patient_type == 'New' else 30

            st.markdown(f"""
            <div class="warning-alert">
                <strong>⏱️ Appointment Duration:</strong> {duration} minutes ({patient_type} Patient)
            </div>
            """, unsafe_allow_html=True)

            with st.form("scheduling_form"):
                col_a, col_b = st.columns(2)

                with col_a:
                    doctors = ['Dr. Sarah Chen', 'Dr. Michael Rodriguez', 'Dr. Emily Johnson', 'Dr. Robert Kim']
                    selected_doctor = st.selectbox("Preferred Doctor 👨‍⚕️", doctors, key="doctor")

                with col_b:
                    # Date selection
                    available_dates = []
                    for i in range(1, 8):
                        future_date = datetime.now() + timedelta(days=i)
                        if future_date.weekday() < 5:  # Weekdays only
                            available_dates.append(future_date.strftime('%Y-%m-%d'))

                    selected_date = st.selectbox("Preferred Date 📅", available_dates, key="date")

                # Time slots
                time_slots = ['09:00', '09:30', '10:00', '10:30', '11:00', '11:30', '14:00', '14:30', '15:00', '15:30']
                selected_time = st.selectbox("Available Time Slots ⏰", time_slots, key="time")

                # Insurance section
                st.markdown("""
                <div class="form-section">
                    <h3>💳 Insurance Information</h3>
                </div>
                """, unsafe_allow_html=True)

                col_c, col_d = st.columns(2)

                with col_c:
                    insurance_company = st.text_input("Insurance Company", 
                        value=st.session_state.current_patient.get('insurance_company', ''), 
                        key="insurance", placeholder="Blue Cross Blue Shield")
                    member_id = st.text_input("Member ID", 
                        value=st.session_state.current_patient.get('member_id', ''), 
                        key="member_id", placeholder="ABC123456")

                with col_d:
                    group_number = st.text_input("Group Number", 
                        value=st.session_state.current_patient.get('group_number', ''), 
                        key="group_num", placeholder="GRP5678")

                st.markdown('<div class="success-button">', unsafe_allow_html=True)
                book_appointment = st.form_submit_button("📅 Confirm Appointment", type="primary", use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

                if book_appointment:
                    # Update patient data with insurance info
                    st.session_state.current_patient.update({
                        'insurance_company': insurance_company,
                        'member_id': member_id,
                        'group_number': group_number
                    })

                    # Book the appointment
                    appointment = agent.book_appointment(
                        st.session_state.current_patient, 
                        selected_doctor, 
                        selected_date, 
                        selected_time, 
                        duration
                    )

                    st.session_state.appointment_data = appointment
                    st.session_state.step = 'confirmation'
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

        elif st.session_state.step == 'confirmation':
            appointment = st.session_state.appointment_data

            # Success header
            st.markdown("""
            <div class="success-alert" style="text-align: center; padding: 3rem; margin: 3rem 0; box-shadow: 0 8px 32px rgba(5, 150, 105, 0.2);">
                <h1 style="color: #059669; font-size: 3rem; margin: 0;">🎉</h1>
                <h2 style="color: #059669; margin: 1rem 0; font-size: 2rem;">Appointment Confirmed!</h2>
                <p style="color: #047857; margin: 0; font-size: 1.2rem;">Your appointment has been successfully scheduled</p>
            </div>
            """, unsafe_allow_html=True)

            # Display appointment card
            display_appointment_card(appointment)

            # Form distribution section
            st.markdown("""
            <div class="medical-form">
                <div class="form-section">
                    <h3>📧 Patient Intake Form Distribution</h3>
                    <p style="color: #64748b; font-size: 1.1rem; line-height: 1.6;">We'll send you a comprehensive intake form to complete before your visit.</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("📨 Send Intake Form Email", type="primary", use_container_width=True):
                # Email preview
                st.markdown(f"""
                <div class="email-preview">
                    <h4>📧 Email Sent Successfully!</h4>
                    <p><strong>To:</strong> {appointment['email']}</p>
                    <p><strong>Subject:</strong> Complete Your Intake Form - Appointment on {appointment['date']}</p>

                    <div class="email-content">
                        <p><strong>Dear {appointment['patient_name']},</strong></p>
                        <p>Thank you for scheduling your appointment with {appointment['doctor']} on {appointment['date']} at {appointment['time']}.</p>

                        <div class="critical-instructions">
                            <p><strong>⚠️ CRITICAL INSTRUCTIONS:</strong></p>
                            <p>Please <strong>STOP taking all antihistamines</strong> (Claritin, Zyrtec, Allegra, Benadryl) <strong>7 days before</strong> your appointment.</p>
                            <p><strong>You may continue:</strong> Nasal sprays, asthma inhalers, and prescription medications.</p>
                        </div>

                        <p><strong>Please bring:</strong></p>
                        <ul>
                            <li>Photo ID</li>
                            <li>Insurance cards</li>
                            <li>List of current medications</li>
                        </ul>

                        <p>Best regards,<br>MediCare Allergy & Wellness Center</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Download button for Excel confirmation
                appointments_df = pd.DataFrame([appointment])
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    appointments_df.to_excel(writer, index=False, sheet_name='Appointment')
                excel_data = output.getvalue()

                st.download_button(
                    label="📥 Download Appointment Confirmation (Excel)",
                    data=excel_data,
                    file_name=f"appointment_{appointment['appointment_id']}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

                # Generate and offer .ics file for download
                ics_file = generate_ics_file(appointment)
                st.download_button(
                    label="📅 Add to Calendar (.ics)",
                    data=ics_file,
                    file_name=f"appointment_{appointment['appointment_id']}.ics",
                    mime="text/calendar",
                    use_container_width=True
                )

                st.session_state.step = 'reminders'
                st.rerun()

        elif st.session_state.step == 'reminders':
            appointment = st.session_state.appointment_data

            # Display reminder system with proper formatting
            display_reminder_system(appointment)

            # Simulate reminder system
            if st.button("🎬 Activate Reminder System", type="primary", use_container_width=True):
                st.markdown("""
                <div class="success-alert" style="text-align: center; padding: 3rem; margin: 3rem 0; box-shadow: 0 8px 24px rgba(5, 150, 105, 0.2);">
                    <h3 style="color: #059669; margin-top: 0; font-size: 2rem;">✅ Reminder System Activated!</h3>
                    <p style="color: #047857; margin-bottom: 0; font-size: 1.2rem;">All automated reminders have been scheduled successfully.</p>
                </div>
                """, unsafe_allow_html=True)

                # Create reminder data
                appointment_date = datetime.strptime(appointment['date'], '%Y-%m-%d')
                reminder1_date = appointment_date - timedelta(days=3)
                reminder2_date = appointment_date - timedelta(days=1)
                reminder3_date = appointment_date - timedelta(hours=4)

                reminder_data = []

                reminder1 = {
                    'reminder_id': 'REM001',
                    'appointment_id': appointment['appointment_id'],
                    'reminder_number': 1,
                    'scheduled_date': reminder1_date.strftime('%Y-%m-%d'),
                    'type': 'Standard',
                    'status': 'Scheduled',
                    'message': f"Hi {appointment['patient_name']}, reminder about your appointment with {appointment['doctor']} on {appointment['date']} at {appointment['time']}. Please complete your intake form.",
                    'channels': 'Email, SMS'
                }

                reminder2 = {
                    'reminder_id': 'REM002',
                    'appointment_id': appointment['appointment_id'],
                    'reminder_number': 2,
                    'scheduled_date': reminder2_date.strftime('%Y-%m-%d'),
                    'type': 'Interactive',
                    'status': 'Scheduled',
                    'message': f"Hi {appointment['patient_name']}, your appointment is tomorrow. Have you completed your intake form? Is your visit confirmed?",
                    'channels': 'Email, SMS'
                }

                reminder3 = {
                    'reminder_id': 'REM003',
                    'appointment_id': appointment['appointment_id'],
                    'reminder_number': 3,
                    'scheduled_date': reminder3_date.strftime('%Y-%m-%d %H:%M'),
                    'type': 'Final',
                    'status': 'Scheduled',
                    'message': f"Final reminder: Your appointment with {appointment['doctor']} is in 4 hours. Please confirm attendance.",
                    'channels': 'Email, SMS'
                }

                reminder_data = [reminder1, reminder2, reminder3]
                reminders_df = pd.DataFrame(reminder_data)

                st.subheader("📱 Reminder Schedule")
                st.dataframe(reminders_df, use_container_width=True)

                # Download reminder schedule as Excel
                output_reminders = io.BytesIO()
                with pd.ExcelWriter(output_reminders, engine='xlsxwriter') as writer:
                    reminders_df.to_excel(writer, index=False, sheet_name='Reminders')
                excel_reminders = output_reminders.getvalue()

                st.download_button(
                    label="📥 Download Reminder Schedule (Excel)",
                    data=excel_reminders,
                    file_name=f"reminders_{appointment['appointment_id']}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

                # Success completion
                st.balloons()

                st.markdown("""
                <div class="completion-card">
                    <h2>🏆 Workflow Complete!</h2>
                    <p>Your appointment has been successfully scheduled with all automated systems activated.</p>
                    <div class="next-steps">
                        <p><strong>Next Steps:</strong></p>
                        <p>• Check your email for the intake form</p>
                        <p>• Stop antihistamines 7 days before your appointment</p>
                        <p>• Bring your ID and insurance cards</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button("🔄 Schedule Another Appointment", use_container_width=True):
                    # Reset session state
                    for key in list(st.session_state.keys()):
                        if key not in ['conversation_history']:
                            del st.session_state[key]
                    st.session_state.step = 'greeting'
                    st.session_state.conversation_history = []
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        # Right column content with proper spacing
        st.markdown("""
        <div class="info-panel">
            <h3>ℹ️ Important Information</h3>
            <div class="warning-alert">
                <p><strong>⚠️ Medication Alert:</strong> Stop all antihistamines 7 days before allergy testing.</p>
            </div>
            <div class="info-alert">
                <p><strong>📋 Forms:</strong> Complete intake forms 24 hours before your visit.</p>
            </div>
            <div class="success-alert">
                <p><strong>🔔 Reminders:</strong> You'll receive 3 automated reminders via email and SMS.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
