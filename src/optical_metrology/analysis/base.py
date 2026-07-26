"""Base data structures and interfaces for the analysis package.

Defines the output container (:class:`AnalysisReport`), the pluggable
module interface (:class:`AnalysisModule`), and the simple orchestrator
(:class:`ImageAnalyzer`) that runs multiple modules and merges results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

import numpy as np


@dataclass
class AnalysisReport:
    """Structured output from an analysis pipeline.

    Attributes
    ----------
    histogram : np.ndarray or None
        1D array of pixel counts per unique intensity value.
    measurements : dict
        Key-value pairs of named scalar measurements
        (e.g. ``mean_intensity``, ``max_intensity``).
    """

    histogram: np.ndarray | None = None
    measurements: Dict[str, Any] = field(default_factory=dict)


class AnalysisModule:
    """Base class for pluggable image analysis modules.

    Subclasses implement :meth:`analyze` to compute specific metrics
    from a :class:`~detector.DigitalImage` and return an :class:`AnalysisReport`.
    """

    def analyze(self, image) -> AnalysisReport:
        """Run analysis on a digital image.

        Parameters
        ----------
        image : DigitalImage
            The image to analyse (must have a ``.pixels`` attribute).

        Returns
        -------
        AnalysisReport
            Histogram and/or measurements derived from the image.
        """
        raise NotImplementedError


class ImageAnalyzer:
    """Orchestrator that runs multiple :class:`AnalysisModule` s and merges results.

    Each module's report is folded into a single :class:`AnalysisReport`:
    measurements are merged via ``dict.update``, and the last non-``None``
    histogram wins.

    Parameters
    ----------
    modules : list of AnalysisModule or None
        Sequence of analysis modules to run in order.
    """

    def __init__(self, modules: List[AnalysisModule] | None = None):
        self.modules = modules or []

    def analyze(self, image) -> AnalysisReport:
        """Run all registered modules and return the merged report.

        Parameters
        ----------
        image : DigitalImage
            Input image for analysis.

        Returns
        -------
        AnalysisReport
            Combined results from all modules.
        """
        report = AnalysisReport()
        for module in self.modules:
            module_report = module.analyze(image)
            report.measurements.update(module_report.measurements)
            if module_report.histogram is not None:
                report.histogram = module_report.histogram
        return report
