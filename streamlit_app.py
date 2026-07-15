import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import base64
import os
import json
import datetime
from supabase import create_client, Client
import calc_engine
import reference_data as ref
import excel_export
import psychro_chart

# --- CONFIG ---
ADMIN_DELETE_PIN = "0712"
@st.cache_resource
def get_supabase_client() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_ANON_KEY"])

supabase = get_supabase_client()

# --- INIT SESSION STATE (Prevents input resetting) ---
if "rooms" not in st.session_state: st.session_state.rooms = [dict(r) for r in ref.SEED_ROOMS]
if "qa_status" not in st.session_state:
    st.session_state.qa_status = {"status": "Draft", "qa_engineer": "", "qa_date": str(datetime.date.today())}

# Initialize Project Detail Keys (This fixes the "revert back" glitch)
if "proj_name" not in st.session_state: st.session_state.proj_name = ""
if "site_addr" not in st.session_state: st.session_state.site_addr = ""
if "client" not in st.session_state: st.session_state.client = ""
if "job_ref" not in st.session_state: st.session_state.job_ref = ""
if "rev" not in st.session_state: st.session_state.rev = ""

st.set_page_config(page_title="MEP Design Platform", layout="wide")

# --- SIDEBAR ---
with st.sidebar:
    st.subheader("Project Details")
    st.text_input("Project Name", key="proj_name")
    st.text_area("Site Address", key="site_addr", height=70)
    st.text_input("Client", key="client")
    st.text_input("Job Reference", key="job_ref")
    st.text_input("Revision", key="rev")

    st.divider()
    st.subheader("📋 QA Sign-Off")
    qastat = st.session_state.qa_status
    qastat["status"] = st.selectbox("Status", ["Draft", "Pending Review", "Approved"], index=["Draft", "Pending Review", "Approved"].index(qastat["status"]))
    qastat["qa_engineer"] = st.text_input("QA Engineer", value=qastat["qa_engineer"])
    qastat["qa_date"] = str(st.date_input("Date", value=datetime.date.today()))

    # --- CLOUD LOGIC ---
    if st.button("💾 Save to Cloud"):
        payload = {
            "project_name": st.session_state.proj_name,
            "design_data": {"rooms": st.session_state.rooms, "qa_status": st.session_state.qa_status}
        }
        supabase.table("user_projects").upsert(payload).execute()
        st.success("Saved!")

    db_projects = [p["project_name"] for p in supabase.table("user_projects").select("project_name").execute().data]
    selected = st.selectbox("Load Project", ["-- Select --"] + db_projects)
    
    if st.button("📂 Load"):
        data = supabase.table("user_projects").select("design_data").eq("project_name", selected).execute().data[0]["design_data"]
        st.session_state.rooms = data["rooms"]
        st.session_state.qa_status = data["qa_status"]
        st.rerun()

    if st.button("🗑️ Delete"):
        pin = st.text_input("Enter Admin PIN:", type="password")
        if pin == ADMIN_DELETE_PIN:
            supabase.table("user_projects").delete().eq("project_name", selected).execute()
            st.rerun()

    # --- LOGO REFRESH FIX ---
    uploaded_logo = st.file_uploader("Upload Logo", type=["png", "jpg"])
    if uploaded_logo:
        st.session_state.logo_bytes = uploaded_logo.read()
        st.session_state.logo_refresh = pd.Timestamp.now().timestamp()
        st.rerun()
    if "logo_bytes" in st.session_state:
        st.image(st.session_state.logo_bytes, width=150, key=f"l_{st.session_state.get('logo_refresh', 0)}")

# --- MAIN CONTENT ---
st.title(f"MEP Design Platform \u2014 {st.session_state.proj_name}")

tabs = st.tabs(["📋 Schedule", "❄️ HVAC", "💨 Vent", "🚰 Water", "🔥 Heat", "🌡️ LTHW", "📈 Psychro", "🖨️ Print", "📚 Data", "📥 Export"])

with tabs[0]: st.subheader("Room Schedule") # Add your schedule logic here
with tabs[1]: st.subheader("HVAC & FCU")    # Add your HVAC logic here
with tabs[2]: st.subheader("Ventilation")   # Add your Vent logic here
with tabs[3]: st.subheader("Water Services")
with tabs[4]: st.subheader("Heat Load")
with tabs[5]: st.subheader("LTHW & CHW")
with tabs[6]: st.subheader("Psychrometric Chart")
with tabs[7]: st.subheader("Print Summary")
with tabs[8]: st.subheader("Data Sources")
with tabs[9]: st.subheader("Export")

# --- FOOTER ---
st.markdown("""<hr><div style="font-size: 0.8em; color: #888; text-align: center;">
    Liability Notice: This is a calculation aid only. Final designs must be approved by a Professional Engineer.
</div>""", unsafe_allow_html=True)