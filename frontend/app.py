# frontend/app.py

import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import re

st.set_page_config(layout="wide")
BACKEND_URL = "http://127.0.0.1:8000"

# -------------------------
# API Functions
# -------------------------
@st.cache_data(ttl=10)
def get_live_hazards():
    try:
        r = requests.get(f"{BACKEND_URL}/hazards/live", timeout=6)
        r.raise_for_status()
        return r.json()
    except:
        return []

def clear_hazards_cache():
    try: get_live_hazards.clear()
    except: pass

def submit_fast_report(report_type, lat, lon, user_id):
    try:
        r = requests.post(f"{BACKEND_URL}/report/fast?user_id={user_id}",
                          json={"report_type":report_type,"lat":lat,"lon":lon},
                          timeout=8)
        r.raise_for_status()
        return True
    except:
        return False

def get_routes(start_address, end_address):
    try:
        r = requests.post(f"{BACKEND_URL}/route/predict-risk",
                          json={"start_address": start_address,
                                "end_address": end_address},
                          timeout=12)
        r.raise_for_status()
        return r.json()
    except:
        return None

def login_api(email, pw):
    try:
        r = requests.post(f"{BACKEND_URL}/users/login",
                          json={"email":email,"password":pw},
                          timeout=6)
        if r.status_code == 200:
            return r.json().get("token")
    except:
        pass
    return None

def signup_api(email, pw):
    try:
        r = requests.post(f"{BACKEND_URL}/users/signup",
                          json={"email":email,"password":pw},
                          timeout=6)
        return r.status_code == 200
    except:
        return False

# -------------------------
# Helpers
# -------------------------
def extract_report_count(reason):
    if not reason: return 0
    m = re.search(r'(\d+)\s+report', reason)
    return int(m.group(1)) if m else 0

def hazard_icon(name):
    icons = {
        "Construction": ("wrench","orange"),
        "Accident": ("car","red"),
        "Pothole": ("road","darkblue"),
        "Waterlogging": ("tint","blue"),
        "Traffic": ("traffic-light","purple")
    }
    i, c = icons.get(name, ("info-circle","gray"))
    return folium.Icon(icon=i, prefix="fa", color=c)

def back_button():
    if st.button("← Back to Home!"):
        st.session_state["page"] = "main"
        st.rerun()

# -------------------------
# Header
# -------------------------
def render_header():
    left, right = st.columns([0.6,0.4])
    with left:
        st.markdown('<h1 style="color:white;margin:0">Traffix</h1>', unsafe_allow_html=True)
        st.markdown('<div style="color:#9aa0a6;margin-bottom:10px">A Proactive Traffic Prediction and Smart Rerouting System</div>',
                    unsafe_allow_html=True)
    with right:
        c1, c2, c3 = st.columns(3)
        if st.session_state.get("logged_in"):
            if c1.button("Profile"): st.session_state["page"]="profile"; st.rerun()
            if c2.button("About Us"): st.session_state["page"]="about"; st.rerun()
            if c3.button("Logout"):
                center = st.session_state.get("map_center")
                st.session_state.clear()
                if center: st.session_state["map_center"]=center
                st.session_state["page"]="main"
                st.rerun()
        else:
            if c1.button("Login"): st.session_state["page"]="login"; st.rerun()
            if c2.button("Sign Up"): st.session_state["page"]="signup"; st.rerun()
            if c3.button("About Us"): st.session_state["page"]="about"; st.rerun()
    st.markdown("---")

