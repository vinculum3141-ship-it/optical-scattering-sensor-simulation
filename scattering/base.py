from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class ScatteredField:
    """Container for the output of a scattering evaluation.

    Attributes
    ----------
    radiance : np.ndarray, shape ``(H, W)``
        Radiance (W·m⁻²·sr⁻¹) scattered toward the observer at each
        grid point.
    outgoing_direction : np.ndarray, shape ``(H, W, 3)``
        Unit vector pointing from each surface point toward the
        observer.
    polarization : object or None
        Polarisation state carried through from the incident light
        field.  ``None`` means unpolarised or undefined.
    """

    radiance: np.ndarray
    outgoing_direction: np.ndarray
    polarization: Optional[object] = None


class ScatteringModel:
    """Base class for surface and volume scattering models.

    Subclasses must implement :meth:`evaluate` which takes an
    incident :class:`~illumination.LightField`, a :class:`~surface.Surface`,
    and a view direction, and returns a :class:`ScatteredField`.
    """

    def evaluate(self, lightfield, surface, view_direction):
        """Evaluate scattering for a given illumination, surface, and view.

        Parameters
        ----------
        lightfield : LightField
            Incident illumination over the spatial grid.
        surface : Surface
            Surface geometry (height, normals, material).
        view_direction : ndarray, shape ``(3,)``
            Unit vector from the surface toward the observer.

        Returns
        -------
        ScatteredField
            Radiance and outgoing direction at each grid point.
        """
        raise NotImplementedError