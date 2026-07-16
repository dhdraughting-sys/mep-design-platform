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
EXTERNAL_RH_PCT = 45.0   # indicative coincident external RH at summer design DBT - not project-specified
INTERNAL_RH_PCT = 50.0   # typical office internal design RH (CIBSE Guide A, Table 1.5) - not project-specified
ATMOS_PRESSURE_KPA = 101.325

# ---- Winter heat loss design conditions & default U-values ----
# External winter design temp: CIBSE Guide A commonly cites -3 to -4degC
# for most of the UK (Coventry area) as a 99.6-99.7% percentile design
# condition - confirm against the specific CIBSE weather data/DSY for the
# actual project location before final design.
WINTER_EXTERNAL_DBT_C = -3.0

# Default fabric U-values (W/m2K) - Approved Document L 2021 (England)
# NEW BUILD backstop (limiting) values, i.e. the worst permitted for any
# individual element regardless of trade-offs elsewhere in the building.
# These are NOT CIBSE Guide C figures (Guide C doesn't set Building Regs
# compliance values) - sourced separately from Part L 2021 and provided
# as a sensible, editable starting point, not a locked-in standard. Part
# L for NON-DOMESTIC buildings (Volume 2) has its own notional/backstop
# figures which may differ from these (drawn from the more commonly
# published Volume 1/dwellings figures) - confirm against the specific
# Approved Document applicable to this building's actual classification
# and location (England/Wales/Scotland/NI all differ) before relying on
# these for real compliance purposes.
DEFAULT_U_VALUES = {
    "External Wall": 0.30,
    "Window": 1.60,
    "Door": 1.60,
    "Roof": 0.20,
    "Ground Floor": 0.25,
}

# These two elements' AREA is not independently entered - it's the same
# as the room's own footprint area (Room Schedule), since a room's ground
# floor area IS its plan area, and likewise for a top-floor/single-storey
# room's roof. Only their U-value is separately editable on the Heat Load
# tab. External Wall/Window/Door have no such natural default (depends on
# perimeter/height/glazing), so those keep an independently entered area.
AREA_LINKED_TO_ROOM_SCHEDULE = ["Ground Floor", "Roof"]

# Fresh air rate for occupancy-based ventilation sizing (l/s/person) -
# this project's design criteria default; editable in the app rather
# than fixed, since different projects/standards may specify a
# different rate (e.g. CIBSE Guide B / Building Regs Part F typically
# cite 10 l/s/person for offices, with 12 l/s/person also commonly used
# as a more conservative design figure).
DEFAULT_FRESH_AIR_RATE_LS_PERSON = 12.0

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
    # Printer Room: Approved Document F Volume 2 (2021), paragraph 1.25
    # specifies 20 litres per second PER MACHINE during use (for rooms
    # containing printers/photocopiers in substantial use, i.e. more
    # than 30 minutes per hour) - a per-machine flat rate, not a room
    # ACH figure at all. This placeholder ACH is NOT the correct sizing
    # method for this room type - select "Direct Airflow (l/s)" as the
    # Sizing Basis instead and enter 20 x (number of machines).
    "Printer Room": 10.0,
}
ROOM_TYPES = list(ACH_BY_ROOM_TYPE.keys())

# Sensible default fixture counts by Room Type (the same Room Type already
# selected on the Ventilation tab) - a starting point for the Water
# Services tab's fixture counts, applied via an explicit button rather
# than automatically, so a room you've already customised never gets
# silently overwritten. Room types not listed here (Office, Meeting Room,
# Reception, Plant Room, Store/Storage, Circulation/Corridor, Lift Lobby)
# default to no fixtures, same as before.
ROOM_TYPE_DEFAULT_FIXTURES = {
    "WC / Washroom": {"WC (Dual-Flush, 6L)": 1, "Wash Hand Basin (WHB)": 1},
    "Changing Room": {"Shower": 1, "WC (Dual-Flush, 6L)": 1, "Wash Hand Basin (WHB)": 1},
    "Kitchenette": {"Kitchen Sink": 1},
}
SIZING_BASIS_OPTIONS = [
    "Stricter of Both", "Occupancy Only", "ACH Only", "Direct Airflow (l/s)",
    "Natural Ventilation/Trickle - TBC by CFD",
]

