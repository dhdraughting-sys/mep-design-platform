"""
Background reference data - ported EXACTLY (same figures, not re-derived)
from the Reference Data tab in generate_mep_workbook.py, so this app's
numbers are identical to the Excel workbook's, not an abridged subset.
"""

# ---- UK city solar design data - identical to the Excel workbook's CITIES
# list, full 8-point compass + Horizontal. ----
_CITIES_RAW = [
    ("London", 51.5, 130, 255, 380, 425, 470, 425, 380, 255, 750),
    ("Bristol", 51.5, 128, 252, 375, 420, 465, 420, 375, 252, 745),
    ("Birmingham", 52.5, 125, 245, 365, 408, 450, 408, 365, 245, 725),
    ("Coventry", 52.4, 125, 246, 366, 409, 451, 409, 366, 246, 726),
    ("Cardiff", 51.5, 128, 252, 375, 419, 462, 419, 375, 252, 742),
    ("Leeds", 53.8, 120, 238, 355, 395, 435, 395, 355, 238, 705),
    ("Manchester", 53.5, 121, 240, 358, 398, 438, 398, 358, 240, 710),
    ("Newcastle", 55.0, 115, 230, 345, 383, 420, 383, 345, 230, 685),
    ("Belfast", 54.6, 116, 232, 348, 386, 424, 386, 348, 232, 690),
    ("Glasgow", 55.9, 112, 225, 338, 374, 410, 374, 338, 225, 670),
    ("Edinburgh", 55.9, 112, 226, 340, 376, 412, 376, 340, 226, 672),
]
ORIENTATIONS = ["North", "North East", "East", "South East", "South",
                "South West", "West", "North West", "Horizontal"]
CITIES = {
    city: dict(zip(ORIENTATIONS, values))
    for city, lat, *values in _CITIES_RAW
}
CITY_LATITUDES = {city: lat for city, lat, *values in _CITIES_RAW}

# ---- Glazing type / solar gain factor (g-value), per CIBSE Guide A ----
_GLAZING_RAW = [
    ("Single - Clear", 0.76, 5.7),
    ("Single - Clear + Blind", 0.45, 5.4),
    ("Double - Clear/Clear", 0.70, 2.7),
    ("Double - Clear/Low-E", 0.55, 1.6),
    ("Double - Clear/Clear + Blind", 0.42, 2.6),
    ("Double - Clear/Blind/Clear", 0.30, 2.6),
    ("Triple - Clear/Clear/Clear", 0.60, 1.0),
    ("Triple - Clear/Clear/Low-E", 0.48, 0.8),
    ("Triple - Clear/Clear/Clear + Blind", 0.38, 1.0),
    ("Triple - Clear/Blind/Clear/Clear", 0.25, 1.0),
]
GLAZING_TYPES = {name: gval for name, gval, uval in _GLAZING_RAW}
GLAZING_U_VALUES = {name: uval for name, gval, uval in _GLAZING_RAW}

# Design & weather conditions - same project criteria as the Excel workbook.
EXTERNAL_DRYBULB_C = 31.0
INTERNAL_DRYBULB_C = 24.0
EXTERNAL_RH_PCT = 45.0
INTERNAL_RH_PCT = 50.0
ATMOS_PRESSURE_KPA = 101.325

# ---- Winter heat loss design conditions & default U-values ----
WINTER_EXTERNAL_DBT_C = -3.0

DEFAULT_U_VALUES = {
    "External Wall": 0.30,
    "Window": 1.60,
    "Door": 1.60,
    "Roof": 0.20,
    "Ground Floor": 0.25,
}
AREA_LINKED_TO_ROOM_SCHEDULE = ["Ground Floor", "Roof"]

ACH_BY_ROOM_TYPE = {
    "Office": 4.0,
    "Meeting Room": 8.0,
    "Reception": 6.0,
    "WC / Washroom": 10.0,
    "Changing Room": 10.0,
    "Kitchenette": 10.0,
    "Plant Room": 6.0,
    "Store / Storage": 1.0,
    "Circulation / Corridor": 2.0,
    "Lift Lobby": 4.0,
}
ROOM_TYPES = list(ACH_BY_ROOM_TYPE.keys())

ROOM_TYPE_DEFAULT_FIXTURES = {
    "WC / Washroom": {"WC (Dual-Flush, 6L)": 1, "Wash Hand Basin (WHB)": 1},
    "Changing Room": {"Shower": 1, "WC (Dual-Flush, 6L)": 1, "Wash Hand Basin (WHB)": 1},
    "Kitchenette": {"Kitchen Sink": 1},
}

