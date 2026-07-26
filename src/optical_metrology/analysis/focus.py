"""Focus / sharpness metric computation for digital images.

Computes a scalar focus score from a single image using one of several
well-known no-reference sharpness metrics.  Useful for through-focus
scanning (UC1), projector focus (UC5), and autofocus applications.
"""

from __future__ import annotations

import numpy as np

from .base import AnalysisModule, AnalysisReport


def _laplacian_variance(pixels: np.ndarray) -> float:
    kernel = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=float)
    lap = _convolve2d(pixels, kernel)
    return float(np.var(lap))


def _tenengrad(pixels: np.ndarray) -> float:
    sobel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=float)
    sobel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=float)
    gx = _convolve2d(pixels, sobel_x)
    gy = _convolve2d(pixels, sobel_y)
    return float(np.mean(gx ** 2 + gy ** 2))


def _brenner(pixels: np.ndarray) -> float:
    diff = pixels[:, :-2] - pixels[:, 2:]
    return float(np.mean(diff ** 2))


def _convolve2d(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    k_h, k_w = kernel.shape
    pad_h = k_h // 2
    pad_w = k_w // 2
    padded = np.pad(image, ((pad_h, pad_h), (pad_w, pad_w)), mode="edge")
    result = np.zeros_like(image, dtype=float)
    for i in range(k_h):
        for j in range(k_w):
            result += kernel[i, j] * padded[i:i + image.shape[0], j:j + image.shape[1]]
    return result


class FocusAnalyzer(AnalysisModule):
    """Compute a scalar focus score from a single image.

    Parameters
    ----------
    method : str
        One of:

        ``"laplacian_variance"``
            Variance of the Laplacian response.  High value = sharp.
            Sensitive to noise but widely used for autofocus.
        ``"tenengrad"``
            Mean squared gradient magnitude from a Sobel operator.
            Robust and commonly used in machine vision.
        ``"brenner"``
            Sum of squared differences between pixels two apart in x.
            Fast, no convolution — pure pixel differences.
    """

    def __init__(self, method: str = "laplacian_variance"):
        if method not in ("laplacian_variance", "tenengrad", "brenner"):
            raise ValueError(f"Unknown focus method: {method!r}")
        self.method = method

    def analyze(self, image) -> AnalysisReport:
        pixels = np.asarray(image.pixels, dtype=float)

        if self.method == "laplacian_variance":
            score = _laplacian_variance(pixels)
        elif self.method == "tenengrad":
            score = _tenengrad(pixels)
        else:
            score = _brenner(pixels)

        return AnalysisReport(measurements={
            "focus_score": score,
            "focus_method": self.method,
        })
