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


# ---- Seed data (same example project as the Excel workbook) ----
SEED_ROOMS = [
    {"name": "Reception (RG-01)", "floor": "Ground", "area_m2": 46.0, "ceiling_height_m": 3.0,
     "design_temp_c": None, "occupancy": 2,
     "city": "Coventry", "orientation": "South", "glazing_area_m2": 0.0,
     "glazing_type": "Double - Clear/Clear", "sensible_w_person": 75.0, "latent_w_person": 55.0,
     "lighting_wm2": 12.0, "small_power_wm2": 15.0, "infiltration_ach": 0.5,
     "manufacturer": "Daikin", "unit_type": "Ducted", "quantity": 1,
     "room_type": "Reception", "sizing_basis": "Stricter of Both", "fixture_counts": {}},
    {"name": "Office (RF-01)", "floor": "First", "area_m2": 37.0, "ceiling_height_m": 2.7,
     "design_temp_c": None, "occupancy": 4,
     "city": "Coventry", "orientation": "South", "glazing_area_m2": 0.0,
     "glazing_type": "Double - Clear/Clear", "sensible_w_person": 75.0, "latent_w_person": 55.0,
     "lighting_wm2": 12.0, "small_power_wm2": 15.0, "infiltration_ach": 0.5,
     "manufacturer": "Daikin", "unit_type": "Ducted", "quantity": 1,
     "room_type": "Office", "sizing_basis": "Stricter of Both", "fixture_counts": {}},
    {"name": "First Floor Office (RF-11)", "floor": "First", "area_m2": 573.0, "ceiling_height_m": 2.7,
     "design_temp_c": None, "occupancy": 57,
     "city": "Coventry", "orientation": "South", "glazing_area_m2": 0.0,
     "glazing_type": "Double - Clear/Clear", "sensible_w_person": 75.0, "latent_w_person": 55.0,
     "lighting_wm2": 12.0, "small_power_wm2": 15.0, "infiltration_ach": 0.5,
     "manufacturer": "Daikin", "unit_type": "Ducted", "quantity": 3,
     "room_type": "Office", "sizing_basis": "Stricter of Both", "fixture_counts": {}},
    {"name": "Office (RS-01)", "floor": "Second", "area_m2": 36.0, "ceiling_height_m": 2.7,
     "design_temp_c": None, "occupancy": 4,
     "city": "Coventry", "orientation": "South", "glazing_area_m2": 0.0,
     "glazing_type": "Double - Clear/Clear", "sensible_w_person": 75.0, "latent_w_person": 55.0,
     "lighting_wm2": 12.0, "small_power_wm2": 15.0, "infiltration_ach": 0.5,
     "manufacturer": "Daikin", "unit_type": "Ducted", "quantity": 1,
     "room_type": "Office", "sizing_basis": "Stricter of Both", "fixture_counts": {}},
    {"name": "Second Floor Office (RS-11)", "floor": "Second", "area_m2": 572.0, "ceiling_height_m": 2.7,
     "design_temp_c": None, "occupancy": 57,
     "city": "Coventry", "orientation": "South", "glazing_area_m2": 0.0,
     "glazing_type": "Double - Clear/Clear", "sensible_w_person": 75.0, "latent_w_person": 55.0,
     "lighting_wm2": 12.0, "small_power_wm2": 15.0, "infiltration_ach": 0.5,
     "manufacturer": "Daikin", "unit_type": "Ducted", "quantity": 3,
     "room_type": "Office", "sizing_basis": "Stricter of Both", "fixture_counts": {}},
]

if "rooms" not in st.session_state:
    st.session_state.rooms = [dict(r) for r in SEED_ROOMS]


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
    schedule_fields = ["floor", "area_m2", "ceiling_height_m", "design_temp_c"]
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


tab_schedule, tab_hvac, tab_vent, tab_water, tab_heatload, tab_print, tab_sources, tab_export = st.tabs(
    ["\U0001F4CB Room Schedule", "\u2744\ufe0f HVAC & FCU Selection", "\U0001F4A8 Ventilation",
     "\U0001F6B0 Water Services", "\U0001F525 Heat Load (Winter)",
     "\U0001F5A8\ufe0f Print Summary", "\U0001F4DA Data Sources", "\U0001F4E5 Export"]
)

