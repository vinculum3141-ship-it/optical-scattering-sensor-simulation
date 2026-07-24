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