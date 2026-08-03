"""Broadband lamp source model with a flat spectrum over a wavelength range."""

from .source import LightSource
from .spectrum import BroadbandSpectrum


class BroadbandLamp(LightSource):
    """A broadband white-light lamp with a flat spectrum over a finite range.

    Useful for modelling halogen or xenon arc lamps in the visible
    band.

    Parameters
    ----------
    wavelength_range : tuple of (float, float)
        Lower and upper bounds of the emitted wavelength band in
        metres (default 400–700 nm).
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
        Full-angle beam divergence in radians (default 0.5 rad).
    """

    def __init__(self, wavelength_range=(400e-9, 700e-9), power=1.0, polarization=None, coherence_length=1e-6, beam_profile=None, propagation_direction=None, origin=None, divergence=0.5):
        super().__init__(
            wavelength=0.5 * (wavelength_range[0] + wavelength_range[1]),
            power=power,
            polarization=polarization or "unpolarized",
            coherence_length=coherence_length,
            beam_profile=beam_profile,
            propagation_direction=propagation_direction,
            origin=origin,
            divergence=divergence,
        )
        self.spectrum = BroadbandSpectrum(wavelength_range=wavelength_range)

    def default_spectrum(self):
        return BroadbandSpectrum(wavelength_range=(400e-9, 700e-9))
