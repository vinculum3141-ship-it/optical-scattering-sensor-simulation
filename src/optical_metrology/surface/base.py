"""Surface geometry representation and analysis.

This module defines the core data structures for representing surface
geometry in the simulation framework:

    - :class:`Material` — simple material descriptor (name, refractive index)
    - :class:`Surface` — a full geometric description derived from a height map
      (normals, slopes, curvature, roughness)
    - :class:`GeometryAnalyzer` — static analysis that converts a raw 2D height
      array into a :class:`Surface` via finite-difference gradients
    - :class:`SurfaceGenerator` — abstract base for creating height maps with
      particular geometric features

Surface generators in :mod:`surface.generators` extend both :class:`Surface`
and :class:`SurfaceGenerator`, acting as both data container and factory.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple, Union

import numpy as np

from ..utils import heatmap


@dataclass(frozen=True)
class SellmeierCoefficients:
    """Sellmeier dispersion coefficients for wavelength-dependent refractive index.

    The Sellmeier equation gives the refractive index as a function of
    wavelength (in metres)::

        n²(λ) = 1 + B₁λ²/(λ² - C₁) + B₂λ²/(λ² - C₂) + B₃λ²/(λ² - C₃)

    where λ is in **micrometres** (the conventional unit for Sellmeier
    coefficients).  Common material coefficients are tabulated in the
    literature (e.g. refractiveindex.info).

    Parameters
    ----------
    B1, B2, B3 : float
        Sellmeier oscillator strengths.
    C1, C2, C3 : float
        Sellmeier oscillator wavelengths squared (µm²).
    """

    B1: float = 0.0
    B2: float = 0.0
    B3: float = 0.0
    C1: float = 0.0
    C2: float = 0.0
    C3: float = 0.0

    def n(self, wavelength_m: float) -> float:
        """Refractive index at *wavelength_m* (metres)."""
        lam_um = wavelength_m * 1e6
        lam2 = lam_um * lam_um
        n2 = 1.0
        n2 += self.B1 * lam2 / (lam2 - self.C1) if self.C1 != 0 else 0.0
        n2 += self.B2 * lam2 / (lam2 - self.C2) if self.C2 != 0 else 0.0
        n2 += self.B3 * lam2 / (lam2 - self.C3) if self.C3 != 0 else 0.0
        return float(np.sqrt(max(n2, 1.0)))


@dataclass
class Material:
    """Material descriptor for a surface with optional wavelength-dependent properties.

    The refractive index can be specified as:

    * a constant scalar via *refractive_index* (simplest, default 1.5),
    * a callable ``n(wavelength)`` via *refractive_index_fn*,
    * Sellmeier dispersion coefficients via *sellmeier*,
    * tabulated ``(wavelength, n)`` data via *nk_table*.

    The first non-None source in this priority order is used.

    Parameters
    ----------
    name : str
        Human-readable label (e.g. "silicon", "glass", "gold").
    refractive_index : float
        Constant refractive index (fallback when no wavelength-dependent
        model is provided).
    extinction : float
        Extinction coefficient k (imaginary part of refractive index).
        Zero for non-absorbing dielectrics.
    sellmeier : SellmeierCoefficients or None
        Sellmeier dispersion model for n(λ).
    nk_table : dict or list of tuples or None
        Tabulated n(λ) and k(λ).  Either a dict mapping wavelength (m)
        → ``(n, k)``, or a list of ``(wavelength_m, n)`` / ``(wavelength_m, n, k)``
        tuples.  Linear interpolation is used between tabulated points.
    refractive_index_fn : Callable or None
        Arbitrary function ``n(wavelength_m) → float``.
    """

    name: str = "default"
    refractive_index: float = 1.5
    extinction: float = 0.0
    sellmeier: Optional[SellmeierCoefficients] = None
    nk_table: Optional[Union[Dict[float, float], List[Tuple[float, float]]]] = None
    refractive_index_fn: Optional[Callable[[float], float]] = None

    def _interp_nk(self, wavelength: float):
        """Return (n, k) interpolated from self.nk_table."""
        nk = self.nk_table
        if isinstance(nk, dict):
            items = sorted(nk.items())
            lambdas = np.array([p[0] for p in items])
            vals = np.array([p[1] for p in items])
            n = float(np.interp(wavelength, lambdas, vals[:, 0]))
            k = float(np.interp(wavelength, lambdas, vals[:, 1]))
        else:
            items = sorted(nk, key=lambda x: x[0])
            lambdas = np.array([p[0] for p in items])
            ns = np.array([p[1] for p in items])
            ks = np.array([p[2] if len(p) > 2 else 0.0 for p in items])
            n = float(np.interp(wavelength, lambdas, ns))
            k = float(np.interp(wavelength, lambdas, ks))
        return n, k

    def refractive_index_at(self, wavelength: float) -> float:
        """Refractive index at the given wavelength (metres).

        Priority: *refractive_index_fn* → *sellmeier* → *nk_table* →
        *refractive_index* (constant fallback).
        """
        if self.refractive_index_fn is not None:
            return self.refractive_index_fn(wavelength)
        if self.sellmeier is not None:
            return self.sellmeier.n(wavelength)
        if self.nk_table is not None:
            return self._interp_nk(wavelength)[0]
        return self.refractive_index

    def extinction_at(self, wavelength: float) -> float:
        """Extinction coefficient k at the given wavelength."""
        if self.nk_table is not None:
            return self._interp_nk(wavelength)[1]
        return self.extinction

    def F0(self, wavelength: float, n_incident: float = 1.0) -> float:
        """Fresnel reflectance at normal incidence (F₀) for *wavelength*.

        Uses the standard formula for normal-incidence Fresnel
        reflectance::

            F₀ = ((n₁ - n₂)² + k₂²) / ((n₁ + n₂)² + k₂²)

        where n₁ = *n_incident* (usually 1.0 for air/vacuum) and
        n₂ + i·k₂ is the complex refractive index of the material.
        """
        n2 = self.refractive_index_at(wavelength)
        k2 = self.extinction_at(wavelength)
        if k2 == 0.0 and n_incident == 1.0:
            return float(((n_incident - n2) / (n_incident + n2)) ** 2)
        num = (n_incident - n2) ** 2 + k2 ** 2
        den = (n_incident + n2) ** 2 + k2 ** 2
        return float(num / den)


@dataclass
class Surface:
    """Geometric description of a surface derived from a height map.

    All geometric quantities are computed from the height map by
    :class:`GeometryAnalyzer`.  The surface is defined on a regular
    2D grid — the same grid that an illumination :class:`~illumination.LightField`
    covers — so that per-pixel scattering calculations are straightforward.

    Attributes
    ----------
    height : np.ndarray, shape ``(H, W)``
        Elevation at each grid point.
    normals : np.ndarray, shape ``(H, W, 3)``
        Unit surface-normal vectors (x, y, z components).
    curvature : np.ndarray, shape ``(H, W)``
        Laplacian of the height field — a scalar measure of local bending.
    slope_x : np.ndarray, shape ``(H, W)``
        Gradient of the height field in the x-direction.
    slope_y : np.ndarray, shape ``(H, W)``
        Gradient of the height field in the y-direction.
    roughness : float
        Root-mean-square deviation of the height from its mean.
    material : Material
        Material descriptor attached to the surface.
    """

    height: np.ndarray
    normals: np.ndarray
    curvature: np.ndarray
    slope_x: np.ndarray
    slope_y: np.ndarray
    roughness: float
    material: Material

    @staticmethod
    def rotation_matrix_x(angle: float) -> np.ndarray:
        """3×3 rotation matrix around the x-axis by *angle* radians."""
        c, s = np.cos(angle), np.sin(angle)
        return np.array([[1.0, 0.0, 0.0],
                         [0.0, c, -s],
                         [0.0, s, c]])

    @staticmethod
    def rotation_matrix_y(angle: float) -> np.ndarray:
        """3×3 rotation matrix around the y-axis by *angle* radians."""
        c, s = np.cos(angle), np.sin(angle)
        return np.array([[c, 0.0, s],
                         [0.0, 1.0, 0.0],
                         [-s, 0.0, c]])

    @staticmethod
    def rotation_matrix_z(angle: float) -> np.ndarray:
        """3×3 rotation matrix around the z-axis by *angle* radians."""
        c, s = np.cos(angle), np.sin(angle)
        return np.array([[c, -s, 0.0],
                         [s, c, 0.0],
                         [0.0, 0.0, 1.0]])

    def transform(self, R: np.ndarray):
        """Apply a 3×3 rotation matrix to the surface normals.

        The rotation acts on the surface normals and slope vectors,
        re-orienting the surface in the lab frame.  The height map
        itself is not modified — the transformation is applied to
        the derived geometric quantities that scattering models use.

        Parameters
        ----------
        R : np.ndarray, shape ``(3, 3)``
            Rotation matrix (must be orthogonal, ‖R‖ = 1).

        Returns
        -------
        Surface
            ``self`` for chaining.
        """
        H, W = self.normals.shape[:2]

        n_flat = self.normals.reshape(-1, 3)
        self.normals = (R @ n_flat.T).T.reshape(H, W, 3)
        norms = np.linalg.norm(self.normals, axis=2, keepdims=True)
        self.normals = self.normals / np.where(norms == 0.0, 1.0, norms)

        s_flat = np.stack([self.slope_x, self.slope_y, np.zeros_like(self.slope_x)], axis=-1)
        s_flat = s_flat.reshape(-1, 3)
        s_rot = (R @ s_flat.T).T.reshape(H, W, 3)
        self.slope_x = s_rot[..., 0]
        self.slope_y = s_rot[..., 1]

        return self

    def rotate_x(self, angle: float):
        """Rotate the surface around the x-axis by *angle* radians."""
        return self.transform(self.rotation_matrix_x(angle))

    def rotate_y(self, angle: float):
        """Rotate the surface around the y-axis by *angle* radians."""
        return self.transform(self.rotation_matrix_y(angle))

    def rotate_z(self, angle: float):
        """Rotate the surface around the z-axis by *angle* radians."""
        return self.transform(self.rotation_matrix_z(angle))

    def visualize(self, max_width: int = 72, color: bool = True) -> str:
        """Render the surface geometry as terminal heatmaps.

        Shows three views side by side:

            **Height**  — elevations (uses :func:`~utils.visualize.heatmap`)
            **Slope**   — gradient magnitude ``√(∂z/∂x² + ∂z/∂y²)``
            **Curvature** — Laplacian; valleys (blue) ← flat (white) → ridges (red)

        Parameters
        ----------
        max_width : int
            Maximum character width per panel.
        color : bool
            If True, use ANSI colour codes.

        Returns
        -------
        str
            Multi-line string ready to ``print()``.
        """
        h, w = self.height.shape

        # Slope magnitude
        slope_mag = np.sqrt(self.slope_x**2 + self.slope_y**2)

        # Curvature — normalised to ±max|κ| with white at zero
        cmax = max(abs(self.curvature.min()), abs(self.curvature.max()))
        if cmax > 0:
            c_norm = self.curvature / cmax  # [-1, 1]
        else:
            c_norm = np.zeros_like(self.curvature)
        # Map to shades: valleys (blue) = left half, ridges (red) = right half
        _C = [" ", "\u2591", "\u2592", "\u2593", "\u2588"]
        c_shade = (np.abs(c_norm) * (len(_C) - 1)).astype(np.intp).clip(0, len(_C) - 1)
        c_lines = []
        if not color:
            c_lines = ["".join(_C[idx] for idx in row) for row in c_shade]
        else:
            for row_idx in range(h):
                buf = []
                for col_idx in range(w):
                    ch = _C[c_shade[row_idx, col_idx]]
                    val = c_norm[row_idx, col_idx]
                    if val < -0.05:
                        colour = 34  # blue — valley
                    elif val > 0.05:
                        colour = 31  # red — ridge
                    else:
                        colour = 37  # white — flat
                    buf.append(f"\033[1;{colour}m{ch}\033[0m")
                c_lines.append("".join(buf))

        # Height panel
        h_panel = heatmap(self.height, max_width=max_width, color=color)
        # Slope panel
        s_panel = heatmap(slope_mag, max_width=max_width, color=color)
        # Curvature panel
        c_panel_lines = "\n".join(c_lines)

        sep = "\u2500" * max_width
        info = (
            f"Surface  ({h}\u00d7{w})  "
            f"material={self.material.name}  "
            f"Rq={self.roughness:.4g}  "
            f"height=[{self.height.min():.4g}, {self.height.max():.4g}]"
        )
        return (
            f"{info}\n{sep}\n"
            f"Height\n{h_panel}\n\n"
            f"Slope\n{s_panel}\n\n"
            f"Curvature (blue=valley  white=flat  red=ridge)\n{c_panel_lines}"
        )

    def phase_screen(self, wavelength: float) -> np.ndarray:
        """Phase delay map [radians] from surface heights.

        For a reflection, the round-trip optical path difference is
        :math:`2h`, giving a phase delay :math:`\\phi = 4\\pi h / \\lambda`.
        This is used to model speckle and interference effects when
        combined with a source's coherence length.

        Parameters
        ----------
        wavelength : float
            Illumination wavelength in metres.

        Returns
        -------
        np.ndarray
            2D array of phase delays in radians, same shape as
            :attr:`height`.
        """
        return 4.0 * np.pi * self.height / wavelength


class GeometryAnalyzer:
    """Compute geometric quantities from a height map.

    The analyzer takes a 2D height array and extracts:
        - surface normals (via finite-difference gradient)
        - curvature (sum of second derivatives)
        - slope components
        - RMS roughness

    Usage
    -----
    >>> height = np.random.randn(32, 32)
    >>> surface = GeometryAnalyzer.analyze(height, material=Material("silicon"))
    """

    @staticmethod
    def analyze(height: np.ndarray, material: Optional[Material] = None) -> Surface:
        """Derive a full :class:`Surface` description from a height map.

        Parameters
        ----------
        height : np.ndarray
            2D array of elevation values.  Must have exactly two dimensions.
        material : Material or None
            Material to attach to the result.  Defaults to a generic ``Material()``.

        Returns
        -------
        Surface
            Structured surface with normals, slopes, curvature, and roughness.
        """
        height = np.asarray(height, dtype=float)
        if height.ndim != 2:
            raise ValueError("height must be a 2D array")

        # Surface normals from gradient of the height field.
        # For a surface z = h(x, y), the normal direction is:
        #   n ∝ (-∂h/∂x, -∂h/∂y, 1)
        # The negative signs ensure the normal points "upward" (+z).
        dzdy, dzdx = np.gradient(height)
        normal = np.dstack((-dzdx, -dzdy, np.ones_like(height)))
        norm = np.linalg.norm(normal, axis=2, keepdims=True)
        normals = normal / np.where(norm == 0.0, 1.0, norm)

        # Curvature is the Laplacian (sum of unmixed second partial derivatives).
        curvature = np.gradient(dzdx)[0] + np.gradient(dzdy)[1]
        # RMS roughness = standard deviation of height about its mean.
        roughness = float(np.sqrt(np.mean((height - np.mean(height)) ** 2)))

        return Surface(
            height=height,
            normals=normals,
            curvature=curvature,
            slope_x=dzdx,
            slope_y=dzdy,
            roughness=roughness,
            material=material or Material(),
        )


class SurfaceGenerator:
    """Base class for creating a height map and turning it into a :class:`Surface`.

    Subclasses override :meth:`generate` to produce a height map with
    particular geometric features (flat, rough, scratched, particle-covered, etc.).

    The :meth:`create_surface` convenience method chains generation and analysis
    into a single call.  The same can be achieved by calling the instance directly:

    >>> gen = MySurfaceGenerator()
    >>> surface = gen(shape=(64, 64), material=Material("glass"))
    """

    def generate(self, shape: Tuple[int, int]) -> np.ndarray:
        """Create a height map for the given grid shape.

        Parameters
        ----------
        shape : tuple of int
            Grid dimensions ``(height, width)`` in pixels.

        Returns
        -------
        np.ndarray
            2D height array of shape ``shape``.
        """
        raise NotImplementedError

    def create_surface(self, shape: Tuple[int, int], material: Optional[Material] = None) -> Surface:
        """Generate a height map and analyse it into a :class:`Surface`.

        Parameters
        ----------
        shape : tuple of int
            Grid dimensions ``(height, width)``.
        material : Material or None
            Material to attach to the surface.

        Returns
        -------
        Surface
        """
        height = self.generate(shape)
        return GeometryAnalyzer.analyze(height, material=material)

    def __call__(self, shape: Tuple[int, int], material: Optional[Material] = None) -> Surface:
        """Convenience — same as :meth:`create_surface`."""
        return self.create_surface(shape, material=material)