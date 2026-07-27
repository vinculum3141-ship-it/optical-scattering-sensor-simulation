"""Detector and digitisation models for optical scattering sensor simulation.

This package provides the final stage of the simulation pipeline:
converting a :class:`~optics.SensorField` into a digital image.

    - :class:`CMOSDetector` — full pipeline from irradiance to digital counts
      (photon conversion, shot noise, dark current, read noise, ADC)
    - :class:`DigitalImage` — output container holding the pixel array and
      capture metadata
    - :class:`DetectorNoiseModel` — extensible base for custom noise stages
"""

from .base import CMOSDetector, DigitalImage, DetectorNoiseModel
from .cfa import CFAConfig, CFADetector
from .spad import SPADDetector
from .noise_models import (
    BloomingNoise,
    ColumnDefectNoise,
    DeadPixelNoise,
    FixedPatternNoise,
    HotPixelNoise,
    PhotoResponseNonUniformity,
    SpeckleNoise,
)

__all__ = [
    "BloomingNoise",
    "CFAConfig",
    "CFADetector",
    "CMOSDetector",
    "ColumnDefectNoise",
    "DeadPixelNoise",
    "DetectorNoiseModel",
    "DigitalImage",
    "FixedPatternNoise",
    "HotPixelNoise",
    "PhotoResponseNonUniformity",
    "SPADDetector",
    "SpeckleNoise",
]
