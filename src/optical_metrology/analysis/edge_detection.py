"""Edge detection analysis module.

Locates and characterises step edges in an image using Sobel-based
gradient magnitude with optional hysteresis thresholding.
"""

from __future__ import annotations

import numpy as np

from .base import AnalysisModule, AnalysisReport


def _sobel_gradient(image: np.ndarray) -> np.ndarray:
    kx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=float)
    ky = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=float)
    h, w = image.shape
    padded = np.pad(image.astype(float), 1, mode="edge")
    gx = np.zeros((h, w), dtype=float)
    gy = np.zeros((h, w), dtype=float)
    for i in range(3):
        for j in range(3):
            gx += kx[i, j] * padded[i:i + h, j:j + w]
            gy += ky[i, j] * padded[i:i + h, j:j + w]
    return np.sqrt(gx ** 2 + gy ** 2)


class EdgeDetectionAnalyzer(AnalysisModule):
    """Detect and characterise step edges in an image.

    Parameters
    ----------
    low_threshold : float
        Fraction of max gradient below which pixels are suppressed
        (default 0.1).  Relative to the maximum gradient in the image.
    high_threshold : float
        Fraction of max gradient for hysteresis edge tracking
        (default 0.3).  Pixels above this are strong edges.
    """

    def __init__(self, low_threshold: float = 0.1, high_threshold: float = 0.3):
        self.low_threshold = float(low_threshold)
        self.high_threshold = float(high_threshold)

    def analyze(self, image) -> AnalysisReport:
        pixels = np.asarray(image.pixels, dtype=float)

        grad = _sobel_gradient(pixels)

        if np.max(grad) > 0:
            grad_norm = grad / np.max(grad)
        else:
            grad_norm = grad

        strong = grad_norm >= self.high_threshold
        weak = (grad_norm >= self.low_threshold) & (grad_norm < self.high_threshold)

        edge_count = int(np.sum(strong))
        edge_density = edge_count / pixels.size
        mean_strength = float(np.mean(grad[strong])) if edge_count > 0 else 0.0

        centroids = np.where(strong)
        if len(centroids[0]) > 0:
            centroid_row = float(np.mean(centroids[0]))
            centroid_col = float(np.mean(centroids[1]))
        else:
            centroid_row = 0.0
            centroid_col = 0.0

        return AnalysisReport(measurements={
            "edge_count": edge_count,
            "edge_density": edge_density,
            "mean_edge_strength": mean_strength,
            "centroid_row": centroid_row,
            "centroid_col": centroid_col,
        })