SIZING_BASIS_OPTIONS = ["Stricter of Both", "Occupancy Only", "ACH Only"]

STANDARD_DUCT_SIZES = [100, 125, 150, 200, 250, 315, 400, 500]

DUCT_FITTING_ZETA = {
    "90\u00b0 Smooth Bend, r/d=1.5 (circular)": 0.15,
    "90\u00b0 Bend (rectangular, square duct)": 1.00,
    "45\u00b0 Smooth Bend (circular)": 0.065,
    "30\u00b0 Smooth Bend (circular)": 0.027,
    "Opposed Blade Damper, Fully Open": 0.52,
    "Tee - Branch (approx., converging flow)": 1.00,
    "Tee - Straight Through (approx.)": 0.30,
}
DUCT_FITTING_TYPES = list(DUCT_FITTING_ZETA.keys())
AIR_DENSITY_KGM3 = 1.2

# ---- Pipe sizing (LTHW / CHW tab) - CIBSE Guide C Chapter 4, Section 4.5 ----
WATER_PROPERTIES_TABLE = {
    10: (999.7, 1.3004), 20: (999.8, 1.0022), 40: (992.2, 0.6561),
    50: (988.0, 0.5506), 60: (983.2, 0.4709), 70: (977.8, 0.4091),
    80: (971.8, 0.3612), 90: (965.3, 0.3222),
}
PIPE_ROUGHNESS_MM = {"Copper": 0.0015, "Steel": 0.045, "Stainless Steel (Pressfit)": 0.0015}
COPPER_PIPE_SIZES_MM = {
    15: 13.6, 22: 20.2, 28: 26.2, 35: 33.0, 42: 40.0,
    54: 52.0, 66.7: 64.3, 76.1: 73.1, 108: 105.0, 133: 130.0,
}
STEEL_PIPE_SIZES_MM = {
    15: 15.8, 20: 21.0, 25: 26.6, 32: 35.2, 40: 41.0,
    50: 52.9, 65: 68.7, 80: 80.8, 100: 105.4, 125: 130.9, 150: 155.4,
}
STAINLESS_PRESSFIT_PIPE_SIZES_MM = dict(COPPER_PIPE_SIZES_MM)
TYPICAL_PIPE_VELOCITY_RANGES = {
    "Small bore (<15mm)": (0.0, 1.0),
    "15-50mm": (0.75, 1.15),
    ">50mm": (1.25, 3.0),
    "Heating/cooling coils": (0.5, 1.5),
}
LTHW_FLOW_RETURN_OPTIONS = {
    "Traditional (82\u00b0C / 71\u00b0C, \u0394T=11K)": (82.0, 71.0),
    "Modern Low-Temperature (80\u00b0C / 60\u00b0C, \u0394T=20K)": (80.0, 60.0),
    "Heat Pump / ASHP (50\u00b0C / 30\u00b0C, \u0394T=20K)": (50.0, 30.0),
    "Custom": None,
}
CHW_FLOW_RETURN_OPTIONS = {
    "Standard (6\u00b0C / 12\u00b0C, \u0394T=6K)": (6.0, 12.0),
    "Custom": None,
}
WATER_SPECIFIC_HEAT_KJKGK = 4.186