# Standard circular duct sizes (mm), for the round-up size-selection lookup.
STANDARD_DUCT_SIZES = [100, 125, 150, 200, 250, 315, 400, 500]

# ---- Duct fitting pressure loss factors (zeta, dimensionless) - CIBSE
# Guide C (2007), Chapter 4 ("Flow of fluids in pipes and ducts"),
# Section 4.11 ("Pressure loss factors for ductwork components"). These
# are REPRESENTATIVE single figures picked from tables that in the full
# Guide vary by diameter, aspect ratio, and/or Reynolds number - not a
# full reproduction of those tables. Confirm the exact figure against
# the specific table for anything beyond a first-pass estimate.
DUCT_FITTING_ZETA = {
    "90\u00b0 Smooth Bend, r/d=1.5 (circular)": 0.15,   # Table 4.42, representative value across 150-250mm
    "90\u00b0 Bend (rectangular, square duct)": 1.00,     # Table 4.109, aspect ratio h/w = 1.0 case
    "45\u00b0 Smooth Bend (circular)": 0.065,             # Table 4.41, 0.347 x the 90deg r/d=1.5 value above
    "30\u00b0 Smooth Bend (circular)": 0.027,             # Table 4.41, 0.177 x the 90deg r/d=1.5 value above
    "Opposed Blade Damper, Fully Open": 0.52,             # Table 4.126, blade angle 0deg
    "Tee - Branch (approx., converging flow)": 1.00,      # Table 4.121/4.123 range, representative
    "Tee - Straight Through (approx.)": 0.30,             # Table 4.120/4.122 range, representative
}
DUCT_FITTING_TYPES = list(DUCT_FITTING_ZETA.keys())
AIR_DENSITY_KGM3 = 1.2  # standard air density at ~20degC, used for velocity pressure calc

# ---- Pipe sizing (LTHW / CHW tab) - CIBSE Guide C (2007), Chapter 4,
# Section 4.5 ("Flow of water in pipes"), using the Haaland equation
# (4.5) Guide C recommends over the iterative Colebrook-White equation
# (4.4) it replaced - "found to have a narrower band of accuracy... the
# use of equation 4.5 is recommended." Verified directly against Guide
# C's own worked example (copper R290 76.1x1.5, di=73.1mm, k=0.0015mm,
# Re=2.16x10^5 -> lambda=0.01540) before being used here.

# Water properties (density kg/m3, kinematic viscosity x1e-6 m2/s) at
# stated temperatures - CIBSE Guide C Table 4.7. Interpolated linearly
# between these points for any other temperature.
WATER_PROPERTIES_TABLE = {
    10: (999.7, 1.3004), 20: (999.8, 1.0022), 40: (992.2, 0.6561),
    50: (988.0, 0.5506), 60: (983.2, 0.4709), 70: (977.8, 0.4091),
    80: (971.8, 0.3612), 90: (965.3, 0.3222),
}

# Surface roughness, k (mm) - CIBSE Guide C Table 4.1 ("commercially
# smooth" for copper; midpoint of the "new" range for steel).
# Surface roughness, k (mm) - CIBSE Guide C Table 4.1 ("commercially
# smooth" for copper; midpoint of the "new" range for steel). Stainless
# Steel (Pressfit) is NOT a CIBSE Guide C figure - Guide C's Table 4.1
# only covers copper and steel, not press-fit stainless tube systems
# (Mapress / Conex >B< Press / Pegler Xpress etc.). Drawn stainless tube
# is manufactured to a similarly fine surface finish to copper ("bright
# annealed", commonly quoted around 1 micrometre or better) - 0.0015mm
# is used here as a reasonable engineering estimate matching that
# smoothness, NOT a cited Guide C value - confirm against the specific
# manufacturer's system data if precision matters.
PIPE_ROUGHNESS_MM = {"Copper": 0.0015, "Steel": 0.045, "Stainless Steel (Pressfit)": 0.0015}

# Copper pipe internal diameters (mm) by nominal size - CIBSE Guide C
# Table 4.3 (BS EN 1057), one representative wall thickness per size.
COPPER_PIPE_SIZES_MM = {
    15: 13.6, 22: 20.2, 28: 26.2, 35: 33.0, 42: 40.0,
    54: 52.0, 66.7: 64.3, 76.1: 73.1, 108: 105.0, 133: 130.0,
}

