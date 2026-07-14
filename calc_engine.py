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
import math
import reference_data as ref


def saturated_vapour_pressure_kpa(theta_c: float) -> float:
    """CIBSE Guide C (2007), Chapter 1, Equation 1.3 - saturated vapour
    pressure over WATER at temperature theta_c (degC), valid for
    theta_c >= 0degC. Uploaded directly from the actual Guide C text,
    replacing the earlier ASHRAE-based approximation used before this."""
    T = theta_c + 273.16
    log_ps = 30.59051 - 8.2 * math.log10(T) + 2.4804e-3 * T - 3142.31 / T
    return 10 ** log_ps


def moisture_content_kgkg(theta_c: float, percentage_saturation: float,
                           pressure_kpa: float = 101.325, fs: float = 1.0) -> float:
    """CIBSE Guide C, Chapter 1, Equations 1.5 and 1.6 - moisture content
    (kg water / kg dry air) of moist air at a given dry-bulb temperature
    and percentage saturation. fs is Guide C's enhancement factor -
    Guide C tabulates this precisely (very close to 1.00-1.01 across
    normal comfort/UK design ranges); left at 1.0 here as a defensible
    simplification rather than transcribing that full table - confirm
    against the actual Guide C Table 1.1 correction if precision beyond
    the 3rd decimal place matters for a specific calculation.
    """
    ps = saturated_vapour_pressure_kpa(theta_c)
    gs = 0.62197 * fs * ps / (pressure_kpa - fs * ps)  # saturated moisture content, Eq 1.5
    return percentage_saturation / 100.0 * gs  # Eq 1.6 rearranged for unsaturated moist air


def moisture_content_difference_gkg(
    external_dbt_c: float = None, external_rh_pct: float = None,
    internal_dbt_c: float = None, internal_rh_pct: float = None,
) -> float:
    """External minus internal moisture content (g/kg dry air), using the
    real CIBSE Guide C formula above instead of a fixed placeholder -
    drives the infiltration latent gain calculation. Defaults to this
    project's design conditions if not given explicitly."""
    external_dbt_c = external_dbt_c if external_dbt_c is not None else ref.EXTERNAL_DRYBULB_C
    external_rh_pct = external_rh_pct if external_rh_pct is not None else ref.EXTERNAL_RH_PCT
    internal_dbt_c = internal_dbt_c if internal_dbt_c is not None else ref.INTERNAL_DRYBULB_C
    internal_rh_pct = internal_rh_pct if internal_rh_pct is not None else ref.INTERNAL_RH_PCT

    g_ext = moisture_content_kgkg(external_dbt_c, external_rh_pct)
    g_int = moisture_content_kgkg(internal_dbt_c, internal_rh_pct)
    return (g_ext - g_int) * 1000.0  # kg/kg -> g/kg


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
    summer_design_temp_c (None or a number)."""
    design_temp = _safe_float(room.get("summer_design_temp_c"), ref.INTERNAL_DRYBULB_C)

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
    delta_g_gkg = moisture_content_difference_gkg()
    infiltration_latent = 3010 * infiltration_airflow * (delta_g_gkg / 1000) / 1000

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


@dataclass
class RoomWaterResult:
    loading_units: float


def _safe_float(value, default=0.0):
    """Converts value to float, treating None/blank/NaN/non-numeric as
    default instead of raising - the editable Loading Unit and fixture
    count tables can produce a None or blank cell mid-edit (e.g. while a
    user is retyping a value), and this is what threw a TypeError on the
    deployed app when a value briefly wasn't a valid number."""
    if value is None:
        return default
    try:
        f = float(value)
    except (TypeError, ValueError):
        return default
    if f != f:  # NaN check (NaN is the only float that isn't equal to itself)
        return default
    return f


def calculate_room_loading_units(room: dict, lu_values: dict = None) -> RoomWaterResult:
    """Cold water Loading Units for one room, per BS EN 806-3 - sums each
    fixture type's count x its LU value. Fixture counts live on the room
    dict as fixture_counts: a dict of {fixture_type_name: count}.
    lu_values overrides reference_data.FIXTURE_LU if given (e.g. the
    editable values from the Water Services tab) - falls back to the
    hardcoded defaults if not provided, so existing calls without this
    argument keep working unchanged."""
    lu_values = lu_values if lu_values is not None else ref.FIXTURE_LU
    fixture_counts = room.get("fixture_counts") or {}
    total_lu = sum(
        _safe_float(fixture_counts.get(fixture, 0)) * _safe_float(lu_value)
        for fixture, lu_value in lu_values.items()
    )
    return RoomWaterResult(loading_units=round(total_lu, 2))


@dataclass
class ColdWaterStorageResult:
    total_loading_units: float
    design_flow_rate_ls: float
    total_occupancy: int
    daily_demand_l: float
    avg_hourly_demand_lhr: float
    peak_flow_ls: float
    storage_duration_hrs: float
    storage_required_l: float
    selected_tank_l: "int | str"
    turnover_hrs: "float | str"
    legionella_compliant: bool


