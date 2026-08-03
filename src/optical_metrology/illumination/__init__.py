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
    - :class:`FlatFieldSource` — uniform square source for calibration
    - :class:`MultiSpectralSource` — multiple discrete spectral bands (UC2)
    - :class:`MultiChannelLightField` — per-channel fields stacked in channels dim (UC2)
    - :class:`FilterWheelSource` — sequentially selects one band per frame (UC2)
    - :class:`TemporalEnvelope` — pulsed / modulated power envelope
    - :class:`SourceExtent` — extended aperture (angular extent in object space)
    - :class:`FringeProjector` — phase-shifted sinusoidal fringe projector (UC5)
    - :class:`ScanningMechanism` — raster/spiral scanner for LiDAR (UC6)

Profile models (:mod:`illumination.profiles`)
    - :class:`UniformBeamProfile` — constant intensity
    - :class:`TopHatBeamProfile` — circular top-hat
    - :class:`GaussianBeamProfile` — TEM\\ :sub:`00` Gaussian

Spectral models (:mod:`illumination.spectrum`)
    - :class:`MonochromaticSpectrum` — single wavelength
    - :class:`GaussianSpectrum` — Gaussian line shape
    - :class:`BlackbodySpectrum` — Planck distribution
    - :class:`BroadbandSpectrum` — flat over a range

Directional lighting helpers
    - :func:`bright_field` — on-axis collimated / ring-light configuration (UC1)
    - :func:`dark_field` — off-axis grazing incidence (UC1)
    - :func:`ring_light` — multi-angle ring configuration (UC1)
"""

from .broadband import BroadbandLamp
from .directional import bright_field, dark_field, ring_light
from .extent import SourceExtent
from .flatfield import FlatFieldSource
from .laser import Laser
from .led import LED
from .lightfield import LightField
from .multispectral import ChannelConfig, FilterWheelSource, MultiChannelLightField, MultiSpectralSource
from .polarization import PolarizationState
from .profiles import BeamProfile, GaussianBeamProfile, TopHatBeamProfile, UniformBeamProfile
from .scanning import ScanningMechanism
from .source import LightSource
from .spectrum import BroadbandSpectrum, BlackbodySpectrum, GaussianSpectrum, MonochromaticSpectrum, SpectralDistribution
from .sunlight import Sunlight
from .structured import FringeProjector
from .temporal import TemporalEnvelope

__all__ = [
    "BeamProfile",
    "BroadbandLamp",
    "bright_field",
    "BroadbandSpectrum",
    "BlackbodySpectrum",
    "dark_field",
    "FlatFieldSource",
    "ChannelConfig",
    "FilterWheelSource",
    "FringeProjector",
    "GaussianBeamProfile",
    "GaussianSpectrum",
    "LED",
    "Laser",
    "LightField",
    "LightSource",
    "MultiChannelLightField",
    "MultiSpectralSource",
    "MonochromaticSpectrum",
    "PolarizationState",
    "ring_light",
    "SpectralDistribution",
    "SourceExtent",
    "ScanningMechanism",
    "Sunlight",
    "TemporalEnvelope",
    "TopHatBeamProfile",
    "UniformBeamProfile",
]
