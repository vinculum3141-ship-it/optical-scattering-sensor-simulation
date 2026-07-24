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


_SHADES = [" ", "\u2591", "\u2592", "\u2593", "\u2588"]


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

    def visualize(self, max_width: int = 72, color: bool = True) -> str:
        """Render the digital image as a terminal heatmap.

        Parameters
        ----------
        max_width : int
            Maximum character width for the output grid.
        color : bool
            If True, use ANSI colour escape codes.

        Returns
        -------
        str
            Multi-line string ready to ``print()``.
        """
        arr = self.pixels.astype(float)
        h, w = arr.shape
        scale = min(1.0, max_width / w)
        if scale < 1.0:
            nh, nw = max(1, int(h * scale)), max_width
            ir, jc = np.mgrid[0:h:nh * 1j, 0:w:nw * 1j]
            vals = arr[ir.astype(np.intp).clip(0, h - 1), jc.astype(np.intp).clip(0, w - 1)]
        else:
            nh, nw, vals = h, w, arr

        vmin, vmax = float(vals.min()), float(vals.max())
        if vmax == vmin:
            norm = np.full_like(vals, 0.5)
        else:
            norm = (vals - vmin) / (vmax - vmin)

        n_shades = len(_SHADES) - 1
        shade_idx = (norm * n_shades).astype(np.intp).clip(0, n_shades)

        if not color:
            lines = ["".join(_SHADES[idx] for idx in row) for row in shade_idx]
        else:
            lines = []
            for row in shade_idx:
                buf = []
                for idx in row:
                    intensity = idx / n_shades
                    if intensity < 0.25:
                        colour = 36
                    elif intensity < 0.5:
                        colour = 32
                    elif intensity < 0.75:
                        colour = 33
                    else:
                        colour = 31
                    buf.append(f"\033[1;{colour}m{_SHADES[idx]}\033[0m")
                lines.append("".join(buf))

        info = (
            f"Digital image  ({nh}\u00d7{nw})  "
            f"min={vmin:.0f}  max={vmax:.0f}  "
            f"mean={float(vals.mean()):.0f}  "
            f"bit-depth={self.metadata.get('bit_depth', '?')}"
        )
        sep = "\u2500" * min(len(info), max_width)
        return f"{info}\n{sep}\n" + "\n".join(lines)


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
    pixel_area : float
        Area of a single pixel in m² (default 5 μm × 5 μm).
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
        pixel_area: float = 25e-12,
        noise_models: Optional[list[DetectorNoiseModel]] = None,
    ):
        self.exposure_time = exposure_time
        self.quantum_efficiency = quantum_efficiency
        self.dark_current = dark_current
        self.read_noise_sigma = read_noise_sigma
        self.full_well_capacity = full_well_capacity
        self.gain = gain
        self.bit_depth = bit_depth
        self.pixel_area = pixel_area
        self.noise_models = noise_models or []

    def capture(self, sensor_field, surface=None) -> DigitalImage:
        """Expose the sensor and return a digital image.

        Parameters
        ----------
        sensor_field : SensorField
            Irradiance distribution from :class:`~optics.OpticalPropagator`
            (or any object with ``.irradiance`` and ``.wavelength``).
        surface : Surface or None
            Optional surface geometry.  If provided, any
            :class:`SpeckleNoise` models in the noise chain are
            prepared with the surface height map and wavelength.

        Returns
        -------
        DigitalImage
            Quantised pixel values and capture metadata.
        """
        irradiance = np.asarray(sensor_field.irradiance, dtype=float)

        # Step 1: irradiance (W/m²) → incident photons per pixel
        #   photon energy E = hc/λ
        #   photon count = (irradiance × pixel_area × time) / E
        photon_energy = 6.62607015e-34 * 2.99792458e8 / sensor_field.wavelength
        photons = (irradiance * self.pixel_area * self.exposure_time) / photon_energy

        # Step 2: quantum efficiency → photoelectrons
        electrons = photons * self.quantum_efficiency

        # Step 3: shot noise (Poisson) + dark current (Poisson)
        electrons = np.random.poisson(electrons)
        dark = np.random.poisson(self.dark_current * self.exposure_time, size=electrons.shape)
        electrons = electrons + dark

        # Step 4: read noise (Gaussian)
        read_noise = np.random.normal(0.0, self.read_noise_sigma, size=electrons.shape)
        electrons = electrons + read_noise

        # Step 4.5: prepare speckle noise models with surface data
        if surface is not None:
            from .noise_models import SpeckleNoise
            for noise_model in self.noise_models:
                if isinstance(noise_model, SpeckleNoise):
                    noise_model.prepare(surface.height, sensor_field.wavelength)

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
            "pixel_area": self.pixel_area,
        }
        return DigitalImage(pixels=counts, metadata=metadata)

    def pipeline_describe(self) -> str:
        """Return a human-readable summary of the detector pipeline steps."""
        area_cm2 = self.pixel_area * 1e4
        lines = [
            "CMOS detector pipeline:",
            f"  Step 1  Irradiance → photons    (E = hc/λ, pixel_area={self.pixel_area:.1e} m² = {area_cm2:.1e} cm² × exposure_time={self.exposure_time} s)",
            f"  Step 2  Quantum efficiency       ({self.quantum_efficiency} e⁻/photon)",
            f"  Step 3  Shot noise (Poisson)     + dark current ({self.dark_current} e⁻/s × {self.exposure_time} s)",
            f"  Step 4  Read noise (Gaussian)    σ = {self.read_noise_sigma} e⁻",
        ]
        if self.noise_models:
            for m in self.noise_models:
                lines.append(f"  Step 5  Custom noise: {type(m).__name__}")
        else:
            lines.append(f"  Step 5  Custom noise:       (none)")
        lines.append(f"  Step 6  Full-well clip         ≤ {self.full_well_capacity} e⁻")
        lines.append(f"  Step 7  ADC quantisation       gain={self.gain} e⁻/ADU, {self.bit_depth}-bit")
        return "\n".join(lines)
