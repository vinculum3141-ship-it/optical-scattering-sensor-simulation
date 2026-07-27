"""Phase extraction and unwrapping for structured light 3D scanning (UC5).

Provides :class:`PhaseExtractor` for N-step phase-shifting and
:class:`PhaseUnwrapper` for spatial flood-fill phase unwrapping.
"""

from __future__ import annotations

from typing import List, Optional

import numpy as np


class PhaseExtractor:
    """Extract wrapped phase from N phase-shifted fringe images.

    Uses the standard N-step phase-shifting algorithm:

        φ(x,y) = -arctan( Σᵢ Iᵢ(x,y) sin(δᵢ) / Σᵢ Iᵢ(x,y) cos(δᵢ) )

    where Iᵢ are the captured fringe intensities and δᵢ are the
    known phase shifts.

    Parameters
    ----------
    phase_shifts : list of float
        Phase offsets in radians used for each fringe pattern.
    """

    def __init__(self, phase_shifts: Optional[List[float]] = None):
        if phase_shifts is None:
            phase_shifts = [0.0, 1.5707963267948966, 3.141592653589793, 4.71238898038469]
        self.phase_shifts = np.asarray(phase_shifts, dtype=float)

    def extract(self, fringe_images):
        """Compute the wrapped phase from a list of fringe images.

        Parameters
        ----------
        fringe_images : list of np.ndarray
            List of 2D fringe intensity arrays captured with the
            phase shifts given at construction.

        Returns
        -------
        np.ndarray
            Wrapped phase map in radians, values in [-π, π).
            Same shape as input images.
        """
        if len(fringe_images) != len(self.phase_shifts):
            raise ValueError(
                f"Expected {len(self.phase_shifts)} fringe images, "
                f"got {len(fringe_images)}"
            )

        numerator = np.zeros_like(fringe_images[0], dtype=float)
        denominator = np.zeros_like(fringe_images[0], dtype=float)

        for img, shift in zip(fringe_images, self.phase_shifts):
            I = np.asarray(img, dtype=float)
            numerator += I * np.sin(shift)
            denominator += I * np.cos(shift)

        return -np.arctan2(numerator, denominator)


class PhaseUnwrapper:
    """Spatial phase unwrapping using flood-fill.

    Unwraps a 2D wrapped phase array by adding or subtracting
    multiples of 2π to remove 2π discontinuities.
    """

    def unwrap(self, phase_wrapped: np.ndarray, seed: tuple = (0, 0)) -> np.ndarray:
        """Unwrap a 2D wrapped phase map using flood-fill.

        Starting from the seed pixel, the algorithm scans outward,
        adding ±2π whenever the phase difference between adjacent
        pixels exceeds π in absolute value.

        Parameters
        ----------
        phase_wrapped : np.ndarray
            2D array of wrapped phase values in [-π, π).
        seed : tuple of int
            (row, col) seed pixel for the flood-fill.

        Returns
        -------
        np.ndarray
            Unwrapped phase map (same shape).
        """
        phase = np.asarray(phase_wrapped, dtype=float).copy()
        h, w = phase.shape
        unwrapped = np.zeros_like(phase)
        visited = np.zeros((h, w), dtype=bool)

        r0, c0 = seed
        unwrapped[r0, c0] = phase[r0, c0]
        visited[r0, c0] = True

        stack = [(r0, c0)]
        while stack:
            r, c = stack.pop()
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w and not visited[nr, nc]:
                    diff = phase[nr, nc] - unwrapped[r, c]
                    if diff > np.pi:
                        unwrapped[nr, nc] = phase[nr, nc] - 2.0 * np.pi
                    elif diff < -np.pi:
                        unwrapped[nr, nc] = phase[nr, nc] + 2.0 * np.pi
                    else:
                        unwrapped[nr, nc] = phase[nr, nc]
                    visited[nr, nc] = True
                    stack.append((nr, nc))

        return unwrapped
