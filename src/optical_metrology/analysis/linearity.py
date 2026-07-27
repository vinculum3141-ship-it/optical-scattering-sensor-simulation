"""Linearity test analysis module.

Quantifies the deviation of a sensor's response from an ideal linear
fit across a range of exposure levels.
"""

from __future__ import annotations

from typing import List

import numpy as np

from .base import AnalysisModule, AnalysisReport


class LinearityTestAnalyzer(AnalysisModule):
    """Analyse sensor linearity from a set of images at known exposure levels.

    Parameters
    ----------
    ideal_exposures : list of float or None
        The expected relative exposure levels corresponding to each
        image (e.g. exposure times or illumination powers).  If
        ``None``, images are assumed to be equally spaced.
    """

    def __init__(self, ideal_exposures: List[float] = None):
        self.ideal_exposures = ideal_exposures

    def analyze(self, images) -> AnalysisReport:
        means = []
        for img in images:
            pixels = np.asarray(img.pixels, dtype=float)
            means.append(float(np.mean(pixels)))

        means = np.array(means)
        n = len(means)

        if self.ideal_exposures is not None:
            exposures = np.array(self.ideal_exposures, dtype=float)
            if len(exposures) != n:
                raise ValueError(
                    f"Expected {n} exposures, got {len(exposures)}"
                )
        else:
            exposures = np.arange(n, dtype=float)

        if n < 2:
            return AnalysisReport(measurements={
                "linearity_error_pct": 0.0,
                "r_squared": 0.0,
            })

        coeffs = np.polyfit(exposures, means, 1)
        predicted = np.polyval(coeffs, exposures)

        residuals = means - predicted
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((means - np.mean(means)) ** 2)
        r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

        max_dev = np.max(np.abs(residuals))
        full_scale = np.max(means) - np.min(means) if n > 1 else 1.0
        linearity_error_pct = 100.0 * max_dev / full_scale if full_scale > 0 else 0.0

        return AnalysisReport(measurements={
            "linearity_error_pct": float(linearity_error_pct),
            "r_squared": float(r_squared),
            "slope": float(coeffs[0]),
            "intercept": float(coeffs[1]),
            "residuals": residuals.tolist(),
        })
