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
        Spatial position of the source in world coordinates.  Used as
        the emission point for :attr:`wavefront` ``"spherical"``.
        Defaults to ``[0, 0, 0]``.
    divergence : float
        Full-angle beam divergence in radians.
    wavefront : str
        Wavefront geometry.
        ``"planar"`` (default) — collimated beam, uniform direction.
        ``"spherical"`` — divergent point source, per-pixel direction.
        ``"converging"`` — rays converge toward a focal point.
    waist_position : float
        Z-coordinate of the Gaussian beam waist in the same coordinate
        system as the grid.  The grid lies in the z = 0 plane.
        When ``waist_position = 0`` (default), the waist is at the grid
        plane and no propagation scaling is applied.  Non-zero values
        cause the beam to expand (or contract) according to Gaussian
        beam propagation, scaling intensity by ``(w0 / w(z))²``.
    focal_distance : Optional[float]
        Distance from the grid plane to the focal point for
        ``wavefront="converging"``.  The focal point is located at
        ``propagation_direction * focal_distance`` beyond the grid.
        If ``None``, defaults to 10× the grid size.
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
    wavefront: str = "planar"
    waist_position: float = 0.0
    focal_distance: Optional[float] = None
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

        if self.wavefront not in ("planar", "spherical", "converging"):
            raise ValueError(f"Unsupported wavefront: {self.wavefront!r}; expected 'planar', 'spherical', or 'converging'")

        if self.spectrum is None:
            self.spectrum = self.default_spectrum()

    @property
    def incidence_angle(self) -> float:
        """Incidence angle in radians, assuming a surface normal of [0, 0, 1].

        Derived from ``propagation_direction``.  0 = normal incidence
        (beam perpendicular to surface), π/2 = grazing.  The property
        converts ``propagation_direction`` to an angle so that the two
        stay synchronised: setting one updates the other.

        For surfaces with arbitrary normals, the per-pixel incidence
        angle is computed in the scattering model via the dot product.
        """
        return float(np.arccos(np.clip(-self.propagation_direction[2], -1.0, 1.0)))

    @incidence_angle.setter
    def incidence_angle(self, angle_rad: float):
        cz = np.cos(float(angle_rad))
        sz = np.sin(float(angle_rad))
        self.propagation_direction = np.array([sz, 0.0, -cz], dtype=float)

    @property
    def incidence_angle_degrees(self) -> float:
        """Incidence angle in degrees.  See :attr:`incidence_angle`."""
        return float(np.degrees(self.incidence_angle))

    @incidence_angle_degrees.setter
    def incidence_angle_degrees(self, angle_deg: float):
        self.incidence_angle = float(np.radians(angle_deg))

    def default_spectrum(self) -> SpectralDistribution:
        """Return the default spectrum for this source type.

        Override in subclasses to attach a specific spectral model.
        """
        return SpectralDistribution(kind="monochromatic")

    def spectral_distribution(self) -> SpectralDistribution:
        """Return the spectral distribution attached to this source."""
        return self.spectrum

    def _compute_grid_coords(self, shape, spacing):
        """Return (xx, yy) meshgrid of physical coordinates for the grid plane."""
        H, W = shape
        x = (np.arange(W) - (W - 1) / 2.0) * spacing
        y = ((H - 1) / 2.0 - np.arange(H)) * spacing
        return np.meshgrid(x, y)

    def _effective_waist(self, profile_waist: Optional[float] = None) -> float:
        """Return the effective beam waist radius in metres.

        Priority: profile waist → waist from ``divergence`` → fallback
        (half the grid size as a sensible default).
        """
        if profile_waist is not None and profile_waist > 0:
            return profile_waist
        if self.divergence > 0:
            return float(self.wavelength / (np.pi * self.divergence))
        return 1.0

    def _gaussian_beam_scaling(self, w0: float) -> float:
        """Compute intensity scaling factor for Gaussian beam propagation.

        Returns the factor ``(w0 / w(z))²`` where ``w(z)`` is the beam
        radius at the grid plane (z=0).  When ``waist_position == 0``
        the waist coincides with the grid plane and the factor is 1.
        """
        if self.waist_position == 0.0:
            return 1.0
        dz = -self.waist_position
        zR = np.pi * w0 ** 2 / self.wavelength
        w_at_grid = w0 * np.sqrt(1.0 + (dz / zR) ** 2)
        return float((w0 / w_at_grid) ** 2)

    def generate_light_field(self, shape: Tuple[int, int], spacing: float = 1.0) -> LightField:
        """Generate a :class:`LightField` over a 2D spatial grid.

        The intensity at each grid point is the product of the
        beam-profile evaluation and the total source power.  The
        direction depends on the :attr:`wavefront`:

        * ``"planar"`` (default) — uniform direction across grid (collimated beam).
        * ``"spherical"`` — per-pixel direction from :attr:`origin` toward
          each grid point (point source).
        * ``"converging"`` — per-pixel direction toward a focal point
          beyond the grid plane.

        When using a :class:`GaussianBeamProfile` with a non-zero
        :attr:`waist_position`, the intensity is scaled according to
        Gaussian beam propagation (beam expansion/contraction with
        distance from the waist).

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
        H, W = int(shape[0]), int(shape[1])

        intensity = self.beam_profile.evaluate(shape, spacing=spacing)

        gaussian_scale = 1.0
        if isinstance(self.beam_profile, GaussianBeamProfile):
            w0 = self._effective_waist(self.beam_profile.w0)
            gaussian_scale = self._gaussian_beam_scaling(w0)
        elif self.divergence > 0 and self.waist_position != 0:
            w0 = self._effective_waist(None)
            gaussian_scale = self._gaussian_beam_scaling(w0)

        if self.wavefront == "spherical":
            xx, yy = self._compute_grid_coords((H, W), spacing)
            dx = xx - self.origin[0]
            dy = yy - self.origin[1]
            dz = 0.0 - self.origin[2]
            norm = np.sqrt(dx**2 + dy**2 + dz**2)
            direction = np.stack([dx / norm, dy / norm, dz / norm], axis=-1)

        elif self.wavefront == "converging":
            fd = self.focal_distance
            if fd is None:
                fd = 10.0 * max(H, W) * spacing
            focal_point = np.array([0.0, 0.0, fd], dtype=float)
            xx, yy = self._compute_grid_coords((H, W), spacing)
            dx = focal_point[0] - xx
            dy = focal_point[1] - yy
            dz = focal_point[2] - 0.0
            norm = np.sqrt(dx**2 + dy**2 + dz**2)
            direction = np.stack([dx / norm, dy / norm, dz / norm], axis=-1)

        else:
            direction = np.repeat(self.propagation_direction[None, None, :], H, axis=0)
            direction = np.repeat(direction, W, axis=1)

        return LightField(
            intensity=intensity * gaussian_scale * self.power,
            direction=direction,
            wavelength=self.wavelength,
            polarization=self.polarization,
            coherence_length=self.coherence_length,
            power=self.power,
            phase=None,
        )
