"""Image analysis and reporting modules for digital detector output.

This package provides the final analysis stage of the simulation pipeline:
extracting quantitative measurements from captured :class:`~detector.DigitalImage` s.

    - :class:`AnalysisReport` — structured output (histogram, measurements dict)
    - :class:`AnalysisModule` — pluggable base for individual analysis routines
    - :class:`HistogramAnalyzer` — computes pixel histogram and basic statistics
    - :class:`ImageAnalyzer` — orchestrator that runs multiple modules and merges
      their reports into one
"""

from .base import AnalysisModule, AnalysisReport, ImageAnalyzer
from .histogram import HistogramAnalyzer
from .contrast import ContrastAnalyzer, SaturationAnalyzer

__all__ = [
    "AnalysisModule",
    "AnalysisReport",
    "ContrastAnalyzer",
    "HistogramAnalyzer",
    "ImageAnalyzer",
    "SaturationAnalyzer",
]
