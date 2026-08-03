"""Optical system and wavefront propagation models.

The central abstraction is :class:`OpticalSystem`, which describes the
imaging chain: aperture, focal length, magnification, and PSF model.
Calling :meth:`OpticalSystem.propagate_field` returns a
:class:`SensorField` — the coherent or incoherent field at the sensor.

PSF models
    - :class:`GaussianPSF` — diffraction-limited Gaussian approximation
    - :class:`AiryPSF` — ideal Airy disc from a circular pupil
    - :class:`ZernikePSF` — aberrated PSF via Zernike wavefront expansion

Wavefront
    - :class:`Wavefront` — 2D wavefront phase map
    - :class:`ZernikePolynomials` — standard Zernike basis functions

Propagation
    - :class:`OpticalPropagator` — angular-spectrum / Fresnel propagation
"""

from .airy import AiryPSF
from .base import OpticalSystem, SensorField
from .propagator import OpticalPropagator
from .psf import GaussianPSF
from .zernike import Wavefront, ZernikePolynomials, ZernikePSF

__all__ = [
    "AiryPSF",
    "GaussianPSF",
    "OpticalPropagator",
    "OpticalSystem",
    "SensorField",
    "Wavefront",
    "ZernikePolynomials",
    "ZernikePSF",
]
