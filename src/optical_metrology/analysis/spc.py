"""Statistical Process Control analysis for registration measurements (UC7).

Computes Cpk, mean shift, and trend statistics from a set of
registration (alignment) measurements.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np

from .base import AnalysisModule, AnalysisReport


class SPCAnalyzer(AnalysisModule):
    """Statistical process control from registration measurements.

    Parameters
    ----------
    usl : float
        Upper specification limit (default 1.0 pixel).
    lsl : float
        Lower specification limit (default -1.0 pixel).
    target : float
        Nominal target value (default 0.0).
    metric : str
        Which field to analyse from the measurement dicts (``"dx"``,
        ``"dy"``, or ``"rotation_deg"``).  Default ``"dx"``.
    """

    def __init__(
        self,
        usl: float = 1.0,
        lsl: float = -1.0,
        target: float = 0.0,
        metric: str = "dx",
    ):
        self.usl = usl
        self.lsl = lsl
        self.target = target
        self.metric = metric

    def analyze(self, image) -> AnalysisReport:
        return AnalysisReport(measurements={
            "note": "SPCAnalyzer requires analyse_measurements(); pass a list of dicts.",
        })

    def analyse_measurements(self, measurements: List[Dict]) -> AnalysisReport:
        """Compute SPC metrics from a list of measurement dicts.

        Each dict should contain the key specified by *metric*
        (e.g. ``"dx"``).

        Parameters
        ----------
        measurements : list of dict
            Registration or template-matching results.

        Returns
        -------
        AnalysisReport
            Contains cpk, mean_shift, ppk, std, and trend fields.
        """
        values = np.array([
            float(m[self.metric]) for m in measurements
            if self.metric in m
        ])

        if len(values) == 0:
            return AnalysisReport(measurements={
                "cpk": 0.0,
                "mean_shift": 0.0,
                "ppk": 0.0,
                "std": 0.0,
                "mean": 0.0,
                "n": 0,
                "metric": self.metric,
            })

        mean = float(np.mean(values))
        std = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0

        if std > 0:
            cpu = (self.usl - mean) / (3.0 * std)
            cpl = (mean - self.lsl) / (3.0 * std)
            cpk = min(cpu, cpl)
            ppk = cpk
        else:
            cpk = float("inf") if self.lsl < mean < self.usl else 0.0
            ppk = cpk

        mean_shift = mean - self.target

        trend = self._compute_trend(values)

        return AnalysisReport(measurements={
            "cpk": cpk,
            "mean_shift": mean_shift,
            "ppk": ppk,
            "std": std,
            "mean": mean,
            "n": len(values),
            "metric": self.metric,
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "trend_slope": trend[0],
            "trend_intercept": trend[1],
        })

    def _compute_trend(self, values: np.ndarray) -> Tuple[float, float]:
        n = len(values)
        if n < 2:
            return 0.0, float(values[0]) if n == 1 else 0.0
        x = np.arange(n, dtype=float)
        coeffs = np.polyfit(x, values, 1)
        return float(coeffs[0]), float(coeffs[1])
