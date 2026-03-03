"""
Reusable Streamlit UI components for the Huygen app.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from visualization import HUYGEN_CMAP


# ---------------------------------------------------------------------------
# Transducer card
# ---------------------------------------------------------------------------

def render_transducer_card(index: int, src: dict) -> dict | None:
    """
    Render a single transducer parameter card inside the sidebar.
    Returns the updated source dict, or None if the user deletes it.
    """
    with st.container(border=True):
        col_title, col_delete = st.columns([4, 1])
        with col_title:
            st.markdown(f"**Transducer {index + 1}**")
        with col_delete:
            if st.button("✕", key=f"del_{index}", help="Remove transducer"):
                return None

        wall = st.radio(
            "Wall",
            ["left", "right"],
            index=0 if src.get("wall", "left") == "left" else 1,
            horizontal=True,
            key=f"wall_{index}",
        )
        position = st.slider(
            "Position (% from bottom)",
            0.0, 100.0,
            value=float(src.get("position", 50.0)),
            step=1.0,
            key=f"pos_{index}",
        )
        power = st.slider(
            "Power (a.u.)",
            0.1, 10.0,
            value=float(src.get("power", 1.0)),
            step=0.1,
            key=f"pow_{index}",
        )
        is_line = st.toggle(
            "Line source",
            value=src.get("is_line", True),
            key=f"line_{index}",
        )
        length = 0.0
        if is_line:
            length = st.number_input(
                "Length (mm)",
                min_value=1.0,
                max_value=1000.0,
                value=max(float(src.get("length", 20.0)), 2.0),
                step=0.1,
                key=f"len_{index}",
            )

    return {
        "wall": wall,
        "position": position,
        "power": power,
        "is_line": is_line,
        "length": length,
    }


# ---------------------------------------------------------------------------
# Preview visualisation
# ---------------------------------------------------------------------------

def render_preview(box_x: float, box_y: float, sources: list[dict], boundaries: dict):
    """
    Draw a schematic of the simulation domain showing boundaries and
    transducer positions.
    """
    height = min(6 * box_y / max(box_x, 1), 6)
    fig, ax = plt.subplots(figsize=(6, height))

    # Domain rectangle
    rect = patches.Rectangle((0, 0), box_x, box_y,
                              linewidth=1.5, edgecolor="black", facecolor="#f0f4ff")
    ax.add_patch(rect)

    # Boundary labels
    boundary_colors = {"rigid": "#2563eb", "free": "#dc2626"}
    for side, kind in boundaries.items():
        color = boundary_colors[kind]
        lw = 3
        if side == "bottom":
            ax.plot([0, box_x], [0, 0], color=color, lw=lw)
        elif side == "top":
            ax.plot([0, box_x], [box_y, box_y], color=color, lw=lw)
        elif side == "left":
            ax.plot([0, 0], [0, box_y], color=color, lw=lw)
        elif side == "right":
            ax.plot([box_x, box_x], [0, box_y], color=color, lw=lw)

    # Transducers
    for i, src in enumerate(sources):
        pos_y = box_y * src["position"] / 100.0
        if src["wall"] == "left":
            sx, direction = 0.0, 1
        else:
            sx, direction = box_x, -1

        marker_color = "#e11d48"
        if src["is_line"] and src["length"] > 0:
            half = src["length"] / 2.0
            ax.plot([sx, sx], [pos_y - half, pos_y + half],
                    color=marker_color, lw=4, solid_capstyle="round")
        else:
            ax.plot(sx, pos_y, "o", color=marker_color, markersize=10)

        # Small arrow showing propagation direction
        ax.annotate("",
                    xy=(sx + direction * box_x * 0.06, pos_y),
                    xytext=(sx, pos_y),
                    arrowprops=dict(arrowstyle="->", color=marker_color, lw=1.5))

        ax.text(sx + direction * box_x * 0.09, pos_y,
                f"T{i+1}", fontsize=8, ha="center", va="center",
                color=marker_color, fontweight="bold")

    # Legend
    from matplotlib.lines import Line2D
    legend_items = [
        Line2D([0], [0], color="#2563eb", lw=3, label="Rigid"),
        Line2D([0], [0], color="#dc2626", lw=3, label="Free"),
        Line2D([0], [0], marker="o", color="#e11d48", lw=0, markersize=8, label="Source"),
    ]
    ax.legend(handles=legend_items, loc="upper right", fontsize=7, framealpha=0.9)

    ax.set_xlim(-box_x * 0.12, box_x * 1.12)
    ax.set_ylim(-box_y * 0.12, box_y * 1.12)
    ax.set_xlabel("x (mm)")
    ax.set_ylabel("y (mm)")
    ax.set_aspect("equal")
    ax.set_title("Domain Preview", fontsize=10)
    plt.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Field visualisation
# ---------------------------------------------------------------------------

def render_field(field: np.ndarray, box_x: float, box_y: float):
    """
    Render the acoustic intensity colormap.
    Colour limits: vmin = 0.1*min, vmax = 0.9*max (per roadmap spec).
    """
    vmin = 0
    vmax = 1.0

    height = min(7 * box_y / max(box_x, 1), 8)
    fig, ax = plt.subplots(figsize=(7, height))
    im = ax.imshow(
        field,
        extent=[0, box_x, 0, box_y],
        origin="lower",
        cmap=HUYGEN_CMAP,
        vmin=vmin,
        vmax=vmax,
        aspect="equal",
    )
    fig.colorbar(im, ax=ax, label="Normalised intensity (a.u.)")
    ax.set_xlabel("x (mm)")
    ax.set_ylabel("y (mm)")
    ax.set_title("Acoustic Field", fontsize=10)
    plt.tight_layout()
    return fig
