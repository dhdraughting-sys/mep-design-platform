"""
MEP Design Platform - Streamlit prototype.

Run with:
    streamlit run streamlit_app.py
(or just double-click run.bat on Windows)

Layout mirrors the Excel workbook's tab structure (Room Schedule / HVAC &
FCU Selection / Ventilation Design), and within HVAC/Ventilation, columns
are grouped into several narrow tables instead of one wide one - same
column groupings the Excel workbook itself uses (Envelope & Solar |
Occupancy & Gains | FCU Selection, etc.), so nothing needs horizontal
scrolling to use.

Rooms can only be ADDED or REMOVED on the Room Schedule tab (matching the
real workbook's design: HVAC/Ventilation read from the Room Schedule,
they don't independently create rooms). Editing a field in any tab updates
that room immediately everywhere else that reads it.
"""
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

import calc_engine
import reference_data as ref
import excel_export
import psychro_chart

st.set_page_config(page_title="MEP Design Platform", layout="wide")

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

    /* Print Summary tab: hide Streamlit's own chrome (header, tab bar,
       buttons, footer, sidebar) so Ctrl+P gives a somewhat cleaner page as
       a FALLBACK. The primary, fully reliable print method is the
       "Print / Save as PDF" button on the Print Summary tab, which opens
       a completely separate, clean document instead of relying on this
       CSS - Ctrl+P still shares the same page as everything else
       (including the on-screen results table, which may not print in
       full if it's scrolled), so it's a rougher fallback, not a
       guarantee. Streamlit's internal DOM attributes can change between
       versions; if a future Streamlit upgrade breaks this, the fix is
       re-identifying which selector now matches the header/toolbar. */
    @media print {
        header[data-testid="stHeader"], #MainMenu, footer,
        .stTabs [data-baseweb="tab-list"], .stButton, .stDownloadButton,
        section[data-testid="stSidebar"] {
            display: none !important;
        }
    }
