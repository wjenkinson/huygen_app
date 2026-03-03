"""
Huygen App – Streamlit frontend.
Run with:  streamlit run app/streamlit_app.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import streamlit as st

from huygens_solver import run_solver
from ui_components import render_transducer_card, render_preview, render_field

APP_DIR = os.path.dirname(__file__)
LOGO_PATH = os.path.join(APP_DIR, "..", "logos", "roseworks_logo.png")


# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Huygen Acoustics Solver",
    page_icon="./logos/roseworks_favicon.png",
    layout="wide",
)

if os.path.exists(LOGO_PATH):
    st.sidebar.image(LOGO_PATH, width="stretch")


# ── Session state defaults ───────────────────────────────────────────────────

def _defaults():
    defaults = {
        "sources": [{"wall": "left", "position": 50.0, "power": 1.0,
                      "is_line": False, "length": 0.0}],
        "field": None,
        "results_stale": False,
        "has_run": False,
        "last_params_hash": None,
        "run_count": 0,
        "promo_dismissed": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_defaults()


def _params_hash() -> int:
    """Quick hash of all user-facing parameters to detect staleness."""
    parts = (
        st.session_state.get("grid_nx"),
        st.session_state.get("grid_ny"),
        st.session_state.get("box_x"),
        st.session_state.get("box_y"),
        st.session_state.get("frequency"),
        st.session_state.get("medium"),
        st.session_state.get("attenuation"),
        st.session_state.get("att_power"),
        st.session_state.get("n_reflections"),
        tuple(st.session_state.get("bd_top", "rigid")),
        tuple(st.session_state.get("bd_bottom", "rigid")),
        tuple(st.session_state.get("bd_left", "rigid")),
        tuple(st.session_state.get("bd_right", "rigid")),
        str(st.session_state["sources"]),
    )
    return hash(parts)


# ── Header ───────────────────────────────────────────────────────────────────

st.title("Huygen Acoustics Solver")
st.caption(
    "Interactive 2-D acoustic field explorer based on Huygens source "
    "superposition."
)

if (
    st.session_state["run_count"] >= 5
    and not st.session_state["promo_dismissed"]
):
    st.info(
        "**💡Enjoying the app?** I provide a range of services to life science "
        "R&D teams considering digital tools. 📩 Reach out on "
        "[LinkedIn](https://www.linkedin.com/in/william-jenkinson/), "
        "[Malt](https://www.malt.fr/profile/billyjenkinson), "
        "or email at [billy@roseworks.fr](mailto:billy@roseworks.fr)."
    )
    if st.button("Dismiss", key="dismiss_promo"):
        st.session_state["promo_dismissed"] = True
        st.rerun()


# ── Sidebar: parameters ─────────────────────────────────────────────────────

with st.sidebar:
    st.header("Parameters")

    # ---- Simulation ----
    st.subheader("Simulation")

    grid_nx = st.slider("Grid X points", 10, 100, 50, step=10, key="grid_nx")
    grid_ny = st.slider("Grid Y points", 10, 200, 100, step=10, key="grid_ny")
    box_x = st.number_input(
        "Box X (mm)",
        min_value=1.0,
        max_value=1000.0,
        value=1.5,
        step=0.1,
        key="box_x",
    )
    box_y = st.number_input(
        "Box Y (mm)",
        min_value=1.0,
        max_value=1000.0,
        value=3.0,
        step=0.1,
        key="box_y",
    )
    n_reflections = st.slider("Number of reflections", 1, 3, 2, step=1, key="n_reflections")

    st.divider()

    # ---- Physical ----
    st.subheader("Physical")

    frequency = st.number_input(
        "Frequency (MHz)",
        min_value=0.001,
        max_value=10.0,
        value=1.0,
        step=0.001,
        format="%.3f",
        key="frequency",
    )

    # Half-wavelength check
    c_water = 1500.0  # m/s
    half_wavelength_mm = (c_water / (frequency * 1e6)) / 2.0 * 1e3
    dx_mm = box_x / max(grid_nx - 1, 1)
    dy_mm = box_y / max(grid_ny - 1, 1)
    if dx_mm > half_wavelength_mm or dy_mm > half_wavelength_mm:
        st.warning(
            f"Grid spacing ({dx_mm:.2f} × {dy_mm:.2f} mm) exceeds "
            f"λ/2 = {half_wavelength_mm:.2f} mm. Results may be under-resolved."
        )

    medium = st.selectbox("Medium", ["Water  (c=1500 m/s, ρ=1000 kg/m³)"], key="medium")
    attenuation = st.slider("Attenuation coeff.", 0.0, 1.0, 0.0, step=0.1, key="attenuation")
    att_power = st.slider("Attenuation power", 1.0, 2.0, 1.0, step=1.0, key="att_power")

    st.divider()

    # ---- Boundaries ----
    st.subheader("Boundaries")
    bd_top = st.radio("Top", ["rigid", "free"], horizontal=True, key="bd_top")
    bd_bottom = st.radio("Bottom", ["rigid", "free"], horizontal=True, key="bd_bottom")
    bd_left = st.radio("Left", ["rigid", "free"], horizontal=True, key="bd_left")
    bd_right = st.radio("Right", ["rigid", "free"], horizontal=True, key="bd_right")

    boundaries = {"top": bd_top, "bottom": bd_bottom, "left": bd_left, "right": bd_right}

    st.divider()

    # ---- Transducers ----
    st.subheader("Transducers")

    updated_sources: list[dict] = []
    deleted = False
    for i, src in enumerate(st.session_state["sources"]):
        result = render_transducer_card(i, src)
        if result is not None:
            updated_sources.append(result)
        else:
            deleted = True

    if st.button("＋ Add transducer"):
        updated_sources.append({
            "wall": "left", "position": 50.0, "power": 1.0,
            "is_line": False, "length": 0.0,
        })
        st.session_state["sources"] = updated_sources
        st.rerun()

    if deleted:
        st.session_state["sources"] = updated_sources if updated_sources else st.session_state["sources"]
        st.rerun()

    st.session_state["sources"] = updated_sources if updated_sources else st.session_state["sources"]

    st.divider()


# ── Staleness detection ──────────────────────────────────────────────────────

current_hash = _params_hash()
if st.session_state["has_run"] and current_hash != st.session_state["last_params_hash"]:
    st.session_state["results_stale"] = True


# ── Main area: two-column layout ─────────────────────────────────────────────

col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("📐 Preview")
    fig_preview = render_preview(box_x, box_y, st.session_state["sources"], boundaries)
    st.pyplot(fig_preview)

with col_right:
    st.subheader("📊 Run")

    n_src = len(st.session_state["sources"])
    est = 0.3 + (grid_nx * grid_ny * n_src * n_reflections) * 5e-6

    col_run, col_est = st.columns([1, 1])
    with col_run:
        run_clicked = st.button("▶  Run", type="primary", width="stretch")
    with col_est:
        st.caption(f"Est. runtime ≈ {est:.1f} s")

    if st.session_state["results_stale"]:
        st.warning("Parameters have changed since the last run — results may be out of date.")

    if run_clicked:
        st.session_state["results_stale"] = False
        progress_bar = st.progress(0, text="Running solver…")

        def _update_progress(frac: float):
            progress_bar.progress(frac, text=f"Running solver… {int(frac*100)}%")

        field = run_solver(
            grid_nx=grid_nx,
            grid_ny=grid_ny,
            box_x=box_x,
            box_y=box_y,
            frequency_mhz=float(frequency),
            sources=st.session_state["sources"],
            n_reflections=n_reflections,
            attenuation=attenuation,
            attenuation_power=att_power,
            boundaries=boundaries,
            progress_callback=_update_progress,
        )

        progress_bar.empty()
        st.session_state["field"] = field
        st.session_state["has_run"] = True
        st.session_state["run_count"] = st.session_state.get("run_count", 0) + 1
        st.session_state["last_params_hash"] = _params_hash()

    if st.session_state["field"] is not None:
        fig_field = render_field(st.session_state["field"], box_x, box_y)
        st.pyplot(fig_field)
    else:
        st.info("Adjust parameters and click **Run** to generate the acoustic field.")


# ── Footer / disclaimer ─────────────────────────────────────────────────────

st.divider()
st.caption(
    "**Limitations:** 2-D slice model only · single-core execution · "
    "simple rectangular geometry · uniform homogeneous liquid medium"
)
st.caption(
    "Intended as an exploratory engineering tool, not a calibrated simulation."
)
