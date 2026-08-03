"""Error map / ground-truth comparison analysis module.

Computes per-pixel difference between a simulated (measured) image and
a known reference (ground-truth) image.  Used for structured light
height reconstruction validation (UC5) and wafer alignment overlay
accuracy (UC7).
"""

from __future__ import annotations

import numpy as np

from .base import AnalysisModule, AnalysisReport


class ErrorMapAnalyzer(AnalysisModule):
    """Compare a measured image against a reference (ground truth).

    Parameters
    ----------
    reference : DigitalImage or np.ndarray
        Reference image to compare against.  Must have the same shape
        as the input image at analysis time.
    """

    def __init__(self, reference):
        self._ref_pixels = np.asarray(reference.pixels if hasattr(reference, "pixels") else reference, dtype=float)

    def analyze(self, image) -> AnalysisReport:
        pixels = np.asarray(image.pixels, dtype=float)
        ref = self._ref_pixels

        if pixels.shape != ref.shape:
            raise ValueError(
                f"Shape mismatch: measured {pixels.shape} vs reference {ref.shape}"
            )

        error_map = np.abs(pixels - ref)
        mae = float(np.mean(error_map))
        rmse = float(np.sqrt(np.mean(error_map ** 2)))
        max_err = float(np.max(error_map))

        max_val = float(np.max([np.max(pixels), np.max(ref)]))
        if rmse > 0 and max_val > 0:
            psnr = 20.0 * np.log10(max_val / rmse)
        else:
            psnr = 120.0

        return AnalysisReport(measurements={
            "error_map": error_map.tolist(),
            "mae": mae,
            "rmse": rmse,
            "max_error": max_err,
            "psnr_db": psnr,
        })
