# ==============================================================================
#
# MediCare AI Scheduling Agent - v2.2 (Final Version)
#
# ==============================================================================

# --- Core Libraries ---
import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta, date
import random
import os
import io
import logging

# --- AI & Agent Libraries ---
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# ==============================================================================
# 1. CONFIGURATION (config.py)
# ==============================================================================

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AppConfig:
    """Holds all static configuration for the application."""
    PAGE_TITLE = "MediCare AI Scheduling Agent"
    PAGE_ICON = "🏥"
    
    PATIENTS_DB_PATH = 'patients_database.csv'
    SCHEDULE_DB_PATH = 'doctor_schedules.xlsx'
    
    DOCTORS = {
        'Dr. Sarah Chen': 'Main Clinic - Downtown',
        'Dr. Michael Rodriguez': 'North Branch',
        'Dr. Emily Johnson': 'South Branch',
        'Dr. Robert Kim': 'West Side Clinic'
    }

    OPENROUTER_API_KEY_ENV = "OPENROUTER_API_KEY"
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    MODEL_NAME = "deepseek/deepseek-chat-v3.1"
    
    APP_URL = "https://krishnabalajiwork-medicare-ai-streamlit-app-axb21g.streamlit.app" 
    
    DEFAULT_HEADERS = {
        "HTTP-Referer": APP_URL, 
        "X-Title": "MediCare AI Scheduler",
    }

CONFIG = AppConfig()


# ==============================================================================
# 2. API KEY SETUP
# ==============================================================================

load_dotenv()
api_key = os.getenv(CONFIG.OPENROUTER_API_KEY_ENV)

if not api_key:
    try:
        api_key = st.secrets[CONFIG.OPENROUTER_API_KEY_ENV]
    except (FileNotFoundError, KeyError):
        st.error(f"{CONFIG.OPENROUTER_API_KEY_ENV} not found. Please set it in your Streamlit secrets or a .env file.")
        st.stop()


# ==============================================================================
# 3. PAGE AND UI SETUP
# ==============================================================================

