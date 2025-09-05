import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
import random
import os

# Configure page
st.set_page_config(
    page_title="MediCare AI Scheduling Agent", 
    page_icon="🏥", 
    layout="wide"
)

# Initialize session state
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'current_patient' not in st.session_state:
    st.session_state.current_patient = {}
if 'appointment_data' not in st.session_state:
    st.session_state.appointment_data = {}
if 'step' not in st.session_state:
    st.session_state.step = 'greeting'

# Load data
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

# AI Agent Functions
class AISchedulingAgent:
    def __init__(self):
        self.patients_df = load_patient_data()
        self.schedule_df = load_schedule_data()

    def greet_patient(self):
        return """
        🏥 **Welcome to MediCare Allergy & Wellness Center!**

        I'm your AI scheduling assistant. I'll help you book an appointment with one of our specialists.

        To get started, I'll need some basic information:
        """

    def search_patient(self, first_name, last_name, dob=None, phone=None):
        """Search for existing patient in database"""
        if self.patients_df.empty:
            return None, False

        # Search by name first
        name_matches = self.patients_df[
            (self.patients_df['first_name'].str.lower() == first_name.lower()) & 
            (self.patients_df['last_name'].str.lower() == last_name.lower())
        ]

        if len(name_matches) == 1:
            return name_matches.iloc[0].to_dict(), True
        elif len(name_matches) > 1:
            # Multiple matches, need additional verification
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

    def get_available_slots(self, doctor, date, duration=30):
        """Get available time slots for a doctor on a specific date"""
        if self.schedule_df.empty:
            return pd.DataFrame()

        day_schedule = self.schedule_df[
            (self.schedule_df['doctor'] == doctor) & 
            (self.schedule_df['date'] == date) & 
            (self.schedule_df['is_available'] == True)
        ].copy()

        if duration == 60:  # New patient needs 60 minutes
            # Find consecutive 30-minute slots
            available_60min_slots = []
            sorted_schedule = day_schedule.sort_values('time_slot')

            for i in range(len(sorted_schedule) - 1):
                current_slot = sorted_schedule.iloc[i]
                next_slot = sorted_schedule.iloc[i + 1]

                current_time = datetime.strptime(current_slot['time_slot'], '%H:%M')
                next_time = datetime.strptime(next_slot['time_slot'], '%H:%M')

                if (next_time - current_time).seconds == 1800:  # 30 minutes apart
                    available_60min_slots.append(current_slot)

            return pd.DataFrame(available_60min_slots)

        return day_schedule

    def book_appointment(self, patient_data, doctor, date, time, duration):
        """Book an appointment and return confirmation details"""
        appointment_id = f"APT{random.randint(10000, 99999)}"

        # Get doctor location
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

    def send_intake_form(self, patient_email, appointment_data):
        """Simulate sending intake form via email"""
        form_message = f"""
📧 **Intake Form Sent Successfully!**

**To:** {patient_email}
**Subject:** Complete Your Intake Form - Appointment on {appointment_data['date']}

**Email Content Preview:**
---
Dear {appointment_data['patient_name']},

Thank you for scheduling your appointment with {appointment_data['doctor']} on {appointment_data['date']} at {appointment_data['time']}.

**IMPORTANT:** Please complete your patient intake form at least 24 hours before your appointment.

📋 **Intake Form Link:** [Secure Form Access - Medicare Allergy & Wellness]

**Pre-Visit Instructions:**
⚠️ **CRITICAL:** Stop taking all antihistamines (Claritin, Zyrtec, Allegra, Benadryl) 7 days before your appointment.

You may continue: Nasal sprays, asthma inhalers, and prescription medications.

Please bring:
• Photo ID
• Insurance cards
• List of current medications

If you have questions, call (555) 123-4567.

Best regards,
MediCare Allergy & Wellness Center
---
        """
        return form_message