# Typical steel pipe sizes (nominal bore, mm) with approximate internal
# diameters (BS EN 10255, medium series) - CIBSE Guide C Table 4.2.
STEEL_PIPE_SIZES_MM = {
    15: 15.8, 20: 21.0, 25: 26.6, 32: 35.2, 40: 41.0,
    50: 52.9, 65: 68.7, 80: 80.8, 100: 105.4, 125: 130.9, 150: 155.4,
}

# Press-fit stainless steel tube sizes - NOT from CIBSE Guide C (Guide C
# doesn't cover this system type at all). Most UK press-fit stainless
# systems (Mapress, Conex >B< Press, Pegler Xpress) are dimensioned on
# the same outside-diameter range as copper tube, marketed as direct
# alternatives/compatible in the same size range - approximated here
# using the same internal diameters as the copper table above as a
# starting point, NOT actual manufacturer wall-thickness data. Confirm
# against the specific system's published internal diameter before
# relying on this for anything beyond a first-pass estimate.
STAINLESS_PRESSFIT_PIPE_SIZES_MM = dict(COPPER_PIPE_SIZES_MM)

# Typical water velocities (m/s) - CIBSE Guide C Table 4.6 (BSRIA) - a
# sense-check range shown alongside calculated velocity, not itself part
# of the calculation.
TYPICAL_PIPE_VELOCITY_RANGES = {
    "Small bore (<15mm)": (0.0, 1.0),
    "15-50mm": (0.75, 1.15),
    ">50mm": (1.25, 3.0),
    "Heating/cooling coils": (0.5, 1.5),
}

# LTHW design flow/return temperatures - BS EN 12828 sets the design
# FRAMEWORK for water-based heating systems (max 105degC, max 6 bar) but
# doesn't mandate specific flow/return temperatures - those are a project/
# heat-source decision. Traditional LTHW (82/71degC) has long been the UK
# default; modern systems (heat pumps, condensing boilers) commonly use a
# wider dT with a lower flow temp for efficiency - both offered here,
# fully editable.
LTHW_FLOW_RETURN_OPTIONS = {
    "Traditional (82\u00b0C / 71\u00b0C, \u0394T=11K)": (82.0, 71.0),
    "Modern Low-Temperature (80\u00b0C / 60\u00b0C, \u0394T=20K)": (80.0, 60.0),
    "Heat Pump / ASHP - Wide \u0394T (50\u00b0C / 30\u00b0C, \u0394T=20K)": (50.0, 30.0),
    "Heat Pump / ASHP - Radiator Retrofit (50\u00b0C / 45\u00b0C, \u0394T=5K)": (50.0, 45.0),
    "Custom": None,
}
# CHW design flow/return - 6/12degC is the long-established UK standard.
CHW_FLOW_RETURN_OPTIONS = {
    "Standard (6\u00b0C / 12\u00b0C, \u0394T=6K)": (6.0, 12.0),
    "Custom": None,
}
WATER_SPECIFIC_HEAT_KJKGK = 4.186

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

