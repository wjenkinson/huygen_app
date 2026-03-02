"""
Smoke tests for Phase 1.
Verifies that the placeholder solver runs and the UI components
can be imported without error.
"""

import sys
import os
import numpy as np

# Ensure the app package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from placeholder_solver import generate_placeholder_field, estimate_runtime, run_placeholder
from ui_components import render_preview, render_field


def test_placeholder_field_shape():
    sources = [{"wall": "left", "position": 50.0, "power": 1.0,
                "is_line": False, "length": 0.0}]
    field = generate_placeholder_field(
        grid_nx=20, grid_ny=40, box_x=100.0, box_y=200.0,
        frequency_mhz=2.0, sources=sources,
    )
    assert field.shape == (40, 20)
    assert field.min() >= 0.0
    assert field.max() <= 1.0


def test_placeholder_field_multiple_sources():
    sources = [
        {"wall": "left", "position": 30.0, "power": 1.0, "is_line": False, "length": 0.0},
        {"wall": "right", "position": 70.0, "power": 2.0, "is_line": True, "length": 20.0},
    ]
    field = generate_placeholder_field(
        grid_nx=30, grid_ny=30, box_x=50.0, box_y=50.0,
        frequency_mhz=5.0, sources=sources, n_reflections=2,
        attenuation=0.5, attenuation_power=1.0,
    )
    assert field.shape == (30, 30)


def test_estimate_runtime_positive():
    est = estimate_runtime(50, 100, 2, 2)
    assert est > 0


def test_run_placeholder_with_progress():
    progress_values = []
    sources = [{"wall": "left", "position": 50.0, "power": 1.0,
                "is_line": False, "length": 0.0}]
    field = run_placeholder(
        grid_nx=10, grid_ny=10, box_x=50.0, box_y=50.0,
        frequency_mhz=1.0, sources=sources,
        progress_callback=lambda frac: progress_values.append(frac),
    )
    assert field.shape == (10, 10)
    assert len(progress_values) == 5
    assert progress_values[-1] == 1.0


def test_render_preview_returns_figure():
    import matplotlib
    matplotlib.use("Agg")
    sources = [{"wall": "left", "position": 50.0, "power": 1.0,
                "is_line": False, "length": 0.0}]
    boundaries = {"top": "rigid", "bottom": "rigid", "left": "rigid", "right": "free"}
    fig = render_preview(100.0, 200.0, sources, boundaries)
    assert fig is not None


def test_render_field_returns_figure():
    import matplotlib
    matplotlib.use("Agg")
    field = np.random.rand(20, 30)
    fig = render_field(field, 100.0, 200.0)
    assert fig is not None


if __name__ == "__main__":
    test_placeholder_field_shape()
    test_placeholder_field_multiple_sources()
    test_estimate_runtime_positive()
    test_run_placeholder_with_progress()
    test_render_preview_returns_figure()
    test_render_field_returns_figure()
    print("All smoke tests passed.")
