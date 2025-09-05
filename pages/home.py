import streamlit as st
from streamlit_lottie import st_lottie
import requests

def render():
    # Function to load Lottie animation from URL
    def load_lottieurl(url: str):
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()

    # Lottie animation URL
    lottie_animation_url = "https://lottie.host/e22025e7-2b3a-4428-9869-ff22f5a6f22c/s7yKk7B2aU.json"
    lottie_anim = load_lottieurl(lottie_animation_url)

    # Banner Section
    st.markdown("""
    <div class="banner">
        <h1>Caring For Life</h1>
    </div>
    """, unsafe_allow_html=True)

    # Main Content
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    
    col1, col2 = st.columns((1.5, 1))

    with col1:
        st.subheader("Welcome to MediCare")
        st.title("Your Health, Our Priority")
        st.write("""
        At MediCare, we are dedicated to providing the highest quality of healthcare with a compassionate touch. 
        Our state-of-the-art facilities and expert medical professionals are here to support you and your family's health and wellness journey.

        - **Expert Doctors:** Access to leading specialists in every field.
        - **Advanced Technology:** Utilizing the latest medical technology for accurate diagnosis and treatment.
        - **Patient-Centered Care:** We listen to our patients and create personalized care plans.
        
        Use our AI Scheduling Agent to book an appointment with one of our specialists today.
        """)
        
    with col2:
        if lottie_anim:
            st_lottie(lottie_anim, height=300, key="medical_animation")

    st.markdown('</div>', unsafe_allow_html=True)
