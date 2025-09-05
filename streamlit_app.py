# app.py
# --------------------------------------------------------------------------------------
# MediCare AI Scheduling Agent - Full Featured Streamlit App (~1000 lines target)
# --------------------------------------------------------------------------------------
# Highlights:
# - Modern UI with custom CSS and accessible components
# - SQLite persistence: patients, doctors, appointments, reminders
# - End-to-end scheduling: create, search, reschedule, cancel, confirm
# - Role-like sections: Home, Patients, Appointments, Doctors, Analytics, Settings
# - Smart availability generator (weekdays, lunch breaks, slot length by appt type)
# - Email/SMS reminder simulation + schedule export
# - Import/Export CSV, XLSX
# - Conversation assistant mock (intent recognition: schedule/reschedule/cancel)
# - Defensive coding, form validation, helpful empty states
# --------------------------------------------------------------------------------------

import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime, timedelta, time, date
import random
import string
from typing import List, Dict, Tuple, Optional
import io
import json
import math

# --------------------------------------------------------------------------------------
# Page Config and Global Styles
# --------------------------------------------------------------------------------------

st.set_page_config(
    page_title="MediCare AI Scheduling Agent",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------------------
# CSS: modern medical theme with accessible contrast and responsive spacing
# --------------------------------------------------------------------------------------

MEDICAL_CSS = """
<style>
:root{
  --mc-primary:#1e40af;
  --mc-primary-2:#3b82f6;
  --mc-green:#059669;
  --mc-green-2:#10b981;
  --mc-orange:#d97706;
  --mc-red:#dc2626;
  --mc-bg:#f8fafc;
  --mc-surface:#ffffff;
  --mc-muted:#64748b;
  --mc-border:#e2e8f0;
  --mc-blue-soft:#e0f2fe;
  --mc-green-soft:#d1fae5;
  --mc-orange-soft:#fef3c7;
  --mc-blue-soft-2:#dbeafe;
  --mc-shadow:0 8px 24px rgba(2,6,23,.06);
}
* { font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; }
.main > div { padding-top: 1rem !important; }
.mh { background: linear-gradient(135deg, var(--mc-primary) 0%, var(--mc-primary-2) 100%);
      color:#fff; padding:1.25rem 1.25rem; border-radius: 0 0 18px 18px; 
      margin:-2rem -2rem 1.25rem -2rem; box-shadow: var(--mc-shadow); }
.mh h1{ margin:0; font-weight:800; letter-spacing:.2px; text-shadow:0 1px 1px rgba(0,0,0,0.15);}
.mh p{ opacity:.95; margin:.25rem 0 0 0; }
.section{ background:var(--mc-surface); border:1px solid var(--mc-border); border-radius:14px;
          padding:1rem 1.25rem; box-shadow: var(--mc-shadow); }
.section-title{ color:var(--mc-primary); font-weight:700; margin:0 0 .5rem 0; }
.badge{ display:inline-flex; align-items:center; gap:.4rem; border-radius:999px; padding:.25rem .6rem; font-size:.85rem; border:1px solid rgba(255,255,255,.35); background:rgba(255,255,255,.15); color:#fff; }
.kpi{ text-align:center; background:var(--mc-surface); border:1px solid var(--mc-border); border-radius:14px; padding:1rem; }
.kpi .num{ font-weight:800; font-size:1.8rem; color:var(--mc-primary); }
.kpi .lbl{ color:var(--mc-muted); font-weight:600; }
.card{ background:#fff; border:1px solid var(--mc-border); border-radius:14px; padding:1rem; box-shadow:var(--mc-shadow); }
.callout-info{ background:var(--mc-blue-soft-2); border-left:4px solid var(--mc-primary); padding:.8rem 1rem; border-radius:.5rem; }
.callout-warn{ background:var(--mc-orange-soft); border-left:4px solid var(--mc-orange); padding:.8rem 1rem; border-radius:.5rem; }
.callout-ok{ background:var(--mc-green-soft); border-left:4px solid var(--mc-green); padding:.8rem 1rem; border-radius:.5rem; }
.btn-primary button{ background: linear-gradient(135deg, var(--mc-primary) 0%, var(--mc-primary-2) 100%) !important; color:#fff !important; border:none; }
.btn-success button{ background: linear-gradient(135deg, var(--mc-green) 0%, var(--mc-green-2) 100%) !important; color:#fff !important; border:none; }
.btn-danger button{ background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important; color:#fff !important; border:none; }
.small-muted{ color:var(--mc-muted); font-size:.9rem;}
.hr{ height:1px; background:var(--mc-border); margin:.75rem 0;}
.tbl-note{ font-size:.85rem; color:var(--mc-muted);}
.search-row{ display:flex; flex-wrap:wrap; gap:.5rem; }
.pill{ padding:.25rem .6rem; border:1px solid var(--mc-border); border-radius:999px; background:#fff; font-size:.82rem; }
.stTextInput>div>div>input, .stSelectbox>div>div>div{ border-radius:10px !important; }
.stDateInput>div>div>input{ border-radius:10px !important; }
.stDataFrame{ border-radius:10px; overflow:hidden; border:1px solid var(--mc-border); box-shadow:var(--mc-shadow);}
.table-top{ display:flex; justify-content:space-between; align-items:center; margin-bottom:.5rem;}
.app-id{ display:inline-block; background:#0ea5e9; color:#fff; border-radius:999px; padding:.25rem .6rem; font-weight:700;}
.label{ font-weight:700; color:#0f172a;}
.footer-note{ opacity:.7; font-size:.9rem;}
.stDownloadButton > button { border-radius:10px !important; }
.st-emotion-cache-13ln4jf, .st-emotion-cache-1kyxreq { padding-top: 0 !important; } /* container top paddings (Streamlit minor versions vary) */
</style>
"""
st.markdown(MEDICAL_CSS, unsafe_allow_html=True)

# --------------------------------------------------------------------------------------
# Utilities
# --------------------------------------------------------------------------------------

DB_PATH = "medicare.db"
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

APPT_TYPES = {
    "Initial Consultation (60m)": {"minutes": 60},
    "Follow-up (30m)": {"minutes": 30},
    "Allergy Testing (45m)": {"minutes": 45},
}

DOCTOR_SPECIALTIES = [
    "Allergy & Immunology",
    "Pulmonology",
    "Dermatology",
    "Pediatrics (Allergy)",
]

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]
DEFAULT_WORK_START = time(9, 0)
DEFAULT_WORK_END = time(17, 0)
DEFAULT_LUNCH_START = time(12, 30)
DEFAULT_LUNCH_END = time(13, 30)

