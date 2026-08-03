"""Scanning mechanism model for LiDAR and structured light.

Models galvanometer / MEMS mirror / rotating polygon scanners.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np


@dataclass
class ScanningMechanism:
    """Geometric model of a beam-steering scanner.

    Parameters
    ----------
    scan_pattern : str
        ``"raster"`` or ``"spiral"``.
    field_of_view_deg : float
        Full angular field of view in degrees.
    resolution : int
        Number of points per line (raster) or per revolution (spiral).
    scan_rate : float
        Line rate (raster) or revolution rate (spiral) in Hz.
    """

    scan_pattern: str = "raster"
    field_of_view_deg: float = 30.0
    resolution: int = 128
    scan_rate: float = 100.0

    def __post_init__(self):
        if self.scan_pattern not in ("raster", "spiral"):
            raise ValueError(f"Unsupported scan pattern: {self.scan_pattern!r}")

    def generate_scan_points(self, duration: float = 1.0) -> List[Tuple[float, float, float]]:
        """Generate (azimuth, elevation, time) scan points over *duration* seconds.

        Returns
        -------
        list of (azimuth_rad, elevation_rad, time_s)
        """
        fov_rad = np.radians(self.field_of_view_deg)
        points = []
        dt = 1.0 / self.scan_rate

        if self.scan_pattern == "raster":
            n_lines = int(duration * self.scan_rate)
            for line in range(n_lines):
                t = line * dt
                for col in range(self.resolution):
                    az = -fov_rad / 2 + fov_rad * col / (self.resolution - 1)
                    el = -fov_rad / 2 + fov_rad * (line % self.resolution) / (self.resolution - 1)
                    points.append((az, el, t + col * dt / self.resolution))
        else:
            n_points = int(duration * self.scan_rate * self.resolution)
            for i in range(n_points):
                t = i * dt / self.resolution
                angle = 2.0 * np.pi * self.scan_rate * t
                radius = fov_rad / 2 * t / duration
                az = radius * np.cos(angle)
                el = radius * np.sin(angle)
                points.append((az, el, t))

        return points
