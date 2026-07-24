"""Built-in detector noise model implementations.

Provides concrete :class:`DetectorNoiseModel` subclasses for common
imaging artefacts: fixed-pattern noise, hot pixels, column defects,
and photo-response non-uniformity.
"""

from __future__ import annotations

import numpy as np

from .base import DetectorNoiseModel


class FixedPatternNoise(DetectorNoiseModel):
    """Additive fixed-pattern noise (FPN).

    FPN is a constant offset per pixel that does not vary from frame
    to frame.  It is characteristic of CMOS sensors and arises from
    pixel-to-pixel variations in the readout chain.

    Parameters
    ----------
    pattern : np.ndarray or float
        If an array, used directly as the per-pixel offset in electrons.
        If a float, the pattern is generated as Gaussian noise with
        that standard deviation (in electrons).
    """

    def __init__(self, pattern=1.0):
        if isinstance(pattern, np.ndarray):
            self.pattern = pattern
        else:
            self._sigma = float(pattern)
            self.pattern = None

    def apply(self, electrons):
        if self.pattern is None:
            return electrons + np.random.normal(0.0, self._sigma, size=electrons.shape)
        if self.pattern.shape != electrons.shape:
            raise ValueError(
                f"FPN pattern shape {self.pattern.shape} does not match "
                f"electron array shape {electrons.shape}"
            )
        return electrons + self.pattern


class PhotoResponseNonUniformity(DetectorNoiseModel):
    """Multiplicative photo-response non-uniformity (PRNU).

    PRNU is a per-pixel gain variation that scales with the signal.
    It is expressed as a fraction of the signal level.

    Parameters
    ----------
    magnitude : float
        Standard deviation of the gain variation as a fraction of
        the signal.  Typical values: 0.001–0.05 (0.1%–5%).
    """

    def __init__(self, magnitude=0.01):
        self.magnitude = magnitude

    def apply(self, electrons):
        gain = np.random.normal(1.0, self.magnitude, size=electrons.shape)
        return electrons * gain


class HotPixelNoise(DetectorNoiseModel):
    """Simulates hot pixels with anomalously high dark current.

    Hot pixels are defective sites that generate more dark current
    than normal.  They appear as bright spots in the image, especially
    at long exposure times.

    Parameters
    ----------
    density : float
        Fraction of pixels that are hot (default 0.001 = 0.1%).
    hot_current : float
        Dark current of hot pixels in electrons per second
        (default 100 e⁻/s, compared to typical ~5 e⁻/s).
    exposure_time : float
        Exposure time in seconds.  Used to compute the total dark
        signal from hot pixels.
    """

    def __init__(self, density=0.001, hot_current=100.0, exposure_time=0.1):
        self.density = density
        self.hot_current = hot_current
        self.exposure_time = exposure_time

    def apply(self, electrons):
        mask = np.random.random(electrons.shape) < self.density
        n_hot = int(mask.sum())
        if n_hot > 0:
            dark_hot = np.random.poisson(
                self.hot_current * self.exposure_time, size=n_hot,
            )
            electrons[mask] += dark_hot
        return electrons


class ColumnDefectNoise(DetectorNoiseModel):
    """Models a defective column with reduced sensitivity.

    Common in CCD and CMOS sensors where a column amplifier or
    readout chain is damaged or degraded.

    Parameters
    ----------
    column_index : int
        Index of the affected column.
    scale_factor : float
        Gain factor applied to the column.  Values < 1 simulate
        reduced sensitivity; 0 produces a dead column; > 1 gives
        a bright column.
    """

    def __init__(self, column_index=0, scale_factor=0.5):
        self.column_index = column_index
        self.scale_factor = scale_factor

    def apply(self, electrons):
        electrons[:, self.column_index] *= self.scale_factor
        return electrons


class DeadPixelNoise(DetectorNoiseModel):
    """Replaces random pixels with a fixed value (dead/stuck pixels).

    Dead pixels output a constant (usually zero) regardless of
    illumination.  Stuck pixels output a constant high value.

    Parameters
    ----------
    density : float
        Fraction of pixels that are dead/stuck (default 0.001).
    stuck_value : float
        Output value in electrons (default 0 for dead pixels).
        Use a large value (e.g. full_well_capacity) for stuck-bright.
    """

    def __init__(self, density=0.001, stuck_value=0.0):
        self.density = density
        self.stuck_value = stuck_value

    def apply(self, electrons):
        mask = np.random.random(electrons.shape) < self.density
        electrons[mask] = self.stuck_value
        return electrons
