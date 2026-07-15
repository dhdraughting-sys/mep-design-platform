
"""
MEP Design Platform - D3D.

Run with:
    streamlit run streamlit_app.py
"""
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import base64
import os
import json
import datetime

# Connection to your Supabase database and storage
from supabase import create_client, Client

import calc_engine
import reference_data as ref
import excel_export
import psychro_chart

# =====================================================================
# SECURITY & ADMIN CONFIGURATION
# =====================================================================
ADMIN_DELETE_PIN = "0712"

# =====================================================================
# SECURE CONNECTION TO SUPABASE
# =====================================================================
@st.cache_resource
def get_supabase_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]
    return create_client(url, key)

try:
    supabase = get_supabase_client()
except Exception as e:
    st.sidebar.error("Could not link to Supabase. Check Streamlit Secrets.")

# =====================================================================
# PAGE CONFIGURATION & INITIALIZATION
# =====================================================================
if "logo_name" not in st.session_state: st.session_state.logo_name = "D3D"
if "selectbox_version" not in st.session_state: st.session_state.selectbox_version = 0
if "qa_status" not in st.session_state:
    st.session_state.qa_status = {"status": "Draft", "qa_engineer": "", "qa_date": str(datetime.date.today())}
if "project_details" not in st.session_state:
    st.session_state.project_details = {"project_name": "", "site_address": "", "client": "", "job_reference": "", "revision": ""}
if "engineer_name" not in st.session_state: st.session_state.engineer_name = ""

st.set_page_config(page_title=f"MEP Design Platform - {st.session_state.logo_name}", layout="wide")

# CSS Styling
st.markdown("""
<style>
    .badge-approved { background-color: #D4EDDA; color: #155724; padding: 3px 8px; border-radius: 4px; font-weight: bold; border: 1px solid #C3E6CB; font-size: 11px; }
    .badge-review { background-color: #FFF3CD; color: #856404; padding: 3px 8px; border-radius: 4px; font-weight: bold; border: 1px solid #FFEBAA; font-size: 11px; }
    .badge-draft { background-color: #E2E3E5; color: #383D41; padding: 3px 8px; border-radius: 4px; font-weight: bold; border: 1px solid #D6D8DB; font-size: 11px; }
    @media print { header, #MainMenu, footer, section[data-testid="stSidebar"] { display: none !important; } }
</style>
""", unsafe_allow_html=True)

st.title(f"MEP Design Platform \u2014 {st.session_state.logo_name}")

# =====================================================================
# SIDEBAR
# =====================================================================
with st.sidebar:
    st.subheader("User Identity")
    st.text_input("Your Name / Email", key="engineer_name")

    st.subheader("📋 QA Review & Sign-Off")
    qastat = st.session_state.qa_status
    status_opts = ["Draft", "Pending Review", "Approved"]
    qastat["status"] = st.selectbox("Current QA Status", status_opts, index=status_opts.index(qastat.get("status", "Draft")))
    qastat["qa_engineer"] = st.text_input("QA Sign-off Engineer", value=qastat.get("qa_engineer", ""))
    qastat["qa_date"] = str(st.date_input("Sign-off Date", value=datetime.date.today()))

    # --- CLOUD DELETION CALLBACK ---
    def execute_safe_cloud_deletion(target_project):
        try:
            supabase.table("user_projects").delete().eq("project_name", target_project).execute()
            st.session_state.selectbox_version += 1 # Forces widget re-instantiation
            st.session_state.show_delete_confirm = False
            st.session_state["delete_success_msg"] = f"Successfully deleted '{target_project}'!"
        except Exception as e:
            st.session_state["delete_error_msg"] = f"Failed to delete: {e}"

    # --- LOAD / DELETE DROPDOWN ---
    db_query = supabase.table("user_projects").select("project_name").execute()
    db_projects = [p["project_name"] for p in db_query.data] if db_query.data else []
    
    dynamic_selector_key = f"db_project_selector_v{st.session_state.selectbox_version}"
    selected_db_project = st.selectbox("Load Project", ["-- Select Project --"] + db_projects, key=dynamic_selector_key)

    if selected_db_project != "-- Select Project --":
        if st.button("📂 Load Project"):
            data = supabase.table("user_projects").select("design_data").eq("project_name", selected_db_project).execute().data[0]["design_data"]
            st.session_state.rooms = data.get("rooms", [])
            st.session_state.qa_status = data.get("qa_status", st.session_state.qa_status)
            st.rerun()
        if st.button("🗑️ Delete Project"): st.session_state.show_delete_confirm = True
        if st.session_state.get("show_delete_confirm"):
            pin = st.text_input("Enter Admin PIN:", type="password")
            if st.button("Confirm Delete", on_click=execute_safe_cloud_deletion, args=(selected_db_project,), disabled=(pin != ADMIN_DELETE_PIN)): pass

    # --- LOGO SECTION ---
    uploaded_logo = st.file_uploader("Upload New Logo", type=["png", "jpg"])
    if uploaded_logo:
        st.session_state.logo_bytes = uploaded_logo.read()
        st.session_state.logo_refresh_token = pd.Timestamp.now().timestamp()
        st.rerun()
    if st.session_state.get("logo_bytes"):
        st.image(st.session_state.logo_bytes, width=180, key=f"logo_img_{st.session_state.get('logo_refresh_token', 0)}")

# =====================================================================
# QA BANNER
# =====================================================================
curr_s = st.session_state.qa_status["status"]
if curr_s == "Approved": status_html = f'<div class="badge-approved">🟢 Approved by {st.session_state.qa_status["qa_engineer"]}</div>'
elif curr_s == "Pending Review": status_html = f'<div class="badge-review">🟡 Pending Review</div>'
else: status_html = '<div class="badge-draft">🔴 Draft</div>'
st.markdown(f"<div style='text-align: right;'>{status_html}</div>", unsafe_allow_html=True)

# ... [Insert the remainder of your Tabbed content here as previously provided] ...