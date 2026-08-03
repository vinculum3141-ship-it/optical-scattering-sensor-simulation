"""LED source model with a Gaussian spectral profile."""

from .source import LightSource
from .spectrum import GaussianSpectrum
from .profiles import GaussianBeamProfile


class LED(LightSource):
    """An LED source with a Gaussian-shaped emission spectrum.

    Defaults to a Gaussian beam profile and moderate divergence
    (0.5 rad), typical of a bare LED die.

    Parameters
    ----------
    peak_wavelength : float
        Centre wavelength of the emission peak in metres (default
        530 nm — green).
    width : float
        FWHM spectral width in metres (default 25 nm).
    power : float
        Optical power in Watts.
    polarization : PolarizationState or str, optional
        Defaults to unpolarized.
    coherence_length : float
        Coherence length in metres (default 10 µm).
    beam_profile : BeamProfile or str, optional
        Defaults to a :class:`GaussianBeamProfile` with ``w0=1.0``.
    propagation_direction : ndarray, optional
        Defaults to ``+z``.
    origin : ndarray, optional
        Defaults to the origin.
    divergence : float
        Full-angle beam divergence in radians (default 0.5 rad).
    """

    def __init__(self, peak_wavelength=530e-9, width=25e-9, power=1.0, polarization=None, coherence_length=1e-5, beam_profile=None, propagation_direction=None, origin=None, divergence=0.5):
        super().__init__(
            wavelength=peak_wavelength,
            power=power,
            polarization=polarization or "unpolarized",
            coherence_length=coherence_length,
            beam_profile=beam_profile or GaussianBeamProfile(w0=1.0),
            propagation_direction=propagation_direction,
            origin=origin,
            divergence=divergence,
        )
        self.spectrum = GaussianSpectrum(peak_wavelength=peak_wavelength, width=width)

    def default_spectrum(self):
        return GaussianSpectrum(peak_wavelength=self.wavelength, width=25e-9)
