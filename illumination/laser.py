"""Laser source model with a monochromatic spectrum and low divergence."""

from .source import LightSource
from .spectrum import MonochromaticSpectrum


class Laser(LightSource):
    """A laser source with a monochromatic (single-wavelength) spectrum.

    Defaults to a uniform beam profile and very low divergence
    (1 mrad), typical of a collimated laser pointer or lab laser.

    Parameters
    ----------
    wavelength : float
        Centre wavelength in metres (default 532 nm — green).
    power : float
        Output power in Watts.
    polarization : PolarizationState or str, optional
        Defaults to unpolarized.
    coherence_length : float
        Typical coherence length in metres (default 1 cm).
    beam_profile : BeamProfile or str, optional
        Defaults to ``"uniform"`` (top-hat).
    propagation_direction : ndarray, optional
        Defaults to ``+z``.
    origin : ndarray, optional
        Defaults to the origin.
    divergence : float
        Full-angle beam divergence in radians (default 1 mrad).
    """

    def __init__(self, wavelength=532e-9, power=1.0, polarization=None, coherence_length=1e-2, beam_profile=None, propagation_direction=None, origin=None, divergence=1e-3):
        super().__init__(
            wavelength=wavelength,
            power=power,
            polarization=polarization or "unpolarized",
            coherence_length=coherence_length,
            beam_profile=beam_profile or "uniform",
            propagation_direction=propagation_direction,
            origin=origin,
            divergence=divergence,
        )
        self.spectrum = MonochromaticSpectrum(wavelength=wavelength)

    def default_spectrum(self):
        return MonochromaticSpectrum(wavelength=self.wavelength)
