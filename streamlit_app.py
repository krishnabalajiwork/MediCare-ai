import streamlit as st
from pages import home, booking, doctors

def load_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"CSS file not found: {file_name}")

def main():
    # Load CSS from the external file
    load_css('assets/styles.css')
    
    PAGES = {
        "Home": home,
        "Book an Appointment": booking,
        "Our Doctors": doctors,
    }

    st.sidebar.title("🩺 MediCare Navigation")
    
    selection = st.sidebar.radio("Go to", list(PAGES.keys()))

    # Render the selected page
    page = PAGES[selection]
    page.render()

if __name__ == "__main__":
    main()
