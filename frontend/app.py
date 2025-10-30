import streamlit as st
import folium
from streamlit_folium import st_folium
import requests # for later
from datetime import datetime

# --- Page Setup ---
st.set_page_config(layout="wide")

# CSS to make it look better
st.markdown("""
<style>
    /* Main title font and size */
    h1 {
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
        font-size: 3rem;
    }
    /* Header buttons for better alignment */
    .stButton>button {
        font-weight: 600;
    }
    /* Remove extra space at the top of the main app container */
    .main .block-container {
        padding-top: 2rem;
    }
    /* Center the login/form pages */
    .form-container {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        padding-top: 3rem;
    }
    .form-box {
        width: 450px;
        padding: 2rem;
        background-color: #f0f2f6; /* A light grey background */
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)


# --- Fake Data & Functions (Backend Simulation) ---

# A few test locations in Delhi
DELHI_LOCATIONS = {
    "Connaught Place": {"lat": 28.6328, "lon": 77.2197},
    "Qutub Minar": {"lat": 28.5245, "lon": 77.1855},
    "India Gate": {"lat": 28.6129, "lon": 77.2295},
    "Red Fort": {"lat": 28.6562, "lon": 77.2410},
    "Shahdara": {"lat": 28.6994, "lon": 77.2941},
    "Airport T3": {"lat": 28.5562, "lon": 77.1000},
    "Hauz Khas Village": {"lat": 28.5521, "lon": 77.1936}
}

# MOCK: pretends to get live hazards from the database
@st.cache_data(ttl=60)
def get_fake_hazards(city_id=1):
    mock_data = [
        {"id": 1, "location": {"lat": 28.6324, "lon": 77.2187}, "report_type": "Construction", "created_at": "2025-01-01T10:00:00Z"},
        {"id": 2, "location": {"lat": 28.5245, "lon": 77.1855}, "report_type": "Accident", "created_at": "2025-01-01T10:30:00Z"},
        {"id": 3, "location": {"lat": 28.5729, "lon": 77.2271}, "report_type": "Pothole", "created_at": "2025-01-01T09:00:00Z"}
    ]
    return mock_data

# MOCK: pretends to save a new hazard report
def save_fake_report(report_data):
    print(f"Submitting Mock Report: {report_data}")
    return True

# MOCK: creates two fake routes
def get_fake_routes(start_coords, end_coords):
    mid_point_orig = {"lat": (start_coords['lat'] + end_coords['lat']) / 2 + 0.02, "lon": (start_coords['lon'] + end_coords['lon']) / 2}
    mid_point_alt = {"lat": (start_coords['lat'] + end_coords['lat']) / 2, "lon": (start_coords['lon'] + end_coords['lon']) / 2 + 0.05}
    
    mock_route_data = {
        "original": {"path": [[start_coords['lat'], start_coords['lon']], [mid_point_orig['lat'], mid_point_orig['lon']], [end_coords['lat'], end_coords['lon']]], "risk": "High", "time": 35, "reason_for_risk": "Multiple Construction reports"},
        "alternative": {"path": [[start_coords['lat'], start_coords['lon']], [mid_point_alt['lat'], mid_point_alt['lon']], [end_coords['lat'], end_coords['lon']]], "risk": "Low", "time": 40, "reason_for_risk": "Clear"}
    }
    return mock_route_data

# Helper to get the right icon for the map
def get_hazard_icon(hazard_type):
    icons = {
        "Construction": folium.Icon(color='orange', icon='wrench', prefix='fa'),
        "Accident": folium.Icon(color='red', icon='car-crash', prefix='fa'),
        "Pothole": folium.Icon(color='darkblue', icon='road', prefix='fa'),
        "Traffic Jam": folium.Icon(color='purple', icon='traffic-light', prefix='fa'),
        "Waterlogging": folium.Icon(color='blue', icon='tint', prefix='fa')
    }
    return icons.get(hazard_type, folium.Icon(color='gray', icon='info-sign', prefix='glyphicon'))

# --- Functions to change pages ---

# This function changes the 'page' variable in our session state
def go_to_page(page_name):
    st.session_state['page'] = page_name

# MOCK: fake login check
def check_login_details(email, password):
    if email == "user@example.com" and password == "12345":
        st.session_state['logged_in'] = True
        st.session_state['user_email'] = email
        return True
    return False

# MOCK: fake signup
def create_fake_user(email, password):
    st.session_state['logged_in'] = True
    st.session_state['user_email'] = email
    return True

# Clears the session to log the user out
def logout():
    st.session_state['logged_in'] = False
    st.session_state.pop('user_email', None)
    st.session_state['page'] = 'main' # Go back to map on logout
    st.rerun()

# --- Functions to draw the app pages ---

# This function draws the header at the top
def show_header():
    header = st.container()
    with header:
        left_col, right_col = st.columns([0.6, 0.4])
        
        with left_col:
            st.markdown("<h1 style='margin: 0;'>Traffix</h1>", unsafe_allow_html=True)
            st.markdown("<p style='margin: 0; color: grey;'>A Proactive Traffic Prediction and Smart Rerouting System</p>", unsafe_allow_html=True)
            
        with right_col:
            cols = st.columns(4) # 4 columns for buttons
            if st.session_state.get('logged_in', False):
                # Show these if user IS logged in
                cols[1].button("Profile", on_click=go_to_page, args=['profile'], use_container_width=True)
                cols[2].button("About Us", on_click=go_to_page, args=['about'], use_container_width=True)
                cols[3].button("Logout", on_click=logout, use_container_width=True)
            else:
                # Show these if user is a GUEST
                cols[1].button("Login", on_click=go_to_page, args=['login'], use_container_width=True)
                cols[2].button("Sign Up", on_click=go_to_page, args=['signup'], use_container_width=True)
                cols[3].button("About Us", on_click=go_to_page, args=['about'], use_container_width=True)
    st.markdown("---")


# This function draws the left sidebar
def show_sidebar():
    with st.sidebar:
        st.image("Images/logo.jpg", width=150) # Smaller logo
        st.markdown("---")
        
        # BUG FIX: Only show the "Actions" on the main map page.
        # This stops the white box from appearing on other pages.
        if st.session_state.get('page', 'main') == 'main':
            st.header("Actions")
            with st.expander("📍 Plan Your Route", expanded=True):
                start_point = st.text_input("Start Location", "Connaught Place")
                end_point = st.text_input("End Location", "Qutub Minar")

                if st.button("Find Best Route"):
                    if start_point in DELHI_LOCATIONS and end_point in DELHI_LOCATIONS:
                        if start_point == end_point:
                            st.warning("Start and end locations cannot be the same.")
                        else:
                            start_coords = DELHI_LOCATIONS[start_point]
                            end_coords = DELHI_LOCATIONS[end_point]
                            with st.spinner("Analyzing route..."):
                                route_info = get_fake_routes(start_coords, end_coords)
                                st.session_state['route_info'] = route_info
                                st.session_state['map_center'] = [(start_coords['lat'] + end_coords['lat']) / 2, (start_coords['lon'] + end_coords['lon']) / 2]
                    else:
                        st.error(f"Location not found. Please try one of: {', '.join(DELHI_LOCATIONS.keys())}")

            with st.expander("⚠️ Report a Hazard", expanded=True):
                st.info("1. Click a hazard button. \n2. Your next click on the map submits the report.")
                hazard_types = ["🚧 Construction", "💥 Accident", "⚫ Pothole", "💧 Waterlogging", "🚦 Traffic Jam"]
                col1, col2 = st.columns(2)
                for i, hazard in enumerate(hazard_types):
                    if i % 2 == 0:
                        if col1.button(hazard, use_container_width=True):
                            st.session_state['selected_hazard'] = hazard.split(" ")[1]
                            st.toast(f"Ready! Click on the map to report {st.session_state['selected_hazard']}.")
                    else:
                        if col2.button(hazard, use_container_width=True):
                            st.session_state['selected_hazard'] = hazard.split(" ")[1]
                            st.toast(f"Ready! Click on the map to report {st.session_state['selected_hazard']}.")
        
        st.markdown("---")
        st.caption("Copyright © Traffix 2025")


# This function draws the main map page
def show_main_map_page():
    # Set default map location (Delhi)
    map_center = st.session_state.get('map_center', [28.6139, 77.2090])
    # Use Google Maps tiles because they look familiar
    google_maps_tile = "https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}"
    m = folium.Map(location=map_center, zoom_start=12, tiles=google_maps_tile, attr="Google")

    # Get fake hazards and draw them on the map
    live_hazards = get_fake_hazards()
    for hazard in live_hazards:
        loc = [hazard['location']['lat'], hazard['location']['lon']]
        popup_text = f"<b>{hazard['report_type']}</b><br>Reported: {hazard['created_at']}"
        folium.Marker(location=loc, popup=popup_text, icon=get_hazard_icon(hazard['report_type']), tooltip=hazard['report_type']).add_to(m)

    # If we have route data, draw the lines
    if 'route_info' in st.session_state:
        route = st.session_state['route_info']
        folium.PolyLine(locations=route['original']['path'], color='red', weight=5, opacity=0.8, tooltip="Original Route").add_to(m)
        folium.PolyLine(locations=route['alternative']['path'], color='green', weight=5, opacity=0.8, tooltip="Suggested Alternative").add_to(m)

    # This displays the map in Streamlit
    map_data = st_folium(m, width="100%", height=700)

    # This part handles clicking on the map to report a hazard
    if map_data and map_data["last_clicked"] and st.session_state.get('selected_hazard'):
        click_coords = map_data["last_clicked"]
        hazard_type = st.session_state['selected_hazard']
        report_payload = {"city_id": 1, "latitude": click_coords['lat'], "longitude": click_coords['lng'], "report_type": hazard_type}
        
        if save_fake_report(report_payload):
            st.success(f"{hazard_type} reported successfully!")
        else:
            st.error("Failed to submit report.")
        # Clear the selected hazard so we don't report again
        del st.session_state['selected_hazard']

    # Show the analysis box below the map
    if 'route_info' in st.session_state:
        st.subheader("Route Analysis")
        route = st.session_state['route_info']
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Original Route", f"~{route['original']['time']} min", f"Risk: {route['original']['risk']}", delta_color="inverse")
            st.caption(f"Reason: {route['original']['reason_for_risk']}")
        with col2:
            st.metric("Suggested Alternative", f"~{route['alternative']['time']} min", f"Risk: {route['alternative']['risk']}", delta_color="normal")
            st.caption(f"Reason: {route['alternative']['reason_for_risk']}")

# --- Functions to show the other pages (Login, Signup, etc.) ---

# This is a template for all our form pages (Login, Signup, Profile, About)
def show_form_page(title, form_content_function):
    st.markdown("<div class='form-container'>", unsafe_allow_html=True)
    st.markdown("<div class='form-box'>", unsafe_allow_html=True)
    
    st.button("← Back to Map", on_click=go_to_page, args=['main'])
    st.title(title)
    form_content_function() # Runs the specific function for login, signup, etc.
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# This holds the content for the login form
def show_login_form():
    with st.form("login_form"):
        email = st.text_input("Email", "user@example.com")
        password = st.text_input("Password", "12345", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if check_login_details(email, password):
                st.success("Logged in successfully!")
                go_to_page('main') # Go back to the map
                st.rerun()
            else:
                st.error("Invalid email or password.")

# This holds the content for the signup form
def show_signup_form():
    with st.form("signup_form"):
        new_email = st.text_input("Email")
        new_password = st.text_input("Create Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        signup_submitted = st.form_submit_button("Sign Up")
        
        if signup_submitted:
            if new_password == confirm_password:
                if create_fake_user(new_email, new_password):
                    st.success("Account created! Logging in...")
                    go_to_page('main') # Go back to the map
                    st.rerun()
                else:
                    st.error("An error occurred during sign up.")
            else:
                st.error("Passwords do not match.")

# This holds the content for the "About Us" page
def show_about_page_content():
    st.markdown("""
    ### Why Traffix?
    Tired of getting stuck in traffic that appears out of nowhere? Traffix is designed to be your proactive co-pilot, helping you avoid jams *before* they even happen.

    ### What Makes Us Different?
    Unlike other apps that only show current traffic, our smart system analyzes data to **predict** congestion 30-60 minutes in the future.

    ### How It Works
    Our unique AI combines three layers of data:
    - **Permanent Road Quality**
    - **Live Community Reports**
    - **Automated Data (Weather)**
    
    ---
    *This prototype was built by Chirag, Dev, and Puluck.*
    """)

# This holds the content for the "Profile" page
def show_profile_page_content():
    st.write(f"**Email:** {st.session_state.get('user_email', 'N/A')}")
    st.write("**Membership:** Premium (mock)")
    st.write("**Reports Filed:** 5 (mock)")


# --- Main App - This part runs first! ---

# 1. Always draw the header and sidebar
show_header()
show_sidebar()

# 2. Figure out which page to show
current_page = st.session_state.get('page', 'main')

# 3. Show the correct page (this is our "Page Router")
if current_page == 'main':
    show_main_map_page()
elif current_page == 'login':
    show_form_page("Login", show_login_form)
elif current_page == 'signup':
    show_form_page("Create Account", show_signup_form)
elif current_page == 'about':
    show_form_page("About Traffix", show_about_page_content)
elif current_page == 'profile':
    show_form_page("Your Profile", show_profile_page_content)