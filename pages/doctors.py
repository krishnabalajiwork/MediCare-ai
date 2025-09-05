import streamlit as st

# Sample data - in a real app, this would come from your database
DOCTOR_DATA = [
    {"name": "Dr. Sarah Chen", "specialty": "Allergy & Immunology", "img": "https://i.pravatar.cc/150?img=1"},
    {"name": "Dr. Michael Rodriguez", "specialty": "Pediatric Allergist", "img": "https://i.pravatar.cc/150?img=3"},
    {"name": "Dr. Emily Johnson", "specialty": "Dermatology", "img": "https://i.pravatar.cc/150?img=5"},
    {"name": "Dr. Robert Kim", "specialty": "Immunology Researcher", "img": "https://i.pravatar.cc/150?img=8"},
]

def render_doctor_card(name, specialty, img_url):
    st.markdown(f"""
    <div class="doctor-card">
        <img src="{img_url}" alt="{name}">
        <h3>{name}</h3>
        <p>{specialty}</p>
    </div>
    """, unsafe_allow_html=True)

def render():
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.header("👩‍⚕️ Our Expert Medical Team")
    st.write("Meet the dedicated professionals who make MediCare a leader in healthcare.")
    
    st.markdown('<div class="doctor-grid">', unsafe_allow_html=True)
    for doc in DOCTOR_DATA:
        render_doctor_card(doc["name"], doc["specialty"], doc["img"])
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
