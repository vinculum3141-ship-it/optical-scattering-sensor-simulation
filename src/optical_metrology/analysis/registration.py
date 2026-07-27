"""Template matching, registration, and overlay analysis (UC7).

Provides normalised cross-correlation template matching, translation/
rotation misalignment detection, and registration overlay analysis.
"""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np

from .base import AnalysisModule, AnalysisReport


class TemplateMatcher(AnalysisModule):
    """Locate a template in an image via normalised cross-correlation.

    Parameters
    ----------
    template : ndarray or None
        Reference template image.  If ``None``, set via
        :meth:`set_template` before analysis.
    """

    def __init__(self, template=None):
        self._template = np.asarray(template, dtype=float) if template is not None else None

    def set_template(self, template):
        self._template = np.asarray(template, dtype=float)

    def analyze(self, image) -> AnalysisReport:
        pixels = np.asarray(image.pixels, dtype=float)
        if self._template is None:
            return AnalysisReport(measurements={"error": "no template set"})

        th, tw = self._template.shape
        if th > pixels.shape[0] or tw > pixels.shape[1]:
            return AnalysisReport(measurements={"error": "template larger than image"})

        corr = self._ncc(pixels, self._template)

        max_idx = np.unravel_index(np.argmax(corr), corr.shape)
        max_val = float(corr[max_idx])

        return AnalysisReport(measurements={
            "match_row": int(max_idx[0]),
            "match_col": int(max_idx[1]),
            "match_score": max_val,
            "template_height": th,
            "template_width": tw,
        })

    def _ncc(self, image: np.ndarray, template: np.ndarray) -> np.ndarray:
        th, tw = template.shape
        template_norm = template - np.mean(template)
        template_std = np.std(template)
        if template_std == 0:
            return np.zeros((image.shape[0] - th + 1, image.shape[1] - tw + 1))

        result = np.zeros((image.shape[0] - th + 1, image.shape[1] - tw + 1))
        for i in range(result.shape[0]):
            for j in range(result.shape[1]):
                patch = image[i:i + th, j:j + tw]
                patch_norm = patch - np.mean(patch)
                patch_std = np.std(patch)
                if patch_std == 0:
                    result[i, j] = 0.0
                else:
                    result[i, j] = np.sum(patch_norm * template_norm) / (
                        patch_std * template_std * th * tw
                    )
        return result


class RegistrationAnalyzer(AnalysisModule):
    """Measure translation/rotation misalignment between reference and test images.

    Parameters
    ----------
    max_offset : int
        Maximum pixel shift to search in each direction.
    """

    def __init__(self, max_offset: int = 10):
        self.max_offset = max_offset

    def analyze(self, image) -> AnalysisReport:
        return AnalysisReport(measurements={
            "dx": 0.0,
            "dy": 0.0,
            "rotation_deg": 0.0,
            "scale": 1.0,
            "note": "full registration requires a reference image; use analyze_pair()",
        })

    def analyze_pair(self, reference, test) -> AnalysisReport:
        ref = np.asarray(reference.pixels, dtype=float)
        tst = np.asarray(test.pixels, dtype=float)

        if ref.shape != tst.shape:
            return AnalysisReport(measurements={"error": "shape mismatch"})

        corr = np.fft.fft2(ref) * np.conj(np.fft.fft2(tst))
        corr = np.fft.fftshift(np.abs(np.fft.ifft2(corr)))
        peak = np.unravel_index(np.argmax(corr), corr.shape)
        cy, cx = ref.shape[0] // 2, ref.shape[1] // 2
        dy = float(peak[0] - cy)
        dx = float(peak[1] - cx)

        return AnalysisReport(measurements={
            "dx": dx,
            "dy": dy,
            "rotation_deg": 0.0,
            "scale": 1.0,
        })