def calculate_cold_water_storage(
    total_loading_units: float, total_occupancy: int,
    daily_demand_rate_l_person_day: float = 45.0,
    storage_duration_hrs: float = 2.0,
) -> ColdWaterStorageResult:
    """Cold water storage sizing and Legionella turnover check, per BS 8558
    / HSE ACOP L8 - direct port of Section B of the Excel workbook's
    (now-removed) Public Health tab. Design Flow Rate uses the same
    BS EN 806-3 Annex A empirical curve-fit as the Loading Unit method:
    Q = 0.032 x SQRT(Total LU)."""
    import math

    design_flow_rate = 0.032 * math.sqrt(total_loading_units) if total_loading_units > 0 else 0.0
    daily_demand = total_occupancy * daily_demand_rate_l_person_day
    avg_hourly_demand = daily_demand / 24 if daily_demand else 0.0
    peak_flow = design_flow_rate  # peak design flow IS the Section A design flow rate
    storage_required = peak_flow * storage_duration_hrs * 3600

    qualifying_tanks = [t for t in ref.STANDARD_TANK_SIZES if t >= storage_required]
    selected_tank = min(qualifying_tanks) if qualifying_tanks else None
    if selected_tank is None:
        # Exceeds even the largest standard tank - report the largest as a
        # starting point, same "use multiple tanks" guidance as the Excel
        # workbook, rather than silently reporting an impossible tank size.
        selected_tank = f"Exceeds Std. Range (largest: {max(ref.STANDARD_TANK_SIZES)} L) - Use Multiple Tanks"

    if avg_hourly_demand > 0 and isinstance(selected_tank, int):
        turnover = selected_tank / avg_hourly_demand
    else:
        turnover = "-"

    compliant = isinstance(turnover, (int, float)) and turnover <= 24

    return ColdWaterStorageResult(
        total_loading_units=round(total_loading_units, 2),
        design_flow_rate_ls=round(design_flow_rate, 3),
        total_occupancy=total_occupancy,
        daily_demand_l=round(daily_demand, 1),
        avg_hourly_demand_lhr=round(avg_hourly_demand, 1),
        peak_flow_ls=round(peak_flow, 3),
        storage_duration_hrs=storage_duration_hrs,
        storage_required_l=round(storage_required, 1),
        selected_tank_l=selected_tank,
        turnover_hrs=round(turnover, 1) if isinstance(turnover, (int, float)) else turnover,
        legionella_compliant=compliant,
    )


@dataclass
class BoosterDutyResult:
    static_head_bar: float
    required_pressure_bar: float
    available_mains_pressure_bar: float
    required_boost_pressure_bar: float
    duty_flow_ls: float
    duty_flow_lmin: float
    duty_flow_m3hr: float


def calculate_booster_duty(
    design_flow_ls: float, highest_outlet_height_m: float,
    residual_pressure_bar: float, mains_pressure_bar: float,
) -> BoosterDutyResult:
    """Booster set DUTY POINT only (flow + required pressure boost) - NOT a
    manufacturer model selection, since (unlike the FCU catalogue, which is
    real client project data) there's no real booster pump catalogue here
    to select from. This is the figure an engineer would hand to a pump
    supplier for their own selection.

    Static head: 1 bar of pressure supports approximately 10.197 m of
    water column (standard conversion, g and water density at 4degC).
    Required Pressure = static head to the highest/furthest outlet +
    minimum residual pressure needed at that outlet (typically ~1.0 bar
    for most sanitary fittings/showers - confirm against manufacturer/
    fitting requirements). Friction/pipe losses are NOT modelled here
    (they depend on actual pipe routing and length) - add an allowance
    separately.
    """
    static_head_bar = highest_outlet_height_m / 10.197
    required_pressure = static_head_bar + residual_pressure_bar
    required_boost = max(0.0, required_pressure - mains_pressure_bar)

    return BoosterDutyResult(
        static_head_bar=round(static_head_bar, 2),
        required_pressure_bar=round(required_pressure, 2),
        available_mains_pressure_bar=mains_pressure_bar,
        required_boost_pressure_bar=round(required_boost, 2),
        duty_flow_ls=round(design_flow_ls, 3),
        duty_flow_lmin=round(design_flow_ls * 60, 1),
        duty_flow_m3hr=round(design_flow_ls * 3.6, 2),
    )


@dataclass
class WinterHeatLossResult:
    fabric_loss_w: float
    infiltration_loss_w: float
    total_heat_loss_w: float
    total_heat_loss_kw: float


