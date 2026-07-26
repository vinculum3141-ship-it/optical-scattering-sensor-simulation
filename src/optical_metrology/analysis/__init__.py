"""Measurement and analysis modules for digital detector output.

This package provides the final stage of the simulation pipeline:
extracting quantitative measurements from captured
:class:`~detector.DigitalImage` s.  Modules fall into three groups:

Quality Assessment
    How good is the image?  Histogram statistics, SNR, contrast
    metrics, focus sharpness, saturation detection.

Optical Characterisation
    How well did the imaging system perform?  MTF, FFT-based
    frequency analysis, PSF estimation.

Metrology
    What are the engineering measurements?  Edge width / feature
    size, surface roughness, defect detection and classification,
    particle sizing, scratch measurement.

This classification mirrors the way real optical inspection systems
are evaluated in semiconductor metrology and industrial machine
vision.

Orchestrator and base classes
-----------------------------
- :class:`AnalysisReport` — structured output container
- :class:`AnalysisModule` — pluggable base for individual routines
- :class:`ImageAnalyzer` — runs multiple modules and merges results

Modules (existing)
------------------
Quality Assessment
- :class:`HistogramAnalyzer` — pixel histogram + mean/min/max
- :class:`ContrastAnalyzer` — RMS, Michelson, Weber contrast
- :class:`SaturationAnalyzer` — saturated pixel fraction

Modules (documented in docs/roadmap-todo.md, implement before use case)
------------------------------------------------------------------------
Quality Assessment       | Optical Characterisation | Metrology
-------------------------|--------------------------|--------------------------
:class:`FocusAnalyzer`   | :class:`MTFAnalyzer`     | :class:`EdgeDetectionAnalyzer`
:class:`SNRAnalyzer`     | :class:`FFTAnalyzer`     | :class:`SpeckleRoughnessEstimator`
                         |                          | :class:`IntensityProfileAnalyzer`
                         |                          | Defect detection (UC1)

See ``docs/roadmap-todo.md`` → *Pre-deployment gaps* for implementation
sketches and trigger use cases.
"""

from .base import AnalysisModule, AnalysisReport, ImageAnalyzer
from .contrast import ContrastAnalyzer, SaturationAnalyzer
from .defects import DefectAnalyzer
from .edge_detection import EdgeDetectionAnalyzer
from .error_map import ErrorMapAnalyzer
from .fft_analyzer import FFTAnalyzer
from .focus import FocusAnalyzer
from .histogram import HistogramAnalyzer
from .intensity_profile import IntensityProfileAnalyzer
from .mtf import MTFAnalyzer
from .snr import SNRAnalyzer
from .speckle_roughness import SpeckleRoughnessEstimator
from .tiled import TiledAcquisition

__all__ = [
    # Orchestration
    "AnalysisModule",
    "AnalysisReport",
    "ImageAnalyzer",
    # Quality Assessment
    "ContrastAnalyzer",
    "DefectAnalyzer",
    "EdgeDetectionAnalyzer",
    "ErrorMapAnalyzer",
    "FFTAnalyzer",
    "FocusAnalyzer",
    "HistogramAnalyzer",
    "IntensityProfileAnalyzer",
    "MTFAnalyzer",
    "SNRAnalyzer",
    "SaturationAnalyzer",
    "SpeckleRoughnessEstimator",
    "TiledAcquisition",
]
