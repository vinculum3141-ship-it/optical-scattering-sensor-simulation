"""Photon transfer curve (PTC) analysis module.

PTC characterises sensor noise by measuring variance vs. mean signal
over a flat-field intensity sweep.  From the curve we extract:
- gain (e⁻/DN) from the slope of the shot-noise region
- read noise from the zero-signal intercept
- full-well capacity from the roll-off
"""

from __future__ import annotations

from typing import List, Tuple

import numpy as np

from .base import AnalysisModule, AnalysisReport


class PTCAnalyzer(AnalysisModule):
    """Photon transfer curve analysis from a set of flat-field images.

    Parameters
    ----------
    fit_region : tuple of (float, float) or None
        Fractional range of the mean signal over which to fit the
        shot-noise slope, e.g. ``(0.1, 0.8)``.  If ``None``, the
        entire range is used minus the lowest and highest 10%.
    """

    def __init__(self, fit_region: Tuple[float, float] = None):
        self.fit_region = fit_region

    def analyze(self, images: List) -> AnalysisReport:
        means = []
        variances = []
        for img in images:
            pixels = np.asarray(img.pixels, dtype=float)
            means.append(float(np.mean(pixels)))
            variances.append(float(np.var(pixels)))

        means = np.array(means)
        variances = np.array(variances)

        order = np.argsort(means)
        means = means[order]
        variances = variances[order]

        if self.fit_region is not None:
            lo, hi = self.fit_region
            lo_val = means[0] + lo * (means[-1] - means[0])
            hi_val = means[0] + hi * (means[-1] - means[0])
            mask = (means >= lo_val) & (means <= hi_val)
        else:
            n = len(means)
            mask = np.zeros(n, dtype=bool)
            mask[int(n * 0.1):int(n * 0.9)] = True

        if np.sum(mask) < 2:
            gain = 0.0
            read_noise = 0.0
        else:
            coeffs = np.polyfit(means[mask], variances[mask], 1)
            gain = float(coeffs[0])
            read_noise = float(np.sqrt(max(0, coeffs[1])))

        full_well = float(means[-1]) if len(means) > 0 else 0.0
        dynamic_range_db = 20.0 * np.log10(full_well / read_noise) if read_noise > 0 and full_well > 0 else 0.0

        return AnalysisReport(measurements={
            "gain": gain,
            "read_noise_electrons": read_noise,
            "full_well_signal": full_well,
            "dynamic_range_db": dynamic_range_db,
            "mean_signal": means.tolist(),
            "variance": variances.tolist(),
        })
