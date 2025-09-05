# streamlit_app.py
# MediCare AI Scheduling Agent - Full Production-style Streamlit Demo (~1000 lines)

import streamlit as st
import pandas as pd
import sqlite3
import os
import io
import random
import string
import json
from datetime import datetime, timedelta, date, time
from typing import List, Optional

# -----------------------------
# Configuration / Constants
# -----------------------------
DB_PATH = "medicare.db"
PATIENT_CSV_PATH = "patients_database.csv"
DOCTOR_SCHEDULE_XLSX = "doctor_schedules.xlsx"
INTAKE_FORM_PDF = "/mnt/data/New Patient Intake Form.pdf"
CASE_STUDY_PDF = "/mnt/data/Data Science Intern - RagaAI.pdf"
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

APPT_TYPES = {
    "Initial Consultation (60m)": {"minutes": 60},
    "Follow-up (30m)": {"minutes": 30},
    "Allergy Testing (45m)": {"minutes": 45},
}

DOCTOR_SAMPLE = [
    {
        "doctor_id": "DOC1001",
        "full_name": "Dr. Sarah Chen",
        "specialty": "Allergy & Immunology",
        "weekday_availability": {"Mon": True, "Tue": True, "Wed": True, "Thu": True, "Fri": True},
        "start_time": "09:00",
        "end_time": "17:00",
        "lunch_start": "12:30",
        "lunch_end": "13:30",
        "location": "Main Clinic - Downtown",
    },
    {
        "doctor_id": "DOC1002",
        "full_name": "Dr. Michael Rodriguez",
        "specialty": "Pulmonology",
        "weekday_availability": {"Mon": True, "Tue": False, "Wed": True, "Thu": False, "Fri": True},
        "start_time": "09:00",
        "end_time": "17:00",
        "lunch_start": "12:30",
        "lunch_end": "13:30",
        "location": "North Branch",
    },
    {
        "doctor_id": "DOC1003",
        "full_name": "Dr. Emily Johnson",
        "specialty": "Pediatrics (Allergy)",
        "weekday_availability": {"Mon": False, "Tue": True, "Wed": True, "Thu": True, "Fri": False},
        "start_time": "09:00",
        "end_time": "17:00",
        "lunch_start": "12:30",
        "lunch_end": "13:30",
        "location": "South Branch",
    },
    {
        "doctor_id": "DOC1004",
        "full_name": "Dr. Robert Kim",
        "specialty": "Dermatology",
        "weekday_availability": {"Mon": True, "Tue": True, "Wed": False, "Thu": True, "Fri": True},
        "start_time": "09:00",
        "end_time": "17:00",
        "lunch_start": "12:30",
        "lunch_end": "13:30",
        "location": "West Side Clinic",
    },
]

# -----------------------------
# Streamlit Page Config + CSS
# -----------------------------
st.set_page_config(page_title="MediCare AI Scheduling Agent", page_icon="🏥", layout="wide", initial_sidebar_state="expanded")

st.title("🏥 MediCare AI Scheduling Agent")
st.caption("Smart appointment scheduling for allergy & wellness care — demo / case-study implementation")

# FIXED CSS (dark text on light background, high contrast)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    .stApp { font-family: Inter, sans-serif; background-color: #f9fafb; color: #111827; }
    .css-1d391kg { background-color: #f1f5f9 !important; color: #111827 !important; } /* sidebar */
    .mh { background: linear-gradient(135deg,#2563eb 0%,#3b82f6 100%); color: #fff; padding: 1.1rem; border-radius: 8px; margin-bottom: 1rem;}
    .section { background: #ffffff; border-radius: 10px; padding: 1rem; border: 1px solid #e5e7eb; box-shadow: 0 4px 14px rgba(0,0,0,0.05); margin-bottom: 1rem; color:#111827;}
    .card { background: #ffffff; border-radius: 10px; padding: 0.8rem; border: 1px solid #e5e7eb; box-shadow: 0 6px 18px rgba(0,0,0,0.04); margin-bottom: .75rem; color:#111827;}
    .pill { display:inline-block; padding: .25rem .6rem; border-radius:999px; background:#e2e8f0; color:#111827; font-weight:600; }
    .small-muted{ font-size: .9rem; color:#6b7280; }
    .app-id{ background:#0ea5e9; color:#fff; padding:.25rem .6rem; border-radius:8px; font-weight:700; }
    .tbl-note{ font-size:.9rem; color:#64748b; }
    .hr{ height:1px; background:#e5e7eb; margin: .75rem 0; border-radius:4px;}
    .stButton>button, .stDownloadButton>button { border-radius:8px; padding: .5rem .9rem; font-weight:700;}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Utility Functions
# -----------------------------
def gen_id(prefix="APT"):
    return f"{prefix}{random.randint(10000,99999)}"

def next_n_weekdays(n: int = 7):
    today = datetime.now().date()
    days = []
    i = 1
    while len(days) < n:
        d = today + timedelta(days=i)
        if d.weekday() < 5:
            days.append(d)
        i += 1
    return days

def available_slots(start="09:00", end="17:00", interval=30, lunch=("12:30", "13:30")):
    st_time = datetime.strptime(start, "%H:%M")
    end_time = datetime.strptime(end, "%H:%M")
    slots = []
    while st_time < end_time:
        s = st_time.strftime("%H:%M")
        if not (lunch[0] <= s < lunch[1]):
            slots.append(s)
        st_time += timedelta(minutes=interval)
    return slots

# -----------------------------
# Database Layer
# -----------------------------
class DAL:
    @staticmethod
    def init():
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            """CREATE TABLE IF NOT EXISTS patients(
                   patient_id TEXT PRIMARY KEY,
                   first_name TEXT,last_name TEXT,
                   dob TEXT,phone TEXT,email TEXT,
                   insurance TEXT,member_id TEXT,group_num TEXT,
                   patient_type TEXT,last_visit TEXT
               )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS doctors(
                   doctor_id TEXT PRIMARY KEY,
                   full_name TEXT,specialty TEXT,
                   location TEXT
               )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS appointments(
                   appointment_id TEXT PRIMARY KEY,
                   patient_id TEXT,doctor_id TEXT,
                   date TEXT,time TEXT,duration INT,
                   type TEXT,status TEXT,location TEXT,
                   booking_time TEXT
               )"""
        )
        conn.commit()
        conn.close()

    @staticmethod
    def add_sample_doctors():
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        for d in DOCTOR_SAMPLE:
            c.execute("INSERT OR IGNORE INTO doctors VALUES(?,?,?,?)", (d["doctor_id"], d["full_name"], d["specialty"], d["location"]))
        conn.commit()
        conn.close()

    @staticmethod
    def all_doctors_df():
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql("SELECT * FROM doctors", conn)
        conn.close()
        return df

    @staticmethod
    def get_doctor(doc_id):
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql(f"SELECT * FROM doctors WHERE doctor_id='{doc_id}'", conn)
        conn.close()
        return df.iloc[0].to_dict() if not df.empty else None

    @staticmethod
    def add_patient(p):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO patients VALUES(?,?,?,?,?,?,?,?,?,?,?)", tuple(p.values()))
        conn.commit()
        conn.close()

    @staticmethod
    def find_patient(first, last, dob):
        conn = sqlite3.connect(DB_PATH)
        q = f"SELECT * FROM patients WHERE first_name='{first}' AND last_name='{last}' AND dob='{dob}'"
        df = pd.read_sql(q, conn)
        conn.close()
        return df.iloc[0].to_dict() if not df.empty else None

    @staticmethod
    def add_appt(a):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO appointments VALUES(?,?,?,?,?,?,?,?,?,?)", tuple(a.values()))
        conn.commit()
        conn.close()

    @staticmethod
    def appts_df():
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql("SELECT * FROM appointments", conn)
        conn.close()
        return df

# Initialize DB
DAL.init()
DAL.add_sample_doctors()

# -----------------------------
# Sidebar Dashboard
# -----------------------------
with st.sidebar:
    st.markdown('<div class="mh"><h3>📊 Medical Dashboard</h3></div>', unsafe_allow_html=True)
    appts = DAL.appts_df()
    docs = DAL.all_doctors_df()
    st.metric("Total Patients", appts["patient_id"].nunique() if not appts.empty else 0)
    st.metric("Appointments", len(appts))
    st.metric("Doctors", len(docs))

    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
    st.subheader("Quick Actions")
    if st.button("View Appointments"):
        st.dataframe(appts)

    if st.button("View Doctors"):
        st.dataframe(docs)

# -----------------------------
# Tabs: Intake | Schedule | Confirm | Reminders | Reports
# -----------------------------
tabs = st.tabs(["📝 Intake", "📅 Scheduling", "✅ Confirmation", "🔔 Reminders", "📑 Reports"])

# -----------------------------
# Intake Tab
# -----------------------------
with tabs[0]:
    st.markdown('<div class="section"><h3>📝 Patient Intake Form</h3>', unsafe_allow_html=True)
    with st.form("intake_form"):
        c1, c2 = st.columns(2)
        with c1:
            f = st.text_input("First Name")
            d = st.date_input("DOB")
            ph = st.text_input("Phone")
        with c2:
            l = st.text_input("Last Name")
            em = st.text_input("Email")
        ins = st.text_input("Insurance Company")
        mid = st.text_input("Member ID")
        gnum = st.text_input("Group Number")
        t = st.selectbox("Patient Type", ["New", "Returning"])
        sub = st.form_submit_button("Save Patient")
        if sub and f and l and em:
            pid = gen_id("PAT")
            p = {
                "patient_id": pid,
                "first_name": f,
                "last_name": l,
                "dob": d.strftime("%Y-%m-%d"),
                "phone": ph,
                "email": em,
                "insurance": ins,
                "member_id": mid,
                "group_num": gnum,
                "patient_type": t,
                "last_visit": datetime.now().strftime("%Y-%m-%d"),
            }
            DAL.add_patient(p)
            st.success(f"Saved patient {p['first_name']} {p['last_name']} with ID {pid}")
    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# Scheduling Tab
# -----------------------------
with tabs[1]:
    st.markdown('<div class="section"><h3>📅 Schedule Appointment</h3>', unsafe_allow_html=True)
    doctors_df = DAL.all_doctors_df()
    doc_opts = doctors_df["doctor_id"].tolist()
    doc_display = st.selectbox(
        "Select Doctor",
        options=doc_opts,
        format_func=lambda did: f"{DAL.get_doctor(did)['full_name']} ({DAL.get_doctor(did)['specialty']})",
    )
    doctor = DAL.get_doctor(doc_display)

    # FIXED: use daydays instead of days
    daydays = next_n_weekdays(7)
    sel_date = st.selectbox("Select Date", daydays)
    slots = available_slots()
    sel_time = st.selectbox("Select Time", slots)
    atype = st.selectbox("Appointment Type", list(APPT_TYPES.keys()))
    if st.button("Book Appointment"):
        aid = gen_id("APT")
        appt = {
            "appointment_id": aid,
            "patient_id": "PAT9999",
            "doctor_id": doctor["doctor_id"],
            "date": sel_date.strftime("%Y-%m-%d"),
            "time": sel_time,
            "duration": APPT_TYPES[atype]["minutes"],
            "type": atype,
            "status": "Confirmed",
            "location": doctor["location"],
            "booking_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        DAL.add_appt(appt)
        st.success(f"Appointment {aid} booked with {doctor['full_name']} on {sel_date} at {sel_time}")

# -----------------------------
# Confirmation Tab
# -----------------------------
with tabs[2]:
    st.markdown('<div class="section"><h3>✅ Appointment Confirmation</h3>', unsafe_allow_html=True)
    df = DAL.appts_df()
    if df.empty:
        st.info("No appointments booked yet")
    else:
        st.dataframe(df)
        sel = st.selectbox("Choose Appointment", df["appointment_id"].tolist())
        appt = df[df["appointment_id"] == sel].iloc[0].to_dict()
        st.markdown(f"<div class='card'><span class='app-id'>ID {appt['appointment_id']}</span> with Doctor {appt['doctor_id']} on {appt['date']} {appt['time']}</div>", unsafe_allow_html=True)

# -----------------------------
# Reminders Tab
# -----------------------------
with tabs[3]:
    st.markdown('<div class="section"><h3>🔔 Automated Reminders</h3>', unsafe_allow_html=True)
    df = DAL.appts_df()
    if df.empty:
        st.info("No appointments")
    else:
        for _, row in df.iterrows():
            d = datetime.strptime(row["date"], "%Y-%m-%d")
            r1 = d - timedelta(days=3)
            r2 = d - timedelta(days=1)
            r3 = d - timedelta(hours=4)
            st.markdown(f"<div class='card'>Reminders for <b>{row['appointment_id']}</b>: {r1}, {r2}, {r3}</div>", unsafe_allow_html=True)

# -----------------------------
# Reports Tab
# -----------------------------
with tabs[4]:
    st.markdown('<div class="section"><h3>📑 Reports</h3>', unsafe_allow_html=True)
    appts = DAL.appts_df()
    if not appts.empty:
        st.bar_chart(appts["doctor_id"].value_counts())
    else:
        st.info("No data yet")
    if os.path.exists(INTAKE_FORM_PDF):
        st.download_button("Download Intake Form PDF", data=open(INTAKE_FORM_PDF, "rb"), file_name="intake_form.pdf")
    if os.path.exists(CASE_STUDY_PDF):
        st.download_button("Download Case Study PDF", data=open(CASE_STUDY_PDF, "rb"), file_name="case_study.pdf")