</style>
""", unsafe_allow_html=True)

st.title("MEP Design Platform \u2014 prototype")

# ---- Project Details (sidebar - persistent across every tab, feeds the
# title block on the Print Summary tab) ----
import base64
import os

if "project_details" not in st.session_state:
    st.session_state.project_details = {
        "project_name": "", "site_address": "", "client": "",
        "job_reference": "", "revision": "",
    }

# ---- Seed data (same example project as the Excel workbook) - moved
# before the sidebar so the Save Project button below can safely read
# st.session_state.rooms on the very first run. ----
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

if "rooms" not in st.session_state:
    st.session_state.rooms = [dict(r) for r in SEED_ROOMS]

with st.sidebar:
    st.subheader("Project Details")
    st.caption("Feeds the title block on the Print Summary tab.")
    pd_ = st.session_state.project_details
    pd_["project_name"] = st.text_input("Project Name", value=pd_["project_name"])
    pd_["site_address"] = st.text_area("Site Address", value=pd_["site_address"], height=70)
    pd_["client"] = st.text_input("Client", value=pd_["client"])
    pd_["job_reference"] = st.text_input("Job Reference", value=pd_["job_reference"])
    pd_["revision"] = st.text_input("Revision", value=pd_["revision"])

    st.divider()
    st.subheader("Logo")
    default_logo_path = os.path.join(os.path.dirname(__file__), "assets", "company_logo.jpg")
    uploaded_logo = st.file_uploader("Upload a different logo (optional)", type=["png", "jpg", "jpeg"])
    if uploaded_logo is not None:
        st.session_state.logo_bytes = uploaded_logo.read()
        st.session_state.logo_mime = uploaded_logo.type
    elif "logo_bytes" not in st.session_state and os.path.exists(default_logo_path):
        with open(default_logo_path, "rb") as f:
            st.session_state.logo_bytes = f.read()
        st.session_state.logo_mime = "image/jpeg"
    if st.session_state.get("logo_bytes"):
        st.image(st.session_state.logo_bytes, width=180)

    st.divider()
    st.subheader("\U0001F4BE Save / Load Project")
    st.caption(
        "This app does NOT save your work automatically - closing it loses anything not saved here. "
        "Download a project file before you stop, and upload it next time to pick up exactly where "
        "you left off (all rooms, every tab's data, project details, and your logo)."
    )
    import json

    def _serialize_project():
        return json.dumps({
            "rooms": st.session_state.rooms,
            "project_details": st.session_state.project_details,
            "fixture_lu_values": st.session_state.get("fixture_lu_values", {}),
            "logo_bytes_b64": (
                base64.b64encode(st.session_state.logo_bytes).decode("utf-8")
                if st.session_state.get("logo_bytes") else None
            ),
            "logo_mime": st.session_state.get("logo_mime"),
        }, indent=2)

    _project_name_for_filename = st.session_state.project_details.get("project_name", "").strip()
    _safe_name = "".join(c if c.isalnum() or c in " -_" else "" for c in _project_name_for_filename).strip()
    _save_filename = f"{_safe_name.replace(' ', '_')}_mep_project.json" if _safe_name else "mep_project_save.json"

    st.download_button(
        "\U0001F4E5 Save Project File",
        data=_serialize_project(),
        file_name=_save_filename,
        mime="application/json",
    )
    st.caption(
        "Each save is a separate file - fill in Project Name above to give it a distinct filename, so "
        "you can keep multiple projects as separate downloads and load whichever one you need back in."
    )

    loaded_project = st.file_uploader("Load a previously saved project file", type=["json"], key="project_loader")
    if loaded_project is not None and st.session_state.get("_last_loaded_project") != loaded_project.file_id:
        try:
            data = json.loads(loaded_project.read())
            st.session_state.rooms = data.get("rooms", [])
            st.session_state.project_details = data.get("project_details", {
                "project_name": "", "site_address": "", "client": "", "job_reference": "", "revision": "",
            })
            st.session_state.fixture_lu_values = data.get("fixture_lu_values") or dict(ref.FIXTURE_LU)
            if data.get("logo_bytes_b64"):
                st.session_state.logo_bytes = base64.b64decode(data["logo_bytes_b64"])
                st.session_state.logo_mime = data.get("logo_mime", "image/jpeg")
            st.session_state["_last_loaded_project"] = loaded_project.file_id
            st.success("Project loaded! Switch tabs to see your restored data.")
            st.rerun()
        except Exception as e:
            st.error(f"Couldn't load that file - is it a project file saved from this app? ({e})")


def sync_group_edits(edited_df: pd.DataFrame, field_names: list):
    """Merge edits from a narrow, Room-Name-keyed table back into the
    shared rooms list, touching ONLY the given fields - every other field
    on each room (owned by a different tab/group) is left untouched."""
    edited_by_name = {row["name"]: row for row in edited_df.to_dict("records")}
    for room in st.session_state.rooms:
        if room["name"] in edited_by_name:
            for field in field_names:
                room[field] = edited_by_name[room["name"]][field]


def sync_schedule_edits(edited_df: pd.DataFrame):
    """Room Schedule is the only tab that can add/remove rooms. Existing
    rooms keep every HVAC/Ventilation field they already had; new rooms
    get sensible defaults; rooms removed here are removed everywhere."""
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
    """Returns a list of (room, gains, ventilation, fcu) for every room, so
    each tab can pull whatever result columns it needs without recomputing."""
    results = []
    for room in st.session_state.rooms:
        gains = calc_engine.calculate_heat_gains(room)
        vent = calc_engine.calculate_ventilation(room, gains.volume_m3)
        fcu = calc_engine.select_fcu(
            gains.total_cooling_load_kw, room.get("manufacturer", "Daikin"),
            room.get("unit_type", "Ducted"), room.get("quantity", 1),
            ref.FCU_CATALOGUE,
        )
        results.append((room, gains, vent, fcu))
    return results


tab_schedule, tab_hvac, tab_vent, tab_water, tab_heatload, tab_pipes, tab_psychro, tab_print, tab_sources, tab_export = st.tabs(
    ["\U0001F4CB Room Schedule", "\u2744\ufe0f HVAC & FCU Selection", "\U0001F4A8 Ventilation",
     "\U0001F6B0 Water Services", "\U0001F525 Heat Load (Winter)", "\U0001F321\ufe0f LTHW & CHW",
     "\U0001F4C8 Psychrometric Chart", "\U0001F5A8\ufe0f Print Summary", "\U0001F4DA Data Sources", "\U0001F4E5 Export"]
)

# =====================================================================
# TAB 1: Room Schedule - the master list. Add/remove rooms here only.
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

    schedule_df = pd.DataFrame([
        {"name": r["name"], "floor": r.get("floor", ""), "area_m2": r.get("area_m2", 0.0),
         "ceiling_height_m": r.get("ceiling_height_m", 2.7),
         "summer_design_temp_c": _temp_to_display(r.get("summer_design_temp_c")),
         "winter_design_temp_c": _temp_to_display(r.get("winter_design_temp_c")),
         "include_in_summary": r.get("include_in_summary", True)}
        for r in st.session_state.rooms
    ])
    all_results = compute_all()
    volumes_by_name = {room["name"]: gains.volume_m3 for room, gains, _, _ in all_results}
    schedule_df["volume_m3"] = schedule_df["name"].map(volumes_by_name)

    edited_schedule = st.data_editor(
        schedule_df,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "name": st.column_config.TextColumn("Room Name", required=True),
            "floor": st.column_config.TextColumn("Floor"),
            "area_m2": st.column_config.NumberColumn("Area (m\u00b2)", min_value=0.0, format="%.1f"),
            "ceiling_height_m": st.column_config.NumberColumn("Ceiling Height (m)", min_value=0.0, format="%.2f"),
            "summer_design_temp_c": st.column_config.SelectboxColumn(
                "Summer Temp (\u00b0C)", options=TEMP_DROPDOWN_OPTIONS,
                help="Used by HVAC & FCU Selection (cooling)."
            ),
            "winter_design_temp_c": st.column_config.SelectboxColumn(
                "Winter Temp (\u00b0C)", options=TEMP_DROPDOWN_OPTIONS,
                help="Used by Heat Load - Winter (heating). Independent of Summer Temp."
            ),
            "volume_m3": st.column_config.NumberColumn("Volume (m\u00b3)", format="%.1f", disabled=True),
            "include_in_summary": st.column_config.CheckboxColumn(
                "Include in Print Summary", default=True,
                help="Untick for rooms not yet complete, so they're left out of the Print Summary / "
                     "client-facing output without deleting them from the working tabs."
            ),
        },
        key="schedule_editor",
    )
    # Convert the dropdown display values back to real numbers/None before syncing
    edited_schedule = edited_schedule.copy()
    edited_schedule["summer_design_temp_c"] = edited_schedule["summer_design_temp_c"].apply(_display_to_temp)
    edited_schedule["winter_design_temp_c"] = edited_schedule["winter_design_temp_c"].apply(_display_to_temp)
    sync_schedule_edits(edited_schedule)

# =====================================================================
# TAB 2: HVAC & FCU Selection - grouped into narrow tables, no scrolling
# =====================================================================
with tab_hvac:
    st.caption("Grouped the same way the Excel workbook's HVAC tab is \u2014 each table below is "
               "narrow on purpose, no horizontal scrolling needed.")

    with st.expander("Envelope & Solar", expanded=True):
        df = pd.DataFrame([
            {"name": r["name"], "city": r.get("city"), "orientation": r.get("orientation"),
             "glazing_area_m2": r.get("glazing_area_m2"), "glazing_type": r.get("glazing_type")}
            for r in st.session_state.rooms
        ])
        edited = st.data_editor(
            df, num_rows="fixed", use_container_width=True, hide_index=True,
            disabled=["name"],
            column_config={
                "name": st.column_config.TextColumn("Room Name"),
                "city": st.column_config.SelectboxColumn("City", options=list(ref.CITIES.keys())),
                "orientation": st.column_config.SelectboxColumn("Orientation", options=ref.ORIENTATIONS),
                "glazing_area_m2": st.column_config.NumberColumn(
                    "Glazing (m\u00b2)", min_value=0.0, max_value=100000.0, step=0.5, format="%.1f"
                ),
                "glazing_type": st.column_config.SelectboxColumn("Glazing Type", options=list(ref.GLAZING_TYPES.keys())),
            },
            key="envelope_editor",
        )
        sync_group_edits(edited, ["city", "orientation", "glazing_area_m2", "glazing_type"])

    with st.expander("Occupancy & Internal Gains", expanded=True):
        df = pd.DataFrame([
            {"name": r["name"], "occupancy": r.get("occupancy"),
             "sensible_w_person": r.get("sensible_w_person"), "latent_w_person": r.get("latent_w_person"),
             "lighting_wm2": r.get("lighting_wm2"), "small_power_wm2": r.get("small_power_wm2"),
             "infiltration_ach": r.get("infiltration_ach")}
            for r in st.session_state.rooms
        ])
        edited = st.data_editor(
            df, num_rows="fixed", use_container_width=True, hide_index=True,
            disabled=["name"],
            column_config={
                "name": st.column_config.TextColumn("Room Name"),
                "occupancy": st.column_config.NumberColumn("Occupancy", min_value=0, max_value=10000, step=1),
                "sensible_w_person": st.column_config.NumberColumn("Sensible/Person (W)", format="%.0f"),
                "latent_w_person": st.column_config.NumberColumn("Latent/Person (W)", format="%.0f"),
                "lighting_wm2": st.column_config.NumberColumn("Lighting (W/m\u00b2)", format="%.0f"),
                "small_power_wm2": st.column_config.NumberColumn("Small Power (W/m\u00b2)", format="%.0f"),
                "infiltration_ach": st.column_config.SelectboxColumn(
                    "Infiltration (ACH)", options=[0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0],
                    help="Typical CIBSE Guide A range: 0.25-0.5 ACH for well-sealed modern offices, "
                         "rising for exposed/naturally-ventilated or poorly-sealed buildings.",
                ),
            },
            key="gains_editor",
        )
        sync_group_edits(edited, ["occupancy", "sensible_w_person", "latent_w_person",
                                   "lighting_wm2", "small_power_wm2", "infiltration_ach"])

    with st.expander("FCU / Indoor Unit Selection", expanded=True):
        df = pd.DataFrame([
            {"name": r["name"], "manufacturer": r.get("manufacturer"), "unit_type": r.get("unit_type"),
             "quantity": r.get("quantity")}
            for r in st.session_state.rooms
        ])
        edited = st.data_editor(
            df, num_rows="fixed", use_container_width=True, hide_index=True,
            disabled=["name"],
            column_config={
                "name": st.column_config.TextColumn("Room Name"),
                "manufacturer": st.column_config.SelectboxColumn("Manufacturer", options=ref.MANUFACTURERS),
                "unit_type": st.column_config.SelectboxColumn("Unit Type", options=ref.UNIT_TYPES),
                "quantity": st.column_config.NumberColumn("Qty", min_value=1, step=1),
            },
            key="fcu_editor",
        )
        sync_group_edits(edited, ["manufacturer", "unit_type", "quantity"])

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
            "Status": ("PASS" if fcu.meets_load else "REVIEW") if fcu else "-",
        }
        for room, gains, vent, fcu in all_results
    ])
    st.dataframe(results_df, use_container_width=True, hide_index=True)
    total_row = results_df[["Sensible (kW)", "Latent (kW)", "Total Load (kW)"]].sum()
    st.markdown(
        f"**TOTALS \u2014 Sensible: {total_row['Sensible (kW)']:.2f} kW \u00b7 "
        f"Latent: {total_row['Latent (kW)']:.2f} kW \u00b7 "
        f"Total Load: {total_row['Total Load (kW)']:.2f} kW**"
    )

    with st.expander("Heat Gain Breakdown (Occupancy / Lighting / Small Power / Solar / Infiltration)"):
        breakdown_df = pd.DataFrame([
            {
                "Room Name": room["name"],
                "Occ. Sensible (kW)": gains.occ_sensible_kw,
                "Occ. Latent (kW)": gains.occ_latent_kw,
                "Lighting (kW)": gains.lighting_kw,
                "Small Power (kW)": gains.small_power_kw,
                "Solar Gain (kW)": gains.solar_gain_kw,
                "Infiltration Sensible (kW)": gains.infiltration_sensible_kw,
                "Infiltration Latent (kW)": gains.infiltration_latent_kw,
            }
            for room, gains, vent, fcu in all_results
        ])
        st.dataframe(breakdown_df, use_container_width=True, hide_index=True)
        st.caption(
            "Solar Gain = Glazing Area \u00d7 g-value (from Glazing Type) \u00d7 peak solar intensity for the "
            "selected City/Orientation. If this shows 0.00 for every room, check Glazing Area is not 0 "
            "on the Envelope & Solar table above \u2014 it's set to 0 by default in the seed data as an "
            "honest placeholder, same as the Excel workbook."
        )

# =====================================================================
# TAB 3: Ventilation Design
# =====================================================================
with tab_vent:
    st.caption("Fresh air requirement (stricter of occupancy or ACH, same project criteria as the "
               "Excel workbook) and Equal Friction Method duct sizing.")

    with st.expander("Room Type & Sizing Basis", expanded=True):
        df = pd.DataFrame([
            {"name": r["name"], "room_type": r.get("room_type"), "sizing_basis": r.get("sizing_basis")}
            for r in st.session_state.rooms
        ])
        edited = st.data_editor(
            df, num_rows="fixed", use_container_width=True, hide_index=True,
            disabled=["name"],
            column_config={
                "name": st.column_config.TextColumn("Room Name"),
                "room_type": st.column_config.SelectboxColumn("Room Type", options=ref.ROOM_TYPES),
                "sizing_basis": st.column_config.SelectboxColumn("Sizing Basis", options=ref.SIZING_BASIS_OPTIONS),
            },
            key="vent_editor",
        )
        sync_group_edits(edited, ["room_type", "sizing_basis"])
        st.caption("Occupancy is shared with the HVAC tab's Occupancy field \u2014 edit it there.")

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
    st.caption(
        "A general-purpose tool - not tied to a specific room - for estimating the TOTAL pressure drop "
        "through a run of ductwork: straight-duct friction (length \u00d7 friction rate) plus fittings "
        "(bends, dampers, tees), using real loss factors (\u03b6, zeta) from CIBSE Guide C, Chapter 4, "
        "Section 4.11. Zeta values are representative single figures picked from tables that vary by "
        "diameter/aspect ratio/Reynolds number in the full Guide - confirm the exact figure against the "
        "specific table for anything beyond a first-pass estimate."
    )
    dcol1, dcol2, dcol3 = st.columns(3)
    with dcol1:
        duct_airflow = st.number_input("Airflow (l/s)", min_value=0.0, max_value=100000.0, value=200.0, step=10.0)
    with dcol2:
        duct_diameter = st.selectbox("Duct Diameter (mm)", ref.STANDARD_DUCT_SIZES, index=4)
    with dcol3:
        duct_length = st.number_input("Straight Duct Length (m)", min_value=0.0, max_value=1000.0, value=10.0, step=1.0)

    fitting_qty_df = pd.DataFrame([
        {"Fitting Type": name, "Quantity": 0} for name in ref.DUCT_FITTING_TYPES
    ])
    edited_fittings = st.data_editor(
        fitting_qty_df, num_rows="fixed", use_container_width=True, hide_index=True,
        disabled=["Fitting Type"],
        column_config={"Quantity": st.column_config.NumberColumn("Quantity", min_value=0, max_value=100, step=1)},
        key="duct_fitting_editor",
    )
    fittings_dict = dict(zip(edited_fittings["Fitting Type"], edited_fittings["Quantity"]))
    duct_result = calc_engine.calculate_duct_fitting_losses(duct_airflow, duct_diameter, fittings_dict)
    friction_rate = calc_engine.calculate_straight_duct_friction_rate(duct_airflow, duct_diameter)
    straight_friction_loss = friction_rate * duct_length
    total_pressure_drop = straight_friction_loss + duct_result.total_pressure_loss_pa

    rcol1, rcol2 = st.columns(2)
    rcol1.metric("Velocity", f"{duct_result.velocity_ms} m/s")
    rcol2.metric("Friction Rate", f"{friction_rate:.3f} Pa/m")

    rcol3, rcol4, rcol5 = st.columns(3)
    rcol3.metric("Straight Duct Friction Loss", f"{straight_friction_loss:.1f} Pa", help=f"{friction_rate:.3f} Pa/m \u00d7 {duct_length} m")
    rcol4.metric("Fitting Loss", f"{duct_result.total_pressure_loss_pa} Pa", help=f"\u03a3\u03b6 = {duct_result.total_zeta} \u00d7 {duct_result.velocity_pressure_pa} Pa velocity pressure")
    rcol5.metric("TOTAL Pressure Drop", f"{total_pressure_drop:.1f} Pa")

# =====================================================================
# TAB 4: Water Services - Cold Water Loading Units (BS EN 806-3) +
# Storage Sizing / Legionella turnover check (BS 8558)
# =====================================================================
with tab_water:
    st.caption("Cold water demand per BS EN 806-3 (Loading Unit method), applied per room via fixture "
               "counts \u2014 storage & turnover per BS 8558 / HSE ACOP L8 (Legionella).")

    if "fixture_lu_values" not in st.session_state:
        st.session_state.fixture_lu_values = dict(ref.FIXTURE_LU)

    with st.expander("Loading Unit Reference Values (BS EN 806-3) \u2014 editable"):
        st.caption(
            "Change any value here if your reference (or a specific project requirement) differs from "
            "the default - e.g. WHB from 1 LU to 2 LU. Takes effect immediately for every room below."
        )
        lu_df = pd.DataFrame([
            {"Fixture Type": k, "Loading Units (LU)": v}
            for k, v in st.session_state.fixture_lu_values.items()
        ])
        edited_lu = st.data_editor(
            lu_df, num_rows="fixed", use_container_width=True, hide_index=True,
            disabled=["Fixture Type"],
            column_config={"Loading Units (LU)": st.column_config.NumberColumn(
                "Loading Units (LU)", min_value=0.0, max_value=100.0, step=0.5, format="%.2f"
            )},
            key="lu_values_editor",
        )
        st.session_state.fixture_lu_values = dict(zip(edited_lu["Fixture Type"], edited_lu["Loading Units (LU)"]))
        if st.button("Reset to BS EN 806-3 defaults"):
            st.session_state.fixture_lu_values = dict(ref.FIXTURE_LU)
            st.rerun()

    def _room_has_any_fixtures(room):
        counts = room.get("fixture_counts") or {}
        return any(counts.get(f, 0) for f in ref.FIXTURE_TYPES)

    if st.button("\u2728 Apply Room Type Defaults"):
        applied = 0
        for room in st.session_state.rooms:
            if not _room_has_any_fixtures(room):
                defaults = ref.ROOM_TYPE_DEFAULT_FIXTURES.get(room.get("room_type"), {})
                if defaults:
                    room["fixture_counts"] = dict(defaults)
                    applied += 1
        st.success(f"Applied defaults to {applied} room(s).")
    st.caption(
        "Fills in sensible fixture counts based on each room's Room Type (set on the Ventilation tab) "
        "\u2014 e.g. a 'WC / Washroom' room gets 1 WC + 1 WHB. **Only affects rooms that currently have "
        "zero fixtures entered** - any room you've already put a fixture count into is left untouched, "
        "so this is always safe to click again later (e.g. after adding new rooms)."
    )

    with st.expander("Fixture Counts per Room", expanded=True):
        fixture_cols = ref.FIXTURE_TYPES
        df = pd.DataFrame([
            {"name": r["name"], **{f: (r.get("fixture_counts") or {}).get(f, 0) for f in fixture_cols}}
            for r in st.session_state.rooms
        ])
        column_config = {"name": st.column_config.TextColumn("Room Name")}
        for f in fixture_cols:
            column_config[f] = st.column_config.NumberColumn(f, min_value=0, max_value=1000, step=1)
        edited = st.data_editor(
            df, num_rows="fixed", use_container_width=True, hide_index=True,
            disabled=["name"], column_config=column_config, key="fixtures_editor",
        )
        # Reconstruct each room's fixture_counts dict from the flattened columns
        edited_by_name = {row["name"]: row for row in edited.to_dict("records")}
        for room in st.session_state.rooms:
            if room["name"] in edited_by_name:
                row = edited_by_name[room["name"]]
                room["fixture_counts"] = {f: row[f] for f in fixture_cols}
        st.caption("LU values used: " + ", ".join(
            f"{k} = {v}" for k, v in st.session_state.fixture_lu_values.items()
        ))

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
            value=total_building_occupancy, step=1,
            help="Defaults to the sum of every room's Occupancy field - override if the building "
                 "serves more people than are captured there (e.g. visitors).",
        )
    with col2:
        daily_demand_rate = st.number_input(
            "Daily Demand Rate (l/person/day)", min_value=0.0, max_value=1000.0,
            value=45.0, step=1.0,
            help="Indicative CIBSE Guide G typical office water demand - confirm against building use class.",
        )
    with col3:
        storage_duration = st.number_input(
            "Peak Storage Duration (hours)", min_value=0.1, max_value=48.0,
            value=2.0, step=0.5,
            help="Storage sized to cover peak demand for this duration (commonly 1-2 hrs per BS 8558).",
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

    st.caption(
        "HSE ACOP L8 and BS 8558 Section 8 recommend minimising cold water storage to the shortest "
        "practicable duration while ensuring the stored volume turns over regularly (commonly \u2264 24 "
        "hours) to limit Legionella risk. Where a single tank cannot achieve adequate turnover at low "
        "occupancy/demand, consider twin tanks with duty/assist changeover, or a reduced-capacity tank "
        "with mains booster backup."
    )

    st.subheader("Booster Set - Duty Point")
    st.caption(
        "This calculates the duty point (flow + required pressure boost) to hand to a pump supplier "
        "for their own selection - it is NOT a manufacturer model lookup, since (unlike the FCU "
        "catalogue, which is real client project data) there's no real booster pump catalogue "
        "available here to select an actual product from."
    )
    bcol1, bcol2, bcol3 = st.columns(3)
    with bcol1:
        outlet_height = st.number_input(
            "Highest Outlet Height Above Incoming Main (m)", min_value=0.0, max_value=500.0,
            value=0.0, step=0.5,
            help="Height of the highest/furthest fitting served, above where the mains supply enters the building.",
        )
    with bcol2:
        residual_pressure = st.number_input(
            "Min. Residual Pressure Required at Outlet (bar)", min_value=0.0, max_value=10.0,
            value=1.0, step=0.1,
            help="Indicative - confirm against the manufacturer/fitting requirements for the actual outlets served (showers, mixer taps, etc.).",
        )
    with bcol3:
        mains_pressure = st.number_input(
            "Incoming Mains Pressure Available (bar)", min_value=0.0, max_value=20.0,
            value=2.0, step=0.1,
            help="Confirm with the water utility - this is a placeholder default, not a site-measured figure.",
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
    st.caption(
        "Friction/pipe losses along the actual pipe run are NOT modelled here (they depend on real "
        "pipe routing and length) - add an allowance separately before finalising the duty point."
    )

# =====================================================================
# TAB 5: Heat Load (Winter) - fabric + infiltration heat loss, steady-
# state method. Default U-values are Approved Document Part L 2021
# backstop figures (see reference_data.DEFAULT_U_VALUES for the honest
# caveats on domestic vs non-domestic and location) - editable per
# element, per room.
# =====================================================================
with tab_heatload:
    st.caption("Winter fabric + infiltration heat loss (steady-state Q = U \u00d7 A \u00d7 \u0394T method). "
               "Default U-values are Part L 2021 backstop figures - see the note below before relying "
               "on them for compliance purposes.")

    winter_col1, winter_col2 = st.columns(2)
    with winter_col1:
        winter_external_temp = st.number_input(
            "Winter External Design Temp (\u00b0C)", min_value=-30.0, max_value=15.0,
            value=ref.WINTER_EXTERNAL_DBT_C, step=0.5,
            help="CIBSE Guide A indicative UK winter design condition - confirm against the actual "
                 "CIBSE weather data/DSY for this project's location.",
        )
    with winter_col2:
        st.caption(
            "Internal temperature uses each room's own Design Temp (set on the Room Schedule tab, same "
            "field HVAC uses) - or the 24\u00b0C global default if left blank there."
        )

    st.warning(
        "**U-value defaults are Approved Document L 2021 (England) NEW BUILD backstop figures** - "
        "the worst permitted for any element, not a recommended target, and drawn from the more "
        "commonly published dwellings (Volume 1) figures. Non-domestic buildings (Volume 2) have their "
        "own notional/backstop values which may differ, and England/Wales/Scotland/NI all have separate "
        "Approved Documents - confirm against whichever applies to this specific building before relying "
        "on these for compliance. They are, however, fully editable per element per room below."
    )

    fabric_element_types = list(ref.DEFAULT_U_VALUES.keys())
    for element in fabric_element_types:
        area_linked = element in ref.AREA_LINKED_TO_ROOM_SCHEDULE
        title = f"{element} (default U-value: {ref.DEFAULT_U_VALUES[element]} W/m\u00b2K)"
        if area_linked:
            title += " \u2014 area comes from Room Schedule"
        with st.expander(title):
            if area_linked:
                st.caption(
                    f"{element} area is the room's own Area (m\u00b2) from the Room Schedule tab - a room's "
                    f"{element.lower()} area is the same as its footprint, so there's nothing extra to "
                    "enter here, just the U-value."
                )
                df = pd.DataFrame([
                    {
                        "name": r["name"],
                        "area_m2": r.get("area_m2", 0.0),  # read-only display, from Room Schedule
                        "u_value": (r.get("fabric_elements") or {}).get(element, {}).get(
                            "u_value", ref.DEFAULT_U_VALUES[element]
                        ),
                    }
                    for r in st.session_state.rooms
                ])
                edited = st.data_editor(
                    df, num_rows="fixed", use_container_width=True, hide_index=True,
                    disabled=["name", "area_m2"],
                    column_config={
                        "name": st.column_config.TextColumn("Room Name"),
                        "area_m2": st.column_config.NumberColumn(
                            f"{element} Area (m\u00b2) \u2014 from Room Schedule", format="%.1f"
                        ),
                        "u_value": st.column_config.NumberColumn(
                            "U-value (W/m\u00b2K)", min_value=0.0, max_value=10.0, step=0.01, format="%.2f"
                        ),
                    },
                    key=f"fabric_editor_{element}",
                )
                edited_by_name = {row["name"]: row for row in edited.to_dict("records")}
                for room in st.session_state.rooms:
                    if room["name"] in edited_by_name:
                        row = edited_by_name[room["name"]]
                        if "fabric_elements" not in room or room["fabric_elements"] is None:
                            room["fabric_elements"] = {}
                        # area_m2 not stored here - calc_engine reads room["area_m2"] directly for
                        # these two elements, so only the U-value needs saving.
                        room["fabric_elements"][element] = {"u_value": row["u_value"]}
            else:
                df = pd.DataFrame([
                    {
                        "name": r["name"],
                        "area_m2": (r.get("fabric_elements") or {}).get(element, {}).get("area_m2", 0.0),
                        "u_value": (r.get("fabric_elements") or {}).get(element, {}).get(
                            "u_value", ref.DEFAULT_U_VALUES[element]
                        ),
                    }
                    for r in st.session_state.rooms
                ])
                edited = st.data_editor(
                    df, num_rows="fixed", use_container_width=True, hide_index=True,
                    disabled=["name"],
                    column_config={
                        "name": st.column_config.TextColumn("Room Name"),
                        "area_m2": st.column_config.NumberColumn(
                            f"{element} Area (m\u00b2)", min_value=0.0, max_value=10000.0, step=0.5, format="%.1f"
                        ),
                        "u_value": st.column_config.NumberColumn(
                            "U-value (W/m\u00b2K)", min_value=0.0, max_value=10.0, step=0.01, format="%.2f"
                        ),
                    },
                    key=f"fabric_editor_{element}",
                )
                edited_by_name = {row["name"]: row for row in edited.to_dict("records")}
                for room in st.session_state.rooms:
                    if room["name"] in edited_by_name:
                        row = edited_by_name[room["name"]]
                        if "fabric_elements" not in room or room["fabric_elements"] is None:
                            room["fabric_elements"] = {}
                        room["fabric_elements"][element] = {"area_m2": row["area_m2"], "u_value": row["u_value"]}

    st.subheader("Winter Heat Loss by Room")
    heatloss_rows = []
    total_heat_loss_kw = 0.0
    for room in st.session_state.rooms:
        gains = calc_engine.calculate_heat_gains(room)  # for volume_m3 only
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

# =====================================================================
# TAB 6: LTHW & CHW - pipe sizing for heating (LTHW) and chilled water
# (CHW) circuits, pulling total loads from Heat Load (Winter) and HVAC
# respectively, with a manual override for either. Pipe friction uses
# the Haaland equation (CIBSE Guide C, Chapter 4, Eq. 4.5) - verified
# against Guide C's own worked example before being used here.
# =====================================================================
with tab_pipes:
    st.caption(
        "Pipe sizing for LTHW (heating) and CHW (chilled water) circuits. Pulls the total load from the "
        "relevant working tab by default, with a manual override for sizing a specific pipe run "
        "independently. Friction uses the Haaland equation, CIBSE Guide C Chapter 4 (verified against "
        "Guide C's own worked example: copper 76.1x1.5mm, Re=2.16\u00d710\u2075 \u2192 \u03bb=0.01540, exact match)."
    )

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
            material = st.selectbox("Pipe Material", ["Copper", "Steel"], key=f"{key_prefix}_material")
        with pcol2:
            sizing_mode = st.radio("Sizing Mode", ["Auto-select", "Manual size"], key=f"{key_prefix}_sizing_mode", horizontal=True)
        with pcol3:
            target_pa_m = st.number_input("Target Pressure Drop (Pa/m)", min_value=10.0, max_value=2000.0,
                                           value=300.0, step=10.0, key=f"{key_prefix}_target_pam",
                                           help="BSRIA rule-of-thumb starting points: 250-360 Pa/m (CIBSE Guide C 4.5.1).")

        mean_temp = (flow_temp + return_temp) / 2
        sizes_dict = ref.COPPER_PIPE_SIZES_MM if material == "Copper" else ref.STEEL_PIPE_SIZES_MM

        if sizing_mode == "Auto-select":
            nominal, result = calc_engine.select_pipe_size(flow_rate_ls, mean_temp, material, target_pa_m)
            if nominal is None:
                st.warning(f"No standard {material.lower()} size in this list achieves {target_pa_m:.0f} Pa/m at this "
                           "flow rate - consider a larger material range, multiple pipe runs, or a higher target.")
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
            st.caption(
                "Typical velocity ranges (CIBSE Guide C Table 4.6, BSRIA): 15-50mm bore 0.75-1.15 m/s, "
                ">50mm bore 1.25-3.0 m/s, heating/cooling coils 0.5-1.5 m/s - a sense-check, not a hard limit."
            )

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

# =====================================================================
# TAB 7: Psychrometric Chart - its own tab (previously embedded in Print
# Summary) so it's easy to find and use on its own.
# =====================================================================
with tab_psychro:
    st.caption(
        "Saturation curve and constant-RH lines computed from the real CIBSE Guide C formula (Chapter "
        "1, Equation 1.3) used elsewhere in this app - marks the selected room's Internal Design point "
        "against the project's External Design point."
    )
    room_names_for_chart = [r["name"] for r in st.session_state.rooms if r.get("name")]
    if room_names_for_chart:
        selected_room_name = st.selectbox("Room", room_names_for_chart, key="psychro_room_select")
        selected_room = next(r for r in st.session_state.rooms if r["name"] == selected_room_name)
        chart_png, chart_details = psychro_chart.build_psychrometric_chart(selected_room)

        chart_col, _ = st.columns([2, 1])  # constrains the chart to ~2/3 width instead of full page
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
# TAB 8: Print Summary - a clean, printable results page. Room Schedule/
# HVAC/Ventilation/Water/Heat Load each have their own working tabs with
# full input columns; this tab is deliberately read-only and combines
# just the final figures, the way the Excel workbook's "Results Summary
# (Print)" tab does.
# =====================================================================
with tab_print:
    st.caption("A clean, results page for printing or saving as PDF (Ctrl+P / Cmd+P, or the button "
               "below). Only final results are shown here \u2014 edit inputs on the other tabs. "
               "Fill in Project Details and a logo in the sidebar \u2190 to complete the title block below.")

    proj = st.session_state.project_details

    st.subheader("What to include")
    st.caption(
        "Choose which sections appear in the printed summary - e.g. include HVAC & FCU, Heat Load, and "
        "Ventilation but leave out Water Services if it's not finished yet. This is separate from the "
        "per-room \"Include in Print Summary\" tick on the Room Schedule tab - both filters apply together."
    )
    tcol1, tcol2, tcol3, tcol4 = st.columns(4)
    include_hvac = tcol1.checkbox("HVAC & FCU", value=True, key="print_include_hvac")
    include_vent = tcol2.checkbox("Ventilation", value=True, key="print_include_vent")
    include_water = tcol3.checkbox("Water Services", value=False, key="print_include_water")
    include_heatload = tcol4.checkbox("Heat Load (Winter)", value=True, key="print_include_heatload")

    all_results = compute_all()
    included_results = [r for r in all_results if r[0].get("include_in_summary", True)]
    excluded_count = len(all_results) - len(included_results)
    if excluded_count:
        st.info(
            f"{excluded_count} room(s) excluded from this summary (unticked \"Include in Print Summary\" "
            "on the Room Schedule tab)."
        )

    # Build each section's table independently - only sections that are
    # both ticked here AND have at least one included room actually appear.
    hvac_df = pd.DataFrame([
        {
            "Room Name": room["name"], "Floor": room.get("floor", ""), "Area (m\u00b2)": room.get("area_m2"),
            "Volume (m\u00b3)": gains.volume_m3, "Sensible (kW)": gains.total_sensible_kw,
            "Latent (kW)": gains.total_latent_kw, "Total Load (kW)": gains.total_cooling_load_kw,
            "Selected FCU": fcu.selected_model if fcu else "No Suitable Unit",
            "Status": ("PASS" if fcu.meets_load else "REVIEW") if fcu else "-",
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

    # Section-specific totals, only computed for included sections
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

    # Build a FULLY SELF-CONTAINED print document (its own <html><head>
    # etc., not a div appended to the current page) - opens in a brand
    # new window/tab containing ONLY this content, so there is no
    # sidebar, no Streamlit chrome, and no duplicate table to leak into it.
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
    <h2>{proj['project_name'] or 'MEP Design Platform \u2014 Results Summary'}</h2>
    <p>{address_html}</p>
    <p>{detail_line}</p>
    <p>Printed results \u2014 final figures only.</p>
    {sections_html}
    <p style="margin-top:16px;"><b>TOTALS \u2014 {totals_line_html}</b></p>
    <div class="disclaimer"><b>Disclaimer:</b> this platform is a calculation aid only and does not hold
    or assume any design liability. All figures must be independently checked and verified by a suitably
    qualified engineer against current standards and project-specific requirements before use for design,
    construction, or compliance purposes. See the Data Sources tab for the standard/reference behind each
    calculation.</div>
</body></html>"""

    # On-screen preview (what you see while working in the app) - this is
    # NOT what gets printed any more; the button below opens a completely
    # separate, clean document instead.
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

    if totals_line_plain:
        st.markdown(f"**TOTALS \u2014 {totals_line_plain}**")
    else:
        st.warning("No sections selected above - tick at least one to see results here and in the printed output.")

    # The button opens print_document in a brand new window and prints
    # THAT window - completely separate from this page, so the sidebar,
    # Streamlit's own chrome, and the on-screen table above genuinely
    # cannot appear in the output, unlike the previous CSS-visibility
    # approach which left them all sharing one page.
    import json
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
    st.caption(
        "Opens a separate, clean print window containing only the results (no sidebar, no app chrome) "
        "and triggers your browser's print dialog there \u2014 choose 'Save as PDF' as the destination to "
        "get a PDF instead of printing to paper. If your browser blocks the pop-up, allow pop-ups for "
        "this site and click the button again."
    )

