"""SPAD / Geiger-mode single-photon avalanche diode detector model.

Simulates photon counting with dead time, dark counts, and jitter.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np


@dataclass
class SPADEvent:
    timestamp: float
    pixel: int


class SPADDetector:
    """Single-photon avalanche diode detector array.

    Parameters
    ----------
    dead_time : float
        Dead time after each detection in seconds.
    photon_detection_efficiency : float
        Probability of detecting an incident photon (0 to 1).
    dark_count_rate : float
        Dark count rate per pixel in Hz.
    jitter_fwhm : float
        Timing jitter (FWHM) in seconds.
    n_pixels : int
        Number of SPAD pixels (default 1 for single-point LiDAR).
    rng_seed : int or None
        Seed for reproducible noise.
    """

    def __init__(
        self,
        dead_time: float = 50e-9,
        photon_detection_efficiency: float = 0.3,
        dark_count_rate: float = 100.0,
        jitter_fwhm: float = 100e-12,
        n_pixels: int = 1,
        rng_seed: Optional[int] = None,
    ):
        self.dead_time = float(dead_time)
        self.photon_detection_efficiency = float(photon_detection_efficiency)
        self.dark_count_rate = float(dark_count_rate)
        self.jitter_sigma = float(jitter_fwhm) / 2.355
        self.n_pixels = int(n_pixels)
        self._rng = np.random.default_rng(rng_seed)

    def detect(self, photon_timestamps: np.ndarray, pixel: int = 0) -> List[SPADEvent]:
        """Process incident photon timestamps and return detection events.

        Parameters
        ----------
        photon_timestamps : ndarray
            Arrival times of photons in seconds.
        pixel : int
            Pixel index.

        Returns
        -------
        list of SPADEvent
            Detected events after dead time and jitter.
        """
        events = []
        last_detection = -np.inf

        max_time = float(np.max(photon_timestamps)) if len(photon_timestamps) > 0 else 1e-6

        if self.dark_count_rate > 0:
            dark_interval = 1.0 / self.dark_count_rate
            dark_t = 0.0
            while dark_t < max_time:
                dark_t += self._rng.exponential(dark_interval)
                photon_timestamps = np.append(photon_timestamps, dark_t)

        photon_timestamps = np.sort(photon_timestamps)

        for t in photon_timestamps:
            if t - last_detection < self.dead_time:
                continue
            if self._rng.random() < self.photon_detection_efficiency:
                jitter = self._rng.normal(0, self.jitter_sigma)
                events.append(SPADEvent(timestamp=t + jitter, pixel=pixel))
                last_detection = t

        return events

    def count_events(self, photon_timestamps: np.ndarray, pixel: int = 0) -> int:
        """Return the number of detected events (convenience wrapper)."""
        return len(self.detect(photon_timestamps, pixel))
