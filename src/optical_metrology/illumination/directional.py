"""Directional illumination configurations for inspection (UC1).

Provides factory functions that return pre-configured :class:`LightSource`
instances for common machine-vision illumination geometries:
bright-field, dark-field, and ring light.
"""

from __future__ import annotations

from typing import Tuple

import numpy as np

from .polarization import PolarizationState
from .source import LightSource


def bright_field(
    wavelength: float = 532e-9,
    power: float = 1.0,
    incidence_angle: float = 0.0,
    polarization: str = "unpolarized",
) -> LightSource:
    """Create a bright-field illumination source.

    Bright-field places the source (nearly) coaxial with the optical
    axis so that the detector receives directly reflected light.
    Ideal for mirror-like surfaces and absorption contrast.

    Parameters
    ----------
    wavelength : float
        Centre wavelength in metres.
    power : float
        Total optical power in Watts.
    incidence_angle : float
        Incidence angle in radians (default 0 = normal incidence).
    polarization : str
        Polarisation state string.

    Returns
    -------
    LightSource
    """
    src = LightSource(
        wavelength=wavelength,
        power=power,
        polarization=PolarizationState(polarization),
        wavefront="planar",
        divergence=0.0,
    )
    src.incidence_angle = incidence_angle
    return src


def dark_field(
    wavelength: float = 532e-9,
    power: float = 2.0,
    incidence_angle: float = 0.785,
    azimuth: float = 0.0,
    polarization: str = "unpolarized",
) -> LightSource:
    """Create a dark-field illumination source.

    Dark-field places the source at a steep incidence angle so that
    the detector collects only scattered light from defects or
    surface features.  The specular reflection misses the entrance
    pupil.

    Parameters
    ----------
    wavelength : float
        Centre wavelength in metres.
    power : float
        Total optical power in Watts (typically higher than
        bright-field to compensate for weaker scattered signal).
    incidence_angle : float
        Incidence angle in radians (default ~45°).
    azimuth : float
        Azimuthal angle in radians (0 = along x-axis).
    polarization : str
        Polarisation state string.

    Returns
    -------
    LightSource
    """
    src = LightSource(
        wavelength=wavelength,
        power=power,
        polarization=PolarizationState(polarization),
        wavefront="planar",
        divergence=0.0,
    )
    src.incidence_angle = incidence_angle
    cz = np.cos(incidence_angle)
    sz = np.sin(incidence_angle)
    az = azimuth
    src.propagation_direction = np.array(
        [sz * np.cos(az), sz * np.sin(az), -cz], dtype=float
    )
    return src


def ring_light(
    wavelength: float = 532e-9,
    power: float = 3.0,
    ring_angle: float = 0.698,
    n_segments: int = 8,
    polarization: str = "unpolarized",
) -> Tuple[LightSource, ...]:
    """Create a multi-segment ring light.

    Returns *n_segments* :class:`LightSource` instances equally
    spaced in azimuth, each at *ring_angle* from the optical axis.
    Summing their contributions approximates a conical dark-field
    illuminator.

    Parameters
    ----------
    wavelength : float
        Centre wavelength in metres.
    power : float
        Total power *per segment* in Watts.
    ring_angle : float
        Angle of each segment from the optical axis in radians
        (default ~40°).
    n_segments : int
        Number of azimuthal segments (default 8).
    polarization : str
        Polarisation state string.

    Returns
    -------
    tuple of LightSource
    """
    segment_power = power
    sources = []
    for k in range(n_segments):
        azimuth = 2.0 * np.pi * k / n_segments
        src = dark_field(
            wavelength=wavelength,
            power=segment_power,
            incidence_angle=ring_angle,
            azimuth=azimuth,
            polarization=polarization,
        )
        sources.append(src)
    return tuple(sources)
