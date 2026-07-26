"""Optical propagation: transforms a scattered field into a sensor-plane image.

The :class:`OpticalPropagator` applies a point-spread function (PSF)
convolution to the radiance map from a scattering evaluation, producing
a :class:`SensorField` that represents the image formed on the sensor.
"""

from __future__ import annotations

import numpy as np

from .base import OpticalSystem, SensorField


class OpticalPropagator:
    """Propagate a scattered field through an optical system to form a sensor image.

    The propagation is performed as a direct convolution of the scattered
    radiance with a PSF kernel.  This models the effect of diffraction and
    optical aberrations as a spatially invariant blur.

    Parameters
    ----------
    psf_model : object or None
        PSF model with a ``kernel(size)`` method (e.g. :class:`~optics.psf.GaussianPSF`).
        If ``None``, a 3×3 box filter (uniform average) is used as the default PSF.
    """

    def __init__(self, psf_model=None):
        self.psf_model = psf_model

    def propagate(self, scattered_field, optical_system: OpticalSystem) -> SensorField:
        """Convolve the scattered radiance with the PSF to form a sensor image.

        Parameters
        ----------
        scattered_field : ScatteredField
            Radiance map from a scattering evaluation.
        optical_system : OpticalSystem
            Parameters of the imaging optics (wavelength, NA, etc.).

        Returns
        -------
        SensorField
            Irradiance distribution at the sensor plane.
        """
        radiance = np.asarray(scattered_field.radiance, dtype=float)
        if radiance.ndim != 2:
            raise ValueError("scattered_field.radiance must be 2D")

        if self.psf_model is None:
            psf = np.ones((3, 3), dtype=float) / 9.0
        else:
            psf = self.psf_model.kernel(size=max(3, int(4 * self.psf_model.sigma)))

        # Manual 2D convolution: pad the radiance array, then slide the
        # PSF kernel over every pixel.  This is O(H·W·K²) and intentionally
        # straightforward — readers can swap in FFT-based convolution
        # (scipy.signal.fftconvolve, torch.nn.functional.conv2d, etc.)
        # for larger grids.
        pad_width = ((psf.shape[0] // 2, psf.shape[0] // 2), (psf.shape[1] // 2, psf.shape[1] // 2))
        padded = np.pad(radiance, pad_width=pad_width, mode="constant")
        irradiance = np.zeros_like(radiance, dtype=float)
        for i in range(radiance.shape[0]):
            for j in range(radiance.shape[1]):
                patch = padded[i : i + psf.shape[0], j : j + psf.shape[1]]
                irradiance[i, j] = np.sum(patch * psf)
        return SensorField(
            irradiance=irradiance,
            wavelength=optical_system.wavelength,
            polarization=scattered_field.polarization,
            optical_path_length=optical_system.focal_length,
        )
