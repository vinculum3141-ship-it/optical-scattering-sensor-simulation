"""Detector pipeline: converts optical sensor fields into digital images.

The :class:`CMOSDetector` models a complete imaging sensor chain:

    irradiance → photons → electrons (with shot, dark, and read noise)
    → full-well clip → ADC quantisation → digital counts

The pipeline is designed to be modular — custom noise stages can be
added via the :class:`DetectorNoiseModel` interface.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class DigitalImage:
    """Digital output from the detector pipeline.

    Attributes
    ----------
    pixels : np.ndarray
        2D array of digital counts (ADU) with dtype ``uint16``.
    metadata : dict
        Capture parameters recorded at exposure time (bit depth,
        exposure time, quantum efficiency, full-well capacity, gain).
    """

    pixels: np.ndarray
    metadata: dict


class DetectorNoiseModel:
    """Base class for optional detector noise stages.

    Subclasses can implement custom noise effects (e.g. fixed-pattern
    noise, thermal noise, column-wise defects) by overriding
    :meth:`apply`.
    """

    def apply(self, electrons: np.ndarray) -> np.ndarray:
        """Apply a noise effect to the electron count array.

        Parameters
        ----------
        electrons : np.ndarray
            Electron counts at each pixel before this noise stage.

        Returns
        -------
        np.ndarray
            Modified electron counts of the same shape.
        """
        raise NotImplementedError


class CMOSDetector:
    """Simple CMOS-style detector pipeline from irradiance to digital counts.

    The pipeline steps are:

    1. Convert irradiance (W/m²) to incident photons via :math:`E = hc/λ`.
    2. Scale by quantum efficiency to get photoelectrons.
    3. Add shot noise (Poisson) and dark current (Poisson).
    4. Add Gaussian read noise.
    5. Apply any custom noise models.
    6. Clip to full-well capacity.
    7. Divide by gain and quantise to the specified bit depth.

    Parameters
    ----------
    exposure_time : float
        Integration time in seconds (default 10 ms).
    quantum_efficiency : float
        Fraction of incident photons converted to electrons (0–1).
    dark_current : float
        Dark current in electrons per second (default 5 e⁻/s).
    read_noise_sigma : float
        Standard deviation of Gaussian read noise in electrons.
    full_well_capacity : float
        Maximum electron capacity per pixel before saturation.
    gain : float
        Electrons per digital count (ADU).  Higher gain = fewer e⁻/ADU.
    bit_depth : int
        Number of bits for ADC quantisation (e.g. 12 → 4096 levels).
    noise_models : list of DetectorNoiseModel or None
        Additional noise stages applied after read noise.
    """

    def __init__(
        self,
        exposure_time: float = 0.01,
        quantum_efficiency: float = 0.9,
        dark_current: float = 5.0,
        read_noise_sigma: float = 2.0,
        full_well_capacity: float = 80000.0,
        gain: float = 2.0,
        bit_depth: int = 12,
        noise_models: Optional[list[DetectorNoiseModel]] = None,
    ):
        self.exposure_time = exposure_time
        self.quantum_efficiency = quantum_efficiency
        self.dark_current = dark_current
        self.read_noise_sigma = read_noise_sigma
        self.full_well_capacity = full_well_capacity
        self.gain = gain
        self.bit_depth = bit_depth
        self.noise_models = noise_models or []

    def capture(self, sensor_field) -> DigitalImage:
        """Expose the sensor and return a digital image.

        Parameters
        ----------
        sensor_field : SensorField
            Irradiance distribution from :class:`~optics.OpticalPropagator`
            (or any object with ``.irradiance`` and ``.wavelength``).

        Returns
        -------
        DigitalImage
            Quantised pixel values and capture metadata.
        """
        irradiance = np.asarray(sensor_field.irradiance, dtype=float)

        # Step 1: irradiance (W/m²) → incident photons per pixel
        #   photon energy E = hc/λ
        #   photon count = (irradiance × area × time) / E
        #   For a unit-area pixel this simplifies to:
        #     photons = (irradiance × exposure_time × λ) / (hc)
        photon_energy = 6.62607015e-34 * 2.99792458e8 / sensor_field.wavelength
        photons = (irradiance * self.exposure_time) / photon_energy
        photons = photons / 1e6  # empirical scaling to keep values in reasonable range

        # Step 2: quantum efficiency → photoelectrons
        electrons = photons * self.quantum_efficiency

        # Step 3: shot noise (Poisson) + dark current (Poisson)
        electrons = np.random.poisson(electrons)
        dark = np.random.poisson(self.dark_current * self.exposure_time, size=electrons.shape)
        electrons = electrons + dark

        # Step 4: read noise (Gaussian)
        read_noise = np.random.normal(0.0, self.read_noise_sigma, size=electrons.shape)
        electrons = electrons + read_noise

        # Step 5: custom noise models
        for noise_model in self.noise_models:
            electrons = noise_model.apply(electrons)

        # Step 6: clip to full-well capacity
        electrons = np.clip(electrons, 0.0, self.full_well_capacity)

        # Step 7: gain → ADU, quantise to bit depth, clamp to valid range
        counts = electrons / self.gain
        levels = 2**self.bit_depth - 1
        counts = np.round(counts).astype(np.uint16)
        counts = np.clip(counts, 0, levels).astype(np.uint16)

        metadata = {
            "bit_depth": self.bit_depth,
            "exposure_time": self.exposure_time,
            "quantum_efficiency": self.quantum_efficiency,
            "full_well_capacity": self.full_well_capacity,
            "gain": self.gain,
        }
        return DigitalImage(pixels=counts, metadata=metadata)
