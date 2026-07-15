"""
MEP Design Platform - D3D.

Run with:
    streamlit run streamlit_app.py
(or just double-click run.bat on Windows)
"""
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import base64
import os
import json

from supabase import create_client, Client

import calc_engine
import reference_data as ref
import excel_export
import psychro_chart

# =====================================================================
# SECURITY & ADMIN CONFIGURATION
# =====================================================================
# FIXED: was a hardcoded PIN in source code ("0712") - that gets pushed to
# GitHub in plain text and stays in the repo history forever, readable by
# anyone with repo access. Reading from st.secrets instead, same as the
# Supabase keys - never committed to the code. Add ADMIN_DELETE_PIN to
# your secrets.toml / Streamlit Cloud secrets the same way as the
# Supabase keys. A 4-digit PIN is still weak on its own (10,000 possible
# values, nothing stops repeated guessing) - fine for "stop an accidental
# click," not a real access-control boundary if that matters more later.
ADMIN_DELETE_PIN = st.secrets.get("ADMIN_DELETE_PIN", None)

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
# LOGO & DYNAMIC TITLE LOGIC (D3D OR CLIENT DETECTED)
# =====================================================================
default_logo_path = os.path.join(os.path.dirname(__file__), "assets", "company_logo.jpg")

if "logo_name" not in st.session_state:
    st.session_state.logo_name = "D3D"

