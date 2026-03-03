"""
Visualization helpers for the Huygen App.

Uses the project's custom pink-to-dark-magenta colormap.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from typing import Tuple

# Custom colormap from the original project
HUYGEN_COLORS = [
    (0.98, 0.88, 0.93),
    (0.95, 0.60, 0.75),
    (0.80, 0.20, 0.45),
    (0.40, 0.00, 0.30),
]

HUYGEN_CMAP = LinearSegmentedColormap.from_list("huygen_pink", HUYGEN_COLORS, N=256)


def render_field(
    field: np.ndarray,
    box_x: float,
    box_y: float,
    figsize: Tuple[float, float] | None = None,
) -> plt.Figure:
    """
    Render the acoustic intensity colormap using the project colormap.

    Parameters
    ----------
    field : np.ndarray, shape (ny, nx)
        Normalised intensity array in [0, 1].
    box_x, box_y : float
        Physical box dimensions in mm.
    figsize : tuple, optional
        Matplotlib figure size. Auto-scaled from aspect ratio if None.

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    if figsize is None:
        aspect = box_y / max(box_x, 1)
        figsize = (7, max(3.5, min(7 * aspect, 10)))

    vmin = 0.1 * field.min()
    vmax = 0.9 * field.max() if field.max() > 0 else 1.0

    fig, ax = plt.subplots(figsize=figsize)
    im = ax.imshow(
        field,
        extent=[0, box_x, 0, box_y],
        origin="lower",
        cmap=HUYGEN_CMAP,
        vmin=vmin,
        vmax=vmax,
        aspect="auto",
    )
    fig.colorbar(im, ax=ax, label="Normalised intensity (a.u.)")
    ax.set_xlabel("x (mm)")
    ax.set_ylabel("y (mm)")
    ax.set_title("Acoustic Field", fontsize=10)
    plt.tight_layout()
    return fig