def main():
    st.title("🏥 MediCare AI Scheduling Agent")
    st.markdown("### Intelligent Appointment Scheduling for Allergy & Wellness Care")

    # Initialize AI agent
    agent = AISchedulingAgent()

    # Sidebar with patient info
    st.sidebar.header("📊 Dashboard")
    if st.session_state.current_patient:
        st.sidebar.success("✅ Patient Information Collected")
        st.sidebar.write(f"**Name:** {st.session_state.current_patient.get('full_name', 'Unknown')}")
        st.sidebar.write(f"**Type:** {st.session_state.current_patient.get('patient_type', 'Unknown')}")

    if st.session_state.appointment_data:
        st.sidebar.success("✅ Appointment Scheduled")
        st.sidebar.write(f"**Date:** {st.session_state.appointment_data.get('date', 'Unknown')}")
        st.sidebar.write(f"**Time:** {st.session_state.appointment_data.get('time', 'Unknown')}")
        st.sidebar.write(f"**Doctor:** {st.session_state.appointment_data.get('doctor', 'Unknown')}")

    # Main conversation area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("💬 Conversation")

        # Display conversation history
        for message in st.session_state.conversation_history:
            if message['role'] == 'assistant':
                st.markdown(f"🤖 **AI Agent:** {message['content']}")
            else:
                st.markdown(f"👤 **You:** {message['content']}")

        # Handle different conversation steps
        if st.session_state.step == 'greeting':
            greeting = agent.greet_patient()
            if not any(msg['content'] == greeting for msg in st.session_state.conversation_history):
                st.session_state.conversation_history.append({'role': 'assistant', 'content': greeting})
                st.markdown(f"🤖 **AI Agent:** {greeting}")

            # Patient information form
            st.subheader("📝 Please provide your information:")

            with st.form("patient_info_form"):
                col_a, col_b = st.columns(2)
                with col_a:
                    first_name = st.text_input("First Name*", key="first_name")
                    dob = st.date_input("Date of Birth*", key="dob")
                with col_b:
                    last_name = st.text_input("Last Name*", key="last_name")
                    phone = st.text_input("Phone Number*", placeholder="(555) 123-4567", key="phone")

                email = st.text_input("Email Address*", key="email")

                submitted = st.form_submit_button("🔍 Find My Information")

                if submitted and first_name and last_name and phone and email:
                    # Search for patient
                    patient_data, found = agent.search_patient(first_name, last_name, dob.strftime('%m/%d/%Y'), phone)

                    if patient_data:
                        st.session_state.current_patient = patient_data
                        patient_type = patient_data['patient_type']
                        st.success(f"✅ Found existing patient: {patient_data['full_name']} ({patient_type})")

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
                        st.info("👋 Welcome! You're a new patient. We'll need to collect some additional information.")

                        response = f"Welcome to MediCare, {first_name}! I see you're a new patient. We'll schedule a 60-minute appointment for your initial consultation."
                        st.session_state.conversation_history.append({'role': 'user', 'content': f"My name is {first_name} {last_name}"})
                        st.session_state.conversation_history.append({'role': 'assistant', 'content': response})

                    st.session_state.step = 'scheduling'
                    st.rerun()

        elif st.session_state.step == 'scheduling':
            st.subheader("📅 Schedule Your Appointment")

            patient_type = st.session_state.current_patient.get('patient_type', 'New')
            duration = 60 if patient_type == 'New' else 30

            st.info(f"**Appointment Duration:** {duration} minutes ({patient_type} Patient)")

            with st.form("scheduling_form"):
                col_a, col_b = st.columns(2)

                with col_a:
                    doctors = ['Dr. Sarah Chen', 'Dr. Michael Rodriguez', 'Dr. Emily Johnson', 'Dr. Robert Kim']
                    selected_doctor = st.selectbox("Preferred Doctor", doctors, key="doctor")

                with col_b:
                    # Date selection (next 7 days for demo)
                    available_dates = []
                    for i in range(1, 8):
                        future_date = datetime.now() + timedelta(days=i)
                        if future_date.weekday() < 5:  # Weekdays only
                            available_dates.append(future_date.strftime('%Y-%m-%d'))

                    selected_date = st.selectbox("Preferred Date", available_dates, key="date")

                # Mock available slots
                time_slots = ['09:00', '09:30', '10:00', '10:30', '11:00', '11:30', '14:00', '14:30', '15:00', '15:30']
                selected_time = st.selectbox("Available Time Slots", time_slots, key="time")

                # Insurance information
                st.subheader("💳 Insurance Information")
                col_c, col_d = st.columns(2)

                with col_c:
                    insurance_company = st.text_input("Insurance Company", 
                        value=st.session_state.current_patient.get('insurance_company', ''), key="insurance")
                    member_id = st.text_input("Member ID", 
                        value=st.session_state.current_patient.get('member_id', ''), key="member_id")

                with col_d:
                    group_number = st.text_input("Group Number", 
                        value=st.session_state.current_patient.get('group_number', ''), key="group_num")

                book_appointment = st.form_submit_button("📅 Confirm Appointment", type="primary")

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

        elif st.session_state.step == 'confirmation':
            st.success("🎉 **Appointment Confirmed!**")

            appointment = st.session_state.appointment_data

            # Display appointment details
            st.subheader("📋 Appointment Details")

            col_a, col_b = st.columns(2)
            with col_a:
                st.write(f"**Appointment ID:** {appointment['appointment_id']}")
                st.write(f"**Patient:** {appointment['patient_name']}")
                st.write(f"**Doctor:** {appointment['doctor']}")
                st.write(f"**Date:** {appointment['date']}")

            with col_b:
                st.write(f"**Time:** {appointment['time']}")
                st.write(f"**Duration:** {appointment['duration']} minutes")
                st.write(f"**Location:** {appointment['location']}")
                st.write(f"**Type:** {appointment['patient_type']}")

            # Send intake form
            st.subheader("📧 Sending Intake Form")

            if st.button("📨 Send Intake Form Email", type="primary"):
                form_email = agent.send_intake_form(appointment['email'], appointment)
                st.text_area("Email Preview:", form_email, height=400)

                # Save appointment to CSV
                appointments_df = pd.DataFrame([appointment])
                csv_data = appointments_df.to_csv(index=False)

                st.download_button(
                    label="📥 Download Appointment Confirmation",
                    data=csv_data,
                    file_name=f"appointment_{appointment['appointment_id']}.csv",
                    mime="text/csv"
                )

                st.session_state.step = 'reminders'
                st.rerun()

        elif st.session_state.step == 'reminders':
            st.subheader("🔔 Automated Reminder System")

            appointment = st.session_state.appointment_data
            appointment_date = datetime.strptime(appointment['date'], '%Y-%m-%d')

            # Calculate reminder dates
            reminder1_date = appointment_date - timedelta(days=3)
            reminder2_date = appointment_date - timedelta(days=1)
            reminder3_date = appointment_date - timedelta(hours=4)

            st.info("The following automated reminders will be sent:")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("### 📅 Reminder 1")
                st.write(f"**Date:** {reminder1_date.strftime('%Y-%m-%d')}")
                st.write(f"**Time:** 72 hours before")
                st.write("**Type:** Standard reminder")
                st.write("**Content:** Please complete your intake form")
                st.write("**Channels:** Email + SMS")

            with col2:
                st.markdown("### ⚠️ Reminder 2")
                st.write(f"**Date:** {reminder2_date.strftime('%Y-%m-%d')}")
                st.write(f"**Time:** 24 hours before")
                st.write("**Type:** Action-based")
                st.write("**Questions:**")
                st.write("• Have you completed the intake form?")
                st.write("• Is your appointment confirmed?")

            with col3:
                st.markdown("### 🚨 Reminder 3")
                st.write(f"**Date:** {reminder3_date.strftime('%Y-%m-%d %H:%M')}")
                st.write(f"**Time:** 4 hours before")
                st.write("**Type:** Final confirmation")
                st.write("**Questions:**")
                st.write("• Final visit confirmation")
                st.write("• If canceling, please provide reason")

            # Demo reminder simulation
            if st.button("🎬 Simulate Reminder System", type="primary"):
                st.subheader("📱 Reminder Simulation")

                reminder_data = []

                # Reminder 1
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

                # Reminder 2
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

                # Reminder 3
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

                st.dataframe(reminders_df, use_container_width=True)

                # Save reminders schedule
                csv_reminders = reminders_df.to_csv(index=False)

                st.download_button(
                    label="📥 Download Reminder Schedule",
                    data=csv_reminders,
                    file_name=f"reminders_{appointment['appointment_id']}.csv",
                    mime="text/csv"
                )

                st.success("✅ **Complete Workflow Finished!**")
                st.balloons()

                if st.button("🔄 Start New Appointment"):
                    # Reset session state
                    for key in list(st.session_state.keys()):
                        if key not in ['conversation_history']:
                            del st.session_state[key]
                    st.session_state.step = 'greeting'
                    st.session_state.conversation_history = []
                    st.rerun()

    with col2:
        st.subheader("📊 System Statistics")

        # Mock statistics
        st.metric("Total Patients in Database", "50")
        st.metric("New Patients", "22") 
        st.metric("Returning Patients", "28")
        st.metric("Available Slots Today", "45")
        st.metric("Booked Slots Today", "12")

        # Quick actions
        st.subheader("⚡ Quick Actions")

        if st.button("👥 View Sample Patients"):
            sample_patients = pd.DataFrame([
                {'Name': 'Kenneth Davis', 'Type': 'New', 'Phone': '(450) 428-3286'},
                {'Name': 'Joseph Lewis', 'Type': 'New', 'Phone': '(206) 977-3615'},
                {'Name': 'Betty Moore', 'Type': 'Returning', 'Phone': '(935) 522-4483'}
            ])
            st.dataframe(sample_patients, use_container_width=True)

        if st.button("📅 View Today's Schedule"):
            today_schedule = pd.DataFrame([
                {'Doctor': 'Dr. Sarah Chen', 'Time': '09:00', 'Available': '✅'},
                {'Doctor': 'Dr. Sarah Chen', 'Time': '09:30', 'Available': '✅'},
                {'Doctor': 'Dr. Sarah Chen', 'Time': '10:00', 'Available': '❌'},
                {'Doctor': 'Dr. Michael Rodriguez', 'Time': '14:00', 'Available': '✅'}
            ])
            st.dataframe(today_schedule, use_container_width=True)

if __name__ == "__main__":
    main()
