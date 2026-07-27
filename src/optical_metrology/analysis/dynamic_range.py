"""Dynamic range analysis module.

Computes the optical dynamic range from an image or a set of flat-field
images: the ratio of the maximum non-saturating signal to the read noise
floor, expressed in dB.
"""

from __future__ import annotations

import numpy as np

from .base import AnalysisModule, AnalysisReport


class DynamicRangeAnalyzer(AnalysisModule):
    """Estimate the dynamic range of a sensor from a single image.

    Dynamic range is computed as 20·log₁₀(max_signal / min_nonzero_signal).
    """

    def analyze(self, image) -> AnalysisReport:
        pixels = np.asarray(image.pixels, dtype=float)

        max_val = float(np.max(pixels))
        min_val = float(np.min(pixels))
        mean_val = float(np.mean(pixels))
        std_val = float(np.std(pixels))

        if min_val > 0 and max_val > 0:
            dr_ratio = max_val / min_val
        else:
            dr_ratio = 1.0

        if mean_val > 0 and std_val > 0:
            snr_ratio = mean_val / std_val
        else:
            snr_ratio = 1.0

        dr_db = 20.0 * np.log10(dr_ratio)
        snr_db = 20.0 * np.log10(snr_ratio)

        return AnalysisReport(measurements={
            "dynamic_range_db": dr_db,
            "max_signal": max_val,
            "min_signal": min_val,
            "mean_signal": mean_val,
            "std_signal": std_val,
            "snr_ratio_db": snr_db,
        })
