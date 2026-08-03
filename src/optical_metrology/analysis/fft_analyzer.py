"""2D FFT / power spectrum analysis module.

Computes the 2D power spectrum of an image via FFT and extracts radial
and angular profiles.  Useful for roughness characterisation (UC4) and
structured-light fringe analysis (UC5).
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from .base import AnalysisModule, AnalysisReport


class FFTAnalyzer(AnalysisModule):
    """Compute and analyse the 2D power spectrum of an image.

    Parameters
    ----------
    dc_removal : bool
        Subtract the mean before the FFT to reduce the DC component
        (default True).
    window : str or None
        Windowing function to reduce spectral leakage.  ``"hann"``
        applies a 2D Hann window.  ``None`` uses no windowing.
    """

    def __init__(self, dc_removal: bool = True, window: Optional[str] = None):
        self.dc_removal = dc_removal
        self.window = window

    def analyze(self, image) -> AnalysisReport:
        pixels = np.asarray(image.pixels, dtype=float)

        data = pixels.copy()
        if self.dc_removal:
            data = data - np.mean(data)

        if self.window == "hann":
            h = np.hanning(data.shape[0])
            w = np.hanning(data.shape[1])
            data = data * np.outer(h, w)

        spectrum = np.fft.fftshift(np.fft.fft2(data))
        power = np.abs(spectrum) ** 2

        H, W = power.shape
        cy, cx = H // 2, W // 2

        dc_power = power[cy, cx]
        total_power = float(np.sum(power))
        dc_fraction = float(dc_power / total_power) if total_power > 0 else 0.0

        y, x = np.ogrid[-cy:H - cy, -cx:W - cx]
        r = np.sqrt(x ** 2 + y ** 2).astype(float)
        r_max = int(min(cy, cx))

        radial = np.zeros(r_max)
        counts = np.zeros(r_max)
        for ri in range(r_max):
            mask = (r >= ri) & (r < ri + 1)
            radial[ri] = float(np.mean(power[mask]))
            counts[ri] = int(np.sum(mask))

        valid = radial > 0
        if np.sum(valid) > 5:
            log_r = np.log(np.arange(1, r_max + 1)[valid][5:])
            log_p = np.log(radial[valid][5:])
            slope = float(np.polyfit(log_r, log_p, 1)[0])
        else:
            slope = 0.0

        peak_idx = np.argmax(radial[1:]) + 1 if len(radial) > 1 else 0
        peak_freq = float(peak_idx / max(W, H))

        return AnalysisReport(measurements={
            "dc_fraction": dc_fraction,
            "radial_profile": radial.tolist(),
            "peak_spatial_frequency": peak_freq,
            "power_spectrum_slope": slope,
        })