def calculate_winter_heat_loss(room: dict, volume_m3: float, external_dbt_c: float = None) -> WinterHeatLossResult:
    """Winter fabric + infiltration heat loss for one room, steady-state
    method (Q = U.A.dT per element, summed, plus infiltration). Fabric
    elements live on the room dict as fabric_elements: a dict of
    {element_name: {"area_m2": x, "u_value": y}} for External Wall/
    Window/Door - Ground Floor and Roof instead use the room's OWN
    area_m2 (Room Schedule) automatically, since a room's ground floor
    area IS its footprint area (see reference_data.AREA_LINKED_TO_ROOM_
    SCHEDULE) - no separate area entry needed or shown for those two.

    Internal design temp uses the room's own winter_design_temp_c - a
    SEPARATE field from the summer_design_temp_c used for cooling, since
    a room can reasonably need a different setpoint for each season (this
    was a single shared field until a bug report pointed out that made no
    sense for a heating calc) - or the global default if not set.
    """
    external_dbt_c = external_dbt_c if external_dbt_c is not None else ref.WINTER_EXTERNAL_DBT_C
    internal_temp = _safe_float(room.get("winter_design_temp_c"), ref.INTERNAL_DRYBULB_C)

    delta_t = internal_temp - external_dbt_c  # positive in winter (internal warmer than external)

    fabric_elements = room.get("fabric_elements") or {}
    fabric_loss = 0.0
    for element_name, default_u in ref.DEFAULT_U_VALUES.items():
        element_data = fabric_elements.get(element_name, {})
        if element_name in ref.AREA_LINKED_TO_ROOM_SCHEDULE:
            area = _safe_float(room.get("area_m2"))
        else:
            area = _safe_float(element_data.get("area_m2"))
        u_value = _safe_float(element_data.get("u_value"), default_u)
        fabric_loss += u_value * area * delta_t

    infiltration_ach = _safe_float(room.get("infiltration_ach"))
    # Standard infiltration heat loss formula: Q (W) = 0.33 x ACH x Volume x dT
    # (0.33 = specific heat capacity of air x density / 3600, the common
    # simplified constant used for infiltration/ventilation heat loss).
    infiltration_loss = 0.33 * infiltration_ach * volume_m3 * delta_t

    total_w = fabric_loss + infiltration_loss
    return WinterHeatLossResult(
        fabric_loss_w=round(fabric_loss, 1),
        infiltration_loss_w=round(infiltration_loss, 1),
        total_heat_loss_w=round(total_w, 1),
        total_heat_loss_kw=round(total_w / 1000, 3),
    )


@dataclass
class DuctFittingLossResult:
    velocity_ms: float
    velocity_pressure_pa: float
    total_zeta: float
    total_pressure_loss_pa: float


def calculate_duct_fitting_losses(airflow_ls: float, duct_diameter_mm: float,
                                   fittings: dict, air_density_kgm3: float = None) -> DuctFittingLossResult:
    """Duct fitting (component) pressure loss, per CIBSE Guide C Chapter 4:
    dP (Pa) = zeta x Pv, where Pv is the velocity pressure (Pa) and zeta
    is the fitting's dimensionless loss factor (reference_data.DUCT_
    FITTING_ZETA). fittings is a dict of {fitting_name: quantity} - each
    fitting's zeta is multiplied by its quantity and summed, then applied
    against the single velocity pressure for the given airflow/diameter
    (i.e. assumes all fittings sit in the same duct size - for a run with
    fittings at different diameters, calculate each size's run segment
    separately and add the results together).
    """
    air_density_kgm3 = air_density_kgm3 if air_density_kgm3 is not None else ref.AIR_DENSITY_KGM3
    area_m2 = math.pi * (duct_diameter_mm / 1000 / 2) ** 2
    velocity = (airflow_ls / 1000) / area_m2 if area_m2 > 0 else 0.0
    velocity_pressure = 0.5 * air_density_kgm3 * velocity ** 2

    total_zeta = 0.0
    for fitting_name, qty in fittings.items():
        zeta = ref.DUCT_FITTING_ZETA.get(fitting_name, 0.0)
        total_zeta += zeta * _safe_float(qty)

    total_loss = total_zeta * velocity_pressure

    return DuctFittingLossResult(
        velocity_ms=round(velocity, 2),
        velocity_pressure_pa=round(velocity_pressure, 2),
        total_zeta=round(total_zeta, 3),
        total_pressure_loss_pa=round(total_loss, 1),
    )


def moist_air_enthalpy_kjkg(theta_c: float, moisture_content_kgkg_value: float) -> float:
    """Standard moist air specific enthalpy (kJ/kg dry air):
    h = 1.006 x theta + g x (2501 + 1.86 x theta). Consistent with the
    CIBSE Guide C moisture content calculation above (same underlying
    psychrometric basis) - used for the Psychrometric Chart's detail
    table, not currently used in any load calculation."""
    return 1.006 * theta_c + moisture_content_kgkg_value * (2501 + 1.86 * theta_c)


def calculate_straight_duct_friction_rate(airflow_ls: float, diameter_mm: float) -> float:
    """Inverse of select_duct_size()'s formula - given a KNOWN duct diameter
    and airflow, returns the resulting friction rate (Pa/m), instead of
    solving for the diameter needed to hit a target rate. Same simplified
    Darcy-Weisbach basis, so it's mathematically consistent with the
    Ventilation tab's duct sizing calculation (round-trips through
    select_duct_size to the same rate, given the same diameter back)."""
    if diameter_mm <= 0:
        return 0.0
    Q = airflow_ls / 1000  # m3/s
    D_m = diameter_mm / 1000
    return (0.020 * 1.2 * 8 * Q ** 2) / ((math.pi ** 2) * (D_m ** 5))
