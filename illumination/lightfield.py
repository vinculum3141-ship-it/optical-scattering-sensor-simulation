"""Data structure that holds the illumination field over a spatial grid.

A :class:`LightField` is the output of
:meth:`LightSource.generate_light_field`.  It is intentionally kept
as a plain container so that downstream modules (scattering, optics,
detector) can consume it without depending on the source details.
"""

from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class LightField:
    """Structured description of illumination over a 2D spatial grid.

    Attributes
    ----------
    intensity : np.ndarray
        2D array of intensity values (W/m²) at each grid point.
        Shape ``(height, width)``.
    direction : np.ndarray
        3D array of unit propagation vectors at each grid point.
        Shape ``(height, width, 3)``.
    wavelength : float
        Centre wavelength of the illumination in metres.
    polarization : PolarizationState
        Polarisation state of the field.
    phase : np.ndarray | None
        2D array of relative optical phase (radians) at each grid
        point.  ``None`` means the phase is undefined or irrelevant
        for the application.
    """

    intensity: np.ndarray
    direction: np.ndarray
    wavelength: float
    polarization: object
    phase: Optional[np.ndarray] = None
