"""Modulation transfer function (MTF) analysis module.

Computes the system MTF from an image of a known test target:
- ``sinusoidal`` — compares measured modulation to input modulation
  at a known spatial frequency.
"""

from __future__ import annotations

import numpy as np

from .base import AnalysisModule, AnalysisReport


class MTFAnalyzer(AnalysisModule):
    """Estimate the modulation transfer function from a test-target image.

    Parameters
    ----------
    target_type : str
        ``"sinusoidal"`` — compute MTF at a known frequency by comparing
        measured modulation to the input modulation.
        (``"slanted_edge"`` is a placeholder for future implementation.)
    lp_per_mm : float or None
        Spatial frequency of the sinusoidal target in line pairs per mm.
        Required for ``target_type="sinusoidal"``.
    pixel_size : float or None
        Pixel pitch in metres.  If provided, frequency axes are also
        reported in lp/mm.
    input_modulation : float
        Modulation of the input test pattern before the optical system
        (default 1.0 for a perfect sinusoidal target).
    """

    def __init__(
        self,
        target_type: str = "sinusoidal",
        lp_per_mm: float = None,
        pixel_size: float = None,
        input_modulation: float = 1.0,
    ):
        if target_type not in ("sinusoidal", "slanted_edge"):
            raise ValueError(f"Unknown target type: {target_type!r}")
        self.target_type = target_type
        self.lp_per_mm = lp_per_mm
        self.pixel_size = pixel_size
        self.input_modulation = float(input_modulation)

    def analyze(self, image) -> AnalysisReport:
        pixels = np.asarray(image.pixels, dtype=float)

        if self.target_type == "sinusoidal":
            return self._analyze_sinusoidal(pixels)
        return self._analyze_slanted_edge(pixels)

    def _analyze_sinusoidal(self, pixels: np.ndarray) -> AnalysisReport:
        if self.lp_per_mm is None:
            raise ValueError("lp_per_mm must be provided for sinusoidal target")

        mean_signal = float(np.mean(pixels))
        min_signal = float(np.min(pixels))
        max_signal = float(np.max(pixels))

        if max_signal == min_signal:
            measured_modulation = 0.0
        else:
            measured_modulation = (max_signal - min_signal) / (max_signal + min_signal)

        if self.input_modulation > 0:
            mtf = measured_modulation / self.input_modulation
        else:
            mtf = 0.0

        mtf = max(0.0, min(1.0, mtf))

        result = {
            "mtf": mtf,
            "mtf50": self.lp_per_mm if mtf >= 0.5 else 0.0,
            "mtf_curve_freq_cy_per_pixel": [self.lp_per_mm / 1000.0],
            "mtf_curve_mtf": [mtf],
            "measured_modulation": measured_modulation,
            "input_modulation": self.input_modulation,
        }

        if self.pixel_size is not None:
            result["mtf50_lp_per_mm"] = self.lp_per_mm if mtf >= 0.5 else 0.0
            result["mtf_curve_freq_lp_per_mm"] = [self.lp_per_mm]

        return AnalysisReport(measurements=result)

    def _analyze_slanted_edge(self, pixels: np.ndarray) -> AnalysisReport:
        return AnalysisReport(measurements={
            "mtf": 0.0,
            "note": "slanted_edge method not yet implemented",
        })
