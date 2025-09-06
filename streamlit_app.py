import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta, date
import random
import os
import io

# New imports for the AI Agent
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI # CHANGED
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

# --- 1. SETUP API KEY ---
# Load environment variables. Create a .env file and add your key:
# GOOGLE_API_KEY="..."
load_dotenv()

# Check if the API key is available
api_key = os.getenv("GOOGLE_API_KEY") # CHANGED
if not api_key:
    st.error("GOOGLE_API_KEY not found. Please set it in your environment or a .env file.") # CHANGED
    st.stop()


# Configure page with medical theme
st.set_page_config(
    page_title="MediCare AI Scheduling Agent", 
    page_icon="🏥", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS (your original CSS is preserved)
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


# --- 2. DATA LOADING & UI HELPERS ---

@st.cache_data
def load_data(file_path, is_excel=False):
    """Loads data from CSV or Excel file."""
    try:
        if is_excel:
            return pd.read_excel(file_path, sheet_name='Full_Schedule')
        else:
            return pd.read_csv(file_path)
    except FileNotFoundError:
        st.error(f"Data file not found: {file_path}")
        return pd.DataFrame()

patients_df = load_data('patients_database.csv')
schedule_df = load_data('doctor_schedules.xlsx', is_excel=True)

def display_appointment_card(appointment):
    """Your original function to display the appointment card."""
    appointment_html = f"""
    <div class="appointment-card">
        <div class="appointment-header">
            <div class="appointment-id">Appointment ID: {appointment['appointment_id']}</div>
            <h3 class="appointment-title">Your Appointment Details</h3>
        </div>
        <div class="appointment-grid">
            <div>
                <div class="appointment-item">Patient: {appointment['patient_name']}</div>
                <div class="appointment-item">Doctor: {appointment['doctor']}</div>
                <div class="appointment-item">Date: {appointment['date']}</div>
                <div class="appointment-item">Time: {appointment['time']}</div>
            </div>
            <div>
                <div class="appointment-item">Duration: {appointment['duration']} minutes</div>
                <div class="appointment-item">Location: {appointment['location']}</div>
                <div class="appointment-item">Type: {appointment['patient_type']}</div>
                <div class="appointment-item">Status: {appointment['status']}</div>
            </div>
        </div>
    </div>
    """
    st.markdown(appointment_html, unsafe_allow_html=True)


# --- 3. AI AGENT TOOLS ---

@tool
def search_patient(first_name: str, last_name: str) -> str:
    """
    Searches the patient database by first_name and last_name.
    Returns the patient's full name and type ('New' or 'Returning').
    Also stores the found patient's data in the session state.
    """
    if patients_df.empty:
        return "Error: Patient database is not loaded."

    match = patients_df[
        (patients_df['first_name'].str.lower() == first_name.lower()) & 
        (patients_df['last_name'].str.lower() == last_name.lower())
    ]
    
    if not match.empty:
        patient_data = match.iloc[0].to_dict()
        st.session_state.current_patient = patient_data
        return json.dumps({
            "status": "Patient Found",
            "full_name": patient_data['full_name'],
            "patient_type": patient_data['patient_type']
        })
    else:
        # If not found, create a new temporary record
        new_patient_data = {
            'first_name': first_name,
            'last_name': last_name,
            'full_name': f"{first_name} {last_name}",
            'patient_type': 'New'
        }
        st.session_state.current_patient = new_patient_data
        return json.dumps({
            "status": "Patient Not Found",
            "full_name": new_patient_data['full_name'],
            "patient_type": "New"
        })

@tool
def get_available_slots(doctor_name: str, preferred_date: str) -> str:
    """
    Finds available time slots for a specific doctor on a preferred date.
    The date should be in 'YYYY-MM-DD' format.
    """
    if schedule_df.empty:
        return "Error: Doctor schedule is not loaded."
        
    try:
        # This is a simplified logic. A real app would have more complex availability checks.
        available_times = ['09:00', '10:00', '11:00', '14:00', '15:00', '16:00']
        return f"Available slots for {doctor_name} on {preferred_date} are: {', '.join(available_times)}."
    except Exception as e:
        return f"Could not check availability. Error: {e}"

@tool
def book_appointment(doctor: str, date: str, time: str) -> str:
    """
    Books an appointment for the patient stored in the session state.
    Requires the doctor's name, and the desired date and time.
    Use this only after confirming the patient's identity.
    """
    if 'current_patient' not in st.session_state or not st.session_state.current_patient:
        return "Error: No patient has been identified. Please use search_patient first."

    patient_data = st.session_state.current_patient
    patient_type = patient_data.get('patient_type', 'New')
    duration = 60 if patient_type == 'New' else 30
    
    appointment_id = f"APT{random.randint(10000, 99999)}"
    location_map = {
        'Dr. Sarah Chen': 'Main Clinic - Downtown',
        'Dr. Michael Rodriguez': 'North Branch',
        'Dr. Emily Johnson': 'South Branch',
        'Dr. Robert Kim': 'West Side Clinic'
    }

    booking_data = {
        'appointment_id': appointment_id,
        'patient_name': patient_data.get('full_name'),
        'doctor': doctor,
        'date': date,
        'time': time,
        'duration': duration,
        'location': location_map.get(doctor, 'Main Clinic - Downtown'),
        'patient_type': patient_type,
        'status': 'Confirmed',
    }

    st.session_state.appointment_data = booking_data
    # Return a JSON string so the AI knows all details of the booking
    return json.dumps(booking_data)


# --- 4. AGENT SETUP ---

@st.cache_resource
def get_agent_executor():
    """Creates and caches the AI agent and its executor."""
    tools = [search_patient, get_available_slots, book_appointment]

    # --- THIS ENTIRE BLOCK IS CHANGED ---
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro-latest",
        google_api_key=api_key
    )
    
    # The prompt tells the agent how to behave
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful and polite medical scheduling assistant for the MediCare Allergy & Wellness Center.
        Your goal is to book an appointment for the user.
        Follow these steps:
        1. Greet the user and ask for their full name to begin.
        2. Use the search_patient tool to find them in the system.
        3. Based on whether they are a 'New' or 'Returning' patient, inform them of their appointment duration (60 mins for New, 30 mins for Returning).
        4. Ask for their preferred doctor and date. Available doctors are Dr. Sarah Chen, Dr. Michael Rodriguez, Dr. Emily Johnson, and Dr. Robert Kim.
        5. Use the get_available_slots tool to find open times.
        6. Ask the user to pick a time from the list.
        7. Once they confirm a time, use the book_appointment tool to finalize.
        8. After booking, respond ONLY with the JSON output from the book_appointment tool. Do not add any other text. Start your response with 'BOOKING_CONFIRMED:' followed by the JSON data.
        """),
        ("user", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)


# --- 5. MAIN APP LOGIC ---

def main():
    # Medical Header (preserved)
    st.markdown("""
    <div class="medical-header">
        <h1>🏥 MediCare AI Scheduling Agent</h1>
        <p>Your Personal Conversational Scheduling Assistant</p>
    </div>
    """, unsafe_allow_html=True)
    
    agent_executor = get_agent_executor()

    # Chat UI
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Welcome to MediCare! I'm your AI assistant. To get started, please tell me your full name."}]

    for msg in st.session_state.messages:
        # Check if the message content is a booking confirmation
        if isinstance(msg["content"], dict) and msg["content"].get("type") == "appointment_card":
            display_appointment_card(msg["content"]["data"])
        else:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
    
    if prompt := st.chat_input("Your message here..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = agent_executor.invoke({"input": prompt, "chat_history": st.session_state.messages})
                ai_response = response['output']

                # Check if the AI returned a booking confirmation
                if ai_response.startswith("BOOKING_CONFIRMED:"):
                    try:
                        # Extract and parse the JSON data
                        json_str = ai_response.replace("BOOKING_CONFIRMED:", "").strip()
                        booking_data = json.loads(json_str)
                        
                        # Display the card and store it as a special message type
                        display_appointment_card(booking_data)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": {
                                "type": "appointment_card",
                                "data": booking_data
                            }
                        })
                    except json.JSONDecodeError:
                        st.error("Failed to process booking confirmation.")
                        st.write(ai_response) # Show raw response on error
                        st.session_state.messages.append({"role": "assistant", "content": ai_response})
                else:
                    st.write(ai_response)
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})

if __name__ == "__main__":
    main()
