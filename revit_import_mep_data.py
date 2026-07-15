"""
MEP Design Platform - Revit Import Script (pyRevit)

Reads the "Export for Revit (CSV)" file from the MEP Design Platform and
writes the calculated values into matching Revit Room parameters, matched
by Room Name.

HONESTY NOTE: written without the ability to test it against a real
Revit project (no Revit/pyRevit installed in the sandbox this was built
in). The Revit API calls below are correct against the documented API,
but this has NOT been run against an actual model. Test on a NON-
PRODUCTION project first, and check the summary dialog's "unmatched"
list carefully before trusting a full import.

ONE-TIME SETUP REQUIRED (see the fuller instructions given alongside
this file) - these Project Parameters must exist on the Rooms category
before running this script:
    MEP_CoolingLoad_kW       (Number)
    MEP_SelectedFCU          (Text)
    MEP_FCUStatus            (Text)
    MEP_RequiredAirflow_ls   (Number)
    MEP_DuctSize_mm          (Number)
    MEP_WinterHeatLoss_kW    (Number)
    MEP_LoadingUnits_LU      (Number)

Install as a pyRevit script (paste into a .pushbutton/script.py inside a
pyRevit extension), or run via pyRevit's script runner.
"""
from pyrevit import revit, DB, forms
import csv

doc = revit.doc

# Maps each CSV column to the Revit Project Parameter it should be
# written into - edit this if you named your parameters differently.
PARAM_MAP = {
    "Total Cooling Load (kW)": "MEP_CoolingLoad_kW",
    "Selected FCU": "MEP_SelectedFCU",
    "FCU Status": "MEP_FCUStatus",
    "Required Airflow (l/s)": "MEP_RequiredAirflow_ls",
    "Duct Size (mm)": "MEP_DuctSize_mm",
    "Winter Heat Loss (kW)": "MEP_WinterHeatLoss_kW",
    "Loading Units (LU)": "MEP_LoadingUnits_LU",
}

csv_path = forms.pick_file(file_ext="csv", title="Select mep_revit_import.csv")
if not csv_path:
    forms.alert("No file selected - cancelled.")
    __import__("sys").exit()

# Collect every Room in the current document, keyed by its Name - this is
# the matching key between the platform's Room Schedule and Revit, so
# names need to match EXACTLY (case-sensitive) for a room to sync.
room_collector = (
    DB.FilteredElementCollector(doc)
    .OfCategory(DB.BuiltInCategory.OST_Rooms)
    .WhereElementIsNotElementType()
)
rooms_by_name = {}
for room in room_collector:
    name_param = room.LookupParameter("Name")
    if name_param and name_param.HasValue:
        rooms_by_name[name_param.AsString().strip()] = room

with open(csv_path, "r") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

matched = []
unmatched = []
missing_params_reported = set()

t = DB.Transaction(doc, "Import MEP Design Platform Data")
t.Start()
try:
    for row in rows:
        room_name = (row.get("Room Name") or "").strip()
        room = rooms_by_name.get(room_name)
        if not room:
            unmatched.append(room_name)
            continue

        for csv_col, param_name in PARAM_MAP.items():
            param = room.LookupParameter(param_name)
            if param is None:
                missing_params_reported.add(param_name)
                continue
            value = row.get(csv_col, "")
            try:
                if param.StorageType == DB.StorageType.Double:
                    param.Set(float(value))
                elif param.StorageType == DB.StorageType.Integer:
                    param.Set(int(float(value)))
                else:  # String / text parameters
                    param.Set(str(value))
            except (ValueError, TypeError):
                pass  # leave that specific parameter untouched rather than fail the whole room

        matched.append(room_name)

    t.Commit()
except Exception as e:
    t.RollBack()
    forms.alert("Error during import - no changes were saved:\n{}".format(e))
    raise

summary_lines = ["Updated {} room(s).".format(len(matched))]

if unmatched:
    summary_lines.append(
        "\n{} row(s) in the CSV had NO matching Revit Room "
        "(check Room Name spelling matches exactly):".format(len(unmatched))
    )
    summary_lines.extend(unmatched)

if missing_params_reported:
    summary_lines.append(
        "\nThese parameters were not found on the Rooms category - "
        "has the one-time setup been done?"
    )
    summary_lines.extend(sorted(missing_params_reported))

forms.alert("\n".join(summary_lines), title="MEP Data Import Complete")
