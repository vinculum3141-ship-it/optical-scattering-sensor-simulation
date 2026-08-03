"""Histogram and basic intensity statistics for digital images."""

from __future__ import annotations

import numpy as np

from .base import AnalysisModule, AnalysisReport


class HistogramAnalyzer(AnalysisModule):
    """Compute a histogram and basic intensity statistics for a digital image.

    For each unique pixel value in the image, the histogram records how
    many pixels share that value.  The report also includes the mean,
    minimum, and maximum intensity as scalar measurements.
    """

    def analyze(self, image) -> AnalysisReport:
        """Compute histogram and intensity statistics.

        Parameters
        ----------
        image : DigitalImage
            Image with a ``.pixels`` attribute (2D ``uint16`` array).

        Returns
        -------
        AnalysisReport
            ``histogram`` : 1D array of bin counts for each unique value.
            ``measurements`` : ``mean_intensity``, ``max_intensity``,
            ``min_intensity``.
        """
        pixels = np.asarray(image.pixels, dtype=float)
        values = np.unique(pixels)
        histogram = np.zeros(len(values), dtype=float)
        for idx, value in enumerate(values):
            histogram[idx] = np.sum(pixels == value)
        measurements = {
            "mean_intensity": float(np.mean(pixels)),
            "max_intensity": float(np.max(pixels)),
            "min_intensity": float(np.min(pixels)),
        }
        return AnalysisReport(histogram=histogram, measurements=measurements)
