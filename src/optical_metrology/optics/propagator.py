"""Optical propagation: transforms a scattered field into a sensor-plane image.

The :class:`OpticalPropagator` applies a point-spread function (PSF)
convolution to the radiance map from a scattering evaluation, producing
a :class:`SensorField` that represents the image formed on the sensor.

The propagator also handles:

* **Optical throughput** — scales the convolved irradiance by the
  system's collection efficiency :math:`\\pi \\cdot \\text{NA}^2`.
* **Magnification** — resamples the scattered radiance so that features
  in object space map to the correct size in sensor space.
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
    throughput_enabled : bool
        If ``True`` (default), scale the convolved irradiance by
        :math:`\\pi \\cdot \\text{NA}^2` to account for the optical
        system's collection efficiency.
    magnification_enabled : bool
        If ``True`` (default), resample the scattered radiance to
        account for :attr:`OpticalSystem.magnification` before
        convolution.
    """

    def __init__(self, psf_model=None, throughput_enabled: bool = True, magnification_enabled: bool = True):
        self.psf_model = psf_model
        self.throughput_enabled = throughput_enabled
        self.magnification_enabled = magnification_enabled

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

        data = self._apply_magnification(radiance, optical_system)

        if self.psf_model is None:
            psf = np.ones((3, 3), dtype=float) / 9.0
        else:
            psf = self.psf_model.kernel(size=max(3, int(4 * self.psf_model.sigma)))

        irradiance = self._convolve(data, psf)

        if self.throughput_enabled:
            na = getattr(optical_system, "numerical_aperture", None)
            if na is not None and na > 0:
                irradiance = irradiance * (np.pi * na ** 2)

        return SensorField(
            irradiance=irradiance,
            wavelength=optical_system.wavelength,
            polarization=scattered_field.polarization,
            optical_path_length=optical_system.focal_length,
        )

    def _apply_magnification(self, radiance: np.ndarray, optical_system) -> np.ndarray:
        if not self.magnification_enabled:
            return radiance
        M = getattr(optical_system, "magnification", None)
        if M is None or abs(M - 1.0) < 1e-6:
            return radiance
        H, W = radiance.shape
        H_new = max(1, int(round(H * M)))
        W_new = max(1, int(round(W * M)))
        if H_new == H and W_new == W:
            return radiance
        return self._resample(radiance, H_new, W_new)

    def _resample(self, data: np.ndarray, H_new: int, W_new: int) -> np.ndarray:
        H, W = data.shape
        rows = np.linspace(0, H - 1, H_new)
        cols = np.linspace(0, W - 1, W_new)
        ri = np.clip(np.floor(rows).astype(int), 0, H - 2)
        rf = rows - ri
        ci = np.clip(np.floor(cols).astype(int), 0, W - 2)
        cf = cols - ci
        tl = data[ri[:, None], ci[None, :]]
        tr = data[ri[:, None], np.clip(ci[None, :] + 1, 0, W - 1)]
        bl = data[np.clip(ri[:, None] + 1, 0, H - 1), ci[None, :]]
        br = data[np.clip(ri[:, None] + 1, 0, H - 1), np.clip(ci[None, :] + 1, 0, W - 1)]
        top = tl + cf[None, :] * (tr - tl)
        bottom = bl + cf[None, :] * (br - bl)
        return top + rf[:, None] * (bottom - top)

    def _convolve(self, data: np.ndarray, psf: np.ndarray) -> np.ndarray:
        pad_width = ((psf.shape[0] // 2, psf.shape[0] // 2), (psf.shape[1] // 2, psf.shape[1] // 2))
        padded = np.pad(data, pad_width=pad_width, mode="constant")
        result = np.zeros_like(data, dtype=float)
        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                patch = padded[i : i + psf.shape[0], j : j + psf.shape[1]]
                result[i, j] = np.sum(patch * psf)
        return result
