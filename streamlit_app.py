import streamlit as st
import pandas as pd
import datetime
from supabase import create_client, Client
import calc_engine
import reference_data as ref
import excel_export
import psychro_chart

# --- CONFIG & INITIALIZATION ---
ADMIN_DELETE_PIN = "0712"
@st.cache_resource
def get_supabase_client() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_ANON_KEY"])

supabase = get_supabase_client()

# --- STATE INIT ---
if "logo_name" not in st.session_state: st.session_state.logo_name = "D3D"
if "selectbox_version" not in st.session_state: st.session_state.selectbox_version = 0
if "qa_status" not in st.session_state:
    st.session_state.qa_status = {"status": "Draft", "qa_engineer": "", "qa_date": str(datetime.date.today())}
if "rooms" not in st.session_state:
    st.session_state.rooms = [dict(r) for r in ref.SEED_ROOMS]

st.set_page_config(page_title=f"MEP Design Platform - {st.session_state.logo_name}", layout="wide")

# --- SIDEBAR: QA, LOAD/DELETE, LOGO ---
with st.sidebar:
    st.subheader("📋 QA Review & Sign-Off")
    qastat = st.session_state.qa_status
    qastat["status"] = st.selectbox("Current QA Status", ["Draft", "Pending Review", "Approved"], index=["Draft", "Pending Review", "Approved"].index(qastat.get("status", "Draft")))
    qastat["qa_engineer"] = st.text_input("QA Sign-off Engineer", value=qastat.get("qa_engineer", ""))
    qastat["qa_date"] = str(st.date_input("Sign-off Date", value=datetime.date.today()))
    
    st.divider()
    
    # Safe Delete Callback
    def execute_safe_cloud_deletion(target_project):
        supabase.table("user_projects").delete().eq("project_name", target_project).execute()
        st.session_state.selectbox_version += 1
        st.rerun()

    db_projects = [p["project_name"] for p in supabase.table("user_projects").select("project_name").execute().data]
    selected_db_project = st.selectbox("Load Project", ["-- Select Project --"] + db_projects, key=f"sel_{st.session_state.selectbox_version}")
    
    if st.button("📂 Load Project") and selected_db_project != "-- Select Project --":
        data = supabase.table("user_projects").select("design_data").eq("project_name", selected_db_project).execute().data[0]["design_data"]
        st.session_state.rooms = data.get("rooms", [])
        st.session_state.qa_status = data.get("qa_status", st.session_state.qa_status)
        st.rerun()

    if st.button("🗑️ Delete Project"):
        pin = st.text_input("Enter Admin PIN:", type="password")
        if pin == ADMIN_DELETE_PIN: execute_safe_cloud_deletion(selected_db_project)

    uploaded_logo = st.file_uploader("Upload New Logo", type=["png", "jpg"])
    if uploaded_logo:
        st.session_state.logo_bytes = uploaded_logo.read()
        st.session_state.logo_refresh_token = pd.Timestamp.now().timestamp()
        st.rerun()
    if "logo_bytes" in st.session_state:
        st.image(st.session_state.logo_bytes, width=180, key=f"logo_{st.session_state.get('logo_refresh_token', 0)}")

# --- MAIN TAB INTERFACE ---
# REPLACE THE CONTENTS BELOW WITH YOUR ORIGINAL CALCULATION LOGIC
tabs = st.tabs(["📋 Room Schedule", "❄️ HVAC & FCU", "💨 Ventilation", "🚰 Water Services", "🔥 Heat Load", "🌡️ LTHW & CHW", "📈 Psychro", "🖨️ Print Summary", "📚 Data", "📥 Export"])

with tabs[0]: st.subheader("Room Schedule")
with tabs[1]: st.subheader("HVAC & FCU Selection")
with tabs[2]: st.subheader("Ventilation Design")
with tabs[3]: st.subheader("Water Services")
with tabs[4]: st.subheader("Heat Load (Winter)")
with tabs[5]: st.subheader("LTHW & CHW Pipe Sizing")
with tabs[6]: st.subheader("Psychrometric Chart")
with tabs[7]: st.subheader("Print Summary")
with tabs[8]: st.subheader("Data Sources")
with tabs[9]: st.subheader("Export")