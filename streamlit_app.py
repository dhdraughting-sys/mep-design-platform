"""
MEP Design Platform - D3D.
Run with: streamlit run streamlit_app.py
"""
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

# --- INIT STATE ---
if "logo_name" not in st.session_state: st.session_state.logo_name = "D3D"
if "selectbox_version" not in st.session_state: st.session_state.selectbox_version = 0
if "qa_status" not in st.session_state:
    st.session_state.qa_status = {"status": "Draft", "qa_engineer": "", "qa_date": str(datetime.date.today())}
if "project_details" not in st.session_state:
    st.session_state.project_details = {"project_name": "", "site_address": "", "client": "", "job_reference": "", "revision": ""}
if "rooms" not in st.session_state:
    st.session_state.rooms = [
        {"name": "Office (RG-01)", "floor": "Ground", "area_m2": 46.0, "ceiling_height_m": 3.0, "occupancy": 2, "city": "Coventry", "orientation": "South", "glazing_area_m2": 0.0, "glazing_type": "Double - Clear/Clear", "sensible_w_person": 75.0, "latent_w_person": 55.0, "lighting_wm2": 12.0, "small_power_wm2": 15.0, "infiltration_ach": 0.5, "manufacturer": "Daikin", "unit_type": "Ducted", "quantity": 1, "room_type": "Office", "sizing_basis": "Stricter of Both", "fixture_counts": {}}
    ]

# --- PAGE LAYOUT ---
st.set_page_config(page_title=f"MEP Design Platform - {st.session_state.logo_name}", layout="wide")
st.markdown("""<style>
    .badge-approved { background-color: #D4EDDA; color: #155724; padding: 3px 8px; border-radius: 4px; font-weight: bold; border: 1px solid #C3E6CB; font-size: 11px; }
    .badge-review { background-color: #FFF3CD; color: #856404; padding: 3px 8px; border-radius: 4px; font-weight: bold; border: 1px solid #FFEBAA; font-size: 11px; }
    .badge-draft { background-color: #E2E3E5; color: #383D41; padding: 3px 8px; border-radius: 4px; font-weight: bold; border: 1px solid #D6D8DB; font-size: 11px; }
</style>""", unsafe_allow_html=True)

st.title(f"MEP Design Platform \u2014 {st.session_state.logo_name}")

# --- SIDEBAR ---
with st.sidebar:
    st.subheader("QA Review & Sign-Off")
    qastat = st.session_state.qa_status
    qastat["status"] = st.selectbox("Status", ["Draft", "Pending Review", "Approved"], index=["Draft", "Pending Review", "Approved"].index(qastat["status"]))
    qastat["qa_engineer"] = st.text_input("QA Engineer", value=qastat["qa_engineer"])
    qastat["qa_date"] = str(st.date_input("Date", value=datetime.date.today()))

    # --- PROJECT LOAD / DELETE ---
    db_projects = [p["project_name"] for p in supabase.table("user_projects").select("project_name").execute().data]
    selected_db_project = st.selectbox("Load Project", ["-- Select Project --"] + db_projects, key=f"sel_{st.session_state.selectbox_version}")
    
    if st.button("📂 Load Project") and selected_db_project != "-- Select Project --":
        data = supabase.table("user_projects").select("design_data").eq("project_name", selected_db_project).execute().data[0]["design_data"]
        st.session_state.rooms = data.get("rooms", [])
        st.session_state.qa_status = data.get("qa_status", st.session_state.qa_status)
        st.rerun()

# --- MAIN TAB INTERFACE ---
tab1, tab2, tab3 = st.tabs(["📋 Room Schedule", "❄️ HVAC & FCU", "🖨️ Print Summary"])

with tab1:
    st.subheader("Room Schedule")
    df = pd.DataFrame(st.session_state.rooms)
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    if st.button("Save Rooms"):
        st.session_state.rooms = edited_df.to_dict("records")
        st.rerun()

with tab2:
    st.subheader("HVAC & FCU")
    st.write("Calculations displayed here...")

with tab3:
    st.subheader("Print Summary")
    st.write("Ready for print.")