# ---- Grilles & Diffusers - rebuilt from HVC Supplies (h-v-c.com), a
# real UK manufacturer, fetched directly from their published product
# datasheets. Being precise about what's real vs calculated, since
# that distinction matters:
#
# REAL (from HVC's datasheets, not estimated):
#   - Egg Crate Grille (Extract): stocked sizes 150-555mm, free area 90%
#     - Series ECG datasheet
#   - Swirl Diffuser: SWF fixed-blade core diameters 254/356/457/535mm
#     - Series SWF/SWA datasheet
#
# NOT taken from a specific manufacturer's published range (HVC's own
# Ceiling Diffuser and Linear Slot Diffuser products are custom-sized to
# order, not fixed standard sizes) - using common suspended-ceiling tile
# module sizes instead, which is a genuine real-world constraint
# (standard grid sizes) even though the airflow figures below aren't
# HVC-specific:
#   - Ceiling Diffuser (4-way): 150/225/300/450/600mm tile modules
#   - Linear Slot Diffuser: 600/1200/1800mm tile modules
#
# CALCULATION METHOD (applied to all four types, since none of HVC's
# datasheets gave a directly-extractable numeric performance table -
# their actual performance data is presented as graphical nomogram
# charts, not text): airflow capacity = free area x a target face
# velocity for an acceptable noise level (2.0-3.0 m/s depending on type,
# a standard design guideline, not read off HVC's own charts). Swirl
# diffusers work by induction rather than simple face velocity, so that
# category's figures are a rougher approximation than the others.
#
# Confirm against the actual manufacturer's performance data before
# finalizing a design - these are early-stage sizing figures, built from
# real product sizes but a general calculation, not manufacturer-tested
# performance numbers.
GRILLE_DIFFUSER_CATALOGUE = [
    {"type": "Ceiling Diffuser (4-way)", "size": "150x150mm", "min_airflow_ls": 16, "max_airflow_ls": 45, "throw_m": 1.5, "nr_rating": 30},
    {"type": "Ceiling Diffuser (4-way)", "size": "225x225mm", "min_airflow_ls": 35, "max_airflow_ls": 101, "throw_m": 2.2, "nr_rating": 30},
    {"type": "Ceiling Diffuser (4-way)", "size": "300x300mm", "min_airflow_ls": 63, "max_airflow_ls": 180, "throw_m": 3.0, "nr_rating": 30},
    {"type": "Ceiling Diffuser (4-way)", "size": "450x450mm", "min_airflow_ls": 142, "max_airflow_ls": 405, "throw_m": 4.5, "nr_rating": 30},
    {"type": "Ceiling Diffuser (4-way)", "size": "600x600mm", "min_airflow_ls": 252, "max_airflow_ls": 720, "throw_m": 6.0, "nr_rating": 30},

    {"type": "Linear Slot Diffuser", "size": "600mm length", "min_airflow_ls": 13, "max_airflow_ls": 36, "throw_m": 2.0, "nr_rating": 30},
    {"type": "Linear Slot Diffuser", "size": "1200mm length", "min_airflow_ls": 25, "max_airflow_ls": 72, "throw_m": 4.0, "nr_rating": 30},
    {"type": "Linear Slot Diffuser", "size": "1800mm length", "min_airflow_ls": 38, "max_airflow_ls": 108, "throw_m": 6.0, "nr_rating": 30},

    {"type": "Swirl Diffuser", "size": "254mm dia", "min_airflow_ls": 53, "max_airflow_ls": 152, "throw_m": 2.5, "nr_rating": 30},
    {"type": "Swirl Diffuser", "size": "356mm dia", "min_airflow_ls": 105, "max_airflow_ls": 299, "throw_m": 3.6, "nr_rating": 30},
    {"type": "Swirl Diffuser", "size": "457mm dia", "min_airflow_ls": 172, "max_airflow_ls": 492, "throw_m": 4.6, "nr_rating": 30},
    {"type": "Swirl Diffuser", "size": "535mm dia", "min_airflow_ls": 236, "max_airflow_ls": 674, "throw_m": 5.3, "nr_rating": 30},

    {"type": "Egg Crate Grille (Extract)", "size": "150x150mm", "min_airflow_ls": 20, "max_airflow_ls": 51, "throw_m": None, "nr_rating": 30},
    {"type": "Egg Crate Grille (Extract)", "size": "200x200mm", "min_airflow_ls": 36, "max_airflow_ls": 90, "throw_m": None, "nr_rating": 30},
    {"type": "Egg Crate Grille (Extract)", "size": "250x250mm", "min_airflow_ls": 56, "max_airflow_ls": 141, "throw_m": None, "nr_rating": 30},
    {"type": "Egg Crate Grille (Extract)", "size": "300x300mm", "min_airflow_ls": 81, "max_airflow_ls": 202, "throw_m": None, "nr_rating": 30},
    {"type": "Egg Crate Grille (Extract)", "size": "350x350mm", "min_airflow_ls": 110, "max_airflow_ls": 276, "throw_m": None, "nr_rating": 30},
    {"type": "Egg Crate Grille (Extract)", "size": "400x400mm", "min_airflow_ls": 144, "max_airflow_ls": 360, "throw_m": None, "nr_rating": 30},
    {"type": "Egg Crate Grille (Extract)", "size": "450x450mm", "min_airflow_ls": 182, "max_airflow_ls": 456, "throw_m": None, "nr_rating": 30},
    {"type": "Egg Crate Grille (Extract)", "size": "500x500mm", "min_airflow_ls": 225, "max_airflow_ls": 562, "throw_m": None, "nr_rating": 30},
    {"type": "Egg Crate Grille (Extract)", "size": "555x555mm", "min_airflow_ls": 277, "max_airflow_ls": 693, "throw_m": None, "nr_rating": 30},
]
GRILLE_TYPES = sorted(set(item["type"] for item in GRILLE_DIFFUSER_CATALOGUE))

# Maps a Room Schedule "Floor" value (free text) to the 2-digit code used
# in grille/diffuser reference tags (e.g. SAD.00.01). Matching is
# case-insensitive; anything not recognised falls back to "XX" rather
# than guessing, so an unrecognised floor name is visibly flagged in the
# schedule instead of silently mis-tagged.
FLOOR_CODE_MAP = {
    "ground": "00", "ground floor": "00", "g": "00", "gf": "00", "0": "00",
    "first": "01", "first floor": "01", "1": "01",
    "second": "02", "second floor": "02", "2": "02",
    "third": "03", "third floor": "03", "3": "03",
    "fourth": "04", "fourth floor": "04", "4": "04",
    "fifth": "05", "fifth floor": "05", "5": "05",
    "basement": "-01", "basement floor": "-01", "basement 1": "-01", "b1": "-01",
    "basement 2": "-02", "b2": "-02",
    "roof": "RF",
}

# ---- Cold water supply - Loading Unit (LU) values per appliance, per
# BS EN 806-3 Table 2 ("Draw-off flow-rates QA, minimum flow-rates at
# draw-off points Qmin and loading units for draw-off points") - actual
# published standard figures, not estimates. Applied PER ROOM here (via
# fixture counts on the Room Schedule), rather than as a separate
# appliance schedule, so a room's water demand lives in the same place as
# everything else about that room.
#
# Table 2 groups several fixture types under the same LU value; mapped
# here as:
#   Row "Washbasin, handbasin, bidet, WC-cistern" (LU=1) -> WHB, Bidet,
#     WC (cistern-fed), and (by the same cistern-fed logic) Urinal
#     (Cistern-fed)
#   Row "Domestic kitchen sink, washing machine, dish washing machine,
#     sink, shower head" (LU=2) -> Kitchen Sink, Washing Machine,
#     Dishwasher, Shower
#   Row "Urinal flush valve" (LU=3) -> Urinal (Flushometer/Valve)
#   Row "Bath domestic" (LU=4) -> Bath
#   Row "Taps (garden/garage)" (LU=5) -> Hose Union Bib Tap (Garden)
#   Row "Non domestic kitchen sink DN20, bath non domestic" (LU=8) ->
#     Cleaner's Sink (treated as non-domestic duty - confirm this is the
#     right category for your specific cleaner's sink installation)
#   Row "Flush valve DN20" (LU=15) -> not currently mapped to a fixture
#     below (no DN20 flush valve fixture type exists yet - add one if needed)
#
# "Drinking Fountain / Bib Tap" is NOT an explicit row in Table 2 - kept
# at the previous indicative value (0.5) pending your confirmation of
# which Table 2 row it should actually draw from.
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
    "Drinking Fountain / Bib Tap": 0.5,  # NOT in BS EN 806-3 Table 2 - please confirm
    "Hose Union Bib Tap (Garden)": 5.0,
}
FIXTURE_TYPES = list(FIXTURE_LU.keys())

