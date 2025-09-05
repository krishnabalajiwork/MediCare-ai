import streamlit as st
from pages import home, booking, doctors

def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def main():
    # Load CSS from the external file
    load_css('assets/style.css')
    
    # Simple dictionary to map page names to their render functions
    PAGES = {
        "Home": home,
        "Book an Appointment": booking,
        "Our Doctors": doctors,
    }

    # Sidebar Navigation
    st.sidebar.title("Navigation")
    
    # Use st.query_params to set the page from button clicks
    if "page" not in st.query_params:
        st.query_params["page"] = "Home"

    # Create a radio button for navigation
    selection_key = st.query_params["page"]
    selection = st.sidebar.radio("Go to", list(PAGES.keys()), index=list(PAGES.keys()).index(selection_key), key="nav_radio")

    # Update query params when radio button changes
    if selection != selection_key:
        st.query_params["page"] = selection
        st.rerun()

    # Render the selected page
    page = PAGES[selection]
    page.render()

if __name__ == "__main__":
    main()
