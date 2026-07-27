"""LiDAR analysis modules: range equation, time-of-flight propagation,
waveform analysis, and point cloud generation (UC6).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

from .base import AnalysisModule, AnalysisReport


class LiDARRangeEquation(AnalysisModule):
    """Compute received LiDAR power from the standard range equation.

    P_r = P_t * (D_r² / (4 * R²)) * η_sys * η_atm * β
    """

    def __init__(
        self,
        transmitter_power: float = 1.0,
        receiver_aperture_diameter: float = 0.1,
        system_efficiency: float = 0.8,
        atmospheric_transmission: float = 0.9,
    ):
        self.transmitter_power = float(transmitter_power)
        self.receiver_aperture_diameter = float(receiver_aperture_diameter)
        self.system_efficiency = float(system_efficiency)
        self.atmospheric_transmission = float(atmospheric_transmission)

    def analyze(self, configs) -> AnalysisReport:
        return AnalysisReport(measurements={
            "received_power": 0.0,
            "note": "use compute_range() with explicit range and backscatter",
        })

    def compute_range(
        self, range_m: float, backscatter_coeff: float = 1e-4
    ) -> float:
        """Compute received power for a given range.

        Parameters
        ----------
        range_m : float
            Target range in metres.
        backscatter_coeff : float
            Backscatter coefficient β (m⁻¹·sr⁻¹).

        Returns
        -------
        float
            Received power in Watts.
        """
        Ar = np.pi * (self.receiver_aperture_diameter / 2.0) ** 2
        return (
            self.transmitter_power
            * Ar
            / (4.0 * range_m ** 2)
            * self.system_efficiency
            * self.atmospheric_transmission
            * backscatter_coeff
        )


class TimeOfFlightPropagator(AnalysisModule):
    """Compute round-trip time delay, pulse broadening, and multiple returns."""

    def analyze(self, configs) -> AnalysisReport:
        return AnalysisReport(measurements={
            "tof": 0.0,
            "note": "use compute_tof() with explicit range",
        })

    def compute_tof(
        self,
        range_m: float,
        pulse_duration: float = 1e-9,
        target_tilt_deg: float = 0.0,
        speed_of_light: float = 3e8,
    ) -> Tuple[float, float]:
        """Compute time-of-flight and pulse broadening.

        Parameters
        ----------
        range_m : float
            Round-trip range in metres.
        pulse_duration : float
            Transmitted pulse FWHM in seconds.
        target_tilt_deg : float
            Target surface tilt in degrees (broadens pulse).
        speed_of_light : float
            Speed of light in m/s.

        Returns
        -------
        tof : float
            Round-trip time in seconds.
        broadened_duration : float
            Broadened pulse FWHM in seconds.
        """
        tof = 2.0 * range_m / speed_of_light
        tilt_broadening = pulse_duration * (1.0 / np.cos(np.radians(target_tilt_deg)) - 1.0)
        broadened = np.sqrt(pulse_duration ** 2 + tilt_broadening ** 2)
        return float(tof), float(broadened)


class WaveformAnalyzer(AnalysisModule):
    """Analyse LiDAR return waveforms: peak detection and CFD."""

    def __init__(self, cf_fraction: float = 0.5):
        self.cf_fraction = float(cf_fraction)

    def analyze(self, waveform) -> AnalysisReport:
        wf = np.asarray(waveform, dtype=float)

        peak_idx = int(np.argmax(wf))
        peak_amplitude = float(wf[peak_idx])

        half_max = peak_amplitude * self.cf_fraction
        above = np.where(wf >= half_max)[0]
        if len(above) > 0:
            fwhm = float(above[-1] - above[0])
        else:
            fwhm = 0.0

        cfd_idx = self._cfd_zero_crossing(wf)

        return AnalysisReport(measurements={
            "peak_index": peak_idx,
            "peak_amplitude": peak_amplitude,
            "fwhm_samples": fwhm,
            "cfd_crossing_index": cfd_idx,
        })

    def _cfd_zero_crossing(self, wf: np.ndarray) -> int:
        threshold = np.max(wf) * self.cf_fraction
        crossings = np.where(wf >= threshold)[0]
        if len(crossings) > 0:
            return int(crossings[0])
        return 0


def generate_point_cloud(
    ranges: np.ndarray,
    azimuths: np.ndarray,
    elevations: np.ndarray,
    intensities: Optional[np.ndarray] = None,
) -> np.ndarray:
    """Convert (range, azimuth, elevation) to (x, y, z, intensity) point cloud.

    Parameters
    ----------
    ranges : ndarray
        Range measurements in metres.
    azimuths : ndarray
        Azimuth angles in radians.
    elevations : ndarray
        Elevation angles in radians.
    intensities : ndarray or None
        Intensity values.  If None, default to range.

    Returns
    -------
    ndarray
        (N, 4) array of [x, y, z, intensity].
    """
    x = ranges * np.cos(elevations) * np.sin(azimuths)
    y = ranges * np.cos(elevations) * np.cos(azimuths)
    z = ranges * np.sin(elevations)
    if intensities is None:
        intensities = ranges
    return np.column_stack([x, y, z, intensities])
