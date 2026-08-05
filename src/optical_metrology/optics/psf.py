"""Gaussian point-spread function model.

Provides a simple isotropic 2D Gaussian PSF for convolution-based
optical propagation.  The PSF is normalised to unit sum so that
energy is conserved during convolution.
"""

from __future__ import annotations

import numpy as np


class GaussianPSF:
    """Simple Gaussian point-spread function for fast propagation.

    Parameters
    ----------
    sigma : float
        Standard deviation of the Gaussian kernel in pixels.
        Controls the width of the blur (larger = more blur).
    """

    def __init__(self, sigma: float = 1.0):
        self.sigma = sigma

    def kernel(self, size: int = 5) -> np.ndarray:
        """Generate a normalised 2D Gaussian convolution kernel.

        Parameters
        ----------
        size : int
            Side length of the square kernel in pixels.
            Must be positive; odd sizes produce a centred kernel.

        Returns
        -------
        np.ndarray
            2D array of shape ``(size, size)``, normalised to unit sum.
        """
        if size <= 0:
            raise ValueError("size must be positive")
        coords = np.arange(-(size // 2), size // 2 + 1, dtype=float)
        yy, xx = np.meshgrid(coords, coords, indexing="ij")
        kernel = np.exp(-(xx**2 + yy**2) / (2.0 * self.sigma**2))
        kernel /= kernel.sum()
        return kernel
