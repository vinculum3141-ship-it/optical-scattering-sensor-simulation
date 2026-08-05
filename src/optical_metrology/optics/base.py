"""Optical system description and sensor-plane output.

This module provides data structures for describing an imaging optical
system and the resulting field at the sensor plane:

    - :class:`OpticalSystem` — physical parameters of the imaging optics
      (aperture, focal length, numerical aperture, magnification, PSF, aberrations)
    - :class:`SensorField` — the output of :class:`~optics.propagator.OpticalPropagator`,
      holding irradiance, wavelength, polarization, and optical path length

The numerical aperture is auto-computed from aperture diameter and focal
length if not explicitly provided.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class OpticalSystem:
    """Physical properties of an optical imaging system.

    Attributes
    ----------
    aperture_diameter : float
        Diameter of the entrance pupil in metres (default 10 mm).
    focal_length : float
        Effective focal length in metres (default 100 mm).
    numerical_aperture : float or None
        NA = D / (2f).  Auto-computed if not provided.
    magnification : float
        Lateral magnification of the imaging system (default 1.0).
    wavelength : float
        Design wavelength in metres (default 532 nm).
    psf : object or None
        Point-spread function model (e.g. :class:`~optics.psf.GaussianPSF`).
    defocus : float
        Axial displacement of the sensor from the focal plane in metres
        (default 0.0 = perfectly in focus).  Positive/negative values
        push the sensor behind/in front of focus and widen the PSF.
    aberrations : dict or None
        Optional dictionary of aberration coefficients
        (reserved for future use).
    """

    aperture_diameter: float = 0.01
    focal_length: float = 0.1
    numerical_aperture: Optional[float] = None
    magnification: float = 1.0
    wavelength: float = 532e-9
    psf: Optional[object] = None
    defocus: float = 0.0
    aberrations: Optional[dict] = None

    def __post_init__(self):
        if self.numerical_aperture is None:
            self.numerical_aperture = self.aperture_diameter / (2.0 * self.focal_length)


@dataclass
class SensorField:
    """Output of optical propagation at the sensor plane.

    Attributes
    ----------
    irradiance : np.ndarray
        2D array of irradiance values (W/m²) at the sensor.
    wavelength : float
        Centre wavelength in metres.
    polarization : object or None
        Polarisation state carried through the optical system.
    optical_path_length : float
        Optical path length from object to image plane (default 0.0).
    """

    irradiance: np.ndarray
    wavelength: float
    polarization: Optional[object] = None
    optical_path_length: float = 0.0