# =====================================================================
# TAB 1: Room Schedule - the master list. Add/remove rooms here only.
# =====================================================================
with tab_schedule:
    st.caption("The master room list \u2014 add or remove rooms here. They then become available "
               "on the HVAC and Ventilation tabs automatically.")
    schedule_df = pd.DataFrame([
        {"name": r["name"], "floor": r.get("floor", ""), "area_m2": r.get("area_m2", 0.0),
         "ceiling_height_m": r.get("ceiling_height_m", 2.7), "design_temp_c": r.get("design_temp_c")}
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
            "design_temp_c": st.column_config.NumberColumn(
                "Design Temp (\u00b0C)", format="%.1f", help="Leave blank to use the 24\u00b0C global default"
            ),
            "volume_m3": st.column_config.NumberColumn("Volume (m\u00b3)", format="%.1f", disabled=True),
        },
        key="schedule_editor",
    )
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
                "infiltration_ach": st.column_config.NumberColumn("Infiltration (ACH)", format="%.2f"),
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
        with st.expander(f"{element} (default U-value: {ref.DEFAULT_U_VALUES[element]} W/m\u00b2K)"):
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
# TAB 6: Print Summary - a clean, printable results page. Room Schedule/
# HVAC/Ventilation/Water/Heat Load each have their own working tabs with
# full input columns; this tab is deliberately read-only and combines
# just the final figures, the way the Excel workbook's "Results Summary
# (Print)" tab does.
# =====================================================================
with tab_print:
    st.caption("A clean, combined results page for printing or saving as PDF (Ctrl+P / Cmd+P, or the "
               "button below). Only final results are shown here \u2014 edit inputs on the other tabs. "
               "Fill in Project Details and a logo in the sidebar \u2190 to complete the title block below.")

    proj = st.session_state.project_details
    all_results = compute_all()
    summary_rows = []
    total_lu_by_room = {}
    for room in st.session_state.rooms:
        water = calc_engine.calculate_room_loading_units(room, st.session_state.get("fixture_lu_values"))
        total_lu_by_room[room["name"]] = water.loading_units

    for room, gains, vent, fcu in all_results:
        summary_rows.append({
            "Room Name": room["name"],
            "Floor": room.get("floor", ""),
            "Area (m\u00b2)": room.get("area_m2"),
            "Volume (m\u00b3)": gains.volume_m3,
            "Sensible (kW)": gains.total_sensible_kw,
            "Latent (kW)": gains.total_latent_kw,
            "Total Load (kW)": gains.total_cooling_load_kw,
            "Selected FCU": fcu.selected_model if fcu else "No Suitable Unit",
            "Load Status": ("PASS" if fcu.meets_load else "REVIEW") if fcu else "-",
            "Required Airflow (l/s)": vent.required_design_airflow_ls,
            "Duct Size (mm)": vent.selected_duct_size_mm,
            "Loading Units (LU)": total_lu_by_room.get(room["name"], 0.0),
        })
    summary_df = pd.DataFrame(summary_rows)
    totals = summary_df[["Sensible (kW)", "Latent (kW)", "Total Load (kW)", "Loading Units (LU)"]].sum()

    # Build a FULLY SELF-CONTAINED print document (its own <html><head>
    # etc., not a div appended to the current page). This is what actually
    # fixes both bugs from the screenshot: it opens in a brand new browser
    # window/tab that contains ONLY this content, so there is no sidebar,
    # no Streamlit chrome, and no duplicate on-screen table to leak into
    # it - none of that exists in this document at all.
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

    print_document = f"""<!DOCTYPE html>
<html><head><title>MEP Results Summary</title>
<style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; padding: 24px; color: #1B1B1B; }}
    h2 {{ color: #1B365D; margin-bottom: 0; }}
    p {{ color: #555; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 12px; }}
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
    {summary_df.to_html(index=False, border=0)}
    <p><b>TOTALS \u2014 Sensible: {totals['Sensible (kW)']:.2f} kW &middot;
    Latent: {totals['Latent (kW)']:.2f} kW &middot;
    Total Cooling Load: {totals['Total Load (kW)']:.2f} kW &middot;
    Total Loading Units: {totals['Loading Units (LU)']:.1f} LU</b></p>
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

    st.dataframe(summary_df, use_container_width=True, hide_index=True)
    st.markdown(
        f"**TOTALS \u2014 Sensible: {totals['Sensible (kW)']:.2f} kW \u00b7 "
        f"Latent: {totals['Latent (kW)']:.2f} kW \u00b7 "
        f"Total Cooling Load: {totals['Total Load (kW)']:.2f} kW \u00b7 "
        f"Total Loading Units: {totals['Loading Units (LU)']:.1f} LU**"
    )

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

    st.divider()
    st.subheader("Psychrometric Chart")
    st.caption(
        "Saturation curve and constant-RH lines computed from the real CIBSE Guide C formula (Chapter "
        "1, Equation 1.3) used elsewhere in this app - marks the selected room's Internal Design point "
        "against the project's External Design point."
    )
    room_names_for_chart = [r["name"] for r in st.session_state.rooms if r.get("name")]
    if room_names_for_chart:
        selected_room_name = st.selectbox("Room", room_names_for_chart, key="psychro_room_select")
        selected_room = next(r for r in st.session_state.rooms if r["name"] == selected_room_name)
        chart_png = psychro_chart.build_psychrometric_chart(selected_room)
        st.image(chart_png, use_container_width=True)
        st.download_button(
            "\U0001F4E5 Download Chart as PNG",
            data=chart_png,
            file_name=f"Psychrometric_Chart_{selected_room_name.replace(' ', '_')}.png",
            mime="image/png",
        )

# =====================================================================
# TAB 7: Export
# =====================================================================
# =====================================================================
# TAB 7: Data Sources - an audit trail showing exactly which standard/
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
            "Specific Reference": "Not yet CIBSE Guide C Chapter 4 data",
            "Used In": "Ventilation tab",
            "Notes": "A non-iterative approximation of the Colebrook-White-based method - CIBSE Guide C "
                     "Chapter 4 fitting/component loss factors (uploaded) not yet incorporated into this "
                     "calculation; currently covers straight-duct friction only, not fittings/bends/tees.",
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
# TAB 8: Export
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
