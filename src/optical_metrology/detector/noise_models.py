"""Built-in detector noise model implementations.

Provides concrete :class:`DetectorNoiseModel` subclasses for common
imaging artefacts: fixed-pattern noise, hot pixels, column defects,
and photo-response non-uniformity.
"""

from __future__ import annotations

from typing import Optional

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
        If a float, the pattern is generated once as Gaussian noise with
        that standard deviation (in electrons) and kept constant across
        frames, as a true fixed-pattern offset.
    """

    def __init__(self, pattern=1.0):
        if isinstance(pattern, np.ndarray):
            self.pattern = pattern
        else:
            self._sigma = float(pattern)
            self.pattern = None
        self._generated: Optional[np.ndarray] = None
        self._generated_shape: Optional[tuple] = None

    def apply(self, electrons):
        if self.pattern is None:
            if self._generated is None or self._generated_shape != electrons.shape:
                self._generated = np.random.normal(0.0, self._sigma, size=electrons.shape)
                self._generated_shape = electrons.shape
            return electrons + self._generated
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


class SpeckleNoise(DetectorNoiseModel):
    """Multiplicative speckle noise from surface roughness and finite coherence.

    When coherent light reflects from a rough surface, the random phase
    delays produce a granular interference pattern (speckle).  The
    contrast of the speckle pattern depends on the ratio of the surface
    roughness :math:`\\sigma_h` to the source coherence length
    :math:`L_c`:

        .. math::

            C = \\frac{1}{\\sqrt{1 + (2 \\sigma_h / L_c)^2}}

    For fully coherent light (:math:`L_c \\gg \\sigma_h`), the speckle is
    fully developed (:math:`C \\approx 1`).  For incoherent light
    (:math:`L_c \\ll \\sigma_h`), no speckle appears (:math:`C \\approx 0`).

    Parameters
    ----------
    coherence_length : float
        Temporal coherence length of the source in metres.
        Set via :meth:`prepare` at capture time.
    """

    def __init__(self, coherence_length: float = 1e-3):
        self.coherence_length = coherence_length
        self._height_map: Optional[np.ndarray] = None
        self._wavelength: Optional[float] = None

    def prepare(self, height_map: np.ndarray, wavelength: float):
        """Supply the surface height map and wavelength before calling :meth:`apply`.

        Parameters
        ----------
        height_map : np.ndarray
            2D array of surface heights in metres.
        wavelength : float
            Illumination wavelength in metres.
        """
        self._height_map = np.asarray(height_map, dtype=float)
        self._wavelength = float(wavelength)

    def apply(self, electrons: np.ndarray) -> np.ndarray:
        if self._height_map is None or self._wavelength is None:
            return electrons

        roughness = float(np.std(self._height_map))
        if roughness < self._wavelength / 4.0 or self.coherence_length <= 0.0:
            return electrons

        contrast = 1.0 / np.sqrt(1.0 + (2.0 * roughness / self.coherence_length)**2)

        speckle = np.random.exponential(scale=1.0, size=electrons.shape)
        speckle = speckle / np.mean(speckle)

        return electrons * ((1.0 - contrast) + contrast * speckle)


class BloomingNoise(DetectorNoiseModel):
    """Charge blooming from saturated pixels into neighbours.

    When a pixel exceeds full-well capacity, excess charge spills into
    adjacent pixels.  This model distributes a fraction of the overflow
    to the four cardinal neighbours for a configurable number of
    iterations, producing the characteristic vertical/horizontal streaks
    seen in saturated CCD and CMOS images.

    The model runs *before* the final full-well clip in
    :class:`~detector.base.CMOSDetector`, so secondary blooming from
    neighbour overflow is handled naturally.

    Parameters
    ----------
    bloom_factor : float
        Fraction of excess charge that spills to *each* neighbouring
        pixel per iteration (default 0.05).  Typical values 0.01–0.1.
        Higher values produce faster, wider blooming.
    iterations : int
        Number of recursive bloom passes (default 2).  More iterations
        propagate blooming further from the original saturated pixel.
    full_well_capacity : float
        Maximum electron capacity per pixel before saturation.
        Should match ``CMOSDetector.full_well_capacity``.
    """

    def __init__(self, bloom_factor: float = 0.05, iterations: int = 2, full_well_capacity: float = 80000.0):
        self.bloom_factor = bloom_factor
        self.iterations = iterations
        self.full_well_capacity = full_well_capacity

    def apply(self, electrons: np.ndarray) -> np.ndarray:
        result = electrons.copy().astype(float)
        for _ in range(self.iterations):
            overflow = np.maximum(result - self.full_well_capacity, 0.0)
            if not np.any(overflow > 0):
                break
            result = np.minimum(result, self.full_well_capacity)
            spill = overflow * self.bloom_factor
            result[:-1, :] += spill[1:, :]
            result[1:, :]  += spill[:-1, :]
            result[:, :-1] += spill[:, 1:]
            result[:, 1:]  += spill[:, :-1]
        return np.minimum(result, self.full_well_capacity)


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
