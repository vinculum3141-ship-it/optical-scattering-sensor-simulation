"""Detector and digitisation models for optical scattering sensor simulation.

This package provides the final stage of the simulation pipeline:
converting a :class:`~optics.SensorField` into a digital image.

Core detector
    - :class:`CMOSDetector` — full pipeline from irradiance to digital counts
      (photon conversion, shot noise, dark current, read noise, ADC)
    - :class:`DigitalImage` — output container holding the pixel array and
      capture metadata
    - :class:`DetectorNoiseModel` — extensible base for custom noise stages

Noise model stages (applied after read noise; :class:`CMOSDetector` already
includes shot, dark-current, and read-noise internally)
    - :class:`FixedPatternNoise` — per-pixel constant offset FPN
    - :class:`PhotoResponseNonUniformity` — pixel-to-pixel PRNU
    - :class:`DeadPixelNoise` — stuck low / stuck high pixels
    - :class:`HotPixelNoise` — excessive dark current pixels
    - :class:`ColumnDefectNoise` — whole-column failure
    - :class:`BloomingNoise` — excess charge spillover
    - :class:`SpeckleNoise` — multiplicative speckle pattern

Specialised detectors
    - :class:`CFAConfig` — colour filter array pattern definition (UC2)
    - :class:`CFADetector` — CMOSDetector + Bayer-mosaic demosaicing (UC2)
    - :class:`SPADDetector` — single-photon avalanche diode (UC6)
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
