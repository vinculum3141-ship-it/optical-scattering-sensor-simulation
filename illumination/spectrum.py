"""Spectral distribution models for optical sources.

Each class represents a different physical model of a source's
wavelength content (monochromatic, Gaussian, blackbody, flat
broadband).  These are used by :class:`LightSource` subclasses to
describe their emission spectrum.
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class SpectralDistribution:
    """Base class for all spectral distribution models.

    Attributes
    ----------
    kind : str
        Human-readable label describing the type of spectrum
        (e.g. ``"monochromatic"``, ``"gaussian"``).
    """

    kind: str = "monochromatic"


@dataclass(frozen=True)
class MonochromaticSpectrum(SpectralDistribution):
    """A single-wavelength (delta-function) spectrum.

    Use for idealised laser sources where the linewidth is negligible.

    Attributes
    ----------
    wavelength : float
        Centre wavelength in metres.
    """

    wavelength: float = 0.0

    def __post_init__(self):
        super().__init__(kind="monochromatic")


@dataclass(frozen=True)
class GaussianSpectrum(SpectralDistribution):
    """Gaussian-shaped spectral line profile.

    Use for sources such as LEDs where the emission spectrum is
    approximately Gaussian.

    Attributes
    ----------
    peak_wavelength : float
        Centre wavelength of the emission peak in metres.
    width : float
        Full-width-at-half-maximum (FWHM) of the spectral line in
        metres.
    """

    peak_wavelength: float = 0.0
    width: float = 0.0

    def __post_init__(self):
        super().__init__(kind="gaussian")


@dataclass(frozen=True)
class BlackbodySpectrum(SpectralDistribution):
    """Planck black-body spectrum.

    Use for thermal sources such as sunlight or incandescent lamps.

    Attributes
    ----------
    temperature : float
        Effective temperature in Kelvin.
    """

    temperature: float = 5778.0

    def __post_init__(self):
        super().__init__(kind="blackbody")


@dataclass(frozen=True)
class BroadbandSpectrum(SpectralDistribution):
    """Flat (constant-power) spectrum over a finite wavelength range.

    Use as a simple model for broadband lamps or white-light sources.

    Attributes
    ----------
    wavelength_range : tuple of (float, float)
        Lower and upper wavelength bounds in metres.
    """

    wavelength_range: Tuple[float, float] = (400e-9, 700e-9)

    def __post_init__(self):
        super().__init__(kind="broadband")
