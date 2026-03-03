"""
Huygens principle-based acoustic field solver with boundary reflections.

Cleaned from solver_OLD.py for integration into the Huygen App (Phase 2).

Key points:
- Supports axis-aligned boundaries (x = const, z = const).
- Image sources clipped to segment footprint in the tangent direction.
- max_reflection_order controls how many reflection orders to include.
- Uses float32/complex64 for faster computation on typical grids.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Tuple, Optional
import numpy as np


# ---------------------------------------------------------------------------
# Boundary definitions
# ---------------------------------------------------------------------------

class BoundaryType(Enum):
    RIGID = auto()        # Neumann-like: in-phase image
    FREE_SURFACE = auto() # Dirichlet-like: π-phase-flipped image


@dataclass
class Point2D:
    """2D point (x, z) in metres."""
    x: float
    z: float

    def distance_to(self, other: "Point2D") -> float:
        return float(np.hypot(self.x - other.x, self.z - other.z))


@dataclass
class Boundary:
    """
    Axis-aligned boundary for the simulation domain.

    axis     : 'x' or 'z'
    position : coordinate value on that axis (metres)
    """
    boundary_type: BoundaryType
    axis: str
    position: float

    def __post_init__(self):
        self.axis = self.axis.lower()
        if self.axis not in ("x", "z"):
            raise ValueError("axis must be 'x' or 'z'")

    @classmethod
    def vertical(cls, boundary_type: BoundaryType, x: float) -> "Boundary":
        return cls(boundary_type=boundary_type, axis="x", position=x)

    @classmethod
    def horizontal(cls, boundary_type: BoundaryType, z: float) -> "Boundary":
        return cls(boundary_type=boundary_type, axis="z", position=z)


# ---------------------------------------------------------------------------
# Sources and material
# ---------------------------------------------------------------------------

@dataclass
class Source:
    """Monochromatic acoustic source (represented by Huygens sub-sources)."""
    position: Point2D
    amplitude: float = 1.0
    phase: float = 0.0
    width: float = 1e-3   # physical aperture width (m)
    num_subsources: int = 1


@dataclass
class MaterialProperties:
    """Material properties for the acoustic medium."""
    velocity: float                # m/s
    density: float = 1000.0        # kg/m³
    attenuation: float = 0.0       # Np/m at 1 MHz
    attenuation_power: float = 1.0 # exponent for f^n law


@dataclass
class SimulationParameters:
    """Simulation parameters for the Huygens solver."""
    material: MaterialProperties = field(
        default_factory=lambda: MaterialProperties(velocity=1480.0)
    )
    frequency: float = 1e6              # Hz
    grid_size_x: float = 0.1            # m
    grid_size_z: float = 0.1            # m
    grid_pts_x: int = 200
    grid_pts_z: int = 200
    max_reflection_order: int = 1

    @property
    def velocity(self) -> float:
        return self.material.velocity

    @property
    def wavelength(self) -> float:
        return self.velocity / self.frequency

    @property
    def wavenumber(self) -> complex:
        """Complex wavenumber including attenuation if specified."""
        k = 2.0 * np.pi * self.frequency / self.velocity
        if self.material.attenuation > 0.0:
            alpha = self.material.attenuation * (
                self.frequency / 1e6
            ) ** self.material.attenuation_power
            k = k + 1j * alpha
        return k


# ---------------------------------------------------------------------------
# Huygens solver
# ---------------------------------------------------------------------------

class HuygensSolver:
    """
    Huygens-based acoustic field solver in a 2D (x, z) slice.

    - Linear, monochromatic acoustics.
    - Superposition of point Huygens sub-sources.
    - Image sources at axis-aligned boundaries.
    """

    def __init__(self, params: SimulationParameters):
        self.params = params
        self.sources: List[Source] = []
        self.boundaries: List[Boundary] = []

        self.x = np.linspace(0, params.grid_size_x, params.grid_pts_x, dtype=np.float32)
        self.z = np.linspace(0, params.grid_size_z, params.grid_pts_z, dtype=np.float32)
        self.X, self.Z = np.meshgrid(self.x, self.z, indexing="ij")

        self.field = np.zeros_like(self.X, dtype=np.complex64)

    # ----- bookkeeping -----

    def add_boundary(self, boundary: Boundary) -> None:
        self.boundaries.append(boundary)

    def add_source(self, source: Source) -> None:
        self.sources.append(source)

    # ----- image source construction -----

    def _get_image_source(self, source: Source, boundary: Boundary) -> Source:
        """Return an image source reflected across an axis-aligned boundary."""
        phase_shift = np.pi if boundary.boundary_type == BoundaryType.FREE_SURFACE else 0.0

        if boundary.axis == "x":
            img_x = 2.0 * boundary.position - source.position.x
            img_z = source.position.z
        else:
            img_x = source.position.x
            img_z = 2.0 * boundary.position - source.position.z

        return Source(
            position=Point2D(img_x, img_z),
            amplitude=source.amplitude,
            phase=source.phase + phase_shift,
            width=source.width,
        )

    # ----- contribution from one physical source -----

    def _calculate_source_contribution(
        self, source: Source, include_boundaries: bool = True
    ) -> np.ndarray:
        """
        Compute the field contribution from a single physical source
        (discretised into Huygens sub-sources) and its image sources.
        """
        field = np.zeros_like(self.X, dtype=np.complex64)

        num_subsources = source.num_subsources
        x_offsets = np.linspace(
            -source.width / 2.0, source.width / 2.0, num_subsources, dtype=np.float32
        )
        sub_amp = source.amplitude / np.sqrt(num_subsources)

        k = self.params.wavenumber
        k_real = np.float32(np.real(k))
        k_imag = np.float32(np.imag(k))
        has_attenuation = k_imag != 0.0

        for dx in x_offsets:
            sub_pos = Point2D(source.position.x, source.position.z + float(dx))
            sub_source = Source(
                position=sub_pos,
                amplitude=sub_amp,
                phase=source.phase,
                width=source.width / num_subsources,
            )

            sources_to_process: List[Source] = [sub_source]

            if include_boundaries and self.boundaries:
                first_order_images: List[Source] = []

                if self.params.max_reflection_order >= 1:
                    for b in self.boundaries:
                        img1 = self._get_image_source(sub_source, b)
                        first_order_images.append(img1)
                        sources_to_process.append(img1)

                if self.params.max_reflection_order >= 2:
                    for img1 in first_order_images:
                        for b in self.boundaries:
                            img2 = self._get_image_source(img1, b)
                            sources_to_process.append(img2)

            for src in sources_to_process:
                dx_grid = self.X - np.float32(src.position.x)
                dz_grid = self.Z - np.float32(src.position.z)
                r = np.hypot(dx_grid, dz_grid)
                r = np.maximum(r, np.float32(1e-10))

                phase = np.float32(src.phase)
                amp = np.float32(src.amplitude) * np.exp(
                    1j * (k_real * r + phase)
                ) / np.sqrt(r)

                if has_attenuation:
                    amp = amp * np.exp(-k_imag * r)

                field += amp.astype(np.complex64)

        return field

    # ----- public API -----

    def calculate_field(self) -> np.ndarray:
        """Compute the full complex pressure field."""
        self.field.fill(0.0)
        for src in self.sources:
            self.field += self._calculate_source_contribution(src, include_boundaries=True)
        return self.field

    def get_pressure(self) -> np.ndarray:
        return self.field

    def get_intensity(self) -> np.ndarray:
        """Return |p|²."""
        return np.abs(self.field) ** 2


# ---------------------------------------------------------------------------
# Bridge: app parameters → solver run
# ---------------------------------------------------------------------------

def run_solver(
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
    Bridge between app-level parameters (mm, MHz, %) and the solver
    (metres, Hz, absolute coords).  Returns a normalised intensity
    field of shape (grid_ny, grid_nx) in [0, 1].
    """
    if boundaries is None:
        boundaries = {side: "rigid" for side in ("top", "bottom", "left", "right")}

    # Convert mm → m
    size_x = box_x * 1e-3
    size_y = box_y * 1e-3

    mat = MaterialProperties(
        velocity=1500.0,
        density=1000.0,
        attenuation=attenuation,
        attenuation_power=attenuation_power,
    )
    params = SimulationParameters(
        material=mat,
        frequency=frequency_mhz * 1e6,
        grid_size_x=size_x,
        grid_size_z=size_y,
        grid_pts_x=grid_nx,
        grid_pts_z=grid_ny,
        max_reflection_order=n_reflections,
    )

    solver = HuygensSolver(params)

    if progress_callback:
        progress_callback(0.1)

    # Map boundary strings → Boundary objects
    type_map = {"rigid": BoundaryType.RIGID, "free": BoundaryType.FREE_SURFACE}
    solver.add_boundary(Boundary.horizontal(type_map[boundaries["bottom"]], 0.0))
    solver.add_boundary(Boundary.horizontal(type_map[boundaries["top"]], size_y))
    solver.add_boundary(Boundary.vertical(type_map[boundaries["left"]], 0.0))
    solver.add_boundary(Boundary.vertical(type_map[boundaries["right"]], size_x))

    if progress_callback:
        progress_callback(0.2)

    # Map source dicts → Source objects
    # Line sources are discretised into sub-sources spaced at the grid resolution
    dx_grid = size_x / max(grid_nx - 1, 1)

    for src_dict in sources:
        wall = src_dict.get("wall", "left")
        pos_pct = src_dict.get("position", 50.0)
        power = src_dict.get("power", 1.0)
        is_line = src_dict.get("is_line", False)
        length_mm = src_dict.get("length", 0.0)

        sy = size_y * pos_pct / 100.0

        if wall == "left":
            sx = 0.0
        else:
            sx = size_x

        if is_line and length_mm > 0:
            width = length_mm * 1e-3
            n_sub = max(int(width / dx_grid), 2)
        else:
            width = 1e-4
            n_sub = 1

        solver.add_source(Source(
            position=Point2D(sx, sy),
            amplitude=power,
            phase=0.0,
            width=width,
            num_subsources=n_sub,
        ))

    if progress_callback:
        progress_callback(0.3)

    # Run solver
    solver.calculate_field()

    if progress_callback:
        progress_callback(0.9)

    # Extract intensity and normalise
    intensity = solver.get_intensity().T  # transpose to (ny, nx) for imshow

    p5, p95 = np.percentile(intensity, 5), np.percentile(intensity, 95)
    if p95 - p5 > 0:
        intensity = np.clip((intensity - p5) / (p95 - p5), 0.0, 1.0)

    if progress_callback:
        progress_callback(1.0)

    return intensity.astype(np.float32)