def gen_id(prefix: str, size: int = 6) -> str:
    return f"{prefix}{''.join(random.choices(string.digits, k=size))}"

def to_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()

def to_datetime(s: str) -> datetime:
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M")
    except:
        return datetime.strptime(s, "%Y-%m-%d")

def safe_int(v, fallback=0):
    try: return int(v)
    except: return fallback

def safe_str(v):
    return "" if v is None else str(v)

def df_empty(columns: List[str]) -> pd.DataFrame:
    return pd.DataFrame([], columns=columns)

def read_df(cur, query: str, params: tuple = ()) -> pd.DataFrame:
    cur.execute(query, params)
    rows = cur.fetchall()
    cols = [c[0] for c in cur.description] if cur.description else []
    return pd.DataFrame(rows, columns=cols)

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# --------------------------------------------------------------------------------------
# Database Setup
# --------------------------------------------------------------------------------------

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as conn:
        cur = conn.cursor()
        # patients
        cur.execute("""
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
        """)
        # doctors
        cur.execute("""
        CREATE TABLE IF NOT EXISTS doctors(
            doctor_id TEXT PRIMARY KEY,
            full_name TEXT,
            specialty TEXT,
            weekday_availability TEXT, -- JSON of {"Mon":true,...}
            start_time TEXT,
            end_time TEXT,
            lunch_start TEXT,
            lunch_end TEXT,
            location TEXT,
            created_at TEXT,
            updated_at TEXT
        );
        """)
        # appointments
        cur.execute("""
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
            status TEXT, -- Confirmed, Cancelled
            booking_time TEXT,
            notes TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
            FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
        );
        """)
        # reminders
        cur.execute("""
        CREATE TABLE IF NOT EXISTS reminders(
            reminder_id TEXT PRIMARY KEY,
            appointment_id TEXT,
            remind_at TEXT, -- YYYY-MM-DD HH:MM
            channel TEXT, -- Email/SMS
            message TEXT,
            state TEXT,   -- Scheduled/Sent/Cancelled
            created_at TEXT,
            FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id)
        );
        """)
        conn.commit()

