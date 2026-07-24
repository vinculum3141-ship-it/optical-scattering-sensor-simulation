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

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np

from utils import heatmap


@dataclass
class Material:
    """Simple material descriptor for a surface.

    Attributes
    ----------
    name : str
        Human-readable label for the material (e.g. "silicon", "glass").
    refractive_index : float
        Refractive index of the material at the illumination wavelength.
    """

    name: str = "default"
    refractive_index: float = 1.5


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