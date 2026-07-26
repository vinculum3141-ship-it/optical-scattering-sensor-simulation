"""Source extent model for extended / partially coherent sources.

A :class:`SourceExtent` describes the spatial extent and coherence
properties of an extended optical source.  When composed into a
:class:`LightSource`, it enables modelling of partial coherence effects
such as blurring from finite source size.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class SourceExtent:
    """Spatial extent and partial coherence of an extended source.

    Parameters
    ----------
    shape : str
        ``"uniform_disk"``, ``"gaussian"``, or ``"rectangle"``.
    radius : float
        Characteristic radius (or half-width) of the source in metres.
        For ``"rectangle"`` this is the half-width along x.
    height : float or None
        Half-height of the source for ``"rectangle"`` shape.  If
        ``None``, defaults to *radius* (square aperture).
    coherence_factor : float
        Spatial coherence factor (0 = fully incoherent, 1 = fully
        coherent).  Defaults to 1.0.
    """

    shape: str = "uniform_disk"
    radius: float = 1e-3
    height: Optional[float] = None
    coherence_factor: float = 1.0

    def __post_init__(self):
        if self.shape not in ("uniform_disk", "gaussian", "rectangle"):
            raise ValueError(f"Unsupported source shape: {self.shape!r}")
        if self.shape == "rectangle" and self.height is None:
            self.height = self.radius
        if not 0.0 <= self.coherence_factor <= 1.0:
            raise ValueError("coherence_factor must be in [0, 1]")

    @property
    def area(self) -> float:
        """Physical area of the source in m²."""
        if self.shape == "uniform_disk":
            return np.pi * self.radius ** 2
        if self.shape == "gaussian":
            return np.pi * self.radius ** 2
        return 4.0 * self.radius * self.height

    def aperture_function(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        """Evaluate the normalised source aperture on a 2D grid.

        Parameters
        ----------
        x, y : ndarray
            Physical coordinate grids.

        Returns
        -------
        ndarray
            Aperture transmission (0 outside, 1 inside for hard apertures;
            Gaussian profile for ``"gaussian"`` shape).
        """
        if self.shape == "uniform_disk":
            r = np.sqrt(x ** 2 + y ** 2)
            return np.where(r <= self.radius, 1.0, 0.0)
        if self.shape == "gaussian":
            return np.exp(-(x ** 2 + y ** 2) / (2.0 * self.radius ** 2))
        half_w = self.radius
        half_h = self.height
        return np.where(
            (np.abs(x) <= half_w) & (np.abs(y) <= half_h), 1.0, 0.0
        )
