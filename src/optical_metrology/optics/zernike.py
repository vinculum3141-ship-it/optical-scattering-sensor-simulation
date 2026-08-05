"""Zernike polynomial wavefront model and aberration-based PSF.

Provides:
- :class:`ZernikePolynomials` — evaluate individual Noll-indexed Zernike
  modes on a normalised pupil coordinate grid.
- :class:`Wavefront` — container for Zernike coefficients; builds a
  2D wavefront error map from the coefficients.
- :class:`ZernikePSF` — computes a diffraction-limited or aberrated PSF
  from the generalised pupil function, using the same
  ``kernel(size, optical_system)`` interface as :class:`~optics.GaussianPSF`
  and :class:`~optics.AiryPSF`.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np


# Standard Zernike polynomials indexed by Noll j (starting at 1).
# Each entry is (n, m, norm) where n = radial order, m = azimuthal order,
# and norm is the normalisation factor sqrt(2*(n+1)) / (1 + delta_{m,0}).
_NOLL = [
    (0, 0),   # j=1  Piston
    (1, -1),  # j=2  Tilt y
    (1, 1),   # j=3  Tilt x
    (2, -2),  # j=4  Astigmatism 45°
    (2, 0),   # j=5  Defocus
    (2, 2),   # j=6  Astigmatism 0°
    (3, -3),  # j=7  Trefoil y
    (3, -1),  # j=8  Coma y
    (3, 1),   # j=9  Coma x
    (3, 3),   # j=10 Trefoil x
    (4, -4),  # j=11 Quadrafoil y
    (4, -2),  # j=12 Secondary astigmatism y
    (4, 0),   # j=13 Spherical
    (4, 2),   # j=14 Secondary astigmatism x
    (4, 4),   # j=15 Quadrafoil x
]


def _noll_to_nm(j: int):
    """Return (n, m) for Noll index *j* (1-indexed)."""
    if j < 1 or j > len(_NOLL):
        raise ValueError(f"Unsupported Noll index: {j}")
    return _NOLL[j - 1]


def _radial_poly(n: int, m: int, r: np.ndarray) -> np.ndarray:
    """Evaluate the radial Zernike polynomial R_n^|m|(r)."""
    m_abs = abs(m)
    result = np.zeros_like(r)
    for k in range((n - m_abs) // 2 + 1):
        coeff = ((-1) ** k * math.factorial(n - k) /
                 (math.factorial(k) *
                  math.factorial((n + m_abs) // 2 - k) *
                  math.factorial((n - m_abs) // 2 - k)))
        result += coeff * r ** (n - 2 * k)
    return result


def zernike_eval(j: int, rho: np.ndarray, theta: np.ndarray) -> np.ndarray:
    """Evaluate the Noll-indexed Zernike polynomial Z_j(ρ, θ).

    Parameters
    ----------
    j : int
        Noll index (1-based).  1 = piston, 2 = tilt y, 3 = tilt x, etc.
    rho : np.ndarray
        Normalised radial coordinate (0 to 1).
    theta : np.ndarray
        Azimuthal angle in radians.

    Returns
    -------
    np.ndarray
        Z_j(ρ, θ) evaluated at every input point.
    """
    n, m = _noll_to_nm(j)
    R = _radial_poly(n, m, rho)
    norm = np.sqrt(2 * (n + 1) / (1 + (m == 0)))
    if m < 0:
        return norm * R * np.sin(abs(m) * theta)
    return norm * R * np.cos(m * theta)


class ZernikePolynomials:
    """Evaluate Noll-indexed Zernike polynomials on a pupil grid.

    Provides cached evaluation of individual modes for building
    wavefront maps.
    """

    @staticmethod
    def evaluate(j: int, rho: np.ndarray, theta: np.ndarray) -> np.ndarray:
        """Evaluate the Noll-indexed Zernike polynomial Z_j."""
        return zernike_eval(j, rho, theta)


class Wavefront:
    """Wavefront error map described by Zernike coefficients.

    Parameters
    ----------
    coefficients : dict of int → float
        Mapping from Noll index *j* to coefficient value in **metres**
        of RMS wavefront error.  Only non-zero coefficients need be
        included.  Typical simulation values are a fraction of a wave:
        e.g. 0.25 µm of defocus is about half a wave at 532 nm.
    """

    def __init__(self, coefficients: Dict[int, float]):
        self.coefficients = dict(coefficients)

    def map(self, rho: np.ndarray, theta: np.ndarray) -> np.ndarray:
        """Compute the wavefront error map W(ρ, θ) in metres.

        Parameters
        ----------
        rho : np.ndarray
            Normalised radial coordinate (0 to 1).
        theta : np.ndarray
            Azimuthal angle in radians.

        Returns
        -------
        np.ndarray
            Wavefront error in metres at each (ρ, θ) point.
        """
        wfe = np.zeros_like(rho, dtype=float)
        for j, coeff in self.coefficients.items():
            wfe += coeff * zernike_eval(j, rho, theta)
        return wfe


class ZernikePSF:
    """Point-spread function computed from a Zernike-aberrated pupil.

    Computes the incoherent PSF via FFT of the generalised pupil
    function:

        P(ρ, θ) = A(ρ, θ) · exp(i · 2π/λ · W(ρ, θ))

    where A is the amplitude transmission (1 inside pupil, 0 outside)
    and W is the wavefront error from a :class:`Wavefront` object.

    The pupil radius in pupil-plane grid pixels is chosen so that the
    diffraction-limited spot scales with the physical parameters: the
    first Airy zero falls at ``0.61 · λ / (NA · pixel_size)`` pixels —
    the same scale as :class:`~optics.airy.AiryPSF`.  If that radius
    would exceed half the kernel (diffraction spot smaller than a
    pixel), the pupil fills the kernel instead and the spot is
    diffraction-limited to ~1 pixel.

    Parameters
    ----------
    wavefront : Wavefront
        Zernike coefficient container for the wavefront error.
    wavelength : float
        Centre wavelength in metres.
    numerical_aperture : float
        Numerical aperture of the optical system.
    pixel_size : float
        Physical size of one sensor pixel in metres.  Used to convert
        the diffraction scale from meters to pixels (default 5 µm).
    """

    def __init__(
        self,
        wavefront: Wavefront,
        wavelength: float,
        numerical_aperture: float,
        pixel_size: float = 5e-6,
    ):
        self.wavefront = wavefront
        self.wavelength = float(wavelength)
        self.numerical_aperture = float(numerical_aperture)
        self.pixel_size = float(pixel_size)

    def _aperture_radius(self, grid: int) -> float:
        """Physical aperture radius in pupil-grid pixels.

        The radius at which the first Airy zero of the FFT PSF lands on
        ``0.61 · λ / (NA · pixel_size)`` pixels.  If that radius would
        exceed the half-width of the grid, the aperture fills the grid
        (sub-pixel diffraction spot).
        """
        return grid * self.numerical_aperture * self.pixel_size / self.wavelength

    def _internal_grid(self, size: int) -> int:
        """Internal FFT grid size for faithful pupil sampling.

        A larger grid than the output kernel decouples the pupil-plane
        sampling from the output resolution: the aperture is sampled on
        ``grid * NA * pixel_size / wavelength`` pixels, keeping the
        pupil well-resolved while the diffraction scale of the PSF stays
        ``0.61 · λ / (NA · pixel_size)`` pixels.
        """
        return max(512, 8 * size)

    def kernel(self, size: int = 31) -> np.ndarray:
        """Generate a normalised PSF kernel.

        The PSF is computed by FFT of the generalised pupil function on
        a large internal grid (see :meth:`_internal_grid`), then the
        central ``size × size`` region is cropped and normalised.

        Parameters
        ----------
        size : int
            Side length of the square kernel in pixels.  Must be odd.

        Returns
        -------
        np.ndarray
            2D array of shape ``(size, size)``, normalised to unit sum.
        """
        if size % 2 == 0:
            size = size + 1  # ensure odd

        half = size // 2
        grid = self._internal_grid(size)
        half_g = grid // 2
        y, x = np.mgrid[-half_g:half_g, -half_g:half_g]
        r = np.sqrt(x ** 2 + y ** 2).astype(float)

        aperture_radius = self._aperture_radius(grid)
        if aperture_radius < half_g:
            rho = r / aperture_radius
        else:
            # Diffraction spot at or below one pixel: pupil fills the grid.
            rho = r / half_g

        # Pupil mask
        pupil = (rho <= 1.0).astype(float)

        theta = np.arctan2(y, x)

        # Wavefront error over the normalised pupil (rho clipped to 1 so
        # the radial Zernike polynomials stay finite outside the pupil).
        rho_wf = np.minimum(rho, 1.0)
        if self.wavefront.coefficients:
            wfe = self.wavefront.map(rho_wf, theta)
        else:
            wfe = np.zeros_like(rho)

        # Generalised pupil function
        k = 2.0 * np.pi / self.wavelength
        P = pupil * np.exp(1j * k * wfe)

        # PSF via FFT: |FFT(P)|^2, then crop the central size x size region.
        psf = np.abs(np.fft.fftshift(np.fft.fft2(P))) ** 2
        psf = psf[half_g - half:half_g + half + 1, half_g - half:half_g + half + 1]
        psf = psf / psf.sum()

        return psf
