"""Height reconstruction and surface comparison for structured light (UC5).

Provides :class:`HeightReconstructor` to convert phase difference to
height via triangulation, and :class:`SurfaceComparator` to evaluate
reconstruction accuracy against ground truth.
"""

from __future__ import annotations

from typing import Tuple

import numpy as np


class HeightReconstructor:
    """Convert phase difference to height map using triangulation.

    The height at each pixel is computed as:

        h(x,y) = (Δφ(x,y) · p) / (2π · tan(θ))

    where:
        Δφ(x,y)  — unwrapped phase difference (measured - reference)
        p         — fringe period in the same spatial units as height
        θ         — projection angle (radians)
    """

    def reconstruct(
        self,
        measured_phase: np.ndarray,
        reference_phase: np.ndarray,
        period: float = 16.0,
        projection_angle: float = 0.5,
    ) -> np.ndarray:
        """Reconstruct height map from measured and reference phase maps.

        Parameters
        ----------
        measured_phase : np.ndarray
            Unwrapped phase of the measured object.
        reference_phase : np.ndarray
            Unwrapped phase of a reference plane (or zeros).
        period : float
            Fringe period in spatial units (same units as output height).
        projection_angle : float
            Projection angle θ in radians.

        Returns
        -------
        np.ndarray
            Reconstructed height map (same shape as input).
        """
        delta_phase = measured_phase - reference_phase
        height = (delta_phase * period) / (2.0 * np.pi * np.tan(projection_angle))
        return height


class SurfaceComparator:
    """Compare a reconstructed height map against ground truth.

    Computes RMS error, MAE, max error, and a pixel-wise error map.
    """

    def compare(
        self,
        reconstructed: np.ndarray,
        ground_truth: np.ndarray,
    ) -> dict:
        """Compute error metrics between reconstructed and ground truth.

        Parameters
        ----------
        reconstructed : np.ndarray
            Reconstructed height map.
        ground_truth : np.ndarray
            Ground truth height map (same shape).

        Returns
        -------
        dict
            ``rms``       — root mean square error
            ``mae``       — mean absolute error
            ``max_error`` — maximum absolute error
            ``error_map`` — pixel-wise signed error (ground_truth - reconstructed)
        """
        if reconstructed.shape != ground_truth.shape:
            raise ValueError(
                f"Shape mismatch: reconstructed {reconstructed.shape} != "
                f"ground_truth {ground_truth.shape}"
            )

        error = ground_truth - reconstructed
        rms = float(np.sqrt(np.mean(error**2)))
        mae = float(np.mean(np.abs(error)))
        max_err = float(np.max(np.abs(error)))

        return {
            "rms": rms,
            "mae": mae,
            "max_error": max_err,
            "error_map": error,
        }
