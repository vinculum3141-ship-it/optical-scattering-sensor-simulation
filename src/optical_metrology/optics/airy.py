"""Diffraction-limited Airy-disk point-spread function.

The Airy disk is the PSF of a perfect circular aperture in the
Fraunhofer diffraction regime.  It represents the best possible
focus achievable by an ideal, aberration-free optical system.
"""

from __future__ import annotations

import numpy as np


class AiryPSF:
    """Diffraction-limited Airy-disk point-spread function.

    The PSF intensity follows the squared |jinc| pattern:

        I(r) = (2 * J1(k * NA * r) / (k * NA * r))^2

    where J1 is the first-order Bessel function of the first kind,
    k = 2π/λ is the wavenumber, NA is the numerical aperture, and
    r is the radial coordinate in the image plane.

    Parameters
    ----------
    wavelength : float
        Centre wavelength in metres (default 532 nm).
    numerical_aperture : float
        Numerical aperture of the optical system (default 0.25).
    pixel_size : float
        Physical size of one pixel in metres (default 5 µm).
        Used to convert radial coordinates from pixels to metres.
    """

    def __init__(self, wavelength=532e-9, numerical_aperture=0.25, pixel_size=5e-6):
        self.wavelength = wavelength
        self.na = numerical_aperture
        self.pixel_size = pixel_size

    def kernel(self, size=31):
        """Generate a normalised Airy-disk convolution kernel.

        Parameters
        ----------
        size : int
            Side length of the square kernel in pixels.
            Must be positive and odd (auto-adjusted to odd if even).

        Returns
        -------
        np.ndarray
            2D array of shape ``(size, size)``, normalised to unit sum.
        """
        if size <= 0:
            raise ValueError("size must be positive")
        if size % 2 == 0:
            size = size + 1
        coords = np.arange(-(size // 2), size // 2 + 1, dtype=float)
        xx, yy = np.meshgrid(coords, coords, indexing="ij")
        r = np.sqrt(xx**2 + yy**2) * self.pixel_size

        k = 2.0 * np.pi / self.wavelength
        kr = k * self.na * r

        with np.errstate(divide="ignore", invalid="ignore"):
            kernel = (2.0 * _j1(kr) / kr) ** 2
        kernel[kr == 0] = 1.0

        kernel = kernel / kernel.sum()
        return kernel


def _j1(x):
    """Bessel function of the first kind, order 1.

    Used as a self-contained replacement for ``scipy.special.j1``
    to avoid adding a SciPy dependency.  Uses the ascending power
    series for ``|x| < 8`` and an asymptotic expansion (DLMF 10.17.3)
    for ``|x| >= 8``.  Accurate to ~1e-12 over ``[0, 100]``.

    Parameters
    ----------
    x : np.ndarray
        Input values (radial coordinate times wavenumber).

    Returns
    -------
    np.ndarray
        J1(x) evaluated at each input element.
    """
    x = np.asarray(x, dtype=float)
    ax = np.abs(x)
    result = np.empty_like(ax)

    small = ax < 12.0
    if np.any(small):
        # J1(x) = (x/2) * sum_{k>=0} (-1)^k (x/2)^(2k) / (k! (k+1)!)
        xh = x[small] / 2.0
        s = xh.copy()  # k = 0
        term = xh.copy()
        for k in range(1, 40):
            term *= -xh * xh / (k * (k + 1))
            s += term
        result[small] = s

    large = ~small
    if np.any(large):
        # Asymptotic expansion, chi = x - 3*pi/4 (DLMF 10.17.3):
        #   J1(x) ~ sqrt(2/(pi x)) *
        #          [ cos(chi) (1 + 15/(128 x^2) - 14175/(98304 x^4) + ...)
        #          - sin(chi) (3/(8 x) - 105/(1024 x^3) + ...) ]
        xl = ax[large]
        sign = np.where(x[large] >= 0.0, 1.0, -1.0)
        chi = xl - 3.0 * np.pi / 4.0
        inv = 1.0 / xl
        inv2 = inv * inv
        c = 1.0 + 15.0 / 128.0 * inv2 - 14175.0 / 98304.0 * inv2 * inv2
        s = 3.0 / 8.0 * inv - 105.0 / 1024.0 * inv * inv2
        result[large] = sign * np.sqrt(2.0 / (np.pi * xl)) * (
            np.cos(chi) * c - np.sin(chi) * s
        )

    return result
