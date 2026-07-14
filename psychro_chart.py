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
import matplotlib.ticker as mticker

import calc_engine
import reference_data as ref

NAVY = "#1B365D"
ICE_BLUE = "#E6F0FA"


def build_psychrometric_chart(room: dict, external_dbt_c: float = None, external_rh_pct: float = None):
    """Returns (png_bytes, details_dict). details_dict has the exact
    computed values (dry-bulb, RH, moisture content, enthalpy) for both
    marked points, for display in a table alongside the chart image."""
    external_dbt_c = external_dbt_c if external_dbt_c is not None else ref.EXTERNAL_DRYBULB_C
    external_rh_pct = external_rh_pct if external_rh_pct is not None else ref.EXTERNAL_RH_PCT

    internal_temp = calc_engine._safe_float(room.get("summer_design_temp_c"), ref.INTERNAL_DRYBULB_C)
    internal_rh_pct = ref.INTERNAL_RH_PCT

    temps = [t * 0.5 for t in range(-20, 91)]  # -10 to 45degC in 0.5degC steps

    fig, ax = plt.subplots(figsize=(6.2, 4.4))

    # Saturation curve (100% RH)
    sat_curve = [calc_engine.moisture_content_kgkg(t, 100.0) * 1000 for t in temps]
    ax.plot(temps, sat_curve, color=NAVY, linewidth=1.8, label="Saturation (100% RH)")
    ax.fill_between(temps, sat_curve, max(sat_curve) * 1.15, color="#CCCCCC", alpha=0.3)

    # Constant RH reference lines - finer detail than before (every 10%)
    for rh in [10, 20, 30, 40, 50, 60, 70, 80, 90]:
        curve = [calc_engine.moisture_content_kgkg(t, rh) * 1000 for t in temps]
        ax.plot(temps, curve, color="#8C8C8C", linewidth=0.6, linestyle="--")
        label_t = 40.0
        label_g = calc_engine.moisture_content_kgkg(label_t, rh) * 1000
        if label_g < max(sat_curve):
            ax.annotate(f"{rh}%", (label_t, label_g), fontsize=6.5, color="#777777")

    # Mark design points
    g_ext = calc_engine.moisture_content_kgkg(external_dbt_c, external_rh_pct) * 1000
    g_int = calc_engine.moisture_content_kgkg(internal_temp, internal_rh_pct) * 1000
    h_ext = calc_engine.moist_air_enthalpy_kjkg(external_dbt_c, g_ext / 1000)
    h_int = calc_engine.moist_air_enthalpy_kjkg(internal_temp, g_int / 1000)

    ax.plot(external_dbt_c, g_ext, marker="o", markersize=8, color="#C0392B", zorder=5)
    ax.annotate(
        "  External", (external_dbt_c, g_ext), fontsize=8, color="#C0392B", fontweight="bold", va="center",
    )

    ax.plot(internal_temp, g_int, marker="o", markersize=8, color="#2E7D32", zorder=5)
    ax.annotate(
        "  Internal", (internal_temp, g_int), fontsize=8, color="#2E7D32", fontweight="bold", va="center",
    )

    ax.set_xlim(-10, 45)
    ax.set_ylim(0, max(sat_curve) * 1.1)
    ax.set_xlabel("Dry-Bulb Temperature (\u00b0C)", fontsize=9)
    ax.set_ylabel("Moisture Content (g/kg dry air)", fontsize=9)
    ax.set_title(f"Psychrometric Chart \u2014 {room.get('name', 'Room')}", fontsize=11, color=NAVY, fontweight="bold")
    ax.tick_params(labelsize=8)
    ax.xaxis.set_minor_locator(mticker.MultipleLocator(5))
    ax.yaxis.set_minor_locator(mticker.MultipleLocator(2))
    ax.grid(True, which="major", color="#DADADA", linewidth=0.5)
    ax.grid(True, which="minor", color="#EEEEEE", linewidth=0.3)
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")
    ax.legend(loc="upper left", fontsize=7.5, frameon=False)
    fig.tight_layout()

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=140)
    plt.close(fig)
    buffer.seek(0)

    details = {
        "External Design": {
            "Dry-Bulb (\u00b0C)": round(external_dbt_c, 1), "RH (%)": external_rh_pct,
            "Moisture Content (g/kg)": round(g_ext, 2), "Enthalpy (kJ/kg)": round(h_ext, 1),
        },
        "Internal Design": {
            "Dry-Bulb (\u00b0C)": round(internal_temp, 1), "RH (%)": internal_rh_pct,
            "Moisture Content (g/kg)": round(g_int, 2), "Enthalpy (kJ/kg)": round(h_int, 1),
        },
    }
    return buffer.getvalue(), details
