"""
Exports the current session's rooms to an Excel workbook - the auditable,
client-issuable deliverable, generated from whatever is currently in the
Streamlit table. Deliberately simple compared to generate_mep_workbook.py's
full styled output - port the styling helpers from that script here once
this concept is validated for real use.
"""
import io
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

import calc_engine
import reference_data as ref

NAVY = "1B365D"
ICE_BLUE = "E6F0FA"
HEADER_FONT = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
HEADER_FILL = PatternFill("solid", fgColor=NAVY)
TOTAL_FILL = PatternFill("solid", fgColor=ICE_BLUE)


def build_export_workbook(rooms: list) -> io.BytesIO:
    wb = Workbook()
    ws = wb.active
    ws.title = "Room Schedule & HVAC"

    headers = [
        "Room Name", "Floor", "Area (m2)", "Ceiling Height (m)", "Volume (m3)",
        "Summer Design Temp (C)", "Total Sensible (kW)", "Total Latent (kW)",
        "Total Cooling Load (kW)", "Selected FCU", "Qty", "Meets Load?",
    ]
    for col, text in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col, value=text)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center")

    total_sensible = total_latent = total_load = 0.0
    r = 2
    for room in rooms:
        gains = calc_engine.calculate_heat_gains(room)
        fcu = calc_engine.select_fcu(
            gains.total_cooling_load_kw, room.get("manufacturer", "Daikin"),
            room.get("unit_type", "Ducted"), room.get("quantity", 1),
            ref.FCU_CATALOGUE,
        )
        ws.cell(row=r, column=1, value=room.get("name"))
        ws.cell(row=r, column=2, value=room.get("floor"))
        ws.cell(row=r, column=3, value=room.get("area_m2"))
        ws.cell(row=r, column=4, value=room.get("ceiling_height_m"))
        ws.cell(row=r, column=5, value=gains.volume_m3)
        ws.cell(row=r, column=6, value=gains.design_temp_c)
        ws.cell(row=r, column=7, value=gains.total_sensible_kw)
        ws.cell(row=r, column=8, value=gains.total_latent_kw)
        ws.cell(row=r, column=9, value=gains.total_cooling_load_kw)
        ws.cell(row=r, column=10, value=fcu.selected_model if fcu else "-")
        ws.cell(row=r, column=11, value=room.get("quantity", 1) if fcu else "-")
        ws.cell(row=r, column=12, value=("PASS" if fcu.meets_load else "REVIEW") if fcu else "-")

        total_sensible += gains.total_sensible_kw
        total_latent += gains.total_latent_kw
        total_load += gains.total_cooling_load_kw
        r += 1

    ws.cell(row=r, column=1, value="TOTALS")
    ws.cell(row=r, column=7, value=round(total_sensible, 2))
    ws.cell(row=r, column=8, value=round(total_latent, 2))
    ws.cell(row=r, column=9, value=round(total_load, 2))
    for col in range(1, 13):
        ws.cell(row=r, column=col).fill = TOTAL_FILL

    for col_letter, width in zip("ABCDEFGHIJKL", [24, 10, 12, 14, 12, 12, 14, 12, 16, 20, 8, 12]):
        ws.column_dimensions[col_letter].width = width

    disclaimer_row = r + 2
    ws.cell(
        row=disclaimer_row, column=1,
        value=(
            "Disclaimer: this platform is a calculation aid only and does not hold or assume any design "
            "liability. All figures must be independently checked and verified by a suitably qualified "
            "engineer against current standards and project-specific requirements before use for design, "
            "construction, or compliance purposes."
        ),
    )
    ws.merge_cells(start_row=disclaimer_row, start_column=1, end_row=disclaimer_row, end_column=12)
    ws.cell(row=disclaimer_row, column=1).font = Font(name="Segoe UI", size=9, italic=True, color="C0392B")
    ws.cell(row=disclaimer_row, column=1).alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[disclaimer_row].height = 30

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer
