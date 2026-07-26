"""Surface roughness estimation from speckle contrast.

Estimates the RMS surface roughness of a uniformly rough surface from
the contrast of a speckle pattern in a coherently illuminated image.
This is the inverse of the speckle contrast model used by
:class:`~detector.noise_models.SpeckleNoise`.
"""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np

from .base import AnalysisModule, AnalysisReport


class SpeckleRoughnessEstimator(AnalysisModule):
    """Estimate surface roughness from speckle contrast in an image.

    The speckle contrast is computed as ``C = std(pixels) / mean(pixels)``
    over the region of interest.  The roughness is then estimated as::

        σₕ = (Lc / 2) · √(1/C² − 1)

    where *Lc* is the source coherence length.

    Parameters
    ----------
    coherence_length : float
        Temporal coherence length of the illumination source in metres.
        Must match the value used in ``SpeckleNoise``.
    wavelength : float
        Illumination wavelength in metres (used for validity checks).
    roi : tuple of (row, col, height, width) or None
        Region of interest within the image.  If ``None``, the full
        image is used.
    """

    def __init__(
        self,
        coherence_length: float,
        wavelength: float,
        roi: Optional[Tuple[int, int, int, int]] = None,
    ):
        self.coherence_length = float(coherence_length)
        self.wavelength = float(wavelength)
        self.roi = roi

    def analyze(self, image) -> AnalysisReport:
        pixels = np.asarray(image.pixels, dtype=float)

        if self.roi is not None:
            r, c, h, w = self.roi
            pixels = pixels[r:r + h, c:c + w]

        mean_val = float(np.mean(pixels))
        std_val = float(np.std(pixels))

        if mean_val <= 0:
            return AnalysisReport(measurements={
                "speckle_contrast": 0.0,
                "estimated_roughness_rms": 0.0,
                "valid": False,
                "validity_reason": "zero mean intensity",
            })

        contrast = std_val / mean_val

        if contrast <= 0.0:
            return AnalysisReport(measurements={
                "speckle_contrast": 0.0,
                "estimated_roughness_rms": 0.0,
                "valid": False,
            })

        contrast = min(contrast, 0.999)

        roughness = (self.coherence_length / 2.0) * np.sqrt(1.0 / contrast ** 2 - 1.0)

        Lc = self.coherence_length
        valid = (contrast > 0.01) and (contrast < 0.99)
        if Lc <= 0 or self.wavelength <= 0:
            valid = False

        return AnalysisReport(measurements={
            "speckle_contrast": float(contrast),
            "estimated_roughness_rms": float(roughness),
            "valid": bool(valid),
        })
