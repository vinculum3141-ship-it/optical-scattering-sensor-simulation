"""Base :class:`LightSource` and its concrete subclasses.

The :class:`LightSource` dataclass holds the physical parameters that
describe an optical emitter and exposes a
:meth:`LightSource.generate_light_field` method that produces a
:class:`LightField` over a user-supplied spatial grid.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple

import numpy as np

from .lightfield import LightField
from .polarization import PolarizationState
from .profiles import BeamProfile, GaussianBeamProfile, UniformBeamProfile
from .spectrum import SpectralDistribution


@dataclass
class LightSource:
    """A physical description of an optical source that can generate a light field.

    This is the central abstraction of the illumination package.
    Subclasses (e.g. :class:`Laser`, :class:`LED`) override
    :meth:`default_spectrum` to attach the appropriate spectral model.

    Parameters
    ----------
    wavelength : float
        Centre wavelength in metres.
    power : float
        Total optical power in Watts.
    polarization : PolarizationState or str
        Polarisation state.  If a string, it is converted to a
        :class:`PolarizationState` on initialisation.
    coherence_length : float
        Temporal coherence length in metres.
    beam_profile : BeamProfile or str
        Spatial intensity profile.  If a string, it must be
        ``"uniform"`` or ``"gaussian"``.
    propagation_direction : ndarray, 3-element
        Unit vector along which the beam propagates.  Normalised on
        input.  Defaults to ``+z``.
    origin : ndarray, 3-element
        Spatial origin of the source in world coordinates.  Defaults
        to the origin.
    divergence : float
        Full-angle beam divergence in radians.
    spectrum : SpectralDistribution or None
        Spectral model.  If ``None``, ``default_spectrum()`` is called.
    """

    wavelength: float = 532e-9
    power: float = 1.0
    polarization: PolarizationState = field(default_factory=lambda: PolarizationState("unpolarized"))
    coherence_length: float = 1e-3
    beam_profile: BeamProfile = field(default_factory=UniformBeamProfile)
    propagation_direction: Optional[np.ndarray] = None
    origin: Optional[np.ndarray] = None
    divergence: float = 0.0
    spectrum: Optional[SpectralDistribution] = None

    def __post_init__(self):
        if self.propagation_direction is None:
            self.propagation_direction = np.array([0.0, 0.0, 1.0], dtype=float)
        else:
            norm = np.linalg.norm(self.propagation_direction)
            if norm == 0.0:
                raise ValueError("propagation_direction must be non-zero")
            self.propagation_direction = self.propagation_direction / norm

        if self.origin is None:
            self.origin = np.zeros(3, dtype=float)

        if isinstance(self.polarization, str):
            self.polarization = PolarizationState(self.polarization)

        if self.beam_profile is None:
            self.beam_profile = UniformBeamProfile()
        elif isinstance(self.beam_profile, str):
            profile_name = self.beam_profile.lower()
            if profile_name == "uniform":
                self.beam_profile = UniformBeamProfile()
            elif profile_name == "gaussian":
                self.beam_profile = GaussianBeamProfile()
            else:
                raise ValueError(f"Unsupported beam profile: {self.beam_profile}")

        if self.spectrum is None:
            self.spectrum = self.default_spectrum()

    def default_spectrum(self) -> SpectralDistribution:
        """Return the default spectrum for this source type.

        Override in subclasses to attach a specific spectral model.
        """
        return SpectralDistribution(kind="monochromatic")

    def spectral_distribution(self) -> SpectralDistribution:
        """Return the spectral distribution attached to this source."""
        return self.spectrum

    def generate_light_field(self, shape: Tuple[int, int], spacing: float = 1.0) -> LightField:
        """Generate a :class:`LightField` over a 2D spatial grid.

        The intensity at each grid point is the product of the
        beam-profile evaluation and the total source power.  The
        direction is constant across the grid (collimated beam).

        Parameters
        ----------
        shape : tuple of int, or int
            Grid dimensions ``(height, width)`` in pixels.  If an
            integer is given, a square grid is assumed.
        spacing : float
            Physical distance between adjacent grid points in the same
            units as the beam-profile parameters.

        Returns
        -------
        LightField
            The illumination field over the requested grid.
        """
        if isinstance(shape, int):
            shape = (shape, shape)
        intensity = self.beam_profile.evaluate(shape, spacing=spacing)
        direction = np.repeat(self.propagation_direction[None, None, :], int(shape[0]), axis=0)
        direction = np.repeat(direction, int(shape[1]), axis=1)
        return LightField(
            intensity=intensity * self.power,
            direction=direction,
            wavelength=self.wavelength,
            polarization=self.polarization,
            phase=None,
        )
