"""
Unit tests for the Huygens solver (Phase 2).
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from huygens_solver import (
    BoundaryType,
    Boundary,
    Point2D,
    Source,
    MaterialProperties,
    SimulationParameters,
    HuygensSolver,
    run_solver,
)


# ---------------------------------------------------------------------------
# Data-class basics
# ---------------------------------------------------------------------------

def test_point2d_distance():
    a = Point2D(0.0, 0.0)
    b = Point2D(3.0, 4.0)
    assert abs(a.distance_to(b) - 5.0) < 1e-9


def test_boundary_axis_validation():
    try:
        Boundary(BoundaryType.RIGID, axis="y", position=0.0)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_simulation_parameters_wavenumber_real():
    mat = MaterialProperties(velocity=1500.0, attenuation=0.0)
    params = SimulationParameters(material=mat, frequency=1e6)
    k = params.wavenumber
    expected = 2.0 * np.pi * 1e6 / 1500.0
    assert abs(np.real(k) - expected) < 1e-3
    assert np.imag(k) == 0.0


def test_simulation_parameters_wavenumber_complex():
    mat = MaterialProperties(velocity=1500.0, attenuation=0.5, attenuation_power=1.0)
    params = SimulationParameters(material=mat, frequency=2e6)
    k = params.wavenumber
    assert np.imag(k) > 0.0


# ---------------------------------------------------------------------------
# Image source reflection
# ---------------------------------------------------------------------------

def test_image_source_rigid_vertical():
    """Rigid vertical boundary at x=0: image should mirror x-coord, same phase."""
    mat = MaterialProperties(velocity=1500.0)
    params = SimulationParameters(material=mat, grid_pts_x=10, grid_pts_z=10,
                                   grid_size_x=0.01, grid_size_z=0.01)
    solver = HuygensSolver(params)
    boundary = Boundary.vertical(BoundaryType.RIGID, x=0.0)

    src = Source(position=Point2D(0.005, 0.005), amplitude=1.0, phase=0.0)
    img = solver._get_image_source(src, boundary)

    assert abs(img.position.x - (-0.005)) < 1e-9
    assert abs(img.position.z - 0.005) < 1e-9
    assert abs(img.phase - 0.0) < 1e-9


def test_image_source_free_horizontal():
    """Free horizontal boundary at z=0: image should mirror z-coord, pi phase shift."""
    mat = MaterialProperties(velocity=1500.0)
    params = SimulationParameters(material=mat, grid_pts_x=10, grid_pts_z=10,
                                   grid_size_x=0.01, grid_size_z=0.01)
    solver = HuygensSolver(params)
    boundary = Boundary.horizontal(BoundaryType.FREE_SURFACE, z=0.0)

    src = Source(position=Point2D(0.005, 0.003), amplitude=1.0, phase=0.0)
    img = solver._get_image_source(src, boundary)

    assert abs(img.position.x - 0.005) < 1e-9
    assert abs(img.position.z - (-0.003)) < 1e-9
    assert abs(img.phase - np.pi) < 1e-9


# ---------------------------------------------------------------------------
# Solver field calculation
# ---------------------------------------------------------------------------

def test_field_shape():
    mat = MaterialProperties(velocity=1500.0)
    params = SimulationParameters(material=mat, grid_pts_x=20, grid_pts_z=30,
                                   grid_size_x=0.01, grid_size_z=0.01)
    solver = HuygensSolver(params)
    solver.add_source(Source(position=Point2D(0.0, 0.005)))
    solver.calculate_field()
    assert solver.field.shape == (20, 30)
    assert solver.field.dtype == np.complex64


def test_field_nonzero():
    mat = MaterialProperties(velocity=1500.0)
    params = SimulationParameters(material=mat, frequency=1e6,
                                   grid_pts_x=20, grid_pts_z=20,
                                   grid_size_x=0.01, grid_size_z=0.01)
    solver = HuygensSolver(params)
    solver.add_source(Source(position=Point2D(0.0, 0.005)))
    solver.calculate_field()
    assert np.max(np.abs(solver.field)) > 0


def test_intensity_nonnegative():
    mat = MaterialProperties(velocity=1500.0)
    params = SimulationParameters(material=mat, frequency=1e6,
                                   grid_pts_x=15, grid_pts_z=15,
                                   grid_size_x=0.01, grid_size_z=0.01)
    solver = HuygensSolver(params)
    solver.add_source(Source(position=Point2D(0.0, 0.005)))
    solver.add_boundary(Boundary.vertical(BoundaryType.RIGID, 0.0))
    solver.calculate_field()
    intensity = solver.get_intensity()
    assert np.all(intensity >= 0)


def test_field_with_reflections():
    """Field with boundaries should differ from field without."""
    mat = MaterialProperties(velocity=1500.0)
    params_ref = SimulationParameters(material=mat, frequency=1e6,
                                       grid_pts_x=20, grid_pts_z=20,
                                       grid_size_x=0.01, grid_size_z=0.01,
                                       max_reflection_order=1)
    solver = HuygensSolver(params_ref)
    solver.add_source(Source(position=Point2D(0.001, 0.005)))
    solver.add_boundary(Boundary.vertical(BoundaryType.RIGID, 0.0))
    field_with = solver.calculate_field().copy()

    solver2 = HuygensSolver(params_ref)
    solver2.add_source(Source(position=Point2D(0.001, 0.005)))
    field_without = solver2.calculate_field().copy()

    assert not np.allclose(field_with, field_without)


# ---------------------------------------------------------------------------
# Bridge function (run_solver)
# ---------------------------------------------------------------------------

def test_run_solver_shape():
    sources = [{"wall": "left", "position": 50.0, "power": 1.0,
                "is_line": False, "length": 0.0}]
    field = run_solver(
        grid_nx=20, grid_ny=30, box_x=50.0, box_y=80.0,
        frequency_mhz=2.0, sources=sources,
    )
    assert field.shape == (30, 20)
    assert field.dtype == np.float32


def test_run_solver_normalised():
    sources = [{"wall": "left", "position": 50.0, "power": 1.0,
                "is_line": False, "length": 0.0}]
    field = run_solver(
        grid_nx=15, grid_ny=15, box_x=50.0, box_y=50.0,
        frequency_mhz=1.0, sources=sources,
    )
    assert field.min() >= 0.0
    assert field.max() <= 1.0 + 1e-6


def test_run_solver_line_source():
    sources = [{"wall": "right", "position": 30.0, "power": 2.0,
                "is_line": True, "length": 10.0}]
    field = run_solver(
        grid_nx=20, grid_ny=20, box_x=50.0, box_y=50.0,
        frequency_mhz=3.0, sources=sources, n_reflections=2,
        attenuation=0.3, attenuation_power=1.0,
        boundaries={"top": "free", "bottom": "rigid", "left": "rigid", "right": "free"},
    )
    assert field.shape == (20, 20)


def test_run_solver_progress():
    progress_values = []
    sources = [{"wall": "left", "position": 50.0, "power": 1.0,
                "is_line": False, "length": 0.0}]
    run_solver(
        grid_nx=10, grid_ny=10, box_x=30.0, box_y=30.0,
        frequency_mhz=1.0, sources=sources,
        progress_callback=lambda f: progress_values.append(f),
    )
    assert len(progress_values) >= 4
    assert progress_values[-1] == 1.0


if __name__ == "__main__":
    test_point2d_distance()
    test_boundary_axis_validation()
    test_simulation_parameters_wavenumber_real()
    test_simulation_parameters_wavenumber_complex()
    test_image_source_rigid_vertical()
    test_image_source_free_horizontal()
    test_field_shape()
    test_field_nonzero()
    test_intensity_nonnegative()
    test_field_with_reflections()
    test_run_solver_shape()
    test_run_solver_normalised()
    test_run_solver_line_source()
    test_run_solver_progress()
    print("All solver tests passed.")
