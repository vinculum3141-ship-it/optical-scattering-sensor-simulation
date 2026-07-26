"""Signal-to-noise ratio (SNR) estimation from digital images.

Supports single-image and flat-field-pair estimation methods.
"""

from __future__ import annotations

from typing import Optional, Tuple, Union

import numpy as np

from .base import AnalysisModule, AnalysisReport


class SNRAnalyzer(AnalysisModule):
    """Estimate SNR from a single image or a pair of flat-field images.

    Parameters
    ----------
    method : str
        ``"single_image"`` — estimate signal as the mean of a region,
        noise as the standard deviation of a region.  Suitable when a
        uniform bright field and a dark region are available in one image.
        ``"flat_field_pair"`` — requires a *second_image* argument at
        construction.  Signal = mean of (im1 + im2)/2, noise = std of
        (im1 - im2)/√2 (suppresses fixed-pattern noise).
    signal_region : tuple of (row, col, height, width) or None
        ROI for signal estimation.  If None, the full image is used.
    noise_region : tuple of (row, col, height, width) or None
        ROI for noise estimation.  If None, the full image is used.
    second_image : DigitalImage or np.ndarray or None
        Second flat-field image for the ``"flat_field_pair"`` method.
    """

    def __init__(
        self,
        method: str = "single_image",
        signal_region: Optional[Tuple[int, int, int, int]] = None,
        noise_region: Optional[Tuple[int, int, int, int]] = None,
        second_image=None,
    ):
        if method not in ("single_image", "flat_field_pair"):
            raise ValueError(f"Unknown SNR method: {method!r}")
        self.method = method
        self.signal_region = signal_region
        self.noise_region = noise_region
        self._second = None
        if second_image is not None:
            self._second = np.asarray(
                second_image.pixels if hasattr(second_image, "pixels") else second_image,
                dtype=float,
            )

    def analyze(self, image) -> AnalysisReport:
        pixels = np.asarray(image.pixels, dtype=float)

        if self.method == "flat_field_pair" and self._second is not None:
            avg = (pixels + self._second) / 2.0
            diff = pixels - self._second
            sig = self._region(avg, self.signal_region)
            noise_sig = self._region(diff, self.noise_region) / np.sqrt(2.0)
            noise_std = float(np.std(noise_sig))
            signal_mean = float(np.mean(sig))
        else:
            sig = self._region(pixels, self.signal_region)
            noise = self._region(pixels, self.noise_region)
            signal_mean = float(np.mean(sig))
            noise_std = float(np.std(noise))

        if noise_std <= 0 or signal_mean <= 0:
            snr_db = 0.0
        else:
            snr_db = 20.0 * np.log10(signal_mean / noise_std)

        return AnalysisReport(measurements={
            "snr_db": snr_db,
            "signal_mean": signal_mean,
            "noise_std": noise_std,
            "snr_method": self.method,
        })

    def _region(self, pixels: np.ndarray, roi: Optional[Tuple[int, int, int, int]]) -> np.ndarray:
        if roi is None:
            return pixels
        r, c, h, w = roi
        return pixels[r:r + h, c:c + w]
