"""Temporal envelope models for pulsed light sources.

A :class:`TemporalEnvelope` describes the temporal shape, duration, and
repetition rate of a pulsed optical source.  It can be composed into a
:class:`LightSource` subclass (e.g. ``Laser``) when pulsed operation is
needed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np


@dataclass
class TemporalEnvelope:
    """Temporal characteristics of a pulsed source.

    Parameters
    ----------
    shape : str
        ``"gaussian"`` or ``"rectangular"`` pulse shape.
    pulse_duration : float
        Full-width at half-maximum (FWHM) of the pulse in seconds.
    repetition_rate : float
        Pulse repetition rate in Hz.
    pulse_energy : float or None
        Energy per pulse in Joules.  If provided, *peak_power* is
        derived as ``pulse_energy / effective_pulse_width``.  If
        ``None``, *peak_power* must be provided.
    peak_power : float or None
        Peak power during the pulse in Watts.  If provided,
        *pulse_energy* is derived as ``peak_power * effective_pulse_width``.
        If ``None``, *pulse_energy* must be provided.
    phase : float
        Carrier-envelope phase offset in radians (default 0).
    """

    shape: str = "gaussian"
    pulse_duration: float = 1e-9
    repetition_rate: float = 1e6
    pulse_energy: float = None
    peak_power: float = None
    phase: float = 0.0

    def __post_init__(self):
        if self.shape not in ("gaussian", "rectangular"):
            raise ValueError(f"Unsupported pulse shape: {self.shape!r}")
        if self.pulse_energy is None and self.peak_power is None:
            raise ValueError("Either pulse_energy or peak_power must be provided")
        if self.pulse_energy is not None and self.peak_power is not None:
            raise ValueError("Provide either pulse_energy or peak_power, not both")
        if self.pulse_energy is None:
            self.pulse_energy = self.peak_power * self.effective_pulse_width
        if self.peak_power is None:
            self.peak_power = self.pulse_energy / self.effective_pulse_width

    @property
    def effective_pulse_width(self) -> float:
        """Effective temporal width of a single pulse in seconds.

        For Gaussian pulses: FWHM / sqrt(2 ln 2) ≈ FWHM / 1.177.
        For rectangular pulses: equals pulse_duration (FWHM = full width).
        """
        if self.shape == "gaussian":
            return self.pulse_duration / np.sqrt(2.0 * np.log(2.0))
        return self.pulse_duration

    @property
    def duty_cycle(self) -> float:
        """Fraction of time the source is emitting."""
        return self.effective_pulse_width * self.repetition_rate

    @property
    def average_power(self) -> float:
        """Average optical power over one repetition period in Watts."""
        return self.pulse_energy * self.repetition_rate

    def envelope(self, t: np.ndarray) -> np.ndarray:
        """Evaluate the normalised temporal envelope at time points *t*.

        Parameters
        ----------
        t : ndarray
            Time coordinates in seconds.

        Returns
        -------
        ndarray
            Normalised intensity envelope (peak = 1.0) at each time point.
        """
        if self.shape == "gaussian":
            sigma = self.pulse_duration / (2.0 * np.sqrt(2.0 * np.log(2.0)))
            return np.exp(-0.5 * (t / sigma) ** 2)
        half = self.pulse_duration / 2.0
        return np.where(np.abs(t) <= half, 1.0, 0.0)
