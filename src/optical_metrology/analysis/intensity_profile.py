"""Intensity profile extraction and analysis along a line through an image.

Useful for measuring scratch depth visibility (UC1), fringe modulation
(UC5), and edge sharpness (UC7).
"""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np

from .base import AnalysisModule, AnalysisReport


def _bilinear_interpolate(image: np.ndarray, rows: np.ndarray, cols: np.ndarray) -> np.ndarray:
    """Bilinear interpolation at fractional (row, col) coordinates."""
    r0 = np.floor(rows).astype(np.int64)
    c0 = np.floor(cols).astype(np.int64)
    r1 = r0 + 1
    c1 = c0 + 1
    dr = rows - r0
    dc = cols - c0

    r0 = np.clip(r0, 0, image.shape[0] - 1)
    c0 = np.clip(c0, 0, image.shape[1] - 1)
    r1 = np.clip(r1, 0, image.shape[0] - 1)
    c1 = np.clip(c1, 0, image.shape[1] - 1)

    top = image[r0, c0] * (1 - dc) + image[r0, c1] * dc
    bot = image[r1, c0] * (1 - dc) + image[r1, c1] * dc
    return top * (1 - dr) + bot * dr


class IntensityProfileAnalyzer(AnalysisModule):
    """Extract a 1D intensity profile along a line through the image.

    The profile is sampled at regular intervals between *start* and
    *end* using bilinear interpolation.  When *linewidth > 1*, the
    profile is averaged over that many parallel lines orthogonal to
    the profile direction for noise reduction.

    Parameters
    ----------
    start : tuple of (row, col)
        Starting pixel coordinates (inclusive).  Default (0, 0).
    end : tuple of (row, col) or None
        Ending pixel coordinates (inclusive).  If None, the profile
        runs to the bottom-right corner of the image.
    num_samples : int
        Number of sample points along the line.  Default 256.
    linewidth : float
        Width of the extraction band in pixels (orthogonal to the
        profile direction).  Values > 1 average multiple profiles
        for noise reduction.  Default 1.
    """

    def __init__(
        self,
        start: Tuple[float, float] = (0.0, 0.0),
        end: Optional[Tuple[float, float]] = None,
        num_samples: int = 256,
        linewidth: float = 1.0,
    ):
        self.start = start
        self.end = end
        self.num_samples = int(num_samples)
        self.linewidth = float(linewidth)

    def analyze(self, image) -> AnalysisReport:
        pixels = np.asarray(image.pixels, dtype=float)
        H, W = pixels.shape

        start = (float(self.start[0]), float(self.start[1]))
        end = self.end
        if end is None:
            end = (float(H - 1), float(W - 1))
        else:
            end = (float(end[0]), float(end[1]))

        num = self.num_samples
        ts = np.linspace(0.0, 1.0, num)
        rows = start[0] + (end[0] - start[0]) * ts
        cols = start[1] + (end[1] - start[1]) * ts

        profile = _bilinear_interpolate(pixels, rows, cols)

        if self.linewidth > 1.0:
            dx = end[1] - start[1]
            dy = end[0] - start[0]
            length = np.sqrt(dx ** 2 + dy ** 2)
            if length > 0:
                nx = -dy / length
                ny = dx / length
                half = self.linewidth / 2.0
                offsets = np.linspace(-half, half, max(3, int(self.linewidth)))
                profiles = []
                for off in offsets:
                    r_off = rows + ny * off
                    c_off = cols + nx * off
                    profiles.append(_bilinear_interpolate(pixels, r_off, c_off))
                profile = np.mean(profiles, axis=0)

        profile_min = float(np.min(profile))
        profile_max = float(np.max(profile))
        profile_mean = float(np.mean(profile))
        contrast = (profile_max - profile_min) / (profile_max + profile_min + 1e-10)

        dist = np.linalg.norm([end[0] - start[0], end[1] - start[1]])
        x_axis = np.linspace(0, float(dist), num)

        return AnalysisReport(measurements={
            "profile": profile.tolist(),
            "profile_x_axis": x_axis.tolist(),
            "profile_min": profile_min,
            "profile_max": profile_max,
            "profile_mean": profile_mean,
            "profile_contrast": contrast,
            "start_row": start[0],
            "start_col": start[1],
            "end_row": end[0],
            "end_col": end[1],
        })
