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
import pandas as pd

import calc_engine
import reference_data as ref
import excel_export

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
</style>
""", unsafe_allow_html=True)

st.title("MEP Design Platform \u2014 prototype")

# ---- Seed data (same example project as the Excel workbook) ----
SEED_ROOMS = [
    {"name": "Reception (RG-01)", "floor": "Ground", "area_m2": 46.0, "ceiling_height_m": 3.0,
     "design_temp_c": None, "occupancy": 2,
     "city": "Coventry", "orientation": "South", "glazing_area_m2": 0.0,
     "glazing_type": "Double - Clear/Clear", "sensible_w_person": 75.0, "latent_w_person": 55.0,
     "lighting_wm2": 12.0, "small_power_wm2": 15.0, "infiltration_ach": 0.5,
     "manufacturer": "Daikin", "unit_type": "Ducted", "quantity": 1,
     "room_type": "Reception", "sizing_basis": "Stricter of Both"},
    {"name": "Office (RF-01)", "floor": "First", "area_m2": 37.0, "ceiling_height_m": 2.7,
     "design_temp_c": None, "occupancy": 4,
     "city": "Coventry", "orientation": "South", "glazing_area_m2": 0.0,
     "glazing_type": "Double - Clear/Clear", "sensible_w_person": 75.0, "latent_w_person": 55.0,
     "lighting_wm2": 12.0, "small_power_wm2": 15.0, "infiltration_ach": 0.5,
     "manufacturer": "Daikin", "unit_type": "Ducted", "quantity": 1,
     "room_type": "Office", "sizing_basis": "Stricter of Both"},
    {"name": "First Floor Office (RF-11)", "floor": "First", "area_m2": 573.0, "ceiling_height_m": 2.7,
     "design_temp_c": None, "occupancy": 57,
     "city": "Coventry", "orientation": "South", "glazing_area_m2": 0.0,
     "glazing_type": "Double - Clear/Clear", "sensible_w_person": 75.0, "latent_w_person": 55.0,
     "lighting_wm2": 12.0, "small_power_wm2": 15.0, "infiltration_ach": 0.5,
     "manufacturer": "Daikin", "unit_type": "Ducted", "quantity": 3,
     "room_type": "Office", "sizing_basis": "Stricter of Both"},
    {"name": "Office (RS-01)", "floor": "Second", "area_m2": 36.0, "ceiling_height_m": 2.7,
     "design_temp_c": None, "occupancy": 4,
     "city": "Coventry", "orientation": "South", "glazing_area_m2": 0.0,
     "glazing_type": "Double - Clear/Clear", "sensible_w_person": 75.0, "latent_w_person": 55.0,
     "lighting_wm2": 12.0, "small_power_wm2": 15.0, "infiltration_ach": 0.5,
     "manufacturer": "Daikin", "unit_type": "Ducted", "quantity": 1,
     "room_type": "Office", "sizing_basis": "Stricter of Both"},
    {"name": "Second Floor Office (RS-11)", "floor": "Second", "area_m2": 572.0, "ceiling_height_m": 2.7,
     "design_temp_c": None, "occupancy": 57,
     "city": "Coventry", "orientation": "South", "glazing_area_m2": 0.0,
     "glazing_type": "Double - Clear/Clear", "sensible_w_person": 75.0, "latent_w_person": 55.0,
     "lighting_wm2": 12.0, "small_power_wm2": 15.0, "infiltration_ach": 0.5,
     "manufacturer": "Daikin", "unit_type": "Ducted", "quantity": 3,
     "room_type": "Office", "sizing_basis": "Stricter of Both"},
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
                "room_type": "Office", "sizing_basis": "Stricter of Both",
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


tab_schedule, tab_hvac, tab_vent, tab_export = st.tabs(
    ["\U0001F4CB Room Schedule", "\u2744\ufe0f HVAC & FCU Selection", "\U0001F4A8 Ventilation", "\U0001F4E5 Export"]
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
# TAB 4: Export
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
- Only a small subset of cities, glazing types, and the Daikin Ducted FCU range are included -
  expand `reference_data.py` with the full lists from `generate_mep_workbook.py`.
- `psychrolib` isn't used here - the moisture content default is a hardcoded approximation.
- Occupancy is shared between the HVAC and Ventilation calculations here, whereas the Excel
  workbook keeps them independent per tab for extra flexibility - a deliberate simplification.
- Air Terminals and the full Reference Data tab from the Excel workbook aren't ported yet.
- This is single-user, in-memory only - stopping the app loses anything not yet exported.
        """)