# =====================================================================
# TAB 9: Data Sources - an audit trail showing exactly which standard/
# guide/table/equation each calculation or default value in this app is
# drawn from, so a reviewing engineer can trace any figure back to its
# origin rather than take it on trust.
# =====================================================================
with tab_sources:
    st.error(
        "**This platform is a calculation aid only. It does not hold, assume, or transfer any design "
        "liability, and its outputs do not constitute professional engineering advice or approval.** "
        "Every figure, formula, and default value shown anywhere in this app must be independently "
        "checked and verified by a suitably qualified and experienced engineer against the current "
        "relevant standards and the specific project's actual requirements before being relied upon "
        "for design, construction, or compliance purposes. Anyone using this tool - whether inside or "
        "outside the organisation that built it - is responsible for that verification themselves; use "
        "of this platform does not discharge that responsibility, and no warranty is given as to the "
        "accuracy, completeness, or fitness for purpose of any result it produces."
    )
    st.caption(
        "Where every calculation method and default figure in this app actually comes from - "
        "chapter/table/equation references, not just a standard name."
    )
    sources_data = [
        {
            "Calculation / Data": "Cold Water Loading Units",
            "Standard / Guide": "BS EN 806-3",
            "Specific Reference": "Table 2 (Draw-off flow-rates)",
            "Used In": "Water Services tab",
            "Notes": "Exact published figures per fixture type, confirmed against the user's own copy of the table.",
        },
        {
            "Calculation / Data": "Cold water storage sizing & Legionella turnover",
            "Standard / Guide": "BS 8558 / HSE ACOP L8",
            "Specific Reference": "Section 8 (storage & turnover guidance)",
            "Used In": "Water Services tab",
            "Notes": "Turnover \u2264 24 hrs target; storage duration and demand rate are editable inputs.",
        },
        {
            "Calculation / Data": "Design Flow Rate (from Loading Units)",
            "Standard / Guide": "BS EN 806-3",
            "Specific Reference": "Annex A empirical curve-fit: Q = 0.032 \u00d7 \u221ATotal LU",
            "Used In": "Water Services tab",
            "Notes": "Simplified curve-fit - verify against the full Annex A graph for LU totals above ~300.",
        },
        {
            "Calculation / Data": "Moisture content / saturated vapour pressure",
            "Standard / Guide": "CIBSE Guide C (2007)",
            "Specific Reference": "Chapter 1, Equations 1.3, 1.5, 1.6",
            "Used In": "HVAC infiltration latent gain; Psychrometric Chart",
            "Notes": "Verified against published steam table reference values (24\u00b0C: 2.983 kPa calculated vs "
                     "~2.985 kPa published). Enhancement factor fs simplified to 1.0 rather than Guide C's full table.",
        },
        {
            "Calculation / Data": "Occupancy sensible/latent heat gain",
            "Standard / Guide": "CIBSE Guide A",
            "Specific Reference": "Table 6.3 (indicative, light/seated office work)",
            "Used In": "HVAC & FCU Selection tab",
            "Notes": "Adjust for activity level (e.g. higher for gyms/kitchens) per the current edition.",
        },
        {
            "Calculation / Data": "Solar gain (intensity by city/orientation, glazing g-values)",
            "Standard / Guide": "CIBSE Guide A",
            "Specific Reference": "Section 5 (solar cooling load data) - simplified/indicative",
            "Used In": "HVAC & FCU Selection tab",
            "Notes": "A peak-condition simplification, not time/month-resolved - use full Guide A tables or "
                     "dynamic simulation for critical or heavily-glazed spaces.",
        },
        {
            "Calculation / Data": "Minimum ventilation rates (ACH by room type)",
            "Standard / Guide": "Building Regulations Part F / CIBSE Guide B",
            "Specific Reference": "Table 1.1-1.4 (Part F) / Table 2.1, 2.25 (Guide B) - indicative",
            "Used In": "Ventilation tab",
            "Notes": "WC/Washroom, Changing Room, Kitchenette set to 10 ACH per this project's own design "
                     "criteria - confirm remaining rates against the current edition for the specific use class.",
        },
        {
            "Calculation / Data": "Duct sizing (Equal Friction Method)",
            "Standard / Guide": "Simplified Darcy-Weisbach approximation",
            "Specific Reference": "Not CIBSE Guide C Chapter 4 data",
            "Used In": "Ventilation tab",
            "Notes": "A non-iterative approximation of the Colebrook-White-based method - straight-duct "
                     "friction only. See the separate Duct Fitting Loss Calculator for fittings/bends/tees.",
        },
        {
            "Calculation / Data": "Duct fitting pressure loss (bends, dampers, tees)",
            "Standard / Guide": "CIBSE Guide C (2007)",
            "Specific Reference": "Chapter 4, Section 4.11, Tables 4.41, 4.42, 4.109, 4.126",
            "Used In": "Ventilation tab \u2014 Duct Fitting Loss Calculator",
            "Notes": "Representative single \u03b6 (zeta) figures picked from tables that vary by diameter/"
                     "aspect ratio/Reynolds number in the full Guide - confirm the exact figure against the "
                     "specific table for anything beyond a first-pass estimate.",
        },
        {
            "Calculation / Data": "Winter fabric & infiltration heat loss",
            "Standard / Guide": "Standard steady-state method (Q = U\u00d7A\u00d7\u0394T + 0.33\u00d7ACH\u00d7V\u00d7\u0394T)",
            "Specific Reference": "General engineering practice, not a single cited standard",
            "Used In": "Heat Load (Winter) tab",
            "Notes": "Winter external design temp is a CIBSE Guide A indicative UK figure - confirm against "
                     "actual weather data/DSY for the project location.",
        },
        {
            "Calculation / Data": "Default fabric U-values",
            "Standard / Guide": "Approved Document L 2021 (England, dwellings, Volume 1)",
            "Specific Reference": "New-build backstop (limiting) U-values",
            "Used In": "Heat Load (Winter) tab",
            "Notes": "NOT from CIBSE Guide C. Non-domestic buildings (Volume 2) have separate figures; "
                     "England/Wales/Scotland/NI each have their own Approved Document - confirm before relying "
                     "on these for actual compliance. Fully editable per element per room.",
        },
        {
            "Calculation / Data": "FCU / indoor unit catalogue (48 models)",
            "Standard / Guide": "Manufacturer published data",
            "Specific Reference": "Daikin FXSQ/FXFQ/FXZQ and Mitsubishi Electric PEFY/PLFY ranges",
            "Used In": "HVAC & FCU Selection tab",
            "Notes": "Real catalogue figures, not estimated - confirm against current manufacturer selection "
                     "software before procurement, as catalogue ranges are periodically revised.",
        },
    ]
    st.dataframe(pd.DataFrame(sources_data), use_container_width=True, hide_index=True)
    st.caption(
        "This table itself is maintained by hand alongside the code - if a calculation changes, this "
        "should be updated to match. Treat it as a map of where to look, not a substitute for reading "
        "the actual code comments, which go into more detail on each item's exact derivation."
    )