# ---- Above Ground Drainage - Discharge Units (DU), per BS EN 12056-2
# Table 3 (System I - the discharge unit method most commonly used for UK
# domestic/office-type buildings). Reuses the SAME fixture names as
# FIXTURE_LU above (and the SAME fixture_counts already entered per room
# for water supply) rather than asking for fixture counts twice - the
# same physical WC/basin/shower etc. has both a supply Loading Unit
# value AND a drainage Discharge Unit value.
#
# A few entries don't map cleanly to a specific BS EN 12056-2 Table 3
# row and are approximated - flagged individually below; confirm these
# against the actual standard for the final design.
DISCHARGE_UNITS_DU = {
    "WC (Dual-Flush, 6L)": 2.0,
    "Wash Hand Basin (WHB)": 0.5,
    "Shower": 0.6,
    "Bath": 0.8,
    "Kitchen Sink": 0.8,
    "Cleaner's Sink": 0.8,  # approximated as a standard sink - confirm for a bucket/slop sink specifically
    "Bidet": 0.5,
    "Washing Machine": 0.8,  # up to 6kg per BS EN 12056-2
    "Dishwasher": 0.2,
    "Urinal (Cistern-fed)": 0.8,
    "Urinal (Flushometer/Valve)": 0.8,  # BS EN 12056-2 doesn't distinguish cistern vs valve for DU
    "Drinking Fountain / Bib Tap": 0.5,  # NOT a standard BS EN 12056-2 row - please confirm
    "Hose Union Bib Tap (Garden)": 0.5,  # NOT a standard BS EN 12056-2 row - please confirm
}

# Frequency factor K, per BS EN 12056-2 - determines how "bunched up" the
# discharge events are expected to be. Qww (l/s) = K x SQRT(Total DU).
DRAINAGE_FREQUENCY_FACTORS = {
    "Intermittent use (e.g. dwellings) - K=0.5": 0.5,
    "Frequent use (e.g. offices, schools, hospitals) - K=0.7": 0.7,
    "Congested use (e.g. public toilets) - K=1.0": 1.0,
    "Special use (e.g. hospital WCs) - K=1.2": 1.2,
}

# Representative discharge stack capacities (NOT taken from a specific
# manufacturer or the full BS EN 12056-2 Table 6/7 fill-ratio tables,
# which depend on gradient and fill ratio assumptions) - a reasonable
# starting point for standard vertical discharge stacks at typical fill
# ratios. Confirm against BS EN 12056-2 Table 6/7 directly for the final
# design, since actual capacity depends on the specific gradient/fill
# ratio combination chosen.
DRAINAGE_PIPE_CAPACITY = [
    {"diameter_mm": 50, "max_flow_ls": 1.2},
    {"diameter_mm": 75, "max_flow_ls": 4.5},
    {"diameter_mm": 100, "max_flow_ls": 9.5},
    {"diameter_mm": 125, "max_flow_ls": 17.0},
    {"diameter_mm": 150, "max_flow_ls": 27.0},
]

# ---- Pumps for below-invert drainage (sump pumps, macerators, packaged
# pumping stations) - representative figures for early-stage sizing,
# NOT taken from a specific manufacturer's published performance curves.
# Confirm against the actual manufacturer's pump curve (flow vs head)
# once a specific product is being specified - pump selection properly
# needs the actual static lift/head, not just flow rate, which this
# simplified catalogue doesn't yet account for.
PUMP_TYPES = ["Sump Pump", "Macerator", "Packaged Pumping Station"]
PUMP_CATALOGUE = [
    {"type": "Macerator", "model": "Compact Macerator (Small)", "max_flow_ls": 0.5, "max_head_m": 5},
    {"type": "Macerator", "model": "Compact Macerator (Standard)", "max_flow_ls": 1.5, "max_head_m": 8},
    {"type": "Sump Pump", "model": "Sump Pump (Small)", "max_flow_ls": 2.0, "max_head_m": 6},
    {"type": "Sump Pump", "model": "Sump Pump (Medium)", "max_flow_ls": 5.0, "max_head_m": 9},
    {"type": "Sump Pump", "model": "Sump Pump (Large)", "max_flow_ls": 10.0, "max_head_m": 12},
    {"type": "Packaged Pumping Station", "model": "Packaged Station (Single Pump)", "max_flow_ls": 8.0, "max_head_m": 10},
    {"type": "Packaged Pumping Station", "model": "Packaged Station (Duty/Standby)", "max_flow_ls": 15.0, "max_head_m": 15},
    {"type": "Packaged Pumping Station", "model": "Packaged Station (Large Duty/Standby)", "max_flow_ls": 30.0, "max_head_m": 18},
]

# Standard GRP sectional cold water storage tank capacities (litres),
# DESCENDING - same list as the Excel workbook, for the round-up lookup.
STANDARD_TANK_SIZES = [13500, 9000, 6000, 4500, 3000, 2250, 1500, 1000, 500, 100]
