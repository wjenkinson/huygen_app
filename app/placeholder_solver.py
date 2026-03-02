"""
Placeholder solver for Phase 1.
Generates synthetic acoustic field data so the UI can be developed
and tested without the real Huygens backend.
Replaced by src/huygens_solver.py in Phase 2.
"""

import numpy as np
import time


def generate_placeholder_field(
    grid_nx: int,
    grid_ny: int,
    box_x: float,
    box_y: float,
    frequency_mhz: float,
    sources: list[dict],
    n_reflections: int = 1,
    attenuation: float = 0.0,
    attenuation_power: float = 1.0,
    boundaries: dict | None = None,
) -> np.ndarray:
    """
    Return a synthetic 2D pressure-intensity field (real, non-negative).

    The output loosely mimics interference patterns so the UI looks
    plausible, but carries **no physical meaning**.

    Parameters
    ----------
    grid_nx, grid_ny : int
        Number of grid points in x and y.
    box_x, box_y : float
        Physical box dimensions (mm).
    frequency_mhz : float
        Driving frequency in MHz (used to set fringe spacing).
    sources : list[dict]
        Each dict must have keys: wall ("left"|"right"), position (0-100 %),
        power (float), is_line (bool), length (float, mm).
    n_reflections : int
        Number of reflection orders (visual complexity knob).
    attenuation : float
        Attenuation coefficient (dims the field away from sources).
    attenuation_power : float
        Frequency-power-law exponent.
    boundaries : dict | None
        Keys "top", "bottom", "left", "right" each "rigid" or "free".

    Returns
    -------
    field : np.ndarray, shape (grid_ny, grid_nx)
        Normalised intensity-like array in [0, 1].
    """
    if boundaries is None:
        boundaries = {side: "rigid" for side in ("top", "bottom", "left", "right")}

    x = np.linspace(0, box_x, grid_nx)
    y = np.linspace(0, box_y, grid_ny)
    X, Y = np.meshgrid(x, y)

    # Wavenumber-like scale from frequency
    k = 2.0 * np.pi * frequency_mhz / (box_x * 0.3)

    field = np.zeros_like(X)

    for src in sources:
        # Source position in physical coords
        wall = src.get("wall", "left")
        pos_pct = src.get("position", 50.0)
        power = src.get("power", 1.0)

        sy = box_y * pos_pct / 100.0

        if wall == "left":
            sx = 0.0
        else:
            sx = box_x

        r = np.sqrt((X - sx) ** 2 + (Y - sy) ** 2) + 1e-9

        # Cylindrical-spreading-like placeholder
        contribution = power * np.cos(k * r) / np.sqrt(r + 1.0)

        # Crude attenuation decay
        if attenuation > 0:
            alpha = attenuation * (frequency_mhz ** attenuation_power)
            contribution *= np.exp(-alpha * r / box_x)

        field += contribution

        # Add simple image-source reflections
        for order in range(1, n_reflections + 1):
            for mirror_y in [2 * box_y * order - sy, -2 * box_y * order + sy]:
                r_img = np.sqrt((X - sx) ** 2 + (Y - mirror_y) ** 2) + 1e-9
                sign = 1.0 if boundaries.get("top", "rigid") == "rigid" else -1.0
                field += sign * power * 0.5 * np.cos(k * r_img) / np.sqrt(r_img + 1.0)

    # Convert to intensity-like quantity
    field = field ** 2

    # Normalise to [0, 1]
    fmin, fmax = field.min(), field.max()
    if fmax - fmin > 0:
        field = (field - fmin) / (fmax - fmin)

    return field


def estimate_runtime(grid_nx: int, grid_ny: int, n_sources: int, n_reflections: int) -> float:
    """
    Return a rough wall-clock estimate in seconds for the placeholder solver.
    In Phase 2 this will be replaced with a proper estimate based on solver benchmarks.
    """
    base = 0.3
    return base + (grid_nx * grid_ny * n_sources * n_reflections) * 1e-6


def run_placeholder(
    grid_nx: int,
    grid_ny: int,
    box_x: float,
    box_y: float,
    frequency_mhz: float,
    sources: list[dict],
    n_reflections: int = 1,
    attenuation: float = 0.0,
    attenuation_power: float = 1.0,
    boundaries: dict | None = None,
    progress_callback=None,
) -> np.ndarray:
    """
    Wrapper that simulates a solver run with artificial delay and
    progress updates so the UI progress bar can be exercised.
    """
    total_steps = 5
    for step in range(total_steps):
        time.sleep(0.25)
        if progress_callback:
            progress_callback((step + 1) / total_steps)

    return generate_placeholder_field(
        grid_nx=grid_nx,
        grid_ny=grid_ny,
        box_x=box_x,
        box_y=box_y,
        frequency_mhz=frequency_mhz,
        sources=sources,
        n_reflections=n_reflections,
        attenuation=attenuation,
        attenuation_power=attenuation_power,
        boundaries=boundaries,
    )
