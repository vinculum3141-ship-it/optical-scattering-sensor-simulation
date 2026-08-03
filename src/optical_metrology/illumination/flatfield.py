"""Flat-field / stepped-intensity source for sensor characterisation.

:class:`FlatFieldSource` provides programmable uniform illumination,
typically used for photon-transfer-curve (PTC) measurements, SNR
analysis, and linearity testing in sensor characterisation (UC3).
"""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

import numpy as np

from .lightfield import LightField
from .profiles import UniformBeamProfile
from .source import LightSource
from .spectrum import BroadbandSpectrum, SpectralDistribution


class FlatFieldSource(LightSource):
    """A programmable uniform source with configurable intensity levels.

    The source always uses a :class:`UniformBeamProfile` regardless of
    the *beam_profile* argument — flat-field illumination requires
    spatially uniform intensity.  The *power* parameter sets the
    maximum output power; fractional intensity levels are realised by
    scaling the generated light field.

    Parameters
    ----------
    wavelength : float
        Centre wavelength in metres (default 550 nm).
    power : float
        Maximum optical power in Watts (default 1.0 W).
    intensity_levels : list of float, optional
        Fractional intensity levels in [0, 1] relative to *power*.
        When provided, :meth:`generate_intensity_sweep` returns one
        :class:`LightField` per level.
    polarization : PolarizationState or str, optional
    coherence_length : float
        Defaults to 0 (incoherent — typical for flat-field sources).
    propagation_direction : ndarray, optional
        Defaults to ``+z`` (normal incidence).
    origin : ndarray, optional
    divergence : float
        Defaults to 0.
    spectrum : SpectralDistribution or None
        Defaults to a broadband spectrum (450–650 nm).
    """

    def __init__(
        self,
        wavelength: float = 550e-9,
        power: float = 1.0,
        intensity_levels: Optional[Sequence[float]] = None,
        polarization=None,
        coherence_length: float = 0.0,
        propagation_direction=None,
        origin=None,
        divergence: float = 0.0,
        spectrum: Optional[SpectralDistribution] = None,
    ):
        super().__init__(
            wavelength=wavelength,
            power=power,
            polarization=polarization or "unpolarized",
            coherence_length=coherence_length,
            beam_profile=UniformBeamProfile(),
            propagation_direction=propagation_direction,
            origin=origin,
            divergence=divergence,
            spectrum=spectrum,
        )
        if intensity_levels is not None:
            levels = np.asarray(intensity_levels, dtype=float)
            if np.any((levels < 0) | (levels > 1)):
                raise ValueError("intensity_levels must be in [0, 1]")
            self.intensity_levels = levels.tolist()
        else:
            self.intensity_levels = [1.0]

    def default_spectrum(self) -> SpectralDistribution:
        return BroadbandSpectrum(wavelength_range=(450e-9, 650e-9))

    def generate_light_field(
        self, shape: Tuple[int, int], spacing: float = 1.0
    ) -> LightField:
        """Generate a flat-field light field at maximum power.

        Fractional intensity levels are applied by calling
        :meth:`generate_intensity_sweep` and indexing the result.
        """
        lf = super().generate_light_field(shape, spacing=spacing)
        return lf

    def generate_intensity_sweep(
        self, shape: Tuple[int, int], spacing: float = 1.0
    ) -> List[LightField]:
        """Generate one :class:`LightField` per configured intensity level.

        The fields are identical apart from their ``intensity`` and
        ``power`` attributes, which are scaled by each level.
        """
        base = self.generate_light_field(shape, spacing=spacing)
        return [
            LightField(
                intensity=base.intensity * level,
                direction=base.direction,
                wavelength=base.wavelength,
                polarization=base.polarization,
                coherence_length=base.coherence_length,
                power=base.power * level,
                phase=base.phase,
            )
            for level in self.intensity_levels
        ]