def seed_demo_data():
    with get_conn() as conn:
        cur = conn.cursor()
        # Seed doctors if empty
        cur.execute("SELECT COUNT(*) AS c FROM doctors")
        if cur.fetchone()["c"] == 0:
            doctors = [
                ("DOC1001","Dr. Sarah Chen","Allergy & Immunology", 
                 json.dumps({"Mon":True,"Tue":True,"Wed":True,"Thu":True,"Fri":True}),
                 "09:00","17:00","12:30","13:30","Main Clinic - Downtown"),
                ("DOC1002","Dr. Michael Rodriguez","Pulmonology", 
                 json.dumps({"Mon":True,"Tue":False,"Wed":True,"Thu":False,"Fri":True}),
                 "09:00","17:00","12:30","13:30","North Branch"),
                ("DOC1003","Dr. Emily Johnson","Pediatrics (Allergy)", 
                 json.dumps({"Mon":False,"Tue":True,"Wed":True,"Thu":True,"Fri":False}),
                 "09:00","17:00","12:30","13:30","South Branch"),
                ("DOC1004","Dr. Robert Kim","Dermatology", 
                 json.dumps({"Mon":True,"Tue":True,"Wed":False,"Thu":True,"Fri":True}),
                 "09:00","17:00","12:30","13:30","West Side Clinic"),
            ]
            for d in doctors:
                cur.execute("""
                    INSERT INTO doctors(doctor_id, full_name, specialty, weekday_availability,
                    start_time, end_time, lunch_start, lunch_end, location, created_at, updated_at)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?)
                """, (*d, now_str(), now_str()))
        # Seed a couple of demo patients
        cur.execute("SELECT COUNT(*) AS c FROM patients")
        if cur.fetchone()["c"] == 0:
            demo_patients = [
                ("PAT1001","Kenneth","Davis","Kenneth Davis","1991-03-12","(450) 428-3286","ken.davis@mail.com","Blue Cross","ABC123","GRP5678","New",None, now_str(), now_str()),
                ("PAT1002","Betty","Moore","Betty Moore","1988-07-21","(935) 522-4483","betty.moore@mail.com","Aetna","M99810","AET-22","Returning","2024-04-10", now_str(), now_str()),
                ("PAT1003","Joseph","Lewis","Joseph Lewis","1995-12-02","(206) 977-3615","joseph.lewis@mail.com","United Health","UH7782","UHG-88","New",None, now_str(), now_str()),
            ]
            cur.executemany("""
                INSERT INTO patients(patient_id, first_name, last_name, full_name, dob, phone, email,
                insurance_company, member_id, group_number, patient_type, last_visit, created_at, updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, demo_patients)
        conn.commit()

init_db()
seed_demo_data()

# --------------------------------------------------------------------------------------
# Data Access Layer
# --------------------------------------------------------------------------------------

class DAL:
    @staticmethod
    def search_patients(q: str) -> pd.DataFrame:
        q_like = f"%{q.strip()}%"
        with get_conn() as conn:
            df = read_df(conn.cursor(), """
                SELECT * FROM patients
                WHERE full_name LIKE ? OR phone LIKE ? OR email LIKE ?
                ORDER BY updated_at DESC
            """, (q_like, q_like, q_like))
        return df

    @staticmethod
    def all_patients() -> pd.DataFrame:
        with get_conn() as conn:
            return read_df(conn.cursor(), "SELECT * FROM patients ORDER BY created_at DESC")

    @staticmethod
    def get_patient(pid: str) -> Optional[dict]:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM patients WHERE patient_id=?", (pid,))
            r = cur.fetchone()
            return dict(r) if r else None

    @staticmethod
    def upsert_patient(data: dict) -> str:
        data = {**data}
        if not data.get("patient_id"):
            data["patient_id"] = gen_id("PAT")
            data["created_at"] = now_str()
        data["updated_at"] = now_str()
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(1) AS c FROM patients WHERE patient_id=?", (data["patient_id"],))
            exists = cur.fetchone()["c"] > 0
            if exists:
                cur.execute("""
                UPDATE patients SET first_name=?, last_name=?, full_name=?, dob=?, phone=?, email=?,
                    insurance_company=?, member_id=?, group_number=?, patient_type=?, last_visit=?, updated_at=?
                WHERE patient_id=?
                """, (data.get("first_name",""), data.get("last_name",""), data.get("full_name",""),
                      data.get("dob",""), data.get("phone",""), data.get("email",""),
                      data.get("insurance_company",""), data.get("member_id",""), data.get("group_number",""),
                      data.get("patient_type","New"), data.get("last_visit"), data.get("updated_at"), data["patient_id"]))
            else:
                cur.execute("""
                INSERT INTO patients(patient_id, first_name, last_name, full_name, dob, phone, email,
                    insurance_company, member_id, group_number, patient_type, last_visit, created_at, updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (data["patient_id"], data.get("first_name",""), data.get("last_name",""), data.get("full_name",""),
                      data.get("dob",""), data.get("phone",""), data.get("email",""),
                      data.get("insurance_company",""), data.get("member_id",""), data.get("group_number",""),
                      data.get("patient_type","New"), data.get("last_visit"), data.get("created_at",now_str()), data.get("updated_at",now_str())))
            conn.commit()
        return data["patient_id"]

    @staticmethod
    def delete_patient(pid: str) -> bool:
        with get_conn() as conn:
            cur = conn.cursor()
            # Cascade delete reminders of appointments of this patient
            cur.execute("SELECT appointment_id FROM appointments WHERE patient_id=?", (pid,))
            appts = [r["appointment_id"] for r in cur.fetchall()]
            for aid in appts:
                cur.execute("DELETE FROM reminders WHERE appointment_id=?", (aid,))
            cur.execute("DELETE FROM appointments WHERE patient_id=?", (pid,))
            cur.execute("DELETE FROM patients WHERE patient_id=?", (pid,))
            conn.commit()
        return True

    # --- Doctors ---
    @staticmethod
    def all_doctors() -> pd.DataFrame:
        with get_conn() as conn:
            return read_df(conn.cursor(), "SELECT * FROM doctors ORDER BY full_name ASC")

    @staticmethod
    def get_doctor(did: str) -> Optional[dict]:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM doctors WHERE doctor_id=?", (did,))
            r = cur.fetchone()
            return dict(r) if r else None

    @staticmethod
    def upsert_doctor(data: dict) -> str:
        if not data.get("doctor_id"):
            data["doctor_id"] = gen_id("DOC")
            data["created_at"] = now_str()
        data["updated_at"] = now_str()
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(1) AS c FROM doctors WHERE doctor_id=?", (data["doctor_id"],))
            exists = cur.fetchone()["c"] > 0
            if exists:
                cur.execute("""
                UPDATE doctors SET full_name=?, specialty=?, weekday_availability=?, start_time=?, end_time=?,
                    lunch_start=?, lunch_end=?, location=?, updated_at=?
                WHERE doctor_id=?
                """, (
                    data.get("full_name",""),
                    data.get("specialty",""),
                    json.dumps(data.get("weekday_availability",{})),
                    data.get("start_time","09:00"),
                    data.get("end_time","17:00"),
                    data.get("lunch_start","12:30"),
                    data.get("lunch_end","13:30"),
                    data.get("location","Main Clinic - Downtown"),
                    data["updated_at"], data["doctor_id"]
                ))
            else:
                cur.execute("""
                INSERT INTO doctors(doctor_id, full_name, specialty, weekday_availability, start_time, end_time,
                    lunch_start, lunch_end, location, created_at, updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    data["doctor_id"], data.get("full_name",""), data.get("specialty",""),
                    json.dumps(data.get("weekday_availability",{})),
                    data.get("start_time","09:00"), data.get("end_time","17:00"),
                    data.get("lunch_start","12:30"), data.get("lunch_end","13:30"),
                    data.get("location","Main Clinic - Downtown"), data.get("created_at",now_str()), data.get("updated_at",now_str())
                ))
            conn.commit()
        return data["doctor_id"]

    @staticmethod
    def delete_doctor(did: str) -> bool:
        with get_conn() as conn:
            cur = conn.cursor()
            # cascade delete doctor's appointments and reminders
            cur.execute("SELECT appointment_id FROM appointments WHERE doctor_id=?", (did,))
            appts = [r["appointment_id"] for r in cur.fetchall()]
            for aid in appts:
                cur.execute("DELETE FROM reminders WHERE appointment_id=?", (aid,))
            cur.execute("DELETE FROM appointments WHERE doctor_id=?", (did,))
            cur.execute("DELETE FROM doctors WHERE doctor_id=?", (did,))
            conn.commit()
        return True

    # --- Appointments ---
    @staticmethod
    def all_appointments() -> pd.DataFrame:
        with get_conn() as conn:
            return read_df(conn.cursor(), """
            SELECT a.*, p.full_name AS patient_name FROM appointments a
            LEFT JOIN patients p ON p.patient_id = a.patient_id
            ORDER BY date DESC, time DESC
            """)

    @staticmethod
    def get_appointment(aid: str) -> Optional[dict]:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM appointments WHERE appointment_id=?", (aid,))
            r = cur.fetchone()
            return dict(r) if r else None

    @staticmethod
    def patient_appointments(pid: str) -> pd.DataFrame:
        with get_conn() as conn:
            return read_df(conn.cursor(), """
            SELECT * FROM appointments WHERE patient_id=? ORDER BY date DESC, time DESC
            """, (pid,))

    @staticmethod
    def doctor_appointments(did: str, day: Optional[str] = None) -> pd.DataFrame:
        with get_conn() as conn:
            if day:
                return read_df(conn.cursor(), """
                SELECT * FROM appointments WHERE doctor_id=? AND date=? ORDER BY time ASC
                """, (did, day))
            return read_df(conn.cursor(), "SELECT * FROM appointments WHERE doctor_id=?", (did,))

    @staticmethod
    def upsert_appointment(data: dict) -> str:
        if not data.get("appointment_id"):
            data["appointment_id"] = gen_id("APT")
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(1) AS c FROM appointments WHERE appointment_id=?", (data["appointment_id"],))
            exists = cur.fetchone()["c"] > 0
            if exists:
                cur.execute("""
                UPDATE appointments SET patient_id=?, doctor_id=?, doctor_name=?, date=?, time=?, duration=?,
                    appt_type=?, location=?, status=?, booking_time=?, notes=?
                WHERE appointment_id=?
                """, (
                    data.get("patient_id",""), data.get("doctor_id",""), data.get("doctor_name",""),
                    data.get("date",""), data.get("time",""), int(data.get("duration",30)),
                    data.get("appt_type","Follow-up (30m)"), data.get("location",""),
                    data.get("status","Confirmed"), data.get("booking_time",now_str()),
                    data.get("notes",""), data["appointment_id"]
                ))
            else:
                cur.execute("""
                INSERT INTO appointments(appointment_id, patient_id, doctor_id, doctor_name, date, time, duration,
                    appt_type, location, status, booking_time, notes)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    data["appointment_id"], data.get("patient_id",""), data.get("doctor_id",""), data.get("doctor_name",""),
                    data.get("date",""), data.get("time",""), int(data.get("duration",30)),
                    data.get("appt_type","Follow-up (30m)"), data.get("location",""),
                    data.get("status","Confirmed"), data.get("booking_time",now_str()), data.get("notes","")
                ))
            conn.commit()
        return data["appointment_id"]

    @staticmethod
    def delete_appointment(aid: str) -> bool:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM reminders WHERE appointment_id=?", (aid,))
            cur.execute("DELETE FROM appointments WHERE appointment_id=?", (aid,))
            conn.commit()
        return True

    # --- Reminders ---
    @staticmethod
    def create_reminder(appointment_id: str, remind_at: str, channel: str, message: str, state: str = "Scheduled") -> str:
        rid = gen_id("REM")
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
            INSERT INTO reminders(reminder_id, appointment_id, remind_at, channel, message, state, created_at)
            VALUES(?,?,?,?,?,?,?)
            """, (rid, appointment_id, remind_at, channel, message, state, now_str()))
            conn.commit()
        return rid

    @staticmethod
    def reminders_for_appointment(aid: str) -> pd.DataFrame:
        with get_conn() as conn:
            return read_df(conn.cursor(), "SELECT * FROM reminders WHERE appointment_id=? ORDER BY remind_at ASC", (aid,))

# --------------------------------------------------------------------------------------
# Availability & Scheduling Helpers
# --------------------------------------------------------------------------------------

def _time_to_minutes(t: time) -> int:
    return t.hour * 60 + t.minute

def _parse_time(ts: str) -> time:
    h, m = ts.split(":")
    return time(int(h), int(m))

def generate_slots_for_day(doctor: dict, day_str: str, appt_minutes: int) -> List[str]:
    """Generate available times for a doctor on a given date (YYYY-MM-DD)."""
    weekday_name = datetime.strptime(day_str, "%Y-%m-%d").strftime("%a")
    weekday_avail = json.loads(doctor.get("weekday_availability") or "{}")
    if not weekday_avail.get(weekday_name, False):
        return []

    start_t = _parse_time(doctor.get("start_time") or "09:00")
    end_t = _parse_time(doctor.get("end_time") or "17:00")
    lunch_s = _parse_time(doctor.get("lunch_start") or "12:30")
    lunch_e = _parse_time(doctor.get("lunch_end") or "13:30")

    day_minutes = range(_time_to_minutes(start_t), _time_to_minutes(end_t), 15)  # slot every 15m
    slots = []
    for m in day_minutes:
        slot_start = time(m // 60, m % 60)
        slot_end_minutes = m + appt_minutes
        if slot_end_minutes > _time_to_minutes(end_t):
            continue
        slot_end = time(slot_end_minutes // 60, slot_end_minutes % 60)

        # avoid lunch overlap
        if not (slot_end <= lunch_s or slot_start >= lunch_e):
            if not (slot_start >= lunch_s and slot_end <= lunch_e):
                # some overlap with lunch, skip
                continue

        slots.append(f"{slot_start.strftime('%H:%M')}")
    return slots

def remove_conflicts(slots: List[str], taken_times: List[str], appt_minutes:int) -> List[str]:
    """Remove times that conflict with existing appointments plus buffer."""
    taken_set = set(taken_times)
    clean = []
    for s in slots:
        # simple check: don't allow same start; optional: pre/post buffer of 5m
        if s in taken_set:
            continue
        clean.append(s)
    return clean

def next_weekdays(n=7) -> List[str]:
    today = datetime.now().date()
    days = []
    d = today
    for _ in range(n*2): # search ahead to skip weekends
        d += timedelta(days=1)
        if d.weekday() < 5:
            days.append(d.strftime("%Y-%m-%d"))
            if len(days) >= n:
                break
    return days

# --------------------------------------------------------------------------------------
# Download Helpers
# --------------------------------------------------------------------------------------

def download_df(df: pd.DataFrame, filename: str, label: str):
    if df is None or df.empty:
        st.caption("No data available.")
        return
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(label=label + " (CSV)", data=csv, file_name=f"{filename}.csv", mime="text/csv")
    # Excel
    bio = io.BytesIO()
    with pd.ExcelWriter(bio, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")
    st.download_button(label=label + " (Excel)", data=bio.getvalue(), file_name=f"{filename}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --------------------------------------------------------------------------------------
# Sidebar: App Nav & KPIs
# --------------------------------------------------------------------------------------

with st.sidebar:
    st.markdown(
        f"""
        <div class="mh">
            <div style="display:flex;align-items:center;justify-content:space-between;">
              <div>
                <h1>🏥 MediCare Agent</h1>
                <p>Allergy & Wellness Clinic</p>
              </div>
              <span class="badge">v1.0 • Live</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    nav = st.radio(
        "Navigation",
        options=["Home", "Patients", "Appointments", "Doctors", "Analytics", "Settings"],
        index=0,
        label_visibility="collapsed",
    )

    with st.expander("📈 Quick KPIs", expanded=True):
        appts = DAL.all_appointments()
        pats = DAL.all_patients()
        docs = DAL.all_doctors()
        colA, colB = st.columns(2)
        with colA:
            st.markdown('<div class="kpi"><div class="num">{}</div><div class="lbl">Appointments</div></div>'.format(len(appts)), unsafe_allow_html=True)
            st.markdown('<div class="kpi"><div class="num">{}</div><div class="lbl">Patients</div></div>'.format(len(pats)), unsafe_allow_html=True)
        with colB:
            st.markdown('<div class="kpi"><div class="num">{}</div><div class="lbl">Doctors</div></div>'.format(len(docs)), unsafe_allow_html=True)
            upcoming = appts[appts["date"] >= datetime.now().strftime("%Y-%m-%d")].shape[0] if not appts.empty else 0
            st.markdown('<div class="kpi"><div class="num">{}</div><div class="lbl">Upcoming</div></div>'.format(upcoming), unsafe_allow_html=True)

