"""
Psychrometric chart (dry-bulb temperature vs. moisture content), built
from the real CIBSE Guide C formula in calc_engine.py (not a generic
chart library) - the saturation curve and constant-RH lines are computed
from the same Equation 1.3 already verified against published steam
table values, so the chart is consistent with every other calculation
in this app rather than a separately-sourced approximation.
"""
import io
import matplotlib
matplotlib.use("Agg")  # headless rendering - no display server needed
import matplotlib.pyplot as plt

import calc_engine
import reference_data as ref

NAVY = "#1B365D"
ICE_BLUE = "#E6F0FA"


def build_psychrometric_chart(room: dict, external_dbt_c: float = None, external_rh_pct: float = None) -> bytes:
    """Returns a PNG image (as bytes) of a psychrometric chart with the
    saturation curve, a few constant-RH reference lines, and this room's
    Internal Design point plus the project's External Design point
    marked on it."""
    external_dbt_c = external_dbt_c if external_dbt_c is not None else ref.EXTERNAL_DRYBULB_C
    external_rh_pct = external_rh_pct if external_rh_pct is not None else ref.EXTERNAL_RH_PCT

    internal_temp = room.get("design_temp_c")
    if internal_temp is None or internal_temp == "":
        internal_temp = ref.INTERNAL_DRYBULB_C
    else:
        internal_temp = float(internal_temp)
    internal_rh_pct = ref.INTERNAL_RH_PCT

    temps = [t * 0.5 for t in range(-20, 91)]  # -10 to 45degC in 0.5degC steps

    fig, ax = plt.subplots(figsize=(9, 6))

    # Saturation curve (100% RH)
    sat_curve = [calc_engine.moisture_content_kgkg(t, 100.0) * 1000 for t in temps]
    ax.plot(temps, sat_curve, color=NAVY, linewidth=2, label="Saturation (100% RH)")
    ax.fill_between(temps, sat_curve, max(sat_curve) * 1.15, color="#CCCCCC", alpha=0.3)

    # Constant RH reference lines
    for rh in [20, 40, 60, 80]:
        curve = [calc_engine.moisture_content_kgkg(t, rh) * 1000 for t in temps]
        ax.plot(temps, curve, color="#8C8C8C", linewidth=0.8, linestyle="--")
        # Label near the right-hand end of each line, where it's still on-chart
        label_t = 40.0
        label_g = calc_engine.moisture_content_kgkg(label_t, rh) * 1000
        if label_g < max(sat_curve):
            ax.annotate(f"{rh}%", (label_t, label_g), fontsize=8, color="#666666")

    # Mark design points
    g_ext = calc_engine.moisture_content_kgkg(external_dbt_c, external_rh_pct) * 1000
    g_int = calc_engine.moisture_content_kgkg(internal_temp, internal_rh_pct) * 1000

    ax.plot(external_dbt_c, g_ext, marker="o", markersize=10, color="#C0392B", zorder=5)
    ax.annotate(
        f"  External Design\n  {external_dbt_c:.0f}\u00b0C / {external_rh_pct:.0f}% RH",
        (external_dbt_c, g_ext), fontsize=9, color="#C0392B", fontweight="bold", va="center",
    )

    ax.plot(internal_temp, g_int, marker="o", markersize=10, color="#2E7D32", zorder=5)
    ax.annotate(
        f"  Internal Design ({room.get('name', 'Room')})\n  {internal_temp:.1f}\u00b0C / {internal_rh_pct:.0f}% RH",
        (internal_temp, g_int), fontsize=9, color="#2E7D32", fontweight="bold", va="center",
    )

    ax.set_xlim(-10, 45)
    ax.set_ylim(0, max(sat_curve) * 1.1)
    ax.set_xlabel("Dry-Bulb Temperature (\u00b0C)", fontsize=11)
    ax.set_ylabel("Moisture Content (g/kg dry air)", fontsize=11)
    ax.set_title(
        f"Psychrometric Chart \u2014 {room.get('name', 'Room')}",
        fontsize=13, color=NAVY, fontweight="bold",
    )
    ax.grid(True, color="#E0E0E0", linewidth=0.5)
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")
    ax.legend(loc="upper left", fontsize=9, frameon=False)
    fig.tight_layout()

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=150)
    plt.close(fig)
    buffer.seek(0)
    return buffer.getvalue()
