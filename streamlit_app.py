# app.py
# MediCare AI Scheduling Agent - Single-file production-style Streamlit app
# Implements the intern case-study MVP: patient greeting, lookup, scheduling,
# insurance collection, confirmation, intake form distribution, reminders, exports.
#
# Save as app.py and run: streamlit run app.py
# Requires: streamlit, pandas, sqlite3, xlsxwriter (optional for Excel export)
# The script will create medicare.db and demo data on first run.

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
PATIENT_CSV_PATH = "patients_database.csv"  # optional; will be generated if not present
DOCTOR_SCHEDULE_XLSX = "doctor_schedules.xlsx"  # optional; will be generated if not present
INTAKE_FORM_PDF = "/mnt/data/New Patient Intake Form.pdf"  # uploaded by user
CASE_STUDY_PDF = "/mnt/data/Data Science Intern - RagaAI.pdf"  # uploaded by user (reference)
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

# Custom CSS for improved UI
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    .css-1d391kg { background-color: #f8fafc; } /* sidebar */
    .stApp { font-family: Inter, sans-serif; background-color: #f8fafc; }
    .mh { background: linear-gradient(135deg,#1e40af 0%,#3b82f6 100%); color: #fff; padding: 1.1rem; border-radius: 8px; margin-bottom: 1rem;}
    .section { background: #fff; border-radius: 10px; padding: 1rem; border: 1px solid #e6eef8; box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04); margin-bottom: 1rem;}
    .card { background: #fff; border-radius: 10px; padding: 0.8rem; border: 1px solid #edf2f7; box-shadow: 0 6px 18px rgba(2,6,23,.03); margin-bottom: .75rem;}
    .pill { display:inline-block; padding: .25rem .6rem; border-radius:999px; background:#e6eef8; color:#0f172a; font-weight:600; }
    .small-muted{ font-size: .9rem; color:#64748b; }
    .app-id{ background:#0ea5e9; color:#fff; padding:.25rem .6rem; border-radius:8px; font-weight:700; }
    .tbl-note{ font-size:.9rem; color:#64748b; }
    .hr{ height:1px; background:#e6eef8; margin: .75rem 0; border-radius:4px;}
    .stButton>button { border-radius:8px; padding: .5rem .9rem; font-weight:700;}
    .stDownloadButton>button { border-radius:8px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Utility Functions
# -----------------------------


def gen_id(prefix: str = "ID", digits: int = 6) -> str:
    return f"{prefix}{''.join(random.choices(string.digits, k=digits))}"


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure_folder(path: str):
    if not os.path.exists(path):
        os.makedirs(path)


# -----------------------------
# Database: SQLite init and helpers
# -----------------------------
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    # patients
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS patients(
        patient_id TEXT PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        full_name TEXT,
        dob TEXT,
        phone TEXT,
        email TEXT,
        insurance_company TEXT,
        member_id TEXT,
        group_number TEXT,
        patient_type TEXT,
        last_visit TEXT,
        created_at TEXT,
        updated_at TEXT
    );
    """
    )
    # doctors
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS doctors(
        doctor_id TEXT PRIMARY KEY,
        full_name TEXT,
        specialty TEXT,
        weekday_availability TEXT, -- JSON
        start_time TEXT,
        end_time TEXT,
        lunch_start TEXT,
        lunch_end TEXT,
        location TEXT,
        created_at TEXT,
        updated_at TEXT
    );
    """
    )
    # appointments
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS appointments(
        appointment_id TEXT PRIMARY KEY,
        patient_id TEXT,
        doctor_id TEXT,
        doctor_name TEXT,
        date TEXT, -- YYYY-MM-DD
        time TEXT, -- HH:MM
        duration INTEGER,
        appt_type TEXT,
        location TEXT,
        status TEXT,
        booking_time TEXT,
        notes TEXT
    );
    """
    )
    # reminders
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS reminders(
        reminder_id TEXT PRIMARY KEY,
        appointment_id TEXT,
        remind_at TEXT, -- YYYY-MM-DD HH:MM
        channel TEXT,
        message TEXT,
        state TEXT,
        created_at TEXT
    );
    """
    )
    conn.commit()
    conn.close()


# -----------------------------
# Seed / Demo Data Generation
# -----------------------------
def seed_demo_patients(num: int = 50):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(1) AS c FROM patients")
    if cur.fetchone()["c"] >= num:
        conn.close()
        return

    # generate synthetic patients
    first_names = ["Alex", "Sam", "Taylor", "Jordan", "Casey", "Riley", "Jamie", "Morgan", "Chris", "Pat"]
    last_names = ["Sharma", "Patel", "Khan", "Gupta", "Iyer", "Mehta", "Singh", "Rao", "Nair", "Das"]
    domains = ["example.com", "mail.com", "testmail.org"]

    for i in range(num):
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        full = f"{fn} {ln}"
        pid = f"PAT{1000 + i}"
        dob = (date.today() - timedelta(days=random.randint(18 * 365, 70 * 365))).strftime("%Y-%m-%d")
        phone = f"+1-555-{random.randint(100,999)}-{random.randint(1000,9999)}"
        email = f"{fn.lower()}.{ln.lower()}{i}@{random.choice(domains)}"
        ptype = random.choice(["New", "Returning"])
        last_visit = (date.today() - timedelta(days=random.randint(1, 365))).strftime("%Y-%m-%d") if ptype == "Returning" else None
        cur.execute(
            """
            INSERT OR IGNORE INTO patients(patient_id, first_name, last_name, full_name, dob, phone, email,
                insurance_company, member_id, group_number, patient_type, last_visit, created_at, updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                pid,
                fn,
                ln,
                full,
                dob,
                phone,
                email,
                random.choice(["Blue Cross", "Aetna", "United Health", "MedLife", "Not provided"]),
                "".join(random.choices(string.ascii_uppercase + string.digits, k=8)),
                "GRP" + str(random.randint(100, 999)),
                ptype,
                last_visit,
                now_str(),
                now_str(),
            ),
        )

    conn.commit()
    conn.close()


def seed_demo_doctors():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(1) AS c FROM doctors")
    if cur.fetchone()["c"] > 0:
        conn.close()
        return
    for d in DOCTOR_SAMPLE:
        cur.execute(
            """
        INSERT OR IGNORE INTO doctors(doctor_id, full_name, specialty, weekday_availability,
            start_time, end_time, lunch_start, lunch_end, location, created_at, updated_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?)
        """,
            (
                d["doctor_id"],
                d["full_name"],
                d["specialty"],
                json.dumps(d["weekday_availability"]),
                d["start_time"],
                d["end_time"],
                d["lunch_start"],
                d["lunch_end"],
                d["location"],
                now_str(),
                now_str(),
            ),
        )
    conn.commit()
    conn.close()


# -----------------------------
# Optional: create doctor_schedules.xlsx if not present (helps the assignment expectation)
# -----------------------------
def ensure_doctor_schedule_xlsx():
    if os.path.exists(DOCTOR_SCHEDULE_XLSX):
        return
    # read doctors from DB if present, else use DOCTOR_SAMPLE
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM doctors")
    rows = cur.fetchall()
    if rows:
        rows_list = [dict(r) for r in rows]
    else:
        rows_list = DOCTOR_SAMPLE
    # create a DataFrame with availability expanded
    data = []
    for d in rows_list:
        weekday_avail = d.get("weekday_availability")
        if isinstance(weekday_avail, str):
            try:
                weekday_avail = json.loads(weekday_avail)
            except:
                weekday_avail = {"Mon": True, "Tue": True, "Wed": True, "Thu": True, "Fri": True}
        data.append(
            {
                "doctor_id": d.get("doctor_id"),
                "full_name": d.get("full_name"),
                "specialty": d.get("specialty"),
                "start_time": d.get("start_time"),
                "end_time": d.get("end_time"),
                "lunch_start": d.get("lunch_start"),
                "lunch_end": d.get("lunch_end"),
                "location": d.get("location"),
                "weekday_availability": json.dumps(weekday_avail),
            }
        )
    df = pd.DataFrame(data)
    df.to_excel(DOCTOR_SCHEDULE_XLSX, index=False)


# -----------------------------
# Data Access Layer (simple wrappers)
# -----------------------------
class DAL:
    @staticmethod
    def conn():
        return get_conn()

    # Patients
    @staticmethod
    def all_patients_df() -> pd.DataFrame:
        conn = get_conn()
        df = pd.read_sql_query("SELECT * FROM patients ORDER BY created_at DESC", conn)
        conn.close()
        return df

    @staticmethod
    def search_patients(q: str) -> pd.DataFrame:
        conn = get_conn()
        like = f"%{q}%"
        df = pd.read_sql_query(
            "SELECT * FROM patients WHERE full_name LIKE ? OR phone LIKE ? OR email LIKE ? ORDER BY updated_at DESC",
            conn,
            params=(like, like, like),
        )
        conn.close()
        return df

    @staticmethod
    def get_patient(pid: str) -> Optional[dict]:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM patients WHERE patient_id=?", (pid,))
        r = cur.fetchone()
        conn.close()
        return dict(r) if r else None

    @staticmethod
    def upsert_patient(p: dict) -> str:
        conn = get_conn()
        cur = conn.cursor()
        pid = p.get("patient_id") or gen_id("PAT", 6)
        now = now_str()
        # check exists
        cur.execute("SELECT COUNT(1) AS c FROM patients WHERE patient_id=?", (pid,))
        exists = cur.fetchone()["c"] > 0
        if exists:
            cur.execute(
                """
                UPDATE patients SET first_name=?, last_name=?, full_name=?, dob=?, phone=?, email=?,
                    insurance_company=?, member_id=?, group_number=?, patient_type=?, last_visit=?, updated_at=?
                WHERE patient_id=?
                """,
                (
                    p.get("first_name"),
                    p.get("last_name"),
                    p.get("full_name"),
                    p.get("dob"),
                    p.get("phone"),
                    p.get("email"),
                    p.get("insurance_company"),
                    p.get("member_id"),
                    p.get("group_number"),
                    p.get("patient_type"),
                    p.get("last_visit"),
                    now,
                    pid,
                ),
            )
        else:
            cur.execute(
                """
                INSERT INTO patients(patient_id, first_name, last_name, full_name, dob, phone, email,
                    insurance_company, member_id, group_number, patient_type, last_visit, created_at, updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    pid,
                    p.get("first_name"),
                    p.get("last_name"),
                    p.get("full_name"),
                    p.get("dob"),
                    p.get("phone"),
                    p.get("email"),
                    p.get("insurance_company"),
                    p.get("member_id"),
                    p.get("group_number"),
                    p.get("patient_type"),
                    p.get("last_visit"),
                    now,
                    now,
                ),
            )
        conn.commit()
        conn.close()
        return pid

    @staticmethod
    def delete_patient(pid: str):
        conn = get_conn()
        cur = conn.cursor()
        # delete related reminders and appointments
        cur.execute("SELECT appointment_id FROM appointments WHERE patient_id=?", (pid,))
        rows = cur.fetchall()
        for r in rows:
            cur.execute("DELETE FROM reminders WHERE appointment_id=?", (r["appointment_id"],))
        cur.execute("DELETE FROM appointments WHERE patient_id=?", (pid,))
        cur.execute("DELETE FROM patients WHERE patient_id=?", (pid,))
        conn.commit()
        conn.close()

    # Doctors
    @staticmethod
    def all_doctors_df() -> pd.DataFrame:
        conn = get_conn()
        df = pd.read_sql_query("SELECT * FROM doctors ORDER BY full_name", conn)
        conn.close()
        return df

    @staticmethod
    def get_doctor(did: str) -> Optional[dict]:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM doctors WHERE doctor_id=?", (did,))
        r = cur.fetchone()
        conn.close()
        return dict(r) if r else None

    @staticmethod
    def upsert_doctor(d: dict) -> str:
        conn = get_conn()
        cur = conn.cursor()
        did = d.get("doctor_id") or gen_id("DOC", 5)
        now = now_str()
        cur.execute("SELECT COUNT(1) AS c FROM doctors WHERE doctor_id=?", (did,))
        exists = cur.fetchone()["c"] > 0
        weekday_avail = d.get("weekday_availability") or {"Mon": True, "Tue": True, "Wed": True, "Thu": True, "Fri": True}
        if exists:
            cur.execute(
                """
                UPDATE doctors SET full_name=?, specialty=?, weekday_availability=?, start_time=?, end_time=?, lunch_start=?, lunch_end=?, location=?, updated_at=? WHERE doctor_id=?
                """,
                (
                    d.get("full_name"),
                    d.get("specialty"),
                    json.dumps(weekday_avail),
                    d.get("start_time"),
                    d.get("end_time"),
                    d.get("lunch_start"),
                    d.get("lunch_end"),
                    d.get("location"),
                    now,
                    did,
                ),
            )
        else:
            cur.execute(
                """
                INSERT INTO doctors(doctor_id, full_name, specialty, weekday_availability, start_time, end_time, lunch_start, lunch_end, location, created_at, updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    did,
                    d.get("full_name"),
                    d.get("specialty"),
                    json.dumps(weekday_avail),
                    d.get("start_time", "09:00"),
                    d.get("end_time", "17:00"),
                    d.get("lunch_start", "12:30"),
                    d.get("lunch_end", "13:30"),
                    d.get("location", "Main Clinic - Downtown"),
                    now,
                    now,
                ),
            )
        conn.commit()
        conn.close()
        return did

    @staticmethod
    def delete_doctor(did: str):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT appointment_id FROM appointments WHERE doctor_id=?", (did,))
        rows = cur.fetchall()
        for r in rows:
            cur.execute("DELETE FROM reminders WHERE appointment_id=?", (r["appointment_id"],))
        cur.execute("DELETE FROM appointments WHERE doctor_id=?", (did,))
        cur.execute("DELETE FROM doctors WHERE doctor_id=?", (did,))
        conn.commit()
        conn.close()

    # Appointments
    @staticmethod
    def all_appointments_df() -> pd.DataFrame:
        conn = get_conn()
        df = pd.read_sql_query(
            "SELECT a.*, p.full_name AS patient_name FROM appointments a LEFT JOIN patients p ON p.patient_id=a.patient_id ORDER BY date DESC, time DESC",
            conn,
        )
        conn.close()
        return df

    @staticmethod
    def get_appointment(aid: str) -> Optional[dict]:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM appointments WHERE appointment_id=?", (aid,))
        r = cur.fetchone()
        conn.close()
        return dict(r) if r else None

    @staticmethod
    def appointments_by_doctor_date(did: str, date_str: str) -> pd.DataFrame:
        conn = get_conn()
        df = pd.read_sql_query("SELECT * FROM appointments WHERE doctor_id=? AND date=? ORDER BY time ASC", conn, params=(did, date_str))
        conn.close()
        return df

    @staticmethod
    def upsert_appointment(a: dict) -> str:
        conn = get_conn()
        cur = conn.cursor()
        aid = a.get("appointment_id") or gen_id("APT", 6)
        cur.execute("SELECT COUNT(1) AS c FROM appointments WHERE appointment_id=?", (aid,))
        exists = cur.fetchone()["c"] > 0
        if exists:
            cur.execute(
                """
                UPDATE appointments SET patient_id=?, doctor_id=?, doctor_name=?, date=?, time=?, duration=?, appt_type=?, location=?, status=?, booking_time=?, notes=?
                WHERE appointment_id=?
                """,
                (
                    a.get("patient_id"),
                    a.get("doctor_id"),
                    a.get("doctor_name"),
                    a.get("date"),
                    a.get("time"),
                    a.get("duration"),
                    a.get("appt_type"),
                    a.get("location"),
                    a.get("status"),
                    a.get("booking_time"),
                    a.get("notes"),
                    aid,
                ),
            )
        else:
            cur.execute(
                """
                INSERT INTO appointments(appointment_id, patient_id, doctor_id, doctor_name, date, time, duration, appt_type, location, status, booking_time, notes)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    aid,
                    a.get("patient_id"),
                    a.get("doctor_id"),
                    a.get("doctor_name"),
                    a.get("date"),
                    a.get("time"),
                    a.get("duration"),
                    a.get("appt_type"),
                    a.get("location"),
                    a.get("status"),
                    a.get("booking_time"),
                    a.get("notes"),
                ),
            )
        conn.commit()
        conn.close()
        return aid

    @staticmethod
    def delete_appointment(aid: str):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM reminders WHERE appointment_id=?", (aid,))
        cur.execute("DELETE FROM appointments WHERE appointment_id=?", (aid,))
        conn.commit()
        conn.close()

    # Reminders
    @staticmethod
    def create_reminder(appointment_id: str, remind_at: str, channel: str, message: str, state: str = "Scheduled") -> str:
        conn = get_conn()
        cur = conn.cursor()
        rid = gen_id("REM", 6)
        cur.execute(
            "INSERT INTO reminders(reminder_id, appointment_id, remind_at, channel, message, state, created_at) VALUES(?,?,?,?,?,?,?)",
            (rid, appointment_id, remind_at, channel, message, state, now_str()),
        )
        conn.commit()
        conn.close()
        return rid

    @staticmethod
    def reminders_for_appointment(aid: str) -> pd.DataFrame:
        conn = get_conn()
        df = pd.read_sql_query("SELECT * FROM reminders WHERE appointment_id=? ORDER BY remind_at ASC", conn, params=(aid,))
        conn.close()
        return df

    @staticmethod
    def all_reminders_df() -> pd.DataFrame:
        conn = get_conn()
        df = pd.read_sql_query("SELECT * FROM reminders ORDER BY remind_at DESC", conn)
        conn.close()
        return df


# -----------------------------
# Scheduling helpers
# -----------------------------
def parse_time_str(ts: str) -> time:
    h, m = ts.split(":")
    return time(int(h), int(m))


def minutes_of_day(t: time) -> int:
    return t.hour * 60 + t.minute


def generate_slots(doctor: dict, date_str: str, appt_minutes: int) -> List[str]:
    """
    Generate candidate start times (HH:MM) for the doctor's schedule on date_str.
    Respects weekday availability and lunch.
    Does not check existing appointments (that is done later).
    """
    # determine weekday shortname like Mon/Tue...
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    weekday_short = dt.strftime("%a")  # Mon, Tue, Wed ...
    # doctor.weekday_availability may be JSON string in DB
    wa = doctor.get("weekday_availability")
    try:
        if isinstance(wa, str):
            wa_dict = json.loads(wa)
        else:
            wa_dict = wa or {}
    except:
        wa_dict = {}

    # map 'Mon' vs 'Mon' - keep using Mon/Tue/Wed/Thu/Fri
    valid = wa_dict.get(weekday_short, wa_dict.get(weekday_short[:3], True))
    if not valid:
        return []

    start = parse_time_str(doctor.get("start_time", "09:00"))
    end = parse_time_str(doctor.get("end_time", "17:00"))
    lunch_start = parse_time_str(doctor.get("lunch_start", "12:30"))
    lunch_end = parse_time_str(doctor.get("lunch_end", "13:30"))

    start_min = minutes_of_day(start)
    end_min = minutes_of_day(end)

    step = 15  # every 15 minutes candidate
    slots = []
    for m in range(start_min, end_min, step):
        slot_start = m
        slot_end = m + appt_minutes
        if slot_end > end_min:
            continue
        # skip if overlaps lunch
        if not (slot_end <= minutes_of_day(lunch_start) or slot_start >= minutes_of_day(lunch_end)):
            continue
        # format slot start time
        hh = slot_start // 60
        mm = slot_start % 60
        slots.append(f"{hh:02d}:{mm:02d}")
    return slots


def filter_taken_slots(candidate_slots: List[str], existing_times: List[str], appt_minutes: int) -> List[str]:
    # naive approach: if same start time exists, remove. Could consider overlapping ranges.
    existing_set = set(existing_times or [])
    return [s for s in candidate_slots if s not in existing_set]


def next_n_weekdays(n=7) -> List[str]:
    result = []
    d = date.today()
    while len(result) < n:
        d += timedelta(days=1)
        if d.weekday() < 5:
            result.append(d.strftime("%Y-%m-%d"))
    return result


# -----------------------------
# Export helpers
# -----------------------------
def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")
    return buffer.getvalue()


# -----------------------------
# Boot / Seed DB & Files
# -----------------------------
init_db()
seed_demo_patients(50)
seed_demo_doctors()
ensure_doctor_schedule_xlsx()

# -----------------------------
# Session State initializations
# -----------------------------
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "current_patient" not in st.session_state:
    st.session_state.current_patient = {}
if "appointment" not in st.session_state:
    st.session_state.appointment = {}
if "step" not in st.session_state:
    st.session_state.step = "greeting"
if "sent_reminders" not in st.session_state:
    st.session_state.sent_reminders = []  # store simulated sends for demo

# -----------------------------
# Layout: Sidebar & Nav
# -----------------------------
with st.sidebar:
    st.markdown('<div class="mh"><h2 style="margin:0">MediCare Agent</h2><div class="small-muted">Allergy & Wellness Center - Demo</div></div>', unsafe_allow_html=True)

    nav = st.radio("Go to", ["Home", "Greeting", "Scheduling", "Appointments", "Patients", "Doctors", "Reminders & Exports", "Settings"], index=0)
    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)

    # quick KPIs
    appts = DAL.all_appointments_df()
    pats = DAL.all_patients_df()
    docs = DAL.all_doctors_df()
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"<div class='card'><div class='pill'>Appointments</div><h3 style='margin:.25rem 0 0 0'>{len(appts)}</h3><div class='small-muted'>Total</div></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='card'><div class='pill'>Doctors</div><h3 style='margin:.25rem 0 0 0'>{len(docs)}</h3><div class='small-muted'>Active</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='card'><div class='pill'>Patients</div><h3 style='margin:.25rem 0 0 0'>{len(pats)}</h3><div class='small-muted'>On File</div></div>", unsafe_allow_html=True)
        upcoming = appts[appts["date"] >= datetime.now().strftime("%Y-%m-%d")].shape[0] if not appts.empty else 0
        st.markdown(f"<div class='card'><div class='pill'>Upcoming</div><h3 style='margin:.25rem 0 0 0'>{upcoming}</h3><div class='small-muted'>Next 7 days</div></div>", unsafe_allow_html=True)

    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)

# -----------------------------
# Home
# -----------------------------
if nav == "Home":
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.subheader("Welcome — MediCare AI Scheduling Agent (Demo)")
    st.write("This app implements the intern case-study MVP: greeting, patient lookup, smart scheduling (60m vs 30m), insurance capture, confirmation, intake form distribution and simulated reminders.")
    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)

    st.markdown("### Conversation Assistant (Quick demo)")
    with st.form("assistant_demo"):
        text = st.text_area("Type a request (ex: 'Book me with Dr. Chen next Wednesday morning')", height=100)
        generate = st.form_submit_button("Analyze Intent & Plan")
    if generate and text.strip():
        ut = text.lower()
        if any(k in ut for k in ["resched", "reschedule", "move", "change time"]):
            intent = "reschedule"
        elif any(k in ut for k in ["cancel", "drop", "remove"]):
            intent = "cancel"
        else:
            intent = "schedule"
        st.info(f"Detected intent: **{intent}**")
        st.markdown(
            """
            **Suggested Plan**
            - Identify patient (name, DOB, phone)
            - Confirm doctor & appointment type
            - Offer top 3 available slots
            - Confirm & create appointment, collect insurance info if missing
            - Send confirmation and schedule reminders (72h, 24h, 4h)
            """
        )
    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# Greeting / Lookup / Start Workflow
# -----------------------------
if nav == "Greeting":
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.subheader("👋 Patient Greeting & Lookup")
    st.write("Enter patient details to find existing record or create a new patient. We'll auto-assign new patients a 60-minute initial slot by default.")
    with st.form("greet_form"):
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("First Name *", key="g_first")
            dob = st.date_input("Date of Birth *", key="g_dob", value=date(1990, 1, 1))
        with col2:
            last_name = st.text_input("Last Name *", key="g_last")
            phone = st.text_input("Phone *", key="g_phone", placeholder="+1-555-123-4567")
        email = st.text_input("Email", key="g_email")
        submitted = st.form_submit_button("🔍 Find My Information")
    if submitted:
        if not first_name or not last_name or not phone:
            st.error("Please provide First Name, Last Name and Phone.")
        else:
            # search by exact name or phone/email substring
            q = f"{first_name} {last_name}"
            df_by_name = DAL.search_patients(q)
            df_by_phone = DAL.search_patients(phone)
            # combine
            combined = pd.concat([df_by_name, df_by_phone]).drop_duplicates(subset=["patient_id"]) if not df_by_name.empty or not df_by_phone.empty else pd.DataFrame()
            if not combined.empty:
                # pick best match by phone/email if available
                st.success("✅ Patient Found")
                st.dataframe(combined[["patient_id", "full_name", "dob", "phone", "email", "patient_type"]], use_container_width=True)
                # allow selecting one
                sel = st.selectbox("Select patient to proceed", options=combined["patient_id"].tolist(), format_func=lambda pid: combined[combined["patient_id"] == pid]["full_name"].iloc[0])
                if sel:
                    patient = DAL.get_patient(sel)
                    st.session_state.current_patient = patient
                    st.session_state.step = "scheduling"
                    st.info(f"Loaded patient: {patient['full_name']} — you can go to Scheduling tab or continue here.")
            else:
                st.info("No existing patient found — creating a new temporary record.")
                new_pid = gen_id("PAT", 6)
                patient = {
                    "patient_id": new_pid,
                    "first_name": first_name.strip(),
                    "last_name": last_name.strip(),
                    "full_name": f"{first_name.strip()} {last_name.strip()}",
                    "dob": dob.strftime("%Y-%m-%d"),
                    "phone": phone.strip(),
                    "email": email.strip(),
                    "insurance_company": "",
                    "member_id": "",
                    "group_number": "",
                    "patient_type": "New",
                    "last_visit": None,
                    "created_at": now_str(),
                    "updated_at": now_str(),
                }
                st.session_state.current_patient = patient
                st.success(f"New patient prepared: {patient['full_name']} (temporary).")
                # Offer to save to DB
                if st.button("💾 Save to Patient Records"):
                    DAL.upsert_patient(patient)
                    st.success("Patient saved to records.")
    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# Scheduling Workflow
# -----------------------------
if nav == "Scheduling":
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.subheader("📅 Scheduling — Smart workflow")
    st.write("Flow: Pick patient → Select doctor → Pick date/time → Capture insurance (if new) → Confirm → Distribute intake form & schedule reminders.")
    # pick patient
    patients_df = DAL.all_patients_df()
    if patients_df.empty:
        st.info("No patients on file. Go to Patients tab to add.")
    else:
        pid_opts = patients_df["patient_id"].tolist()
        pid_display = st.selectbox("Select Patient", options=pid_opts, format_func=lambda pid: f"{DAL.get_patient(pid)['full_name']} ({pid})", index=0)
        patient = DAL.get_patient(pid_display)
        st.markdown(f"**Patient:** {patient['full_name']} — Type: {patient['patient_type']}")
        # doctor selection
doctors_df = DAL.all_doctors_df()
doc_opts = doctors_df["doctor_id"].tolist()
doc_display = st.selectbox(
    "Select Doctor",
    options=doc_opts,
    format_func=lambda did: f"{DAL.get_doctor(did)['full_name']} ({DAL.get_doctor(did)['specialty']})"
)
doctor = DAL.get_doctor(doc_display)

        # appointment type (auto-select by patient type)
        suggested_type = "Initial Consultation (60m)" if patient["patient_type"] == "New" else "Follow-up (30m)"
        appt_type = st.selectbox("Appointment Type", options=list(APPT_TYPES.keys()), index=list(APPT_TYPES.keys()).index(suggested_type))
        duration = APPT_TYPES[appt_type]["minutes"]
        # date selection: next 7 weekdays
        days = next_n := next_n_weekdays(7)
        sel_date = st.selectbox("Select Date", days)
        # generate candidate slots
        candidate_slots = generate_slots(doctor, sel_date, duration)
        # remove existing appointment times
        existing_df = DAL.appointments_by_doctor_date(doctor["doctor_id"], sel_date)
        existing_times = existing_df["time"].tolist() if not existing_df.empty else []
        free_slots = filter_taken_slots(candidate_slots, existing_times, duration)
        if not free_slots:
            st.warning("No available slots for this date & doctor. Try another date or doctor.")
        else:
            sel_time = st.selectbox("Available Time (select)", free_slots)
            # insurance capture if missing
            st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
            st.markdown("### Insurance (capture or confirm)")
            col1, col2, col3 = st.columns(3)
            insurer = col1.text_input("Insurance Company", value=patient.get("insurance_company", ""))
            member_id = col2.text_input("Member ID", value=patient.get("member_id", ""))
            group_num = col3.text_input("Group Number", value=patient.get("group_number", ""))
            notes = st.text_area("Notes (optional)")
            # confirm booking
            if st.button("📅 Confirm & Book Appointment"):
                # update patient insurance if empty
                patient_update = patient.copy()
                patient_update["insurance_company"] = insurer.strip()
                patient_update["member_id"] = member_id.strip()
                patient_update["group_number"] = group_num.strip()
                patient_update["updated_at"] = now_str()
                DAL.upsert_patient(patient_update)
                # create appointment in DB
                appt = {
                    "patient_id": patient["patient_id"],
                    "doctor_id": doctor["doctor_id"],
                    "doctor_name": doctor["full_name"],
                    "date": sel_date,
                    "time": sel_time,
                    "duration": duration,
                    "appt_type": appt_type,
                    "location": doctor.get("location", "Main Clinic - Downtown"),
                    "status": "Confirmed",
                    "booking_time": now_str(),
                    "notes": notes,
                }
                aid = DAL.upsert_appointment(appt)
                st.success(f"Appointment confirmed — ID: {aid} — {sel_date} {sel_time} with {doctor['full_name']}")
                # schedule reminders (72h, 24h, 4h)
                appt_dt = datetime.strptime(f"{sel_date} {sel_time}", "%Y-%m-%d %H:%M")
                r1 = (appt_dt - timedelta(hours=72)).strftime("%Y-%m-%d %H:%M")
                r2 = (appt_dt - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M")
                r3 = (appt_dt - timedelta(hours=4)).strftime("%Y-%m-%d %H:%M")
                msg1 = f"Reminder: You have an appointment with {doctor['full_name']} on {sel_date} at {sel_time}."
                msg2 = f"Interactive: Have you completed your intake form for your appointment on {sel_date} at {sel_time}?"
                msg3 = f"Final: Is your visit on {sel_date} at {sel_time} confirmed? Reply 'C' to confirm or 'X' to cancel."
                # create both Email and SMS reminders for each stage (simulation)
                for ch, msg, ts in [("Email", msg1, r1), ("SMS", msg1, r1), ("Email", msg2, r2), ("SMS", msg2, r2), ("Email", msg3, r3), ("SMS", msg3, r3)]:
                    DAL.create_reminder(aid, ts, ch, msg, "Scheduled")
                # attach intake form (allow download)
                if os.path.exists(INTAKE_FORM_PDF):
                    st.info("Intake form attached — patient may download it below.")
                    with open(INTAKE_FORM_PDF, "rb") as f:
                        btn = st.download_button(label="📥 Download Intake Form (PDF)", data=f, file_name="New_Patient_Intake_Form.pdf", mime="application/pdf")
                else:
                    st.warning("Intake form PDF not found on server.")
                # export appointment summary to excel/csv for admin
                appt_df = DAL.all_appointments_df()
                # show appointment summary for this appointment
                st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
                st.subheader("Appointment Summary (Saved)")
                st.dataframe(appt_df[appt_df["appointment_id"] == aid], use_container_width=True)
                # prepare downloadable exports
                csv_bytes = df_to_csv_bytes(appt_df[appt_df["appointment_id"] == aid])
                st.download_button("Download Appointment (CSV)", csv_bytes, file_name=f"appointment_{aid}.csv", mime="text/csv")
                excel_bytes = df_to_excel_bytes(appt_df[appt_df["appointment_id"] == aid])
                st.download_button("Download Appointment (Excel)", excel_bytes, file_name=f"appointment_{aid}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                # save session state
                st.session_state.appointment = DAL.get_appointment(aid)
                st.session_state.step = "confirmation"
    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# Appointments list / manage
# -----------------------------
if nav == "Appointments":
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.subheader("📋 Appointments — View / Reschedule / Cancel")
    appts_df = DAL.all_appointments_df()
    if appts_df.empty:
        st.info("No appointments scheduled yet.")
    else:
        # filter controls
        col1, col2, col3 = st.columns([2, 1, 1])
        q = col1.text_input("Search by patient name or appointment ID")
        date_filter = col2.date_input("Date (optional)", value=None)
        status_filter = col3.selectbox("Status", options=["All", "Confirmed", "Cancelled"], index=0)
        filtered = appts_df.copy()
        if q:
            filtered = filtered[filtered["patient_name"].str.contains(q, case=False, na=False) | filtered["appointment_id"].str.contains(q, na=False)]
        if date_filter:
            filtered = filtered[filtered["date"] == date_filter.strftime("%Y-%m-%d")]
        if status_filter != "All":
            filtered = filtered[filtered["status"] == status_filter]
        st.dataframe(filtered[["appointment_id", "patient_name", "doctor_name", "date", "time", "appt_type", "status"]], use_container_width=True, height=360)
        # Manage one appointment by ID
        st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
        st.subheader("Manage Appointment")
        aid = st.text_input("Enter Appointment ID", placeholder="APT123456")
        if st.button("Load Appointment"):
            if not aid.strip():
                st.error("Enter an appointment ID.")
            else:
                app = DAL.get_appointment(aid.strip())
                if not app:
                    st.error("Appointment not found.")
                else:
                    st.markdown(f"**Appointment:** {app['appointment_id']} — {app['date']} {app['time']} with {app['doctor_name']}")
                    cols = st.columns(3)
                    new_date = cols[0].date_input("New Date", value=datetime.strptime(app["date"], "%Y-%m-%d").date())
                    # compute available times based on doctor
                    doc = DAL.get_doctor(app["doctor_id"])
                    cand_slots = generate_slots(doc, new_date.strftime("%Y-%m-%d"), app["duration"])
                    taken_df = DAL.appointments_by_doctor_date(doc["doctor_id"], new_date.strftime("%Y-%m-%d"))
                    taken = taken_df["time"].tolist() if not taken_df.empty else []
                    free = filter_taken_slots(cand_slots, taken, app["duration"])
                    new_time = cols[1].selectbox("New Time", options=free) if free else None
                    if cols[2].button("Reschedule"):
                        if not new_time:
                            st.error("No free time selected.")
                        else:
                            app["date"] = new_date.strftime("%Y-%m-%d")
                            app["time"] = new_time
                            DAL.upsert_appointment(app)
                            st.success("Appointment rescheduled.")
                            st.experimental_rerun()
                    if st.button("Cancel Appointment"):
                        app["status"] = "Cancelled"
                        DAL.upsert_appointment(app)
                        st.warning("Appointment cancelled.")
                        st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# Patients CRUD
# -----------------------------
if nav == "Patients":
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.subheader("👥 Patients — Search / Add / Edit / Delete")
    q = st.text_input("Search (name, phone, email)")
    if q:
        df = DAL.search_patients(q)
    else:
        df = DAL.all_patients_df()
    if df.empty:
        st.info("No patients found.")
    else:
        st.dataframe(df[["patient_id", "full_name", "dob", "phone", "email", "insurance_company", "patient_type"]], use_container_width=True, height=300)

    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
    st.subheader("Add or Edit Patient")
    with st.form("patient_upsert"):
        col1, col2 = st.columns(2)
        pid = col1.text_input("Patient ID (leave blank to create new)")
        first = col1.text_input("First Name")
        last = col2.text_input("Last Name")
        dob = col1.date_input("DOB", value=date(1990, 1, 1))
        phone = col2.text_input("Phone")
        email = col1.text_input("Email")
        insurance_company = col2.text_input("Insurance Company")
        member_id = col1.text_input("Member ID")
        group_number = col2.text_input("Group Number")
        patient_type = col1.selectbox("Patient Type", options=["New", "Returning"])
        last_visit = col2.text_input("Last Visit (YYYY-MM-DD)", value="")
        save = st.form_submit_button("Save Patient")
        if save:
            if not first or not last or not phone:
                st.error("First name, last name and phone are required.")
            else:
                pdata = {
                    "patient_id": pid.strip() or None,
                    "first_name": first.strip(),
                    "last_name": last.strip(),
                    "full_name": f"{first.strip()} {last.strip()}",
                    "dob": dob.strftime("%Y-%m-%d"),
                    "phone": phone.strip(),
                    "email": email.strip(),
                    "insurance_company": insurance_company.strip(),
                    "member_id": member_id.strip(),
                    "group_number": group_number.strip(),
                    "patient_type": patient_type,
                    "last_visit": last_visit.strip() or None,
                }
                new_pid = DAL.upsert_patient(pdata)
                st.success(f"Saved patient {pdata['full_name']} (ID: {new_pid})")
                st.experimental_rerun()

    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
    st.subheader("Delete Patient")
    pid_del = st.text_input("Enter Patient ID to delete")
    if st.button("Delete Patient"):
        if not pid_del.strip():
            st.error("Provide a patient ID.")
        else:
            DAL.delete_patient(pid_del.strip())
            st.warning(f"Deleted patient {pid_del.strip()}")
            st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# Doctors CRUD
# -----------------------------
if nav == "Doctors":
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.subheader("👨‍⚕️ Doctors — Manage availability & profiles")
    docs_df = DAL.all_doctors_df()
    if docs_df.empty:
        st.info("No doctors found.")
    else:
        # show doctor table with important columns
        display_cols = ["doctor_id", "full_name", "specialty", "location", "weekday_availability", "start_time", "end_time"]
        st.dataframe(docs_df[display_cols], use_container_width=True, height=300)

    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
    st.subheader("Add / Edit Doctor")
    with st.form("doctor_form"):
        did = st.text_input("Doctor ID (leave blank to create new)")
        full_name = st.text_input("Full Name")
        specialty = st.text_input("Specialty", value="Allergy & Immunology")
        location = st.text_input("Location", value="Main Clinic - Downtown")
        start_time = st.text_input("Start Time (HH:MM)", value="09:00")
        end_time = st.text_input("End Time (HH:MM)", value="17:00")
        lunch_start = st.text_input("Lunch Start (HH:MM)", value="12:30")
        lunch_end = st.text_input("Lunch End (HH:MM)", value="13:30")
        # weekday availability
        cols = st.columns(5)
        wk = ["Mon", "Tue", "Wed", "Thu", "Fri"]
        avail = {}
        for i, w in enumerate(wk):
            avail[w] = cols[i].checkbox(w, value=True)
        saved = st.form_submit_button("Save Doctor")
        if saved:
            if not full_name.strip():
                st.error("Doctor name required.")
            else:
                d = {
                    "doctor_id": did.strip() or None,
                    "full_name": full_name.strip(),
                    "specialty": specialty.strip(),
                    "weekday_availability": avail,
                    "start_time": start_time.strip(),
                    "end_time": end_time.strip(),
                    "lunch_start": lunch_start.strip(),
                    "lunch_end": lunch_end.strip(),
                    "location": location.strip(),
                }
                new_id = DAL.upsert_doctor(d)
                st.success(f"Saved doctor {full_name} (ID: {new_id})")
                st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# Reminders & Exports
# -----------------------------
if nav == "Reminders & Exports":
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.subheader("🔔 Reminders — Simulated sends & export")
    reminders_df = DAL.all_reminders_df()
    if reminders_df.empty:
        st.info("No reminders scheduled.")
    else:
        st.dataframe(reminders_df[["reminder_id", "appointment_id", "remind_at", "channel", "state"]], use_container_width=True, height=300)
    # Simulate sending reminders whose time <= now (for demo)
    if st.button("Simulate sending due reminders now"):
        now = datetime.now()
        to_send = reminders_df[reminders_df["state"] == "Scheduled"]
        sent_count = 0
        for _, r in to_send.iterrows():
            # treat remind_at as YYYY-MM-DD HH:MM; if <= now then "send"
            try:
                remind_dt = datetime.strptime(r["remind_at"], "%Y-%m-%d %H:%M")
            except:
                # if parsing fails, send them all in simulation
                remind_dt = now
            if remind_dt <= now:
                # simulate send
                st.write(f"Simulated send -> {r['channel']} for {r['appointment_id']}: {r['message']}")
                # mark as sent in DB
                conn = get_conn()
                cur = conn.cursor()
                cur.execute("UPDATE reminders SET state='Sent' WHERE reminder_id=?", (r["reminder_id"],))
                conn.commit()
                conn.close()
                sent_count += 1
        if sent_count == 0:
            st.info("No scheduled reminders were due at this time (simulation).")
        else:
            st.success(f"Simulated sending {sent_count} reminder(s).")
        st.experimental_rerun()

    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
    st.subheader("Export Data")
    appts_df = DAL.all_appointments_df()
    pats_df = DAL.all_patients_df()
    docs_df = DAL.all_doctors_df()
    if not appts_df.empty:
        st.download_button("Export Appointments (CSV)", df_to_csv_bytes(appts_df), file_name="appointments_export.csv", mime="text/csv")
        st.download_button("Export Appointments (Excel)", df_to_excel_bytes(appts_df), file_name="appointments_export.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    if not pats_df.empty:
        st.download_button("Export Patients (CSV)", df_to_csv_bytes(pats_df), file_name="patients_export.csv", mime="text/csv")
    if not docs_df.empty:
        st.download_button("Export Doctors (CSV)", df_to_csv_bytes(docs_df), file_name="doctors_export.csv", mime="text/csv")
    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# Settings / Import & Reset
# -----------------------------
if nav == "Settings":
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.subheader("⚙️ Settings — Import Data / Reset DB")
    st.markdown("**Import sample patients CSV**")
    uploaded = st.file_uploader("Upload patients CSV (optional, will append)", type=["csv"])
    if uploaded is not None:
        try:
            df = pd.read_csv(uploaded)
            imported = 0
            for _, row in df.iterrows():
                pdata = {
                    "patient_id": row.get("patient_id", None),
                    "first_name": row.get("first_name", ""),
                    "last_name": row.get("last_name", ""),
                    "full_name": row.get("full_name", f"{row.get('first_name','')} {row.get('last_name','')}"),
                    "dob": row.get("dob", ""),
                    "phone": row.get("phone", ""),
                    "email": row.get("email", ""),
                    "insurance_company": row.get("insurance_company", ""),
                    "member_id": row.get("member_id", ""),
                    "group_number": row.get("group_number", ""),
                    "patient_type": row.get("patient_type", "New"),
                    "last_visit": row.get("last_visit", None),
                }
                DAL.upsert_patient(pdata)
                imported += 1
            st.success(f"Imported {imported} patients.")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Failed to import: {e}")

    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
    st.markdown("**Doctor schedule (Excel)**")
    if os.path.exists(DOCTOR_SCHEDULE_XLSX):
        st.markdown(f"- Found schedule file: `{DOCTOR_SCHEDULE_XLSX}`")
        if st.button("Download sample doctor_schedules.xlsx"):
            with open(DOCTOR_SCHEDULE_XLSX, "rb") as f:
                st.download_button("Download doctor schedule", f, file_name="doctor_schedules.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("Doctor schedule file not found; a sample will be generated from doctors table.")
    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
    st.markdown("#### Dangerous actions")
    if st.checkbox("Enable destructive actions"):
        if st.button("Reset Database to demo state (Deletes medicare.db and recreates)"):
            if os.path.exists(DB_PATH):
                os.remove(DB_PATH)
            init_db()
            seed_demo_patients(50)
            seed_demo_doctors()
            st.success("Database reset complete.")
            st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# Footer + Helpful Links (intake form, case-study PDF)
# -----------------------------
st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
col1, col2 = st.columns([1, 2])
with col1:
    if os.path.exists(INTAKE_FORM_PDF):
        with open(INTAKE_FORM_PDF, "rb") as f:
            st.download_button("📄 Intake Form (PDF)", f, file_name="New_Patient_Intake_Form.pdf", mime="application/pdf")
    else:
        st.caption("Intake form not available.")
with col2:
    if os.path.exists(CASE_STUDY_PDF):
        with open(CASE_STUDY_PDF, "rb") as f:
            st.download_button("📁 Case-Study Brief (PDF)", f, file_name="Data_Science_Intern_RagaAI.pdf", mime="application/pdf")
    st.caption("Use Settings to import sample patient CSV or reset DB (demo mode).")

st.markdown("<div style='margin-top:10px; font-size:0.9rem' class='small-muted'>Built for the AI Scheduling Agent case study — demonstrates scheduling flow, reminders, export & basic admin operations.</div>", unsafe_allow_html=True)
