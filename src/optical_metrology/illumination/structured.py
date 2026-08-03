"""Structured illumination source for fringe projection profilometry.

Generates phase-shifted sinusoidal fringe patterns as :class:`LightField`
intensity distributions for structured light 3D scanning (UC5).
"""

from __future__ import annotations

from typing import List, Optional

import numpy as np

from .lightfield import LightField
from .polarization import PolarizationState


class FringeProjector:
    """Generates phase-shifted sinusoidal fringe patterns.

    Parameters
    ----------
    period : float
        Fringe period in pixels (one full sinusoidal cycle).
    phase_shifts : list of float
        Phase offsets in radians for each pattern (e.g. ``[0, π/2, π, 3π/2]``).
    orientation : str
        ``"horizontal"`` or ``"vertical"`` fringe direction.
    wavelength : float
        Centre wavelength in metres (carried into each LightField).
    polarization : object
        Polarisation state carried into each LightField.
    """

    def __init__(
        self,
        period: float = 16.0,
        phase_shifts: Optional[List[float]] = None,
        orientation: str = "vertical",
        wavelength: float = 532e-9,
        polarization: object = None,
    ):
        if orientation not in ("horizontal", "vertical"):
            raise ValueError(f"orientation must be 'horizontal' or 'vertical', got {orientation!r}")
        self.period = period
        self.phase_shifts = phase_shifts if phase_shifts is not None else [0.0, 1.5707963267948966, 3.141592653589793, 4.71238898038469]
        self.orientation = orientation
        self.wavelength = wavelength
        self.polarization = polarization if polarization is not None else PolarizationState("unpolarized")

    def generate_patterns(self, shape, spacing=1.0):
        """Generate phase-shifted fringe patterns as a list of LightFields.

        Parameters
        ----------
        shape : tuple of int
            Grid dimensions ``(height, width)``.
        spacing : float
            Physical pixel spacing (not used for pattern geometry, but
            passed to the LightField for consistency).

        Returns
        -------
        list of LightField
            One LightField per phase shift, each with a sinusoidal
            intensity distribution.
        """
        height, width = shape
        if self.orientation == "vertical":
            x = np.arange(width, dtype=float)
            X = np.broadcast_to(x, (height, width))
        else:
            y = np.arange(height, dtype=float)
            X = np.broadcast_to(y[:, None], (height, width))

        fields = []
        direction = np.zeros((height, width, 3), dtype=float)
        direction[..., 2] = 1.0

        for shift in self.phase_shifts:
            intensity = 0.5 * (1.0 + np.sin(2.0 * np.pi * X / self.period + shift))
            lf = LightField(
                intensity=intensity,
                direction=direction,
                wavelength=self.wavelength,
                polarization=self.polarization,
                power=float(np.sum(intensity)),
            )
            fields.append(lf)

        return fields