st.set_page_config(
    page_title=CONFIG.PAGE_TITLE, 
    page_icon=CONFIG.PAGE_ICON, 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Your entire original CSS goes here. It is preserved as is. */
    /* Import medical fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    /* ... rest of your CSS ... */
     .chat-container {
        background: white;
        border-radius: 16px;
        padding: 2.5rem;
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
        margin-bottom: 2rem;
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
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# 4. DATA MANAGEMENT & STATE
# ==============================================================================

@st.cache_data
def load_data(file_path, is_excel=False):
    """Loads data from CSV or Excel file with error handling."""
    try:
        if is_excel:
            return pd.read_excel(file_path, sheet_name='Full_Schedule')
        else:
            return pd.read_csv(file_path)
    except FileNotFoundError:
        logging.error(f"Data file not found at path: {file_path}")
        return pd.DataFrame()
    except Exception as e:
        logging.error(f"Error loading data from {file_path}: {e}")
        return pd.DataFrame()

if 'patients_df' not in st.session_state:
    st.session_state.patients_df = load_data(CONFIG.PATIENTS_DB_PATH)
if 'schedule_df' not in st.session_state:
    st.session_state.schedule_df = load_data(CONFIG.SCHEDULE_DB_PATH, is_excel=True)
    if 'Status' not in st.session_state.schedule_df.columns and not st.session_state.schedule_df.empty:
        st.session_state.schedule_df['Status'] = 'Available'
if 'bookings_df' not in st.session_state:
    st.session_state.bookings_df = pd.DataFrame(columns=['appointment_id', 'patient_name', 'doctor', 'date', 'time'])


# ==============================================================================
# 5. TOOL SCHEMAS (schemas.py)
# ==============================================================================

class PatientSearchInput(BaseModel):
    first_name: str = Field(description="The first name of the patient.")
    last_name: str = Field(description="The last name of the patient.")

class AvailabilityInput(BaseModel):
    doctor_name: str = Field(description="The full name of the doctor, e.g., 'Dr. Sarah Chen'.")
    preferred_date: str = Field(description="The preferred date for the appointment in 'YYYY-MM-DD' format.")

class BookingInput(BaseModel):
    doctor: str = Field(description="The full name of the doctor for the appointment.")
    date: str = Field(description="The confirmed date of the appointment in 'YYYY-MM-DD' format.")
    time: str = Field(description="The confirmed time of the appointment in 'HH:MM' format.")

class CancellationInput(BaseModel):
    appointment_id: str = Field(description="The unique ID of the appointment to be cancelled, e.g., 'APT12345'.")


# ==============================================================================
# 6. AI AGENT TOOLS (tools.py)
# ==============================================================================

@tool(args_schema=PatientSearchInput)
def search_patient(first_name: str, last_name: str) -> str:
    """
    Searches the patient database by first and last name. Returns the patient's
    details and type. Stores the found patient's data in the session state.
    """
    logging.info(f"Searching for patient: {first_name} {last_name}")
    patients_df = st.session_state.patients_df
    if patients_df.empty:
        logging.warning("Patient database is empty.")
        return "Error: Patient database could not be loaded."

    match = patients_df[
        (patients_df['first_name'].str.lower() == first_name.lower()) & 
        (patients_df['last_name'].str.lower() == last_name.lower())
    ]
    
    if not match.empty:
        patient_data = match.iloc[0].to_dict()
        st.session_state.current_patient = patient_data
        logging.info(f"Found returning patient: {patient_data['full_name']}")
        return json.dumps({
            "status": "Patient Found",
            "full_name": patient_data['full_name'],
            "patient_type": patient_data['patient_type']
        })
    else:
        new_patient_data = {
            'first_name': first_name, 'last_name': last_name,
            'full_name': f"{first_name} {last_name}", 'patient_type': 'New'
        }
        st.session_state.current_patient = new_patient_data
        logging.info(f"Identified new patient: {new_patient_data['full_name']}")
        return json.dumps({
            "status": "Patient Not Found",
            "full_name": new_patient_data['full_name'],
            "patient_type": "New"
        })

@tool(args_schema=AvailabilityInput)
def get_available_slots(doctor_name: str, preferred_date: str) -> str:
    """
    Finds genuinely available 30-minute time slots for a specific doctor on a
    preferred date by checking the schedule.
    """
    logging.info(f"Checking availability for {doctor_name} on {preferred_date}")
    schedule_df = st.session_state.schedule_df
    if schedule_df.empty:
        logging.warning("Doctor schedule is empty.")
        return "Error: Doctor schedule could not be loaded."
        
    try:
        schedule_df['Date_str'] = pd.to_datetime(schedule_df['Date']).dt.strftime('%Y-%m-%d')
        
        slots = schedule_df[
            (schedule_df['Doctor'] == doctor_name) &
            (schedule_df['Date_str'] == preferred_date) &
            (schedule_df['Status'].str.lower() == 'available')
        ]
        
        if slots.empty:
            logging.info("No available slots found.")
            return f"Unfortunately, there are no available slots for {doctor_name} on {preferred_date}."
        
        available_times = sorted(slots['Time'].tolist())
        logging.info(f"Found available slots: {available_times}")
        return f"Available slots for {doctor_name} on {preferred_date} are: {', '.join(available_times)}."
    except Exception as e:
        logging.error(f"Error checking availability: {e}")
        return f"I encountered an error while checking the schedule. Please try again."

@tool(args_schema=BookingInput)
def book_appointment(doctor: str, date: str, time: str) -> str:
    """
    Books an appointment for the currently identified patient. This action is final
    and modifies the schedule.
    """
    logging.info(f"Attempting to book appointment for Dr. {doctor} at {date} {time}")
    if 'current_patient' not in st.session_state or not st.session_state.current_patient:
        logging.warning("Booking attempt failed: No patient identified.")
        return "Error: I can't book an appointment because I haven't identified a patient yet. Please provide the patient's name first."

    patient_data = st.session_state.current_patient
    patient_type = patient_data.get('patient_type', 'New')
    duration = 60 if patient_type == 'New' else 30
    
    schedule_df = st.session_state.schedule_df
    schedule_df['Date_str'] = pd.to_datetime(schedule_df['Date']).dt.strftime('%Y-%m-%d')
    
    slot_index = schedule_df[
        (schedule_df['Doctor'] == doctor) &
        (schedule_df['Date_str'] == date) &
        (schedule_df['Time'] == time) &
        (schedule_df['Status'].str.lower() == 'available')
    ].index

    if slot_index.empty:
        logging.warning("Booking failed: Slot is no longer available.")
        return f"I'm sorry, the {time} slot with {doctor} on {date} was just taken. Please check for other available slots."
    
    st.session_state.schedule_df.loc[slot_index, 'Status'] = 'Booked'
    
    appointment_id = f"APT{random.randint(10000, 99999)}"
    booking_data = {
        'appointment_id': appointment_id, 'patient_name': patient_data.get('full_name'),
        'doctor': doctor, 'date': date, 'time': time, 'duration': duration,
        'location': CONFIG.DOCTORS.get(doctor, 'Main Clinic - Downtown'),
        'patient_type': patient_type, 'status': 'Confirmed',
    }
    
    new_booking = pd.DataFrame([booking_data])
    st.session_state.bookings_df = pd.concat([st.session_state.bookings_df, new_booking], ignore_index=True)
    
    st.session_state.appointment_data = booking_data
    logging.info(f"Successfully booked appointment {appointment_id}.")
    return json.dumps(booking_data)

@tool(args_schema=CancellationInput)
def cancel_appointment(appointment_id: str) -> str:
    """
    Cancels a previously booked appointment using its unique ID. This action
    frees up the slot on the doctor's schedule.
    """
    logging.info(f"Attempting to cancel appointment {appointment_id}")
    bookings_df = st.session_state.bookings_df
    
    if bookings_df[bookings_df['appointment_id'] == appointment_id].empty:
        logging.warning(f"Cancellation failed: Appointment ID {appointment_id} not found.")
        return f"I couldn't find an appointment with the ID '{appointment_id}'. Please double-check the ID."
        
    booking_details = bookings_df[bookings_df['appointment_id'] == appointment_id].iloc[0]
    
    schedule_df = st.session_state.schedule_df
    schedule_df['Date_str'] = pd.to_datetime(schedule_df['Date']).dt.strftime('%Y-%m-%d')
    
    slot_index = schedule_df[
        (schedule_df['Doctor'] == booking_details['doctor']) &
        (schedule_df['Date_str'] == booking_details['date']) &
        (schedule_df['Time'] == booking_details['time'])
    ].index
    
    if not slot_index.empty:
        st.session_state.schedule_df.loc[slot_index, 'Status'] = 'Available'
    
    st.session_state.bookings_df = bookings_df[bookings_df['appointment_id'] != appointment_id]
    
    logging.info(f"Successfully cancelled appointment {appointment_id}.")
    return f"Success! The appointment {appointment_id} for {booking_details['patient_name']} has been cancelled."


# ==============================================================================
# 7. AGENT SETUP (agent.py)
# ==============================================================================

@st.cache_resource
def get_agent_executor():
    """Creates and caches the AI agent and its executor."""
    tools = [search_patient, get_available_slots, book_appointment, cancel_appointment]

    llm = ChatOpenAI(
        model=CONFIG.MODEL_NAME,
        api_key=api_key,
        base_url=CONFIG.OPENROUTER_BASE_URL,
        default_headers=CONFIG.DEFAULT_HEADERS
    )
    
    system_prompt = """You are a highly capable and polite medical scheduling assistant for the MediCare Allergy & Wellness Center.
    Your main purpose is to help users book or cancel appointments.

    **Conversation Flow:**
    1.  Always start by greeting the user and asking for their full name to begin any process.
    2.  Use the `search_patient` tool to identify them. The user's status (New/Returning) determines the appointment duration (60/30 mins).
    3.  To book, gather their preferred doctor and date. Use `get_available_slots` to find openings.
    4.  Present the options and let the user choose a time.
    5.  Once all details are confirmed, use `book_appointment` to finalize. This is a critical step, so confirm all details before calling it.
    6.  To cancel, ask for the appointment ID and use the `cancel_appointment` tool.
    
    **Important Rules:**
    -   Be conversational and clear. Use the chat history for context.
    -   If a tool returns an error, apologize to the user and explain the issue clearly (e.g., "I'm sorry, that time slot was just taken.").
    -   After a successful booking, your final response must be ONLY the JSON output from the `book_appointment` tool. This is a system requirement for displaying the confirmation card.
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    logging.info("Agent created successfully.")
    return AgentExecutor(agent=agent, tools=tools, verbose=True)


# ==============================================================================
# 8. UI COMPONENTS (ui_components.py)
# ==============================================================================

def display_main_header():
    """Renders the main header of the application."""
    st.markdown("""
    <div class="medical-header">
        <h1>🏥 MediCare AI Scheduling Agent</h1>
        <p>Your Personal Conversational Scheduling Assistant</p>
    </div>
    """, unsafe_allow_html=True)

def setup_sidebar():
    """Sets up the sidebar with a clear conversation button and status info."""
    with st.sidebar:
        st.header("Dashboard")
        
        if st.button("🔄 Start New Conversation"):
            st.session_state.messages = [{"role": "assistant", "content": "Welcome! Please tell me your full name to begin."}]
            # Clear other session state variables as well
            st.session_state.pop('current_patient', None)
            st.session_state.pop('appointment_data', None)
            st.rerun()

        st.markdown("---")
        if 'current_patient' in st.session_state and st.session_state.current_patient:
            st.info(f"**Current Patient:** {st.session_state.current_patient['full_name']} ({st.session_state.current_patient['patient_type']})")
        
        if 'appointment_data' in st.session_state and st.session_state.appointment_data:
            st.success(f"**Appointment Booked:** {st.session_state.appointment_data['appointment_id']}")

def display_appointment_card_from_dict(appointment):
    """Renders the appointment card from a dictionary."""
    appointment_html = f"""
    <div class="appointment-card">
        <div class="appointment-header">
            <div class="appointment-id">Appointment ID: {appointment.get('appointment_id', 'N/A')}</div>
            <h3 class="appointment-title">Your Appointment Details</h3>
        </div>
        <div class="appointment-grid">
            <div>
                <div class="appointment-item">Patient: {appointment.get('patient_name', 'N/A')}</div>
                <div class="appointment-item">Doctor: {appointment.get('doctor', 'N/A')}</div>
                <div class="appointment-item">Date: {appointment.get('date', 'N/A')}</div>
                <div class="appointment-item">Time: {appointment.get('time', 'N/A')}</div>
            </div>
            <div>
                <div class="appointment-item">Duration: {appointment.get('duration', 'N/A')} minutes</div>
                <div class="appointment-item">Location: {appointment.get('location', 'N/A')}</div>
                <div class="appointment-item">Type: {appointment.get('patient_type', 'N/A')}</div>
                <div class="appointment-item">Status: {appointment.get('status', 'N/A')}</div>
            </div>
        </div>
    </div>
    """
    st.markdown(appointment_html, unsafe_allow_html=True)

def render_chat_message(message):
    """Renders a single chat message, handling special formats like appointment cards."""
    content = message.get("content", "")
    role = message.get("role", "assistant")

    with st.chat_message(role):
        if isinstance(content, dict) and content.get("type") == "appointment_card":
            display_appointment_card_from_dict(content["data"])
        else:
            st.write(content)

def is_valid_booking_json(json_string):
    """Checks if a string is a valid JSON representing a booking confirmation."""
    try:
        data = json.loads(json_string)
        return isinstance(data, dict) and 'appointment_id' in data and 'doctor' in data
    except (json.JSONDecodeError, TypeError):
        return False

# ==============================================================================
# 9. MAIN APPLICATION (app.py)
# ==============================================================================

def main():
    """Main function to run the Streamlit application."""
    display_main_header()
    setup_sidebar()
    
    agent_executor = get_agent_executor()

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Welcome to MediCare! I can help you book or cancel an appointment. To get started, please tell me your full name."}]

    for msg in st.session_state.messages:
        render_chat_message(msg)
    
    if user_input := st.chat_input("How can I help you today?"):
        st.session_state.messages.append({"role": "user", "content": user_input})
        render_chat_message({"role": "user", "content": user_input})

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                history = [msg for msg in st.session_state.messages[:-1]]

                try:
                    response = agent_executor.invoke({
                        "input": user_input,
                        "chat_history": history
                    })
                    ai_response = response['output']

                    if is_valid_booking_json(ai_response):
                        booking_data = json.loads(ai_response)
                        display_appointment_card_from_dict(booking_data)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": {"type": "appointment_card", "data": booking_data}
                        })
                    else:
                        st.write(ai_response)
                        st.session_state.messages.append({"role": "assistant", "content": ai_response})
                
                except Exception as e:
                    logging.error(f"An error occurred during agent invocation: {e}")
                    error_message = "I'm sorry, I've encountered a technical issue. Please try rephrasing your request or restarting the conversation."
                    st.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})

if __name__ == "__main__":
    main()
