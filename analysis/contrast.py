"""Contrast and signal-to-noise ratio analysis modules."""

from __future__ import annotations

import numpy as np

from .base import AnalysisModule, AnalysisReport


class ContrastAnalyzer(AnalysisModule):
    """Compute contrast metrics for a digital image.

    Provides:
        - RMS (root-mean-square) contrast
        - Michelson contrast (for periodic patterns)
        - Weber contrast (relative to mean)

    RMS contrast  = σ(I) / μ(I)
    Michelson     = (I_max - I_min) / (I_max + I_min)
    Weber         = (I_max - μ) / μ  (or (I_max - I_bg) / I_bg)

    Parameters
    ----------
    background : float or None
        Background level for Weber contrast.  If ``None``, the image
        mean is used.
    """

    def __init__(self, background=None):
        self.background = background

    def analyze(self, image) -> AnalysisReport:
        pixels = np.asarray(image.pixels, dtype=float)
        mean = float(np.mean(pixels))
        std = float(np.std(pixels))
        max_val = float(np.max(pixels))
        min_val = float(np.min(pixels))

        rms_contrast = std / mean if mean > 0 else 0.0
        michelson = (max_val - min_val) / (max_val + min_val) if (max_val + min_val) > 0 else 0.0
        bg = self.background if self.background is not None else mean
        weber = (max_val - bg) / bg if bg > 0 else 0.0

        return AnalysisReport(measurements={
            "rms_contrast": rms_contrast,
            "michelson_contrast": michelson,
            "weber_contrast": weber,
            "mean_intensity": mean,
            "std_intensity": std,
        })


class SaturationAnalyzer(AnalysisModule):
    """Detect and quantify saturated pixels in a digital image.

    Reports the fraction of pixels at or near the maximum digital
    value, and the maximum pixel level relative to the bit-depth
    limit.

    Parameters
    ----------
    threshold : float
        Fraction of max digital value above which a pixel is
        considered saturated.  Default 0.99 (≥ 99% of max).
    """

    def __init__(self, threshold=0.99):
        self.threshold = threshold

    def analyze(self, image) -> AnalysisReport:
        pixels = np.asarray(image.pixels, dtype=float)
        bit_depth = image.metadata.get("bit_depth", 12)
        max_digital = float(2**bit_depth - 1)
        sat_level = max_digital * self.threshold

        total = pixels.size
        saturated = int(np.sum(pixels >= sat_level))
        fraction = saturated / total if total > 0 else 0.0

        return AnalysisReport(measurements={
            "saturated_pixels": saturated,
            "saturation_fraction": fraction,
            "max_digital_value": max_digital,
            "pixel_max": float(np.max(pixels)),
        })