# -------------------------
# Sidebar
# -------------------------
def render_sidebar():
    with st.sidebar:
        st.image("Images/logo.png", width=175)
        st.markdown("---")
        st.header("Actions")

        # Route Planner
        with st.expander("📍 Plan Your Route", expanded=True):
            start = st.text_input("Start Location", st.session_state.get("start", "Shahdara"))
            end = st.text_input("End Location", st.session_state.get("end", "Qutub Minar"))
            if st.button("Find Best Route"):
                st.session_state["start"]=start
                st.session_state["end"]=end
                route = get_routes(start, end)
                if route:
                    st.session_state["route_info"]=route
                    try:
                        coords=route["original_route"]["geometry"]["coordinates"]
                        mid=coords[len(coords)//2]; st.session_state["map_center"]=[mid[1],mid[0]]
                    except:
                        st.session_state["map_center"]=[28.6139,77.2090]
                    st.rerun()

        st.markdown("---")

        # Hazard Reporting
        with st.expander("⚠️ Report a Hazard", expanded=True):
            if not st.session_state.get("logged_in"):
                st.info("Login first to report.")
            else:
                st.info("Choose hazard then click map.")
                haz=["Construction","Accident","Pothole","Waterlogging","Traffic"]
                a,b=st.columns(2)
                for i,h in enumerate(haz):
                    if (a if i%2==0 else b).button(h):
                        st.session_state["selected_hazard"]=h
                        st.success(f"Selected {h}")

        st.markdown("---")
        st.caption("© Traffix 2025")

# -------------------------
# Map + Analysis
# -------------------------
def render_map_and_analysis():
    center = st.session_state.get("map_center",[28.61,77.20])
    google="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}"

    m=folium.Map(location=center,zoom_start=12,tiles=None)
    folium.TileLayer(tiles=google,attr="Google",control=False).add_to(m)

    # live hazards
    for h in get_live_hazards():
        try:
            folium.Marker([h["lat"],h["lon"]],
                          popup=h["report_type"],
                          icon=hazard_icon(h["report_type"])
                          ).add_to(m)
        except: pass

    # routes
    rinfo=st.session_state.get("route_info")
    if rinfo:
        orig=rinfo["original_route"]
        alt=rinfo.get("alternative_route")

        try:
            folium.GeoJson(orig["geometry"],
                           style_function=lambda f:{
                               "color":"red" if orig["risk_score"] else "green",
                               "weight":6}).add_to(m)
        except: pass

        if alt:
            try:
                folium.GeoJson(alt["geometry"],
                               style_function=lambda f:{
                                   "color":"gray" if not alt["risk_score"] else "red",
                                   "weight":5}).add_to(m)
            except: pass

    map_data = st_folium(m, width="100%", height=620, key="mainmap")

    # click to report
    if map_data and map_data.get("last_clicked") and st.session_state.get("selected_hazard"):
        if not st.session_state.get("user_id"):
            st.warning("Login required.")
        else:
            c = map_data["last_clicked"]
            ok = submit_fast_report(st.session_state["selected_hazard"],
                                    c["lat"], c["lng"], st.session_state["user_id"])
            if ok:
                clear_hazards_cache()
                st.success("Hazard reported.")
            else:
                st.error("Failed.")
        st.session_state.pop("selected_hazard",None)
        st.rerun()

    st.markdown("---")
    live=len(get_live_hazards())
    st.write(f"Live hazards: **{live}**")

    if rinfo:
        orig=rinfo["original_route"]
        alt=rinfo.get("alternative_route")
        count=extract_report_count(orig.get("reason",""))

        c1,c2=st.columns(2)
        with c1:
            st.metric("Main Route",
                      f"{orig['duration_min']} min",
                      f"Risk: {'High' if orig['risk_score'] else 'Low'}")
            st.caption(orig["reason"])
            st.write(f"Reports near route: **{count}**")

        with c2:
            if alt:
                st.metric("Alternative Route",
                          f"{alt['duration_min']} min",
                          f"Risk: {'High' if alt['risk_score'] else 'Low'}")
                st.caption(alt["reason"])
            else:
                st.info("No alternative route available.")

# -------------------------
# Pages
# -------------------------
def page_login():
    back_button()
    st.header("Login")
    with st.form("login"):
        email=st.text_input("Email")
        pw=st.text_input("Password",type="password")
        if st.form_submit_button("Login"):
            token=login_api(email,pw)
            if token:
                st.session_state["logged_in"]=True
                st.session_state["user_id"]=token
                st.session_state["user_email"]=email
                st.session_state["page"]="main"; st.rerun()
            else:
                st.error("Invalid credentials")

def page_signup():
    back_button()
    st.header("Sign Up")
    with st.form("signup"):
        email=st.text_input("Email")
        p1=st.text_input("Password",type="password")
        p2=st.text_input("Confirm Password",type="password")
        if st.form_submit_button("Create Account"):
            if p1!=p2: st.error("Mismatch")
            else:
                if signup_api(email,p1):
                    token=login_api(email,p1)
                    st.session_state["logged_in"]=True
                    st.session_state["user_id"]=token
                    st.session_state["user_email"]=email
                    st.session_state["page"]="main"; st.rerun()
                else:
                    st.error("Signup failed")

def page_about():
    back_button()
    st.header("About Traffix")
    st.write("Student project for predictive traffic and smart rerouting. ")
    st.write("Made By Chirag , Puluck , Preet and Dev .")

def page_profile():
    back_button()
    st.header("Profile")
    st.write("Email:", st.session_state.get("user_email"))

# -------------------------
# Router
# -------------------------
render_header()
render_sidebar()
p=st.session_state.get("page","main")

if p=="main": render_map_and_analysis()
elif p=="login": page_login()
elif p=="signup": page_signup()
elif p=="about": page_about()
elif p=="profile": page_profile()
