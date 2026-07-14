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

# ---- Glazing type / solar gain factor (g-value), per CIBSE Guide A -
# identical to the Excel workbook's GLAZING_TYPES list (u-value included
# for reference, though - same as the Excel version - it isn't used in any
# formula here). ----
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
# Moisture content difference (g/kg) - in the Excel version this is derived
# via psychrolib from 28C/45%RH external, 22C/50%RH internal. Hardcoded here
# as the same approximate value; swap in real psychrolib before relying on
# this for anything beyond evaluating the prototype.
DEFAULT_DELTA_G_GKG = 3.37

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
SIZING_BASIS_OPTIONS = ["Stricter of Both", "Occupancy Only", "ACH Only"]

# Standard circular duct sizes (mm), for the round-up size-selection lookup.
STANDARD_DUCT_SIZES = [100, 125, 150, 200, 250, 315, 400, 500]

# ---- FCU / VRF indoor unit catalogue - all 6 (Manufacturer, Unit Type)
# combinations, identical figures to the Excel workbook's Reference Data
# tab (extracted from the client's own project workbook). Airflow is only
# tracked for Ducted units in the source data; Cassette/Compact Cassette
# show None (not an invented figure) - same as the Excel version's
# "N/A - Not Tracked". ----
_FCU_MEL_DUCTED = [
    ("PEFY-M20VMA-A1", 2.0, 1.9, 166), ("PEFY-M25VMA-A1", 2.5, 2.1, 166),
    ("PEFY-M32VMA-A1", 3.2, 2.6, 208), ("PEFY-M40VMA-A1", 4.0, 3.6, 316),
    ("PEFY-M50VMA-A1", 5.0, 4.8, 426), ("PEFY-M63VMA-A1", 6.4, 5.4, 436),
    ("PEFY-M80VMA-A1", 8.1, 7.2, 518), ("PEFY-M100VMA-A1", 10.0, 7.2, 616),
    ("PEFY-M125VMA-A1", 8.1, 7.2, 616),  # source anomaly, see generate_mep_workbook.py's note
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
