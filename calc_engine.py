"""
HVAC heat gain + FCU selection calculations - direct port of the formulas
in build_hvac_sheet() from generate_mep_workbook.py (columns O-AI), same
methodology as the FastAPI prototype's calc_engine.py. Operates on plain
dicts here (a DataFrame row as a dict) rather than SQLAlchemy models, since
Streamlit works naturally with dicts/DataFrames rather than an ORM.

These formulas were cross-checked against the real Excel workbook
(recalculated in LibreOffice) during development - Reception (RG-01) with
default inputs gives 1.554 kW sensible / 0.304 kW latent / 1.859 kW total,
an exact match to the Excel version.
"""
from dataclasses import dataclass, asdict
import reference_data as ref


@dataclass
class HeatGainResult:
    volume_m3: float
    infiltration_airflow_ls: float
    occ_sensible_kw: float
    occ_latent_kw: float
    lighting_kw: float
    small_power_kw: float
    solar_gain_kw: float
    infiltration_sensible_kw: float
    infiltration_latent_kw: float
    total_sensible_kw: float
    total_latent_kw: float
    total_cooling_load_kw: float
    design_temp_c: float

    def as_dict(self):
        return asdict(self)


def calculate_heat_gains(room: dict) -> HeatGainResult:
    """room is a dict with keys: area_m2, ceiling_height_m, occupancy,
    sensible_w_person, latent_w_person, lighting_wm2, small_power_wm2,
    infiltration_ach, glazing_area_m2, glazing_type, city, orientation,
    design_temp_c (None or a number)."""
    design_temp = room.get("design_temp_c")
    if design_temp is None or design_temp == "":
        design_temp = ref.INTERNAL_DRYBULB_C
    else:
        design_temp = float(design_temp)

    area = float(room.get("area_m2") or 0)
    height = float(room.get("ceiling_height_m") or 0)
    volume = area * height
    infiltration_ach = float(room.get("infiltration_ach") or 0)
    infiltration_airflow = volume * infiltration_ach / 3.6

    occupancy = float(room.get("occupancy") or 0)
    sensible_w_person = float(room.get("sensible_w_person") or 0)
    latent_w_person = float(room.get("latent_w_person") or 0)
    occ_sensible = occupancy * sensible_w_person / 1000
    occ_latent = occupancy * latent_w_person / 1000

    lighting_wm2 = float(room.get("lighting_wm2") or 0)
    small_power_wm2 = float(room.get("small_power_wm2") or 0)
    lighting = area * lighting_wm2 / 1000
    small_power = area * small_power_wm2 / 1000

    city_data = ref.CITIES.get(room.get("city"), {})
    solar_intensity = city_data.get(room.get("orientation"), 0)
    g_value = ref.GLAZING_TYPES.get(room.get("glazing_type"), 0)
    glazing_area = float(room.get("glazing_area_m2") or 0)
    solar_gain = glazing_area * g_value * solar_intensity / 1000

    infiltration_sensible = 1.21 * infiltration_airflow * (ref.EXTERNAL_DRYBULB_C - design_temp) / 1000
    infiltration_latent = 3010 * infiltration_airflow * (ref.DEFAULT_DELTA_G_GKG / 1000) / 1000

    total_sensible = occ_sensible + lighting + small_power + solar_gain + infiltration_sensible
    total_latent = occ_latent + infiltration_latent
    total_cooling_load = total_sensible + total_latent

    return HeatGainResult(
        volume_m3=round(volume, 2),
        infiltration_airflow_ls=round(infiltration_airflow, 2),
        occ_sensible_kw=round(occ_sensible, 3),
        occ_latent_kw=round(occ_latent, 3),
        lighting_kw=round(lighting, 3),
        small_power_kw=round(small_power, 3),
        solar_gain_kw=round(solar_gain, 3),
        infiltration_sensible_kw=round(infiltration_sensible, 3),
        infiltration_latent_kw=round(infiltration_latent, 3),
        total_sensible_kw=round(total_sensible, 3),
        total_latent_kw=round(total_latent, 3),
        total_cooling_load_kw=round(total_cooling_load, 3),
        design_temp_c=design_temp,
    )