# =====================================================================
# TAB 10: Export
# =====================================================================
with tab_export:
    st.caption("Generates a Room Schedule + HVAC Summary workbook from everything currently entered.")
    excel_buffer = excel_export.build_export_workbook(st.session_state.rooms)
    st.download_button(
        "\U0001F4E5 Export to Excel",
        data=excel_buffer,
        file_name="Room_Schedule_HVAC_Export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    with st.expander("What's simplified in this prototype (read before relying on results)"):
        st.markdown("""
- Moisture content difference now uses the real CIBSE Guide C (Chapter 1) formula, verified against
  published steam table reference values - no longer a hardcoded placeholder.
- Occupancy is shared between the HVAC and Ventilation calculations here, whereas the Excel
  workbook keeps them independent per tab for extra flexibility - a deliberate simplification.
- Water Services covers cold water Loading Units and storage sizing (BS EN 806-3 / BS 8558) only -
  foul drainage Discharge Units (BS EN 12056-2) and the pipe capacity schedule aren't ported.
- Heat Load (Winter) uses simple area + U-value per fabric element per room, not full wall-by-wall
  geometry - and does not yet include duct/pipe fitting pressure losses (CIBSE Guide C Chapter 4.11)
  or fabric elements beyond Wall/Window/Door/Roof/Ground Floor.
- Default U-values are Approved Document Part L 2021 (England, dwellings) backstop figures - not
  CIBSE Guide C data, and not necessarily correct for this building's actual classification/location.
- Air Terminals & Dampers (grilles, diffusers, louvres, volume control dampers) isn't ported yet.
- This is single-user, in-memory only - stopping the app loses anything not yet exported.
        """)
