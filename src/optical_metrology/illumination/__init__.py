"""Illumination models for optical scattering sensor simulation.

This package provides a modular set of classes for describing optical
sources in physically meaningful terms.  The central abstraction is
:class:`LightSource`, which combines wavelength, power, polarisation,
a beam profile, and a spectral model.  Calling
:meth:`LightSource.generate_light_field` produces a
:class:`LightField` — a structured array of intensity, direction,
wavelength, and polarisation over a 2D grid.

Concrete source types
    - :class:`Laser` — monochromatic, low-divergence source
    - :class:`LED` — Gaussian spectrum source with moderate divergence
    - :class:`Sunlight` — black-body thermal source
    - :class:`BroadbandLamp` — flat-spectrum white-light source

Profile models (:mod:`illumination.profiles`)
    - :class:`UniformBeamProfile` — constant intensity
    - :class:`TopHatBeamProfile` — circular top-hat
    - :class:`GaussianBeamProfile` — TEM\\ :sub:`00` Gaussian

Spectral models (:mod:`illumination.spectrum`)
    - :class:`MonochromaticSpectrum` — single wavelength
    - :class:`GaussianSpectrum` — Gaussian line shape
    - :class:`BlackbodySpectrum` — Planck distribution
    - :class:`BroadbandSpectrum` — flat over a range
"""

from .broadband import BroadbandLamp
from .flatfield import FlatFieldSource
from .laser import Laser
from .led import LED
from .lightfield import LightField
from .polarization import PolarizationState
from .profiles import BeamProfile, GaussianBeamProfile, TopHatBeamProfile, UniformBeamProfile
from .source import LightSource
from .spectrum import BroadbandSpectrum, BlackbodySpectrum, GaussianSpectrum, MonochromaticSpectrum, SpectralDistribution
from .sunlight import Sunlight

__all__ = [
    "BeamProfile",
    "BroadbandLamp",
    "FlatFieldSource",
    "BroadbandSpectrum",
    "BlackbodySpectrum",
    "GaussianBeamProfile",
    "GaussianSpectrum",
    "LED",
    "Laser",
    "LightField",
    "LightSource",
    "MonochromaticSpectrum",
    "PolarizationState",
    "SpectralDistribution",
    "Sunlight",
    "TopHatBeamProfile",
    "UniformBeamProfile",
]