# ---- FCU / VRF indoor unit catalogue ----
_FCU_MEL_DUCTED = [
    ("PEFY-M20VMA-A1", 2.0, 1.9, 166), ("PEFY-M25VMA-A1", 2.5, 2.1, 166),
    ("PEFY-M32VMA-A1", 3.2, 2.6, 208), ("PEFY-M40VMA-A1", 4.0, 3.6, 316),
    ("PEFY-M50VMA-A1", 5.0, 4.8, 426), ("PEFY-M63VMA-A1", 6.4, 5.4, 436),
    ("PEFY-M80VMA-A1", 8.1, 7.2, 518), ("PEFY-M100VMA-A1", 10.0, 7.2, 616),
    ("PEFY-M125VMA-A1", 8.1, 7.2, 616),
]
_FCU_DAIKIN_DUCTED = [
    ("FXSQ15A", 1.7, 1.2, 145), ("FXSQ20A", 2.2, 1.6, 150), ("FXSQ25A", 2.8, 2.0, 150),
    ("FXSQ32A", 3.6, 2.6, 158), ("FXSQ40A", 4.5, 3.3, 250), ("FXSQ50A", 5.6, 4.1, 253),
    ("FXSQ63A", 7.1, 5.2, 350), ("FXSQ80A", 9.0, 6.5, 383), ("FXSQ100A", 11.2, 8.3, 533),
    ("FXSQ125A", 14.0, 10.2, 600), ("FXSQ140A", 16.0, 11.7, 650),
]
_FCU_MEL_CASSETTE = [
    ("PLFY-M32VEM6-E", 3.2, 3.0, None), ("PLFY-M40VEM6-E", 4.0, 3.5, None),
    ("PLFY-M50VEM6-E", 5.0, 4.6, None), ("PLFY-M63VEM6-E", 6.4, 5.8, None),
    ("PLFY-M80VEM6-E", 8.1, 6.7, None), ("PLFY-M100VEM6-E", 10.0, 7.7, None),
    ("PLFY-M125VEM6-E", 12.5, 9.1, None),
]
_FCU_DAIKIN_CASSETTE = [
    ("FXFQ20A", 2.2, 1.6, None), ("FXFQ25A", 2.8, 2.0, None), ("FXFQ32A", 3.6, 2.6, None),
    ("FXFQ40A", 4.5, 3.3, None), ("FXFQ50A", 6.5, 4.1, None), ("FXFQ63A", 7.1, 5.2, None),
    ("FXFQ80A", 9.0, 6.5, None), ("FXFQ100A", 11.2, 8.3, None), ("FXFQ125A", 14.0, 10.2, None),
]
_FCU_MEL_COMPACT = [
    ("PLFY-P15VFM-E", 1.5, 1.3, None), ("PLFY-P20VFM-E", 2.0, 1.6, None),
    ("PLFY-P25VFM-E", 2.5, 2.0, None), ("PLFY-P32VFM-E", 3.2, 2.4, None),
    ("PLFY-P40VFM-E", 4.0, 2.9, None), ("PLFY-P50VFM-E", 5.0, 3.6, None),
]
_FCU_DAIKIN_COMPACT = [
    ("FXZQ15A", 1.4, 1.3, None), ("FXZQ20A", 1.8, 1.5, None), ("FXZQ25A", 2.3, 1.8, None),
    ("FXZQ32A", 2.9, 2.1, None), ("FXZQ40A", 3.6, 2.9, None), ("FXZQ50A", 4.5, 3.6, None),
]


def _build_catalogue(manufacturer, unit_type, raw):
    return [
        {"manufacturer": manufacturer, "unit_type": unit_type, "model": model,
         "total_kw": total, "sensible_kw": sensible, "airflow_ls": airflow}
        for model, total, sensible, airflow in raw
    ]


FCU_CATALOGUE = (
    _build_catalogue("Mitsubishi Electric", "Ducted", _FCU_MEL_DUCTED)
    + _build_catalogue("Daikin", "Ducted", _FCU_DAIKIN_DUCTED)
    + _build_catalogue("Mitsubishi Electric", "Cassette", _FCU_MEL_CASSETTE)
    + _build_catalogue("Daikin", "Cassette", _FCU_DAIKIN_CASSETTE)
    + _build_catalogue("Mitsubishi Electric", "Compact Cassette", _FCU_MEL_COMPACT)
    + _build_catalogue("Daikin", "Compact Cassette", _FCU_DAIKIN_COMPACT)
)
MANUFACTURERS = ["Daikin", "Mitsubishi Electric"]
UNIT_TYPES = ["Ducted", "Cassette", "Compact Cassette"]

FIXTURE_LU = {
    "WC (Dual-Flush, 6L)": 1.0,
    "Wash Hand Basin (WHB)": 1.0,
    "Shower": 2.0,
    "Bath": 4.0,
    "Kitchen Sink": 2.0,
    "Cleaner's Sink": 8.0,
    "Bidet": 1.0,
    "Washing Machine": 2.0,
    "Dishwasher": 2.0,
    "Urinal (Cistern-fed)": 1.0,
    "Urinal (Flushometer/Valve)": 3.0,
    "Drinking Fountain / Bib Tap": 0.5,
    "Hose Union Bib Tap (Garden)": 5.0,
}
FIXTURE_TYPES = list(FIXTURE_LU.keys())

STANDARD_TANK_SIZES = [13500, 9000, 6000, 4500, 3000, 2250, 1500, 1000]