# --------------------------------------------------------------------------------------
# HOME
# --------------------------------------------------------------------------------------

if nav == "Home":
    st.markdown(
        """
        <div class="section">
          <h3 class="section-title">✨ Welcome</h3>
          <p class="small-muted">This assistant helps you schedule, manage, and analyze appointments across MediCare clinics. Use the navigation to access key areas.</p>
          <div class="hr"></div>
          <div class="callout-warn"><b>Medication Reminder:</b> Stop antihistamines 7 days before allergy testing. You may continue nasal sprays, inhalers, and other prescriptions.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")
    c1, c2 = st.columns([1.85, 1])
    with c1:
        st.markdown('<div class="section"><h3 class="section-title">💬 Conversation Assistant</h3>', unsafe_allow_html=True)
        with st.form("assistant_form", clear_on_submit=False):
            user_text = st.text_area("Type your request (e.g., “Schedule me with Dr. Chen next Tuesday morning”)", height=110)
            submitted = st.form_submit_button("Generate Plan")
        plan_box = st.empty()
        if submitted and user_text.strip():
            # naive intent detection
            ut = user_text.lower()
            if any(k in ut for k in ["reschedule", "move", "change time"]):
                intent = "reschedule"
            elif any(k in ut for k in ["cancel", "remove", "drop"]):
                intent = "cancel"
            else:
                intent = "schedule"
            st.session_state["assistant_intent"] = intent
            # Basic response plan
            resp = {
                "intent": intent,
                "steps": [
                    "Identify patient (name, DOB, phone).",
                    "Confirm doctor preference, appointment type, and date range.",
                    "Check availability and propose top 3 slots.",
                    "Confirm & book; collect insurance if missing.",
                    "Send confirmation & schedule reminders."
                ]
            }
            plan_box.info(f"Intent detected: **{intent.upper()}**\n\nProposed Steps:\n- " + "\n- ".join(resp["steps"]))
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="section"><h3 class="section-title">📅 Today</h3>', unsafe_allow_html=True)
        today = datetime.now().strftime("%Y-%m-%d")
        df = DAL.all_appointments()
        if df.empty:
            st.caption("No appointments found.")
        else:
            td = df[df["date"] == today][["appointment_id","doctor_name","time","appt_type","status"]].sort_values("time")
            st.dataframe(td, use_container_width=True, height=270)
        st.markdown("</div>", unsafe_allow_html=True)

# --------------------------------------------------------------------------------------
# PATIENTS
# --------------------------------------------------------------------------------------

if nav == "Patients":
    st.markdown('<div class="section"><h3 class="section-title">👤 Patients</h3>', unsafe_allow_html=True)

    # Search & actions
    qcol1, qcol2, qcol3, qcol4 = st.columns([2,1.2,1.2,1.2])
    q = qcol1.text_input("Search by name, phone, or email", "")
    add_new = qcol2.button("➕ Add Patient", use_container_width=True)
    export_btn = qcol3.button("⬇️ Export All", use_container_width=True)
    reset_btn = qcol4.button("🔄 Refresh", use_container_width=True)

    if reset_btn:
        st.experimental_rerun()

    if export_btn:
        pats = DAL.all_patients()
        download_df(pats, "patients_export", "Download Patients")

    # Listing
    if q.strip():
        df = DAL.search_patients(q)
    else:
        df = DAL.all_patients()
    if df.empty:
        st.info("No patients found. Try adding a new one.")
    else:
        show_cols = ["patient_id","full_name","dob","phone","email","insurance_company","patient_type","last_visit","updated_at"]
        st.markdown('<div class="table-top"><div class="tbl-note">Showing {} records</div></div>'.format(len(df)), unsafe_allow_html=True)
        st.dataframe(df[show_cols], use_container_width=True, height=350)

    # Create/Edit Modal (inline form)
    st.markdown('<div class="hr"></div><h4>Add / Edit Patient</h4>', unsafe_allow_html=True)
    with st.form("patient_form", clear_on_submit=True):
        colsA = st.columns(3)
        first_name = colsA[0].text_input("First Name *")
        last_name  = colsA[1].text_input("Last Name *")
        dob        = colsA[2].date_input("DOB *", value=date(1990,1,1), format="YYYY-MM-DD")
        colsB = st.columns(3)
        phone      = colsB[0].text_input("Phone *", placeholder="(555) 123-4567")
        email      = colsB[1].text_input("Email *", placeholder="you@example.com")
        ptype      = colsB[2].selectbox("Patient Type", ["New","Returning"])
        colsC = st.columns(3)
        insurer   = colsC[0].text_input("Insurance Company", placeholder="Blue Cross Blue Shield")
        member_id = colsC[1].text_input("Member ID", placeholder="ABC123456")
        group_num = colsC[2].text_input("Group Number", placeholder="GRP5678")
        last_visit = st.text_input("Last Visit (YYYY-MM-DD)", value="")
        pid_existing = st.text_input("Existing Patient ID (optional for edit)", placeholder="PAT123456")

        s1, s2 = st.columns([1,4])
        with s1:
            submitted = st.form_submit_button("💾 Save Patient", use_container_width=True)
        with s2:
            delete_click = st.form_submit_button("🗑️ Delete (Enter Patient ID above)", use_container_width=True)

        if submitted:
            errs = []
            if not first_name or not last_name:
                errs.append("Name is required.")
            if not phone or not email:
                errs.append("Phone and Email are required.")
            if errs:
                st.error(" • " + " • ".join(errs))
            else:
                full_name = f"{first_name.strip()} {last_name.strip()}"
                pdict = {
                    "patient_id": pid_existing.strip() if pid_existing.strip() else None,
                    "first_name": first_name.strip(),
                    "last_name": last_name.strip(),
                    "full_name": full_name,
                    "dob": dob.strftime("%Y-%m-%d"),
                    "phone": phone.strip(),
                    "email": email.strip(),
                    "insurance_company": insurer.strip(),
                    "member_id": member_id.strip(),
                    "group_number": group_num.strip(),
                    "patient_type": ptype,
                    "last_visit": last_visit.strip() or None
                }
                pid = DAL.upsert_patient(pdict)
                st.success(f"Saved: {full_name} (ID: {pid})")
                st.experimental_rerun()

        if delete_click:
            if pid_existing.strip():
                DAL.delete_patient(pid_existing.strip())
                st.warning(f"Deleted patient {pid_existing.strip()}")
                st.experimental_rerun()
            else:
                st.error("Provide a Patient ID to delete.")

    st.markdown('</div>', unsafe_allow_html=True)

# --------------------------------------------------------------------------------------
# DOCTORS
# --------------------------------------------------------------------------------------

if nav == "Doctors":
    st.markdown('<div class="section"><h3 class="section-title">👨‍⚕️ Doctors</h3>', unsafe_allow_html=True)
    dc = DAL.all_doctors()
    if dc.empty:
        st.info("No doctors found.")
    else:
        show_cols = ["doctor_id","full_name","specialty","location","weekday_availability","start_time","end_time","lunch_start","lunch_end","updated_at"]
        st.dataframe(dc[show_cols], use_container_width=True, height=320)

    st.markdown('<div class="hr"></div><h4>Add / Edit Doctor</h4>', unsafe_allow_html=True)
    with st.form("doctor_form", clear_on_submit=True):
        c = st.columns(3)
        did = c[0].text_input("Existing Doctor ID (optional to edit)", placeholder="DOC123456")
        full_name = c[1].text_input("Full Name *", value="")
        specialty = c[2].selectbox("Specialty *", DOCTOR_SPECIALTIES)

        c2 = st.columns(3)
        location = c2[0].text_input("Location *", value="Main Clinic - Downtown")
        start_time = c2[1].text_input("Start Time (HH:MM)", value="09:00")
        end_time = c2[2].text_input("End Time (HH:MM)", value="17:00")

        c3 = st.columns(3)
        lunch_start = c3[0].text_input("Lunch Start", value="12:30")
        lunch_end   = c3[1].text_input("Lunch End", value="13:30")
        weekdays = {}
        with c3[2]:
            st.caption("Weekday Availability")
            wcols = st.columns(5)
            for i, w in enumerate(WEEKDAYS):
                weekdays[w] = wcols[i].checkbox(w, value=True)

        s1, s2 = st.columns([1,4])
        save_doc = s1.form_submit_button("💾 Save Doctor", use_container_width=True)
        del_doc = s2.form_submit_button("🗑️ Delete Doctor", use_container_width=True)

        if save_doc:
            d = {
                "doctor_id": did.strip() or None,
                "full_name": full_name.strip(),
                "specialty": specialty.strip(),
                "weekday_availability": weekdays,
                "start_time": start_time.strip(),
                "end_time": end_time.strip(),
                "lunch_start": lunch_start.strip(),
                "lunch_end": lunch_end.strip(),
                "location": location.strip(),
            }
            if not full_name:
                st.error("Full name is required.")
            else:
                doc_id = DAL.upsert_doctor(d)
                st.success(f"Saved: {full_name} (ID: {doc_id})")
                st.experimental_rerun()

        if del_doc:
            if did.strip():
                DAL.delete_doctor(did.strip())
                st.warning(f"Deleted doctor {did.strip()}")
                st.experimental_rerun()
            else:
                st.error("Provide Doctor ID to delete.")

# --------------------------------------------------------------------------------------
# APPOINTMENTS
# --------------------------------------------------------------------------------------

if nav == "Appointments":
    st.markdown('<div class="section"><h3 class="section-title">📆 Appointments</h3>', unsafe_allow_html=True)
    colA, colB = st.columns([1.8, 1])

    # Left: list & filters
    with colA:
        filt = st.container()
        with filt:
            f1, f2, f3, f4 = st.columns(4)
            date_from = f1.date_input("From", value=datetime.now().date(), format="YYYY-MM-DD")
            date_to = f2.date_input("To", value=(datetime.now().date()+timedelta(days=7)), format="YYYY-MM-DD")
            status_sel = f3.multiselect("Status", ["Confirmed","Cancelled"], default=["Confirmed"])
            type_sel = f4.multiselect("Type", list(APPT_TYPES.keys()), default=list(APPT_TYPES.keys()))

        df = DAL.all_appointments()
        if not df.empty:
            df["dt"] = pd.to_datetime(df["date"], errors="coerce")
            df = df[(df["dt"] >= pd.to_datetime(date_from)) & (df["dt"] <= pd.to_datetime(date_to))]
            df = df[df["status"].isin(status_sel)]
            df = df[df["appt_type"].isin(type_sel)]
        st.markdown('<div class="table-top"><div class="tbl-note">Showing {} appointments</div></div>'.format(len(df)), unsafe_allow_html=True)
        if df.empty:
            st.info("No appointments for selected filters.")
        else:
            show_cols = ["appointment_id","patient_id","patient_name","doctor_name","date","time","duration","appt_type","status","location"]
            st.dataframe(df[show_cols].sort_values(["date","time"]), use_container_width=True, height=360)
            with st.expander("⬇️ Export Current View"):
                download_df(df[show_cols], "appointments_filtered", "Download")

    # Right: create / modify
    with colB:
        st.markdown('<div class="card"><h4 class="section-title">➕ New / Modify Appointment</h4>', unsafe_allow_html=True)
        patients = DAL.all_patients()
        doctors = DAL.all_doctors()
        if patients.empty or doctors.empty:
            st.warning("Need at least one patient and one doctor to create appointments.")
        else:
            pcol = st.columns(1)
            sel_patient_name = pcol[0].selectbox("Patient", options=patients["full_name"].tolist())
            sel_patient = patients[patients["full_name"]==sel_patient_name].iloc[0].to_dict()

            dcol = st.columns(1)
            sel_doctor_name = dcol[0].selectbox("Doctor", options=doctors["full_name"].tolist())
            sel_doctor = doctors[doctors["full_name"]==sel_doctor_name].iloc[0].to_dict()

            tcol = st.columns(2)
            appt_type = tcol[0].selectbox("Type", list(APPT_TYPES.keys()))
            duration = APPT_TYPES[appt_type]["minutes"]
            days = next_weekdays(7)
            sel_day = tcol[1].selectbox("Date", days)

            # Generate available times
            taken_today = DAL.doctor_appointments(sel_doctor["doctor_id"], sel_day)
            taken_times = taken_today["time"].tolist() if not taken_today.empty else []
            slots = generate_slots_for_day(sel_doctor, sel_day, duration)
            slots = remove_conflicts(slots, taken_times, duration)

            scol = st.columns(2)
            if len(slots) == 0:
                st.info("No slots available for selected date. Try another date.")
                sel_time = None
            else:
                sel_time = scol[0].selectbox("Time", slots)
            notes = scol[1].text_input("Notes", placeholder="Optional")

            loc = st.text_input("Location", value=sel_doctor.get("location","Main Clinic - Downtown"))
            existing_id = st.text_input("Existing Appointment ID (to reschedule/cancel)", placeholder="APT123456")

            cbtn1, cbtn2 = st.columns(2)
            with cbtn1:
                create_btn = st.button("✅ Confirm Booking", use_container_width=True)
            with cbtn2:
                cancel_btn = st.button("🛑 Cancel Appointment", use_container_width=True)

            if create_btn:
                if not sel_time:
                    st.error("Select a valid time.")
                else:
                    data = {
                        "appointment_id": existing_id.strip() or None,
                        "patient_id": sel_patient["patient_id"],
                        "doctor_id": sel_doctor["doctor_id"],
                        "doctor_name": sel_doctor["full_name"],
                        "date": sel_day,
                        "time": sel_time,
                        "duration": duration,
                        "appt_type": appt_type,
                        "location": loc,
                        "status": "Confirmed",
                        "booking_time": now_str(),
                        "notes": notes
                    }
                    aid = DAL.upsert_appointment(data)
                    st.success(f"Appointment confirmed: {aid}")
                    # Create simulated reminders
                    # 72h, 24h, 4h prior
                    appt_dt = datetime.strptime(f"{sel_day} {sel_time}", "%Y-%m-%d %H:%M")
                    r1 = (appt_dt - timedelta(hours=72)).strftime("%Y-%m-%d %H:%M")
                    r2 = (appt_dt - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M")
                    r3 = (appt_dt - timedelta(hours=4)).strftime("%Y-%m-%d %H:%M")
                    msg1 = f"Reminder: {sel_patient['full_name']} has {appt_type.lower()} with {sel_doctor['full_name']} on {sel_day} at {sel_time}. Please complete intake form."
                    msg2 = "Interactive check: Have you completed the intake form? Is the visit confirmed?"
                    msg3 = "Final reminder: Your appointment is in 4 hours. Reply C to confirm or X to cancel."
                    for ch, msg, ts in [("Email",msg1,r1), ("SMS",msg1,r1), ("Email",msg2,r2), ("SMS",msg2,r2), ("Email",msg3,r3), ("SMS",msg3,r3)]:
                        DAL.create_reminder(aid, ts, ch, msg, "Scheduled")
                    st.balloons()
                    st.experimental_rerun()

            if cancel_btn:
                if not existing_id.strip():
                    st.error("Enter an existing Appointment ID to cancel.")
                else:
                    app = DAL.get_appointment(existing_id.strip())
                    if not app:
                        st.error("Appointment not found.")
                    else:
                        app["status"] = "Cancelled"
                        DAL.upsert_appointment(app)
                        st.warning(f"Appointment {existing_id.strip()} cancelled.")
                        st.experimental_rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    # Appointment detail inspector
    st.markdown('<div class="hr"></div><h4>🔎 Appointment Inspector</h4>', unsafe_allow_html=True)
    sel_id = st.text_input("Enter Appointment ID to view", placeholder="APT123456")
    if sel_id.strip():
        app = DAL.get_appointment(sel_id.strip())
        if not app:
            st.error("No appointment found for that ID.")
        else:
            st.markdown(f"""
            <div class="card">
              <div><span class="app-id">{app['appointment_id']}</span></div>
              <p><span class="label">Patient ID:</span> {app['patient_id']}</p>
              <p><span class="label">Doctor:</span> {app['doctor_name']} &nbsp;|&nbsp; <span class="label">Type:</span> {app['appt_type']}</p>
              <p><span class="label">Date/Time:</span> {app['date']} {app['time']} &nbsp;|&nbsp; <span class="label">Duration:</span> {app['duration']}m</p>
              <p><span class="label">Location:</span> {app['location']} &nbsp;|&nbsp; <span class="label">Status:</span> {app['status']}</p>
              <p><span class="label">Notes:</span> {safe_str(app['notes'])}</p>
            </div>
            """, unsafe_allow_html=True)

            # Reminders
            rms = DAL.reminders_for_appointment(app["appointment_id"])
            st.subheader("📨 Reminders")
            if rms.empty:
                st.caption("No reminders.")
            else:
                st.dataframe(rms, use_container_width=True, height=220)
                download_df(rms, f"reminders_{app['appointment_id']}", "Download Reminders")

# --------------------------------------------------------------------------------------
# ANALYTICS
# --------------------------------------------------------------------------------------

if nav == "Analytics":
    st.markdown('<div class="section"><h3 class="section-title">📊 Analytics & Insights</h3>', unsafe_allow_html=True)

    appts = DAL.all_appointments()
    pats = DAL.all_patients()
    docs = DAL.all_doctors()

    if appts.empty:
        st.info("No appointment data available.")
    else:
        appts["dt"] = pd.to_datetime(appts["date"], errors="coerce")
        appts["weekday"] = appts["dt"].dt.day_name()
        appts["month"] = appts["dt"].dt.to_period("M").astype(str)

        colA, colB = st.columns(2)
        with colA:
            st.markdown("**Appointments by Month**")
            by_month = appts.groupby("month").size().reset_index(name="count").sort_values("month")
            st.bar_chart(by_month.set_index("month"))
        with colB:
            st.markdown("**Appointments by Weekday**")
            by_wd = appts.groupby("weekday").size().reset_index(name="count")
            # reorder
            wd_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
            by_wd["weekday"] = pd.Categorical(by_wd["weekday"], categories=wd_order, ordered=True)
            by_wd = by_wd.sort_values("weekday")
            st.bar_chart(by_wd.set_index("weekday"))

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        colC, colD = st.columns(2)
        with colC:
            st.markdown("**Doctor Workload**")
            by_doc = appts.groupby("doctor_name").size().reset_index(name="count").sort_values("count", ascending=False)
            st.bar_chart(by_doc.set_index("doctor_name"))
        with colD:
            st.markdown("**Patient Type Mix**")
            if pats.empty:
                st.caption("No patients.")
            else:
                mix = pats.groupby("patient_type").size().reset_index(name="count")
                st.bar_chart(mix.set_index("patient_type"))

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        with st.expander("📥 Export Datasets"):
            download_df(appts.drop(columns=["dt"], errors="ignore"), "analytics_appointments", "Appointments")
            download_df(pats, "analytics_patients", "Patients")
            download_df(docs, "analytics_doctors", "Doctors")

    st.markdown('</div>', unsafe_allow_html=True)

# --------------------------------------------------------------------------------------
# SETTINGS (Import/Export, Data Reset)
# --------------------------------------------------------------------------------------

if nav == "Settings":
    st.markdown(
    '<div class="section"><h3 class="section-title">⚙️ Settings</h3></div>',
    unsafe_allow_html=True
)