@dataclass
class VentilationResult:
    airflow_by_occupancy_ls: float
    ach_requirement: float
    airflow_by_ach_ls: float
    required_design_airflow_ls: float
    calculated_diameter_mm: float
    selected_duct_size_mm: "int | str"


def calculate_ventilation(room: dict, volume_m3: float) -> VentilationResult:
    """Direct port of the Ventilation Design tab's per-room formulas
    (columns E-H) plus the Equal Friction Method duct sizing calculation -
    see build_ventilation_sheet() in generate_mep_workbook.py for the
    equivalent Excel formulas. Fresh air rate is 12 l/s/person per this
    project's design criteria (same as the Excel workbook)."""
    occupancy = float(room.get("occupancy") or 0)
    airflow_by_occupancy = occupancy * 12

    room_type = room.get("room_type") or "Office"
    ach_requirement = ref.ACH_BY_ROOM_TYPE.get(room_type, 0.0)
    airflow_by_ach = volume_m3 * ach_requirement / 3.6

    sizing_basis = room.get("sizing_basis") or "Stricter of Both"
    if sizing_basis == "Occupancy Only":
        required_airflow = airflow_by_occupancy
    elif sizing_basis == "ACH Only":
        required_airflow = airflow_by_ach
    else:
        required_airflow = max(airflow_by_occupancy, airflow_by_ach)

    diameter_mm, selected_size = select_duct_size(required_airflow)

    return VentilationResult(
        airflow_by_occupancy_ls=round(airflow_by_occupancy, 2),
        ach_requirement=ach_requirement,
        airflow_by_ach_ls=round(airflow_by_ach, 2),
        required_design_airflow_ls=round(required_airflow, 2),
        calculated_diameter_mm=round(diameter_mm, 1),
        selected_duct_size_mm=selected_size,
    )


def select_duct_size(required_airflow_ls: float, target_friction_pam: float = 1.0):
    """Equal Friction Method, same simplified Darcy-Weisbach-based formula
    as the Ventilation Design tab's duct sizing calculation: diameter (mm)
    solved directly at the target friction rate, then rounded UP to the
    smallest standard size that meets or exceeds it."""
    import math
    if required_airflow_ls <= 0:
        return 0.0, ref.STANDARD_DUCT_SIZES[0]
    diameter_mm = (
        0.020 * 1.2 * 8 * ((required_airflow_ls / 1000) ** 2)
        / ((math.pi ** 2) * target_friction_pam)
    ) ** (1 / 5) * 1000
    selected = next((s for s in ref.STANDARD_DUCT_SIZES if s >= diameter_mm), "Exceeds Std. Range")
    return diameter_mm, selected


@dataclass
class FCUSelectionResult:
    selected_model: str
    capacity_kw: float
    sensible_kw: float
    airflow_ls: float
    total_installed_kw: float
    meets_load: bool


def select_fcu(total_cooling_load_kw: float, manufacturer: str, unit_type: str,
               quantity: int, catalogue: list) -> "FCUSelectionResult | None":
    """Round-up match on the smallest catalogue unit whose Total Cooling
    capacity still meets or exceeds the PER-UNIT target load (Total
    Cooling Load / Quantity) - same MATCH(target, capacities, -1) semantics
    as the Excel version. catalogue is a list of dicts with keys:
    manufacturer, unit_type, model, total_kw, sensible_kw, airflow_ls."""
    quantity = max(int(quantity or 1), 1)
    per_unit_load = total_cooling_load_kw / quantity

    candidates = [
        m for m in catalogue
        if m["manufacturer"] == manufacturer and m["unit_type"] == unit_type
    ]
    if not candidates:
        return None

    candidates.sort(key=lambda m: m["total_kw"])
    chosen = next((m for m in candidates if m["total_kw"] >= per_unit_load), None)
    if chosen is None:
        return None  # no catalogue unit big enough - "No Suitable Unit" in the Excel version

    total_installed = quantity * chosen["total_kw"]
    return FCUSelectionResult(
        selected_model=chosen["model"],
        capacity_kw=chosen["total_kw"],
        sensible_kw=chosen["sensible_kw"],
        airflow_ls=chosen["airflow_ls"],
        total_installed_kw=round(total_installed, 2),
        meets_load=total_installed >= total_cooling_load_kw,
    )