display_title = f"MEP Design Platform - {st.session_state.logo_name}"
st.set_page_config(page_title=display_title, layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    h1 { color: #1B365D; font-size: 1.6rem; }
    .stButton>button, .stDownloadButton>button {
        background-color: #1B365D; color: white; border: none;
    }
    .stButton>button:hover, .stDownloadButton>button:hover {
        background-color: #274a7a; color: white;
    }
    .stTabs [data-baseweb="tab"] { font-weight: 600; }

    @media print {
        header[data-testid="stHeader"], #MainMenu, footer,
        .stTabs [data-baseweb="tab-list"], .stButton, .stDownloadButton,
        section[data-testid="stSidebar"] {
            display: none !important;
        }
    }
</style>
""", unsafe_allow_html=True)

st.title(f"MEP Design Platform \u2014 {st.session_state.logo_name}")
st.caption(
    "\u26a0\ufe0f Calculation aid only \u2014 all outputs must be reviewed and approved by a qualified "
    "Professional Engineer before use. Full liability notice in Reports \u2192 Data Sources."
)

# ---- Project Details (sidebar - persistent across every tab) ----
if "project_details" not in st.session_state:
    st.session_state.project_details = {
        "project_name": "", "site_address": "", "client": "",
        "job_reference": "", "revision": "",
    }

if "engineer_name" not in st.session_state:
    st.session_state.engineer_name = ""

# Forces the cloud-projects selectbox to become a genuinely NEW widget
# after any save/delete, instead of relying on Streamlit's rerun to
# refresh its options list cleanly in the browser - see the fuller note
# where this is used, further down.
if "db_selector_version" not in st.session_state:
    st.session_state.db_selector_version = 0

# Tracks when st.session_state.rooms changes from an EXTERNAL source
# (seeding, or loading a cloud project) as opposed to normal in-app
# editing - see the fuller note in the Room Schedule tab where this is
# used, further down.
if "rooms_external_version" not in st.session_state:
    st.session_state.rooms_external_version = 0

# Bumped every time data is loaded from an EXTERNAL source (a cloud
# project load) - every widget key that displays room or project-detail
# data includes this number, so a fresh load forces genuinely NEW widget
# keys instead of leaving old ones showing stale values. This is what
# was actually behind room names / project details / drawing register
# not following through after loading a project - the underlying DATA
# was updating correctly, but the WIDGETS showing it were still holding
# onto whatever they'd displayed before, since Streamlit prioritises a
# widget's own stored value over a freshly-passed one once that widget's
# key has been used once.
if "data_gen" not in st.session_state:
    st.session_state.data_gen = 0
gen = st.session_state.data_gen

# ---- Seed data ----
SEED_ROOMS = [
    {"name": "Reception (RG-01)", "floor": "Ground", "area_m2": 46.0, "ceiling_height_m": 3.0,
     "summer_design_temp_c": None, "winter_design_temp_c": None, "occupancy": 2,
     "city": "Coventry", "orientation": "South", "glazing_area_m2": 0.0,
     "glazing_type": "Double - Clear/Clear", "sensible_w_person": 75.0, "latent_w_person": 55.0,
     "lighting_wm2": 12.0, "small_power_wm2": 15.0, "infiltration_ach": 0.5,
     "manufacturer": "Daikin", "unit_type": "Ducted", "quantity": 1,
     "room_type": "Reception", "sizing_basis": "Stricter of Both", "fixture_counts": {}},
    {"name": "Office (RF-01)", "floor": "First", "area_m2": 37.0, "ceiling_height_m": 2.7,
     "summer_design_temp_c": None, "winter_design_temp_c": None, "occupancy": 4,
     "city": "Coventry", "orientation": "South", "glazing_area_m2": 0.0,
     "glazing_type": "Double - Clear/Clear", "sensible_w_person": 75.0, "latent_w_person": 55.0,
     "lighting_wm2": 12.0, "small_power_wm2": 15.0, "infiltration_ach": 0.5,
     "manufacturer": "Daikin", "unit_type": "Ducted", "quantity": 1,
     "room_type": "Office", "sizing_basis": "Stricter of Both", "fixture_counts": {}},
    {"name": "First Floor Office (RF-11)", "floor": "First", "area_m2": 573.0, "ceiling_height_m": 2.7,
     "summer_design_temp_c": None, "winter_design_temp_c": None, "occupancy": 57,
     "city": "Coventry", "orientation": "South", "glazing_area_m2": 0.0,
     "glazing_type": "Double - Clear/Clear", "sensible_w_person": 75.0, "latent_w_person": 55.0,
     "lighting_wm2": 12.0, "small_power_wm2": 15.0, "infiltration_ach": 0.5,
     "manufacturer": "Daikin", "unit_type": "Ducted", "quantity": 3,
     "room_type": "Office", "sizing_basis": "Stricter of Both", "fixture_counts": {}},
    {"name": "Office (RS-01)", "floor": "Second", "area_m2": 36.0, "ceiling_height_m": 2.7,
     "summer_design_temp_c": None, "winter_design_temp_c": None, "occupancy": 4,
     "city": "Coventry", "orientation": "South", "glazing_area_m2": 0.0,
     "glazing_type": "Double - Clear/Clear", "sensible_w_person": 75.0, "latent_w_person": 55.0,
     "lighting_wm2": 12.0, "small_power_wm2": 15.0, "infiltration_ach": 0.5,
     "manufacturer": "Daikin", "unit_type": "Ducted", "quantity": 1,
     "room_type": "Office", "sizing_basis": "Stricter of Both", "fixture_counts": {}},
    {"name": "Second Floor Office (RS-11)", "floor": "Second", "area_m2": 572.0, "ceiling_height_m": 2.7,
     "summer_design_temp_c": None, "winter_design_temp_c": None, "occupancy": 57,
     "city": "Coventry", "orientation": "South", "glazing_area_m2": 0.0,
     "glazing_type": "Double - Clear/Clear", "sensible_w_person": 75.0, "latent_w_person": 55.0,
     "lighting_wm2": 12.0, "small_power_wm2": 15.0, "infiltration_ach": 0.5,
     "manufacturer": "Daikin", "unit_type": "Ducted", "quantity": 3,
     "room_type": "Office", "sizing_basis": "Stricter of Both", "fixture_counts": {}},
]

# Starts blank by default - SEED_ROOMS above is kept as example/reference
# data (and as a quick way to restore it below) rather than auto-loaded,
# since a new session showing someone else's example project data was
# confusing to start from. Add rooms manually, or load a saved project
# from Cloud Projects in the sidebar.
if "rooms" not in st.session_state:
    st.session_state.rooms = []

# =====================================================================
# SIDEBAR - Project Details, Cloud Database Save/Load, & Drawing Toggle
# =====================================================================
with st.sidebar:
    st.subheader("User Identity")
    st.text_input("Your Name / Email", key="engineer_name", placeholder="e.g. John Thomas")

    st.subheader("Project Details")
    st.caption("Feeds the title block on the Print Summary tab.")
    pd_ = st.session_state.project_details
    pd_["project_name"] = st.text_input("Project Name", value=pd_["project_name"], key=f"project_name_input_{gen}")
    pd_["site_address"] = st.text_area("Site Address", value=pd_["site_address"], height=70, key=f"site_address_input_{gen}")
    pd_["client"] = st.text_input("Client", value=pd_["client"], key=f"client_input_{gen}")
    pd_["job_reference"] = st.text_input("Job Reference", value=pd_["job_reference"], key=f"job_reference_input_{gen}")
    pd_["revision"] = st.text_input("Revision", value=pd_["revision"], key=f"revision_input_{gen}")

    st.divider()

    st.divider()
    st.subheader("\U0001F195 Reset")
    st.caption(
        "Clears the current session back to a blank canvas - rooms, project details, fixture values, "
        "and logo all reset. Anything not already saved to Cloud Projects will be lost."
    )
    if st.checkbox("I understand this clears unsaved work", key="reset_confirm_checkbox"):
        if st.button("\U0001F195 Reset to Blank Canvas", key="reset_blank_canvas_button"):
            st.session_state.rooms = []
            st.session_state.project_details = {
                "project_name": "", "site_address": "", "client": "",
                "job_reference": "", "revision": "",
            }
            st.session_state.fixture_lu_values = dict(ref.FIXTURE_LU)
            st.session_state.logo_name = "D3D"
            st.session_state.pop("logo_bytes", None)
            st.session_state.pop("logo_mime", None)
            # Same mechanism used everywhere else in the app to force
            # every widget to show fresh (blank) values instead of
            # whatever was left over from before - see the note by
            # data_gen's definition for the fuller explanation.
            st.session_state.rooms_external_version += 1
            st.session_state.data_gen += 1
            st.success("Reset to a blank canvas.")
            st.rerun()

    st.divider()
    st.subheader("\u2601\ufe0f Cloud Database Save / Load")
    st.caption(
        "Save your active MEP calculations directly to our central cloud database "
        "so colleagues can access, review, or QA them instantly."
    )

    if st.button("\U0001F4BE Save Project to Cloud", key="save_project_cloud_button"):
        if not st.session_state.engineer_name.strip():
            st.warning("\u26a0\ufe0f Please enter your Name/Email above before saving.")
        elif not pd_["project_name"].strip():
            st.warning("\u26a0\ufe0f Please enter a Project Name under Project Details before saving.")
        else:
            try:
                payload = {
                    "project_name": pd_["project_name"].strip(),
                    "user_email": st.session_state.engineer_name.strip(),
                    "design_data": {
                        "rooms": st.session_state.rooms,
                        "project_details": st.session_state.project_details,
                        "fixture_lu_values": st.session_state.get("fixture_lu_values", {}),
                        "logo_name": st.session_state.logo_name,
                    }
                }

                existing_check = supabase.table("user_projects")\
                    .select("id")\
                    .eq("project_name", pd_["project_name"].strip())\
                    .execute()

                if existing_check.data:
                    supabase.table("user_projects")\
                        .update({"design_data": payload["design_data"], "user_email": payload["user_email"]})\
                        .eq("project_name", pd_["project_name"].strip())\
                        .execute()
                    st.success(f"\U0001F504 Updated '{pd_['project_name']}' in the database!")
                else:
                    supabase.table("user_projects").insert(payload).execute()
                    st.session_state.db_selector_version += 1
                    st.success(f"\U0001F389 Saved '{pd_['project_name']}' to the database!")

                st.rerun()
            except Exception as e:
                st.error(f"Could not save to database: {e}")

    st.write("---")

    try:
        db_query = supabase.table("user_projects").select("project_name").execute()
        db_projects = [p["project_name"] for p in db_query.data] if db_query.data else []

        if db_projects:
            selected_db_project = st.selectbox(
                "Load Project from Cloud",
                ["-- Select Project --"] + db_projects,
                key=f"db_project_selector_v{st.session_state.db_selector_version}"
            )

            if selected_db_project != "-- Select Project --":
                bcol1, bcol2 = st.columns(2)
                with bcol1:
                    if st.button("\U0001F4C2 Load Project", key="load_project_button"):
                        project_data_query = supabase.table("user_projects")\
                            .select("design_data")\
                            .eq("project_name", selected_db_project)\
                            .execute()

                        if project_data_query.data:
                            loaded_data = project_data_query.data[0]["design_data"]
                            st.session_state.rooms = loaded_data.get("rooms", [])
                            st.session_state.project_details = loaded_data.get("project_details", {})
                            st.session_state.fixture_lu_values = loaded_data.get("fixture_lu_values", {})
                            st.session_state.logo_name = loaded_data.get("logo_name", "D3D")
                            st.session_state.rooms_external_version += 1
                            st.session_state.data_gen += 1
                            st.success(f"Loaded '{selected_db_project}' successfully!")
                            st.rerun()

                with bcol2:
                    if st.button("\U0001F5D1\ufe0f Delete Project", key="delete_project_button"):
                        st.session_state.show_delete_confirm = True

                if st.session_state.get("show_delete_confirm"):
                    st.warning(f"Confirm deletion of '{selected_db_project}'")
                    pin_input = st.text_input("Enter Admin Delete PIN:", type="password", key="admin_pin_input")

                    confirm_col, cancel_col = st.columns(2)
                    with confirm_col:
                        if st.button("Confirm Delete", key="confirm_delete_button"):
                            if ADMIN_DELETE_PIN is None:
                                st.error(
                                    "ADMIN_DELETE_PIN isn't set in your Streamlit secrets - add it there "
                                    "before deleting is possible (see the note in the code)."
                                )
                            elif pin_input == ADMIN_DELETE_PIN:
                                try:
                                    supabase.table("user_projects")\
                                        .delete()\
                                        .eq("project_name", selected_db_project)\
                                        .execute()
                                    st.session_state.db_selector_version += 1
                                    st.session_state.show_delete_confirm = False
                                    st.success(f"Successfully deleted '{selected_db_project}'!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed to delete: {e}")
                            else:
                                st.error("\u274c Invalid PIN. Action Blocked.")
                    with cancel_col:
                        if st.button("Cancel", key="cancel_delete_button"):
                            st.session_state.show_delete_confirm = False
                            st.rerun()
        else:
            st.info("No projects found in cloud database.")
    except Exception as e:
        st.caption("Ready to list cloud database projects.")

    st.divider()
    st.subheader("Logo")
    uploaded_logo = st.file_uploader(
        "Upload a different logo (optional)", type=["png", "jpg", "jpeg"], key="logo_uploader"
    )

    # FIXED: Streamlit keeps returning the same uploaded file on every
    # rerun, not just the moment you upload it - not just after page
    # loads, but after ANY interaction anywhere in the app (clicking an
    # unrelated button, editing an unrelated field). Without this guard,
    # "if uploaded_logo is not None:" ran again on every single rerun,
    # repeatedly calling .rerun() itself - which is very likely what
    # caused "the name changes but the logo doesn't": the name gets
    # reset from the (already-consumed) file's filename each time, but
    # the actual image bytes weren't being read cleanly a second time.
    # Tracking file_id (a stable per-upload identifier) means this block
    # now only runs ONCE per actual new upload, exactly like the
    # Save/Load Project file uploader elsewhere in this app already does.
    if uploaded_logo is not None and st.session_state.get("_last_logo_file_id") != uploaded_logo.file_id:
        st.session_state.logo_bytes = uploaded_logo.read()
        st.session_state.logo_mime = uploaded_logo.type
        raw_name = os.path.splitext(uploaded_logo.name)[0]
        st.session_state.logo_name = raw_name.replace("_", " ").replace("-", " ").title()
        st.session_state["_last_logo_file_id"] = uploaded_logo.file_id
        st.rerun()

    elif "logo_bytes" not in st.session_state and os.path.exists(default_logo_path):
        with open(default_logo_path, "rb") as f:
            st.session_state.logo_bytes = f.read()
        st.session_state.logo_mime = "image/jpeg"
        st.session_state.logo_name = "D3D"

    if st.session_state.get("logo_bytes"):
        st.image(st.session_state.logo_bytes, width=180)


def sync_group_edits(edited_df: pd.DataFrame, field_names: list):
    edited_by_name = {row["name"]: row for row in edited_df.to_dict("records")}
    for room in st.session_state.rooms:
        if room["name"] in edited_by_name:
            for field in field_names:
                room[field] = edited_by_name[room["name"]][field]


def sync_schedule_edits(edited_df: pd.DataFrame):
    schedule_fields = ["floor", "area_m2", "ceiling_height_m", "summer_design_temp_c",
                        "winter_design_temp_c", "include_in_summary"]
    existing_by_name = {r["name"]: r for r in st.session_state.rooms}
    new_rooms = []
    for row in edited_df.to_dict("records"):
        name = row.get("name")
        if not name:
            continue
        if name in existing_by_name:
            room = existing_by_name[name]
            for f in schedule_fields:
                room[f] = row[f]
        else:
            room = {
                "name": name, **{f: row.get(f) for f in schedule_fields},
                "occupancy": 0, "city": "Coventry", "orientation": "South",
                "glazing_area_m2": 0.0, "glazing_type": "Double - Clear/Clear",
                "sensible_w_person": 75.0, "latent_w_person": 55.0,
                "lighting_wm2": 12.0, "small_power_wm2": 15.0, "infiltration_ach": 0.5,
                "manufacturer": "Daikin", "unit_type": "Ducted", "quantity": 1,
                "room_type": "Office", "sizing_basis": "Stricter of Both", "fixture_counts": {},
            }
        new_rooms.append(room)
    st.session_state.rooms = new_rooms


def compute_all():
    results = []
    fresh_air_rate = st.session_state.get("fresh_air_rate_ls_person", ref.DEFAULT_FRESH_AIR_RATE_LS_PERSON)
    for room in st.session_state.rooms:
        gains = calc_engine.calculate_heat_gains(room)
        vent = calc_engine.calculate_ventilation(room, gains.volume_m3, fresh_air_rate)
        fcu = calc_engine.select_fcu(
            gains.total_cooling_load_kw, room.get("manufacturer", "Daikin"),
            room.get("unit_type", "Ducted"), room.get("quantity", 1),
            ref.FCU_CATALOGUE,
        )
        results.append((room, gains, vent, fcu))
    return results


def cached_data_editor(cache_key, build_df_fn, version, **editor_kwargs):
    """Feeds st.data_editor a dataframe that's cached in session_state and
    only rebuilt from scratch when `version` changes (e.g. rooms loaded
    from the cloud) - NOT on every single rerun, which is what every
    table in this app was doing before this fix. Rebuilding a fresh
    DataFrame object on every rerun - even with a stable `key=` and even
    with matching content - was the actual, general cause of edits
    reverting immediately after being typed, on every table across the
    whole app (Room Schedule, HVAC, Water Services - all of them):
    Streamlit's data_editor can lose track of an in-progress edit when
    handed a brand new DataFrame object each render, rather than
    recognising "this is the same data as before, just apply the
    pending edit on top." Used by every editable table in this app now,
    not just the one that was originally reported."""
    version_key = f"{cache_key}_version"
    needs_rebuild = cache_key not in st.session_state or st.session_state.get(version_key) != version
    if needs_rebuild:
        st.session_state[cache_key] = build_df_fn()
        st.session_state[version_key] = version
    edited = st.data_editor(st.session_state[cache_key], **editor_kwargs)
    st.session_state[cache_key] = edited
    return edited


tab_home, tab_schedule, tab_calculators, tab_reports, tab_documents = st.tabs(
    ["\U0001F3E0 Home", "\U0001F4CB Room Schedule", "\U0001F9EE Calculators", "\U0001F5A8\ufe0f Reports", "\U0001F4C2 Document Control"]
)


with tab_home:
    st.title("MEP Design Platform \u2014 Home")
    st.caption("A quick look at what's changed recently, and where the current project stands.")

    st.subheader("\U0001F4CB Welcome")
    st.markdown("""
Welcome to the MEP Design Platform. Use **Room Schedule** to add rooms, then **Calculators** for
HVAC/Ventilation/Water/Heat Load/Pipe sizing, **Reports** to print or export, and **Document Control**
to attach project drawings. Save your work anytime via Cloud Projects in the sidebar.
    """)

    st.subheader("\U0001F4CA Current Project at a Glance")
    all_results_home = compute_all()
    total_sensible = sum(g.total_sensible_kw for _, g, _, _ in all_results_home)
    total_cooling = sum(g.total_cooling_load_kw for _, g, _, _ in all_results_home)
    total_heatloss_home = sum(
        calc_engine.calculate_winter_heat_loss(r, calc_engine.calculate_heat_gains(r).volume_m3).total_heat_loss_kw
        for r in st.session_state.rooms
    )
    total_lu_home = sum(
        calc_engine.calculate_room_loading_units(r, st.session_state.get("fixture_lu_values")).loading_units
        for r in st.session_state.rooms
    )

    hcol1, hcol2, hcol3, hcol4 = st.columns(4)
    hcol1.metric("Rooms", len(st.session_state.rooms))
    hcol2.metric("Total Cooling Load", f"{total_cooling:.1f} kW")
    hcol3.metric("Total Winter Heat Loss", f"{total_heatloss_home:.1f} kW")
    hcol4.metric("Total Loading Units", f"{total_lu_home:.1f} LU")

# =====================================================================
# TAB: Room Schedule
# =====================================================================
with tab_schedule:
    st.caption("The master room list \u2014 add or remove rooms here. They then become available "
               "on the HVAC and Ventilation tabs automatically.")

    TEMP_DEFAULT_LABEL = "Default (24\u00b0C)"
    TEMP_DROPDOWN_OPTIONS = [TEMP_DEFAULT_LABEL] + list(range(-20, 51))

    def _temp_to_display(value):
        return TEMP_DEFAULT_LABEL if value is None else value

    def _display_to_temp(value):
        if value == TEMP_DEFAULT_LABEL or value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    # Each room gets a permanent, stable ID (assigned once, never reused)
    # for widget keys - using list POSITION instead would mean that after
    # deleting a room, the next room shifts into that position and
    # inherits the deleted room's leftover widget values, since Streamlit
    # widgets keep whatever's in session_state for a key rather than
    # re-reading value= once that key has been used once.
    if "_next_room_uid" not in st.session_state:
        st.session_state._next_room_uid = 0
    for room in st.session_state.rooms:
        if "_uid" not in room:
            room["_uid"] = st.session_state._next_room_uid
            st.session_state._next_room_uid += 1

    for room in st.session_state.rooms:
        i = room["_uid"]
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 1, 1])
            room["name"] = c1.text_input("Room Name", value=room.get("name", ""), key=f"room_name_{i}_{gen}")
            room["floor"] = c2.text_input("Floor", value=room.get("floor", ""), key=f"room_floor_{i}_{gen}")
            room["include_in_summary"] = c3.checkbox(
                "Include in Print Summary", value=room.get("include_in_summary", True), key=f"room_include_{i}_{gen}"
            )

            c4, c5, c6, c7 = st.columns(4)
            room["area_m2"] = c4.number_input(
                "Area (m\u00b2)", min_value=0.0, value=float(room.get("area_m2", 0.0)),
                step=0.5, format="%.1f", key=f"room_area_{i}_{gen}"
            )
            room["ceiling_height_m"] = c5.number_input(
                "Ceiling Height (m)", min_value=0.0, value=float(room.get("ceiling_height_m", 2.7)),
                step=0.1, format="%.2f", key=f"room_ceiling_{i}_{gen}"
            )
            summer_display = c6.selectbox(
                "Summer Temp (\u00b0C)", TEMP_DROPDOWN_OPTIONS,
                index=TEMP_DROPDOWN_OPTIONS.index(_temp_to_display(room.get("summer_design_temp_c"))),
                key=f"room_summer_temp_{i}_{gen}",
                help="Used by HVAC & FCU Selection (cooling).",
            )
            room["summer_design_temp_c"] = _display_to_temp(summer_display)
            winter_display = c7.selectbox(
                "Winter Temp (\u00b0C)", TEMP_DROPDOWN_OPTIONS,
                index=TEMP_DROPDOWN_OPTIONS.index(_temp_to_display(room.get("winter_design_temp_c"))),
                key=f"room_winter_temp_{i}_{gen}",
                help="Used by Heat Load - Winter (heating). Independent of Summer Temp.",
            )
            room["winter_design_temp_c"] = _display_to_temp(winter_display)

            volume = float(room.get("area_m2", 0.0)) * float(room.get("ceiling_height_m", 2.7))
            st.caption(f"Volume: {volume:.1f} m\u00b3 (read-only, computed from Area \u00d7 Ceiling Height)")

            if st.button("\U0001F5D1\ufe0f Remove This Room", key=f"remove_room_{i}_{gen}"):
                st.session_state.rooms = [r for r in st.session_state.rooms if r["_uid"] != i]
                st.rerun()

    st.divider()
    if st.button("\u2795 Add New Room", key="add_new_room_button"):
        st.session_state.rooms.append({
            "name": f"New Room {len(st.session_state.rooms) + 1}", "floor": "", "area_m2": 0.0,
            "ceiling_height_m": 2.7, "summer_design_temp_c": None, "winter_design_temp_c": None,
            "occupancy": 0, "city": "Coventry", "orientation": "South",
            "glazing_area_m2": 0.0, "glazing_type": "Double - Clear/Clear",
            "sensible_w_person": 75.0, "latent_w_person": 55.0,
            "lighting_wm2": 12.0, "small_power_wm2": 15.0, "infiltration_ach": 0.5,
            "manufacturer": "Daikin", "unit_type": "Ducted", "quantity": 1,
            "room_type": "Office", "sizing_basis": "Stricter of Both", "fixture_counts": {},
            "include_in_summary": True,
        })
        st.rerun()


# =====================================================================
# TAB: Calculators - HVAC, Ventilation, Water Services, Heat Load, LTHW/CHW,
# Psychrometric Chart, all grouped as sub-tabs under one parent tab.
# =====================================================================
with tab_calculators:
    sub_hvac, sub_vent, sub_water, sub_heatload, sub_pipes, sub_psychro = st.tabs(
        ["\u2744\ufe0f HVAC & FCU Selection", "\U0001F4A8 Ventilation", "\U0001F6B0 Water Services",
         "\U0001F525 Heat Load (Winter)", "\U0001F321\ufe0f LTHW & CHW", "\U0001F4C8 Psychrometric Chart"]
    )

    with sub_hvac:
        st.caption("Grouped the same way the Excel workbook's HVAC tab is \u2014 each table below is "
                   "narrow on purpose, no horizontal scrolling needed.")

        with st.expander("Envelope & Solar", expanded=True):
            for room in st.session_state.rooms:
                i = room["_uid"]
                ec1, ec2, ec3, ec4, ec5 = st.columns([2, 1, 1, 1, 1])
                ec1.text_input("Room Name", value=room["name"], key=f"env_name_{i}_{gen}", disabled=True)
                room["city"] = ec2.selectbox(
                    "City", list(ref.CITIES.keys()),
                    index=list(ref.CITIES.keys()).index(room.get("city")) if room.get("city") in ref.CITIES else 0,
                    key=f"env_city_{i}_{gen}",
                )
                room["orientation"] = ec3.selectbox(
                    "Orientation", ref.ORIENTATIONS,
                    index=ref.ORIENTATIONS.index(room.get("orientation")) if room.get("orientation") in ref.ORIENTATIONS else 0,
                    key=f"env_orient_{i}_{gen}",
                )
                room["glazing_area_m2"] = ec4.number_input(
                    "Glazing (m\u00b2)", min_value=0.0, max_value=100000.0,
                    value=float(room.get("glazing_area_m2") or 0.0), step=0.5, format="%.1f", key=f"env_glazing_area_{i}_{gen}",
                )
                glazing_options = list(ref.GLAZING_TYPES.keys())
                room["glazing_type"] = ec5.selectbox(
                    "Glazing Type", glazing_options,
                    index=glazing_options.index(room.get("glazing_type")) if room.get("glazing_type") in glazing_options else 0,
                    key=f"env_glazing_type_{i}_{gen}",
                )

        with st.expander("Occupancy & Internal Gains", expanded=True):
            for room in st.session_state.rooms:
                i = room["_uid"]
                st.markdown(f"**{room['name']}**")
                gc1, gc2, gc3 = st.columns(3)
                room["occupancy"] = gc1.number_input(
                    "Occupancy", min_value=0, max_value=10000, value=int(room.get("occupancy") or 0),
                    step=1, key=f"gains_occ_{i}_{gen}",
                )
                room["sensible_w_person"] = gc2.number_input(
                    "Sensible/Person (W)", value=float(room.get("sensible_w_person") or 75.0),
                    format="%.0f", key=f"gains_sens_{i}_{gen}",
                )
                room["latent_w_person"] = gc3.number_input(
                    "Latent/Person (W)", value=float(room.get("latent_w_person") or 55.0),
                    format="%.0f", key=f"gains_lat_{i}_{gen}",
                )

                gc4, gc5, gc6 = st.columns(3)
                room["lighting_wm2"] = gc4.number_input(
                    "Lighting (W/m\u00b2)", value=float(room.get("lighting_wm2") or 12.0),
                    format="%.0f", key=f"gains_light_{i}_{gen}",
                )
                room["small_power_wm2"] = gc5.number_input(
                    "Small Power (W/m\u00b2)", value=float(room.get("small_power_wm2") or 15.0),
                    format="%.0f", key=f"gains_power_{i}_{gen}",
                )
                ach_options = [0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, "Custom"]
                current_ach = room.get("infiltration_ach") or 0.5
                ach_index = ach_options.index(current_ach) if current_ach in ach_options else len(ach_options) - 1
                ach_choice = gc6.selectbox(
                    "Infiltration (ACH)", ach_options, index=ach_index, key=f"gains_ach_{i}_{gen}",
                )
                if ach_choice == "Custom":
                    room["infiltration_ach"] = gc6.number_input(
                        "Custom ACH", min_value=0.0, max_value=50.0,
                        value=float(current_ach) if current_ach not in ach_options else 0.5,
                        step=0.05, format="%.2f", key=f"gains_ach_custom_{i}_{gen}",
                    )
                else:
                    room["infiltration_ach"] = ach_choice
                st.divider()

        with st.expander("FCU / Indoor Unit Selection", expanded=True):
            for room in st.session_state.rooms:
                i = room["_uid"]
                fc1, fc2, fc3, fc4 = st.columns([2, 1, 1, 1])
                fc1.text_input("Room Name", value=room["name"], key=f"fcu_name_{i}_{gen}", disabled=True)
                room["manufacturer"] = fc2.selectbox(
                    "Manufacturer", ref.MANUFACTURERS,
                    index=ref.MANUFACTURERS.index(room.get("manufacturer")) if room.get("manufacturer") in ref.MANUFACTURERS else 0,
                    key=f"fcu_mfr_{i}_{gen}",
                )
                room["unit_type"] = fc3.selectbox(
                    "Unit Type", ref.UNIT_TYPES,
                    index=ref.UNIT_TYPES.index(room.get("unit_type")) if room.get("unit_type") in ref.UNIT_TYPES else 0,
                    key=f"fcu_type_{i}_{gen}",
                )
                room["quantity"] = fc4.number_input(
                    "Qty (0 = not yet decided, shows as TBC)", min_value=0,
                    value=int(room.get("quantity")) if room.get("quantity") is not None else 1,
                    step=1, key=f"fcu_qty_{i}_{gen}",
                )

        st.subheader("Results")
        all_results = compute_all()
        results_df = pd.DataFrame([
            {
                "Room Name": room["name"],
                "Volume (m\u00b3)": gains.volume_m3,
                "Sensible (kW)": gains.total_sensible_kw,
                "Latent (kW)": gains.total_latent_kw,
                "Total Load (kW)": gains.total_cooling_load_kw,
                "Selected FCU": fcu.selected_model if fcu else "No Suitable Unit",
                "Status": ("TBC" if (fcu and fcu.is_tbc) else (("PASS" if fcu.meets_load else "REVIEW") if fcu else "-")),
            }
            for room, gains, vent, fcu in all_results
        ])
        st.dataframe(results_df, use_container_width=True, hide_index=True)
        if not results_df.empty:
            total_row = results_df[["Sensible (kW)", "Latent (kW)", "Total Load (kW)"]].sum()
            st.markdown(
                f"**TOTALS \u2014 Sensible: {total_row['Sensible (kW)']:.2f} kW \u00b7 "
                f"Latent: {total_row['Latent (kW)']:.2f} kW \u00b7 "
                f"Total Load: {total_row['Total Load (kW)']:.2f} kW**"
            )
        else:
            st.caption("No rooms yet - add some on the Room Schedule tab.")


    with sub_vent:
        st.caption("Fresh air requirements and Equal Friction Method duct sizing.")

        if "fresh_air_rate_ls_person" not in st.session_state:
            st.session_state.fresh_air_rate_ls_person = ref.DEFAULT_FRESH_AIR_RATE_LS_PERSON
        st.session_state.fresh_air_rate_ls_person = st.number_input(
            "Fresh Air Rate (l/s/person) - applies to Airflow by Occupancy for every room",
            min_value=0.0, max_value=100.0, value=float(st.session_state.fresh_air_rate_ls_person),
            step=0.5, key="fresh_air_rate_input",
            help="Was fixed at 12 l/s/person in the code - now editable. CIBSE Guide B / Building Regs "
                 "Part F commonly cite 10 l/s/person for offices; 12 l/s/person is also a commonly used, "
                 "more conservative design figure - confirm against the specific standard for this project.",
        )

        with st.expander("Room Type & Sizing Basis", expanded=True):
            st.caption(
                "ACH starts at each Room Type's default but is fully editable - type your own value to "
                "override it. Changing Room Type resets ACH to that type's default; changing it back "
                "remembers whatever override you'd set for that type."
            )
            for room in st.session_state.rooms:
                i = room["_uid"]
                vc1, vc2, vc3, vc4 = st.columns([2, 1, 1, 1])
                vc1.text_input("Room Name", value=room["name"], key=f"vent_name_{i}_{gen}", disabled=True)
                room["room_type"] = vc2.selectbox(
                    "Room Type", ref.ROOM_TYPES,
                    index=ref.ROOM_TYPES.index(room.get("room_type")) if room.get("room_type") in ref.ROOM_TYPES else 0,
                    key=f"vent_type_{i}_{gen}",
                )
                room["sizing_basis"] = vc3.selectbox(
                    "Sizing Basis", ref.SIZING_BASIS_OPTIONS,
                    index=ref.SIZING_BASIS_OPTIONS.index(room.get("sizing_basis")) if room.get("sizing_basis") in ref.SIZING_BASIS_OPTIONS else 0,
                    key=f"vent_basis_{i}_{gen}",
                )
                room_type_default_ach = ref.ACH_BY_ROOM_TYPE.get(room.get("room_type"), 0.0)
                room["vent_ach"] = vc4.number_input(
                    "ACH", min_value=0.0, max_value=100.0, value=float(room_type_default_ach),
                    step=0.5, format="%.1f", key=f"vent_ach_{i}_{room.get('room_type')}_{gen}",
                )

        st.subheader("Results")
        all_results = compute_all()
        vent_results_df = pd.DataFrame([
            {
                "Room Name": room["name"],
                "Room Type": room.get("room_type"),
                "ACH Requirement": vent.ach_requirement,
                "Airflow by Occupancy (l/s)": vent.airflow_by_occupancy_ls,
                "Airflow by ACH (l/s)": vent.airflow_by_ach_ls,
                "Required Design Airflow (l/s)": vent.required_design_airflow_ls,
                "Calculated Diameter (mm)": vent.calculated_diameter_mm,
                "Selected Duct Size (mm)": vent.selected_duct_size_mm,
            }
            for room, gains, vent, fcu in all_results
        ])
        st.dataframe(vent_results_df, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("\U0001F300 Duct Run Pressure Drop Calculator")
        dcol1, dcol2, dcol3 = st.columns(3)
        with dcol1:
            duct_airflow = st.number_input("Airflow (l/s)", min_value=0.0, max_value=100000.0, value=200.0, step=10.0, key="duct_airflow_input")
        with dcol2:
            duct_diameter = st.selectbox("Duct Diameter (mm)", ref.STANDARD_DUCT_SIZES, index=4, key="duct_diameter_input")
        with dcol3:
            duct_length = st.number_input("Straight Duct Length (m)", min_value=0.0, max_value=1000.0, value=10.0, step=1.0, key="duct_length_input")

        if "duct_fitting_quantities" not in st.session_state:
            st.session_state.duct_fitting_quantities = {name: 0 for name in ref.DUCT_FITTING_TYPES}
        for name in ref.DUCT_FITTING_TYPES:
            st.session_state.duct_fitting_quantities[name] = st.number_input(
                name, min_value=0, max_value=100,
                value=st.session_state.duct_fitting_quantities.get(name, 0),
                step=1, key=f"duct_fitting_qty_{name}",
            )
        fittings_dict = st.session_state.duct_fitting_quantities
        duct_result = calc_engine.calculate_duct_fitting_losses(duct_airflow, duct_diameter, fittings_dict)
        friction_rate = calc_engine.calculate_straight_duct_friction_rate(duct_airflow, duct_diameter)
        straight_friction_loss = friction_rate * duct_length
        total_pressure_drop = straight_friction_loss + duct_result.total_pressure_loss_pa

        rcol1, rcol2 = st.columns(2)
        rcol1.metric("Velocity", f"{duct_result.velocity_ms} m/s")
        rcol2.metric("Friction Rate", f"{friction_rate:.3f} Pa/m")

        rcol3, rcol4, rcol5 = st.columns(3)
        rcol3.metric("Straight Duct Friction Loss", f"{straight_friction_loss:.1f} Pa")
        rcol4.metric("Fitting Loss", f"{duct_result.total_pressure_loss_pa} Pa")
        rcol5.metric("TOTAL Pressure Drop", f"{total_pressure_drop:.1f} Pa")


    with sub_water:
        st.caption("Cold water demand per BS EN 806-3 (Loading Unit method), applied per room via fixture "
                   "counts \u2014 storage & turnover per BS 8558 / HSE ACOP L8 (Legionella).")

        if "fixture_lu_values" not in st.session_state:
            st.session_state.fixture_lu_values = dict(ref.FIXTURE_LU)

        with st.expander("Loading Unit Reference Values (BS EN 806-3) \u2014 editable"):
            for fixture_name in list(st.session_state.fixture_lu_values.keys()):
                st.session_state.fixture_lu_values[fixture_name] = st.number_input(
                    fixture_name, min_value=0.0, max_value=100.0,
                    value=float(st.session_state.fixture_lu_values[fixture_name]),
                    step=0.5, format="%.2f", key=f"lu_value_{fixture_name}_{gen}",
                )
            if st.button("Reset to BS EN 806-3 defaults", key="reset_lu_defaults_button"):
                st.session_state.fixture_lu_values = dict(ref.FIXTURE_LU)
                # Bumping gen here forces every lu_value_* widget to become a
                # brand new key next render, so it picks up the fresh
                # default value instead of whatever was last typed - same
                # mechanism as a cloud project load, just triggered locally.
                st.session_state.data_gen += 1
                st.rerun()

        def _room_has_any_fixtures(room):
            counts = room.get("fixture_counts") or {}
            return any(counts.get(f, 0) for f in ref.FIXTURE_TYPES)

        if st.button("\u2728 Apply Room Type Defaults", key="apply_room_type_defaults_button"):
            applied = 0
            for room in st.session_state.rooms:
                if not _room_has_any_fixtures(room):
                    defaults = ref.ROOM_TYPE_DEFAULT_FIXTURES.get(room.get("room_type"), {})
                    if defaults:
                        room["fixture_counts"] = dict(defaults)
                        applied += 1
            # Same reasoning as the LU reset button - bump gen so the
            # fixture count widgets actually show the newly-applied
            # defaults instead of whatever was cached in them before.
            st.session_state.data_gen += 1
            st.success(f"Applied defaults to {applied} room(s).")

        with st.expander("Fixture Counts per Room", expanded=True):
            fixture_cols = ref.FIXTURE_TYPES
            fixtures_per_row = 4
            for room in st.session_state.rooms:
                i = room["_uid"]
                st.markdown(f"**{room['name']}**")
                if "fixture_counts" not in room or room["fixture_counts"] is None:
                    room["fixture_counts"] = {}
                for row_start in range(0, len(fixture_cols), fixtures_per_row):
                    row_fixtures = fixture_cols[row_start:row_start + fixtures_per_row]
                    row_columns = st.columns(fixtures_per_row)
                    for col, fixture_name in zip(row_columns, row_fixtures):
                        room["fixture_counts"][fixture_name] = col.number_input(
                            fixture_name, min_value=0, max_value=1000,
                            value=int(room["fixture_counts"].get(fixture_name, 0)),
                            step=1, key=f"fixture_{fixture_name}_{i}_{gen}",
                        )
                st.divider()

        st.subheader("Loading Units by Room")
        lu_rows = []
        total_lu = 0.0
        for room in st.session_state.rooms:
            water_result = calc_engine.calculate_room_loading_units(room, st.session_state.fixture_lu_values)
            lu_rows.append({"Room Name": room["name"], "Loading Units (LU)": water_result.loading_units})
            total_lu += water_result.loading_units
        st.dataframe(pd.DataFrame(lu_rows), use_container_width=True, hide_index=True)

        st.subheader("Cold Water Storage Sizing (BS 8558)")
        total_building_occupancy = sum(int(r.get("occupancy") or 0) for r in st.session_state.rooms)

        col1, col2, col3 = st.columns(3)
        with col1:
            building_occupancy = st.number_input(
                "Building Occupancy (persons)", min_value=0, max_value=100000,
                value=total_building_occupancy, step=1, key="building_occupancy_input",
            )
        with col2:
            daily_demand_rate = st.number_input(
                "Daily Demand Rate (l/person/day)", min_value=0.0, max_value=1000.0,
                value=45.0, step=1.0, key="daily_demand_rate_input",
            )
        with col3:
            storage_duration = st.number_input(
                "Peak Storage Duration (hours)", min_value=0.1, max_value=48.0,
                value=2.0, step=0.5, key="storage_duration_input",
            )

        storage = calc_engine.calculate_cold_water_storage(
            total_lu, building_occupancy, daily_demand_rate, storage_duration
        )

        st.markdown(f"**Total Loading Units: {storage.total_loading_units} LU**")
        st.markdown(f"**Design Flow Rate, Q: {storage.design_flow_rate_ls} l/s** (Q = 0.032 \u00d7 \u221ATotal LU, per BS EN 806-3 Annex A)")

        results_col1, results_col2 = st.columns(2)
        with results_col1:
            st.metric("Storage Required", f"{storage.storage_required_l:,.0f} l")
            st.metric("Selected Tank Capacity", f"{storage.selected_tank_l} l" if isinstance(storage.selected_tank_l, int) else storage.selected_tank_l)
        with results_col2:
            st.metric("Turnover Time", f"{storage.turnover_hrs} hrs" if isinstance(storage.turnover_hrs, (int, float)) else storage.turnover_hrs)
            if storage.legionella_compliant:
                st.success("Legionella Compliance (BS 8558 / HSE ACOP L8): PASS \u2014 turnover \u2264 24 hrs")
            else:
                st.warning("Legionella Compliance (BS 8558 / HSE ACOP L8): REVIEW \u2014 stagnation risk, turnover > 24 hrs")

        st.subheader("Booster Set - Duty Point")
        bcol1, bcol2, bcol3 = st.columns(3)
        with bcol1:
            outlet_height = st.number_input(
                "Highest Outlet Height Above Incoming Main (m)", min_value=0.0, max_value=500.0,
                value=0.0, step=0.5, key="outlet_height_input",
            )
        with bcol2:
            residual_pressure = st.number_input(
                "Min. Residual Pressure Required at Outlet (bar)", min_value=0.0, max_value=10.0,
                value=1.0, step=0.1, key="residual_pressure_input",
            )
        with bcol3:
            mains_pressure = st.number_input(
                "Incoming Mains Pressure Available (bar)", min_value=0.0, max_value=20.0,
                value=2.0, step=0.1, key="mains_pressure_input",
            )

        booster = calc_engine.calculate_booster_duty(
            storage.design_flow_rate_ls, outlet_height, residual_pressure, mains_pressure
        )
        bres1, bres2 = st.columns(2)
        with bres1:
            st.metric("Duty Flow", f"{booster.duty_flow_ls} l/s ({booster.duty_flow_lmin} l/min)")
            st.metric("Static Head to Highest Outlet", f"{booster.static_head_bar} bar")
        with bres2:
            st.metric("Required Pressure at Outlet", f"{booster.required_pressure_bar} bar")
            if booster.required_boost_pressure_bar > 0:
                st.warning(f"Required Boost Pressure: {booster.required_boost_pressure_bar} bar \u2014 booster set needed")
            else:
                st.success("Incoming mains pressure is sufficient \u2014 no boost required")


    with sub_heatload:
        st.caption("Winter fabric + infiltration heat loss (steady-state Q = U \u00d7 A \u00d7 \u0394T method).")

        winter_col1, winter_col2 = st.columns(2)
        with winter_col1:
            winter_external_temp = st.number_input(
                "Winter External Design Temp (\u00b0C)", min_value=-30.0, max_value=15.0,
                value=ref.WINTER_EXTERNAL_DBT_C, step=0.5, key="winter_external_temp_input",
            )
        with winter_col2:
            st.caption(
                "Internal temperature uses each room's own Design Temp - or 24\u00b0C global default."
            )

        fabric_element_types = list(ref.DEFAULT_U_VALUES.keys())
        for element in fabric_element_types:
            area_linked = element in ref.AREA_LINKED_TO_ROOM_SCHEDULE
            title = f"{element} (default U-value: {ref.DEFAULT_U_VALUES[element]} W/m\u00b2K)"
            if area_linked:
                title += " \u2014 area comes from Room Schedule"
            with st.expander(title):
                for room in st.session_state.rooms:
                    i = room["_uid"]
                    if "fabric_elements" not in room or room["fabric_elements"] is None:
                        room["fabric_elements"] = {}
                    existing = room["fabric_elements"].get(element, {})
                    fc1, fc2, fc3 = st.columns([2, 1, 1])
                    fc1.text_input("Room Name", value=room["name"], key=f"fabric_name_{element}_{i}_{gen}", disabled=True)
                    if area_linked:
                        fc2.number_input(
                            f"{element} Area (m\u00b2) \u2014 from Room Schedule",
                            value=float(room.get("area_m2", 0.0)), format="%.1f",
                            key=f"fabric_area_{element}_{i}_{gen}", disabled=True,
                        )
                        u_value = fc3.number_input(
                            "U-value (W/m\u00b2K)", min_value=0.0, max_value=10.0,
                            value=float(existing.get("u_value", ref.DEFAULT_U_VALUES[element])),
                            step=0.01, format="%.2f", key=f"fabric_uvalue_{element}_{i}_{gen}",
                        )
                        room["fabric_elements"][element] = {"u_value": u_value}
                    else:
                        area_m2 = fc2.number_input(
                            f"{element} Area (m\u00b2)", min_value=0.0, max_value=10000.0,
                            value=float(existing.get("area_m2", 0.0)), step=0.5, format="%.1f",
                            key=f"fabric_area_{element}_{i}_{gen}",
                        )
                        u_value = fc3.number_input(
                            "U-value (W/m\u00b2K)", min_value=0.0, max_value=10.0,
                            value=float(existing.get("u_value", ref.DEFAULT_U_VALUES[element])),
                            step=0.01, format="%.2f", key=f"fabric_uvalue_{element}_{i}_{gen}",
                        )
                        room["fabric_elements"][element] = {"area_m2": area_m2, "u_value": u_value}

        st.subheader("Winter Heat Loss by Room")
        heatloss_rows = []
        total_heat_loss_kw = 0.0
        for room in st.session_state.rooms:
            gains = calc_engine.calculate_heat_gains(room)
            heatloss = calc_engine.calculate_winter_heat_loss(room, gains.volume_m3, winter_external_temp)
            heatloss_rows.append({
                "Room Name": room["name"],
                "Fabric Loss (W)": heatloss.fabric_loss_w,
                "Infiltration Loss (W)": heatloss.infiltration_loss_w,
                "Total Heat Loss (kW)": heatloss.total_heat_loss_kw,
            })
            total_heat_loss_kw += heatloss.total_heat_loss_kw
        st.dataframe(pd.DataFrame(heatloss_rows), use_container_width=True, hide_index=True)
        st.markdown(f"**TOTAL BUILDING WINTER HEAT LOSS: {total_heat_loss_kw:.2f} kW**")


    with sub_pipes:
        st.caption("Pipe sizing for LTHW (heating) and CHW (chilled water) circuits.")

        lthw_tab, chw_tab = st.tabs(["\U0001F525 LTHW (Heating)", "\u2744\ufe0f CHW (Chilled Water)"])

        def _pipe_sizing_section(mode: str, default_load_kw: float, temp_options: dict, key_prefix: str):
            col1, col2 = st.columns(2)
            with col1:
                use_auto = st.checkbox(
                    f"Auto-pull total load from {'Heat Load (Winter)' if mode == 'LTHW' else 'HVAC & FCU Selection'}",
                    value=True, key=f"{key_prefix}_auto",
                )
                if use_auto:
                    load_kw = default_load_kw
                    st.metric("Total Load (auto)", f"{load_kw:.2f} kW")
                else:
                    load_kw = st.number_input("Load (kW) - manual entry", min_value=0.0, max_value=100000.0,
                                               value=default_load_kw, step=1.0, key=f"{key_prefix}_manual_load")
            with col2:
                temp_choice = st.selectbox("Flow / Return Temperatures", list(temp_options.keys()), key=f"{key_prefix}_temps")
                if temp_options[temp_choice] is None:
                    tcol1, tcol2 = st.columns(2)
                    flow_temp = tcol1.number_input("Flow Temp (\u00b0C)", value=82.0 if mode == "LTHW" else 6.0, key=f"{key_prefix}_flow_t")
                    return_temp = tcol2.number_input("Return Temp (\u00b0C)", value=71.0 if mode == "LTHW" else 12.0, key=f"{key_prefix}_return_t")
                else:
                    flow_temp, return_temp = temp_options[temp_choice]
                    st.caption(f"Flow: {flow_temp}\u00b0C \u00b7 Return: {return_temp}\u00b0C \u00b7 \u0394T: {abs(flow_temp-return_temp)}K")

            flow_rate_ls = calc_engine.calculate_water_flow_rate_ls(load_kw, flow_temp, return_temp)
            st.metric("Required Flow Rate", f"{flow_rate_ls:.3f} l/s")

            st.subheader("Pipe Sizing")
            pcol1, pcol2, pcol3 = st.columns(3)
            with pcol1:
                material = st.selectbox("Pipe Material", ["Copper", "Steel", "Stainless Steel (Pressfit)"], key=f"{key_prefix}_material")
            with pcol2:
                sizing_mode = st.radio("Sizing Mode", ["Auto-select", "Manual size"], key=f"{key_prefix}_sizing_mode", horizontal=True)
            with pcol3:
                target_pa_m = st.number_input("Target Pressure Drop (Pa/m)", min_value=10.0, max_value=2000.0,
                                               value=300.0, step=10.0, key=f"{key_prefix}_target_pam")

            mean_temp = (flow_temp + return_temp) / 2
            sizes_dict = calc_engine._pipe_sizes_for_material(material)

            if sizing_mode == "Auto-select":
                nominal, result = calc_engine.select_pipe_size(flow_rate_ls, mean_temp, material, target_pa_m)
                if nominal is None:
                    st.warning(f"No standard {material.lower()} size in this list achieves {target_pa_m:.0f} Pa/m.")
                else:
                    st.success(f"Selected size: **{nominal} mm nominal** ({material})")
            else:
                nominal = st.selectbox("Nominal Size (mm)", sorted(sizes_dict.keys()), key=f"{key_prefix}_manual_size")
                result = calc_engine.calculate_pipe_friction(
                    flow_rate_ls, sizes_dict[nominal], mean_temp, ref.PIPE_ROUGHNESS_MM[material]
                )

            if nominal is not None:
                rcol1, rcol2, rcol3, rcol4 = st.columns(4)
                rcol1.metric("Velocity", f"{result.velocity_ms} m/s")
                rcol2.metric("Reynolds No.", f"{result.reynolds_number:,.0f}")
                rcol3.metric("Friction Factor (\u03bb)", f"{result.friction_factor}")
                rcol4.metric("Pressure Drop", f"{result.pressure_drop_pa_per_m} Pa/m")

        with lthw_tab:
            total_heatload_kw = sum(
                calc_engine.calculate_winter_heat_loss(
                    room, calc_engine.calculate_heat_gains(room).volume_m3
                ).total_heat_loss_kw
                for room in st.session_state.rooms
            )
            _pipe_sizing_section("LTHW", total_heatload_kw, ref.LTHW_FLOW_RETURN_OPTIONS, "lthw")

        with chw_tab:
            total_cooling_kw = sum(
                calc_engine.calculate_heat_gains(room).total_cooling_load_kw
                for room in st.session_state.rooms
            )
            _pipe_sizing_section("CHW", total_cooling_kw, ref.CHW_FLOW_RETURN_OPTIONS, "chw")


    with sub_psychro:
        st.caption("Saturation curve and constant-RH lines computed from real formulas.")
        room_names_for_chart = [r["name"] for r in st.session_state.rooms if r.get("name")]
        if room_names_for_chart:
            selected_room_name = st.selectbox("Room", room_names_for_chart, key="psychro_room_select")
            selected_room = next(r for r in st.session_state.rooms if r["name"] == selected_room_name)
            chart_png, chart_details = psychro_chart.build_psychrometric_chart(selected_room)

            chart_col, _ = st.columns([2, 1])
            with chart_col:
                st.image(chart_png)

            st.dataframe(pd.DataFrame(chart_details).T, use_container_width=True)

            st.download_button(
                "\U0001F4E5 Download Chart as PNG",
                data=chart_png,
                file_name=f"Psychrometric_Chart_{selected_room_name.replace(' ', '_')}.png",
                mime="image/png",
            )


# =====================================================================
# TAB: Reports - Print Summary, Export, Data Sources, grouped as sub-tabs.
# =====================================================================
with tab_reports:
    sub_print, sub_export, sub_sources = st.tabs(
        ["\U0001F5A8\ufe0f Print Summary", "\U0001F4E5 Export", "\U0001F4DA Data Sources"]
    )

    with sub_print:
        st.caption("A clean, results page for printing or saving as PDF.")

        proj = st.session_state.project_details
        current_proj_name = proj['project_name'].strip() if proj['project_name'].strip() else "Unnamed Project"

        st.subheader("What to include")
        tcol1, tcol2, tcol3, tcol4, tcol5 = st.columns(5)
        include_hvac = tcol1.checkbox("HVAC & FCU", value=True, key="print_include_hvac")
        include_vent = tcol2.checkbox("Ventilation", value=True, key="print_include_vent")
        include_water = tcol3.checkbox("Water Services", value=False, key="print_include_water")
        include_heatload = tcol4.checkbox("Heat Load (Winter)", value=True, key="print_include_heatload")
        include_drawings = tcol5.checkbox("Drawing Register", value=True, key="print_include_drawings")

        all_results = compute_all()
        included_results = [r for r in all_results if r[0].get("include_in_summary", True)]
        excluded_count = len(all_results) - len(included_results)
        if excluded_count:
            st.info(f"{excluded_count} room(s) excluded from this summary.")

        hvac_df = pd.DataFrame([
            {
                "Room Name": room["name"], "Floor": room.get("floor", ""), "Area (m\u00b2)": room.get("area_m2"),
                "Volume (m\u00b3)": gains.volume_m3, "Sensible (kW)": gains.total_sensible_kw,
                "Latent (kW)": gains.total_latent_kw, "Total Load (kW)": gains.total_cooling_load_kw,
                "Selected FCU": fcu.selected_model if fcu else "No Suitable Unit",
                "Status": ("TBC" if (fcu and fcu.is_tbc) else (("PASS" if fcu.meets_load else "REVIEW") if fcu else "-")),
            }
            for room, gains, vent, fcu in included_results
        ]) if include_hvac else None

        vent_df = pd.DataFrame([
            {
                "Room Name": room["name"], "Required Airflow (l/s)": vent.required_design_airflow_ls,
                "Duct Size (mm)": vent.selected_duct_size_mm,
            }
            for room, gains, vent, fcu in included_results
        ]) if include_vent else None

        water_df = None
        if include_water:
            water_rows = []
            for room, gains, vent, fcu in included_results:
                water = calc_engine.calculate_room_loading_units(room, st.session_state.get("fixture_lu_values"))
                water_rows.append({"Room Name": room["name"], "Loading Units (LU)": water.loading_units})
            water_df = pd.DataFrame(water_rows)

        heatload_df = None
        if include_heatload:
            heatload_rows = []
            for room, gains, vent, fcu in included_results:
                heatloss = calc_engine.calculate_winter_heat_loss(room, gains.volume_m3)
                heatload_rows.append({
                    "Room Name": room["name"], "Fabric Loss (W)": heatloss.fabric_loss_w,
                    "Infiltration Loss (W)": heatloss.infiltration_loss_w,
                    "Total Heat Loss (kW)": heatloss.total_heat_loss_kw,
                })
            heatload_df = pd.DataFrame(heatload_rows)

        drawings_list = []
        if include_drawings:
            try:
                response = supabase.table("drawings_registry").select("*").eq("project_name", current_proj_name).execute()
                drawings_list = response.data
            except Exception as e:
                drawings_list = []

        totals_lines = []
        if include_hvac and not hvac_df.empty:
            totals_lines.append(
                f"Sensible: {hvac_df['Sensible (kW)'].sum():.2f} kW &middot; "
                f"Latent: {hvac_df['Latent (kW)'].sum():.2f} kW &middot; "
                f"Total Cooling Load: {hvac_df['Total Load (kW)'].sum():.2f} kW"
            )
        if include_water and water_df is not None and not water_df.empty:
            totals_lines.append(f"Total Loading Units: {water_df['Loading Units (LU)'].sum():.1f} LU")
        if include_heatload and heatload_df is not None and not heatload_df.empty:
            totals_lines.append(f"Total Winter Heat Loss: {heatload_df['Total Heat Loss (kW)'].sum():.2f} kW")
        totals_line_html = " &middot; ".join(totals_lines)
        totals_line_plain = " \u00b7 ".join(totals_lines)

        logo_img_tag = ""
        if st.session_state.get("logo_bytes"):
            logo_b64 = base64.b64encode(st.session_state.logo_bytes).decode("utf-8")
            logo_mime = st.session_state.get("logo_mime", "image/jpeg")
            logo_img_tag = f'<img src="data:{logo_mime};base64,{logo_b64}" style="max-width:180px; float:right;">'

        address_html = proj["site_address"].replace("\n", "<br>") if proj["site_address"] else ""
        detail_line = " &middot; ".join([b for b in [
            f"Client: {proj['client']}" if proj["client"] else None,
            f"Job Ref: {proj['job_reference']}" if proj["job_reference"] else None,
            f"Rev: {proj['revision']}" if proj["revision"] else None,
        ] if b])

        sections_html = ""
        if include_hvac and not hvac_df.empty:
            sections_html += f"<h3>HVAC & FCU Selection</h3>{hvac_df.to_html(index=False, border=0)}"
        if include_vent and vent_df is not None and not vent_df.empty:
            sections_html += f"<h3>Ventilation</h3>{vent_df.to_html(index=False, border=0)}"
        if include_water and water_df is not None and not water_df.empty:
            sections_html += f"<h3>Water Services</h3>{water_df.to_html(index=False, border=0)}"
        if include_heatload and heatload_df is not None and not heatload_df.empty:
            sections_html += f"<h3>Heat Load (Winter)</h3>{heatload_df.to_html(index=False, border=0)}"

        if include_drawings:
            sections_html += "<h3>Project Document & Drawing Register</h3>"
            if drawings_list:
                drawings_table_rows = ""
                for doc in drawings_list:
                    doc_date = doc['created_at'][:10] if 'created_at' in doc else "N/A"
                    drawings_table_rows += f"""
                    <tr>
                        <td>{doc['file_name']}</td>
                        <td>{doc['uploaded_by']}</td>
                        <td>{doc_date}</td>
                        <td><a href="{doc['file_url']}" target="_blank">View File</a></td>
                    </tr>
                    """
                sections_html += f"""
                <table>
                    <thead>
                        <tr>
                            <th>Document / Drawing Title</th>
                            <th>Uploaded By</th>
                            <th>Upload Date</th>
                            <th>Cloud Archive Link</th>
                        </tr>
                    </thead>
                    <tbody>
                        {drawings_table_rows}
                    </tbody>
                </table>
                """
            else:
                sections_html += "<p><i>No linked layout drawings or specifications recorded in project database.</i></p>"

        print_document = f"""<!DOCTYPE html>
    <html><head><title>MEP Results Summary</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; padding: 24px; color: #1B1B1B; }}
        h2 {{ color: #1B365D; margin-bottom: 0; }}
        h3 {{ color: #1B365D; margin-top: 24px; margin-bottom: 4px; }}
        p {{ color: #555; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 8px; }}
        th, td {{ border: 1px solid #B7C6D9; padding: 6px 10px; text-align: left; font-size: 13px; }}
        th {{ background-color: #1B365D; color: white; }}
        tr:nth-child(even) {{ background-color: #F3F6FA; }}
        .disclaimer {{ margin-top: 20px; padding: 10px; border: 1px solid #C0392B; font-size: 11px; color: #C0392B; }}
    </style>
    </head><body>
        {logo_img_tag}
        <h2>{proj['project_name'] or 'MEP Design Platform \u2014 ' + st.session_state.logo_name}</h2>
        <p>{address_html}</p>
        <p>{detail_line}</p>
        <p style="color:#C0392B; font-weight:bold;">\u26a0\ufe0f LIABILITY NOTICE: This document is a calculation aid only. Final layout designs must be independently cross-checked and certified by a qualified Professional Engineer using primary standard source data.</p>
        {sections_html}
        <p style="margin-top:16px;"><b>TOTALS \u2014 {totals_line_html}</b></p>
    </body></html>"""

        title_col1, title_col2 = st.columns([1, 3])
        with title_col1:
            if st.session_state.get("logo_bytes"):
                st.image(st.session_state.logo_bytes, width=140)
        with title_col2:
            st.markdown(f"### {proj['project_name'] or '(Project Name not yet entered)'}")
            if proj["site_address"]:
                st.markdown(proj["site_address"].replace("\n", "  \n"))
            detail_bits = [b for b in [
                f"Client: {proj['client']}" if proj["client"] else None,
                f"Job Ref: {proj['job_reference']}" if proj["job_reference"] else None,
                f"Rev: {proj['revision']}" if proj["revision"] else None,
            ] if b]
            if detail_bits:
                st.caption(" \u00b7 ".join(detail_bits))

        if include_hvac and not hvac_df.empty:
            st.markdown("#### HVAC & FCU Selection")
            st.dataframe(hvac_df, use_container_width=True, hide_index=True)
        if include_vent and vent_df is not None and not vent_df.empty:
            st.markdown("#### Ventilation")
            st.dataframe(vent_df, use_container_width=True, hide_index=True)
        if include_water and water_df is not None and not water_df.empty:
            st.markdown("#### Water Services")
            st.dataframe(water_df, use_container_width=True, hide_index=True)
        if include_heatload and heatload_df is not None and not heatload_df.empty:
            st.markdown("#### Heat Load (Winter)")
            st.dataframe(heatload_df, use_container_width=True, hide_index=True)

        if include_drawings:
            st.markdown("#### Project Document & Drawing Register")
            if drawings_list:
                display_docs = []
                for doc in drawings_list:
                    display_docs.append({
                        "Drawing / File Name": doc["file_name"],
                        "Uploaded By": doc["uploaded_by"],
                        "Upload Date": doc["created_at"][:10] if "created_at" in doc else "N/A"
                    })
                st.dataframe(pd.DataFrame(display_docs), use_container_width=True, hide_index=True)
            else:
                st.info("No drawings uploaded to this project yet.")

        if totals_line_plain:
            st.markdown(f"**TOTALS \u2014 {totals_line_plain}**")
        else:
            st.warning("No sections selected above.")

        components.html(
            f"""
            <button onclick='printMepSummary()' style="
                background-color:#1B365D; color:white; border:none;
                padding:8px 18px; border-radius:4px; cursor:pointer;
                font-family:'Segoe UI',sans-serif; font-size:14px;">
                \U0001F5A8\ufe0f Print / Save as PDF
            </button>
            <script>
                function printMepSummary() {{
                    var content = {json.dumps(print_document)};
                    var w = window.open('', '_blank');
                    w.document.write(content);
                    w.document.close();
                    w.focus();
                    setTimeout(function() {{ w.print(); }}, 250);
                }}
            </script>
            """,
            height=50,
        )


    with sub_export:
        st.caption("Generates a Room Schedule + HVAC Summary workbook from everything currently entered.")
        excel_buffer = excel_export.build_export_workbook(
            st.session_state.rooms,
            st.session_state.get("fresh_air_rate_ls_person", ref.DEFAULT_FRESH_AIR_RATE_LS_PERSON),
        )
        st.download_button(
            "\U0001F4E5 Export to Excel",
            data=excel_buffer,
            file_name="Room_Schedule_HVAC_Export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


    with sub_sources:
        st.error(
            "**CRITICAL NOTICE: This platform functions solely as a calculation verification tool. "
            "It does not hold, assume, transfer, or mitigate core engineering design or calculation liability.**"
        )
        sources_data = [
            {"Calculation Module": "Heat Gains & Solar Cooling", "Standard / Reference Guide": "CIBSE Guide A (2015)", "Section / Clause Reference": "Chapter 5: Thermal Response and Plant Sizing", "Engineering Notes": "Used for internal structural gains, occupancy profiles, and metabolic configurations."},
            {"Calculation Module": "Winter Fabric Heat Loss", "Standard / Reference Guide": "CIBSE Guide A (2015)", "Section / Clause Reference": "Chapter 3: Thermal Properties of Building Structures", "Engineering Notes": "Steady-state linear thermal transmittance equations (Q = U \u00d7 A \u00d7 \u0394T)."},
            {"Calculation Module": "Ventilation Requirements", "Standard / Reference Guide": "CIBSE Guide B2 / Building Regs Part F", "Section / Clause Reference": "Section 2.3: Ventilation Flow Rates per Activity Status", "Engineering Notes": "Determines minimum l/s per person rates and macro ACH volumes."},
            {"Calculation Module": "Equal Friction Duct Sizing", "Standard / Guide Reference": "CIBSE Guide C (2007)", "Section / Clause Reference": "Chapter 4, Section 4.11 & Annex 4.A1", "Engineering Notes": "Representative single-figure fitting resistance coefficients and sizing metrics."},
            {"Calculation Module": "Cold Water Loading Units", "Standard / Reference Guide": "BS EN 806-3", "Section / Clause Reference": "Table 2: Loading Units for Standard Appliances", "Engineering Notes": "Exact published figures map loading capacities directly to demand requirements."},
            {"Calculation Module": "Cold Water Flow Rates (Q)", "Standard / Reference Guide": "BS EN 806-3", "Section / Clause Reference": "Annex A: Design Flow Equation (Q = 0.032 \u00d7 \u221a\u03a3LU)", "Engineering Notes": "Calculates simultaneous building peak design water velocity requirements."},
            {"Calculation Module": "Water Storage Capacity", "Standard / Reference Guide": "BS 8558 / HSE ACOP L8", "Section / Clause Reference": "Section 4.3: Domestic Water Services / Legionella Control", "Engineering Notes": "Calculates fluid volume turnovers ensuring complete storage renewal under 24 hours."},
            {"Calculation Module": "Pipework Friction & Fluid Flow", "Standard / Reference Guide": "CIBSE Guide C (2007)", "Section / Clause Reference": "Chapter 4: Flow of Fluids in Pipes and Ducts", "Engineering Notes": "Uses the Haaland equation (Guide C's recommended replacement for Colebrook-White) - verified against Guide C's own worked example."}
        ]
        st.dataframe(pd.DataFrame(sources_data), use_container_width=True, hide_index=True)


# =====================================================================
# TAB: Document Control - the Drawing Upload Hub, now a proper tab instead
# of a sidebar-gated toggle.
# =====================================================================
with tab_documents:
    st.header("\U0001F4C2 Project Document & Drawing Register")

    if not st.session_state.engineer_name.strip():
        st.warning("\u26a0\ufe0f Please provide your Name/Email in the sidebar before uploading drawings.")
    else:
        up_col1, up_col2 = st.columns(2)
        with up_col1:
            st.subheader("Add Document to Cloud")
            uploaded_file = st.file_uploader(
                "Upload PDF Drawing / Spec Layout", type=["pdf", "png", "jpg", "jpeg"], key="drawing_uploader"
            )

            if uploaded_file is not None:
                file_name = uploaded_file.name
                storage_path = f"{current_proj_name}/{st.session_state.engineer_name}_{file_name}"

                if st.button("\U0001F4E4 Upload Document", key="upload_drawing_button"):
                    try:
                        file_bytes = uploaded_file.getvalue()
                        supabase.storage.from_("mep-drawings").upload(
                            path=storage_path,
                            file=file_bytes,
                            file_options={"content-type": uploaded_file.type}
                        )
                        file_url = supabase.storage.from_("mep-drawings").get_public_url(storage_path)

                        payload = {
                            "project_name": current_proj_name,
                            "uploaded_by": st.session_state.engineer_name,
                            "file_name": file_name,
                            "file_url": file_url
                        }
                        supabase.table("drawings_registry").insert(payload).execute()
                        st.success(f"Successfully uploaded and catalogued: {file_name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Upload failed: {e}. Check bucket RLS configurations.")

        with up_col2:
            st.subheader("Linked Project Documents")
            try:
                response = supabase.table("drawings_registry").select("*").eq("project_name", current_proj_name).execute()
                drawings_list = response.data

                if drawings_list:
                    for doc in drawings_list:
                        col_doc, col_lnk = st.columns([4, 1])
                        with col_doc:
                            st.write(f"\U0001F4C4 **{doc['file_name']}** (by {doc['uploaded_by']})")
                        with col_lnk:
                            st.markdown(f"[\U0001F517 View]({doc['file_url']})")
                else:
                    st.info("No documents linked to this active project yet.")
            except Exception as e:
                st.info("Ready to fetch drawings register once Supabase setup is complete.")
