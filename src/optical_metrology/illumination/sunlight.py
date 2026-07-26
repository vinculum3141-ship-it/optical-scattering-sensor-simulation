"""Sunlight (black-body) source model."""

from .source import LightSource
from .spectrum import BlackbodySpectrum


class Sunlight(LightSource):
    """A thermal source approximating sunlight with a black-body spectrum.

    Defaults to the Sun's effective photospheric temperature (5778 K)
    and modest divergence (0.53 rad, the angular diameter of the Sun
    as seen from Earth).

    Parameters
    ----------
    temperature : float
        Effective black-body temperature in Kelvin (default 5778 K).
    power : float
        Optical power in Watts.
    polarization : PolarizationState or str, optional
        Defaults to unpolarized.
    coherence_length : float
        Coherence length in metres (default 1 µm).
    beam_profile : BeamProfile, optional
        Defaults to ``None`` (uniform).
    propagation_direction : ndarray, optional
        Defaults to ``+z``.
    origin : ndarray, optional
        Defaults to the origin.
    divergence : float
        Full-angle beam divergence in radians (default 0.53 rad).
    """

    def __init__(self, temperature=5778.0, power=1.0, polarization=None, coherence_length=1e-6, beam_profile=None, propagation_direction=None, origin=None, divergence=0.53):
        super().__init__(
            wavelength=550e-9,
            power=power,
            polarization=polarization or "unpolarized",
            coherence_length=coherence_length,
            beam_profile=beam_profile or "uniform",
            propagation_direction=propagation_direction,
            origin=origin,
            divergence=divergence,
        )
        self.spectrum = BlackbodySpectrum(temperature=temperature)

    def default_spectrum(self):
        return BlackbodySpectrum(temperature=5778.0)
