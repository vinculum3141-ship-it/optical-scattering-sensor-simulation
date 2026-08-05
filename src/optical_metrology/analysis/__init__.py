"""Measurement and analysis modules for digital detector output.

This package provides the final stage of the simulation pipeline:
extracting quantitative measurements from captured
:class:`~detector.DigitalImage` s.  Modules fall into three groups:

Quality Assessment
    How good is the image?  Histogram statistics, SNR, contrast
    metrics, focus sharpness, saturation detection, sensor
    characterisation (PTC, dynamic range, linearity).

Optical Characterisation
    How well did the imaging system perform?  MTF, FFT-based
    frequency analysis, phase extraction, height reconstruction.

Metrology
    What are the engineering measurements?  Edge width / feature
    size, surface roughness, defect detection and classification,
    particle sizing, scratch measurement, registration, SPC.

This classification mirrors the way real optical inspection systems
are evaluated in semiconductor metrology and industrial machine
vision.

Orchestrator and base classes
-----------------------------
- :class:`AnalysisReport` — structured output container
- :class:`AnalysisModule` — pluggable base for individual routines
- :class:`ImageAnalyzer` — runs multiple modules and merges results

Modules by group
----------------
Quality Assessment
    :class:`HistogramAnalyzer` — pixel histogram + mean/min/max
    :class:`ContrastAnalyzer` — RMS, Michelson, Weber contrast
    :class:`SaturationAnalyzer` — saturated pixel fraction
    :class:`FocusAnalyzer` — Laplacian/Tenengrad/Brenner sharpness
    :class:`SNRAnalyzer` — single-image and flat-field-pair SNR
    :class:`PTCAnalyzer` — photon transfer curve (gain, read noise, FWC)
    :class:`DynamicRangeAnalyzer` — max/min dynamic range
    :class:`LinearityTestAnalyzer` — linearity error vs. exposure

Optical Characterisation
    :class:`MTFAnalyzer` — modulation transfer function (sinusoidal)
    :class:`FFTAnalyzer` — 2D power spectrum, radial profile
    :class:`PhaseExtractor` — N-step phase-shifting algorithm (UC5)
    :class:`PhaseUnwrapper` — spatial flood-fill unwrapping (UC5)
    :class:`HeightReconstructor` — phase→height via triangulation (UC5)
    :class:`SurfaceComparator` — RMS error vs. ground truth (UC5)

Metrology
    :class:`EdgeDetectionAnalyzer` — Sobel edge detection, hysteresis
    :class:`SpeckleRoughnessEstimator` — inverse speckle contrast
    :class:`IntensityProfileAnalyzer` — line cross-section, contrast
    :class:`ErrorMapAnalyzer` — RMSE, MAE, PSNR vs. reference
    :class:`DefectAnalyzer` — blob/scratch detection, classification,
        pass/fail decision (UC1)
    :class:`TiledAcquisition` — multi-FOV scanning and stitching (UC1)
    :class:`SpectralAnalyzer` — band ratios, spectral angle mapper,
        material classification (UC2)
    :class:`GoniometricSweep` — angle-resolved BRDF sweep (UC4)
    :class:`BRDFFitter` — fits model params to BRDF data (UC4)
    :class:`ScatteringSweep` — multi-parameter sweep (roughness, angle,
        wavelength, refractive index, model) (UC4)
    :class:`TemplateMatcher` — normalised cross-correlation (UC7)
    :class:`RegistrationAnalyzer` — translation/rotation alignment (UC7)
    :class:`SPCAnalyzer` — Cpk, mean shift, trend (UC7)
    :class:`LiDARRangeEquation` — received power from range eqn (UC6)
    :class:`TimeOfFlightPropagator` — ToF + pulse broadening (UC6)
    :class:`WaveformAnalyzer` — peak detection, CFD (UC6)
    :func:`generate_point_cloud` — (range, az, el) → xyz + intensity (UC6)

Test chart generators (UC3)
    :func:`siemens_star` — spatial frequency test
    :func:`slanted_edge` — MTF edge target
    :func:`greyscale_wedge` — linearity ramp
"""

from .base import AnalysisModule, AnalysisReport, ImageAnalyzer
from .brdf_fit import BRDFFitter
from .contrast import ContrastAnalyzer, SaturationAnalyzer
from .defects import DefectAnalyzer
from .dynamic_range import DynamicRangeAnalyzer
from .edge_detection import EdgeDetectionAnalyzer
from .error_map import ErrorMapAnalyzer
from .fft_analyzer import FFTAnalyzer
from .focus import FocusAnalyzer
from .goniometry import GoniometricSweep
from .histogram import HistogramAnalyzer
from .intensity_profile import IntensityProfileAnalyzer
from .lidar import LiDARRangeEquation, TimeOfFlightPropagator, WaveformAnalyzer, generate_point_cloud
from .linearity import LinearityTestAnalyzer
from .mtf import MTFAnalyzer
from .phase import PhaseExtractor, PhaseUnwrapper
from .ptc import PTCAnalyzer
from .reconstruction import HeightReconstructor, SurfaceComparator
from .registration import RegistrationAnalyzer, TemplateMatcher
from .scattering_sweep import ScatteringSweep, SweepCase
from .spc import SPCAnalyzer
from .snr import SNRAnalyzer
from .spectral import ReferenceSpectrum, SpectralAnalyzer
from .speckle_roughness import SpeckleRoughnessEstimator
from .test_charts import greyscale_wedge, siemens_star, slanted_edge
from .tiled import TiledAcquisition

__all__ = [
    # Orchestration
    "AnalysisModule",
    "AnalysisReport",
    "ImageAnalyzer",
    # BRDF fitting
    "BRDFFitter",
    # Quality Assessment
    "ContrastAnalyzer",
    "DefectAnalyzer",
    "DynamicRangeAnalyzer",
    "EdgeDetectionAnalyzer",
    "ErrorMapAnalyzer",
    "FFTAnalyzer",
    "FocusAnalyzer",
    "GoniometricSweep",
    "greyscale_wedge",
    "HistogramAnalyzer",
    "IntensityProfileAnalyzer",
    "LiDARRangeEquation",
    "LinearityTestAnalyzer",
    "HeightReconstructor",
    "generate_point_cloud",
    "MTFAnalyzer",
    "PhaseExtractor",
    "PhaseUnwrapper",
    "PTCAnalyzer",
    "SurfaceComparator",
    "SNRAnalyzer",
    "ReferenceSpectrum",
    "RegistrationAnalyzer",
    "SaturationAnalyzer",
    "ScatteringSweep",
    "siemens_star",
    "TimeOfFlightPropagator",
    "WaveformAnalyzer",
    "slanted_edge",
    "SPCAnalyzer",
    "SpectralAnalyzer",
    "SpeckleRoughnessEstimator",
    "TemplateMatcher",
    "SweepCase",
    "TiledAcquisition",
]
