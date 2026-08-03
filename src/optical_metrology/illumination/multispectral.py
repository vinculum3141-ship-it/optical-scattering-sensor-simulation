"""Multi-spectral illumination sources and multi-channel light fields.

Provides:
- :class:`MultiChannelLightField` — a stack of :class:`LightField` objects
  at different wavelengths.
- :class:`MultiSpectralSource` — generates a stack of light fields
  from a list of (wavelength, power) channel configurations.
- :class:`FilterWheelSource` — programmable filter-wheel / AOTF source
  that cycles through a sequence of spectral channels.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterator, List, Optional, Tuple, Union

import numpy as np

from .lightfield import LightField
from .source import LightSource
from .spectrum import MonochromaticSpectrum, SpectralDistribution


@dataclass
class MultiChannelLightField:
    """A collection of :class:`LightField` objects at multiple wavelengths.

    Provides wavelength-based indexing and convenient access to the
    intensity stack.

    Attributes
    ----------
    fields : list of LightField
        One :class:`LightField` per spectral channel, ordered by the
        user-supplied channel list.
    wavelengths : np.ndarray
        1D array of centre wavelengths for each channel (metres).
    """

    fields: List[LightField] = field(default_factory=list)

    def __post_init__(self):
        self._wavelengths = np.array([f.wavelength for f in self.fields])

    @property
    def wavelengths(self) -> np.ndarray:
        return self._wavelengths

    @property
    def n_channels(self) -> int:
        return len(self.fields)

    @property
    def shape(self) -> Tuple[int, ...]:
        if not self.fields:
            return (0,)
        h, w = self.fields[0].intensity.shape
        return (h, w, self.n_channels)

    def intensity_stack(self) -> np.ndarray:
        """Return a 3D array ``(H, W, N_λ)`` of intensities."""
        return np.dstack([f.intensity for f in self.fields])

    def __getitem__(self, index: Union[int, float]) -> LightField:
        """Index by position (int) or nearest wavelength (float)."""
        if isinstance(index, (int, np.integer)):
            return self.fields[index]
        idx = int(np.argmin(np.abs(self._wavelengths - float(index))))
        return self.fields[idx]

    def __len__(self) -> int:
        return len(self.fields)

    def __iter__(self) -> Iterator[LightField]:
        return iter(self.fields)


@dataclass
class ChannelConfig:
    """Configuration for a single spectral channel.

    Parameters
    ----------
    wavelength : float
        Centre wavelength in metres.
    power : float
        Optical power for this channel in Watts.
    spectrum : SpectralDistribution or None
        Spectral model.  Defaults to :class:`MonochromaticSpectrum`.
    label : str or None
        Optional human-readable label (e.g. ``"red"``, ``"blue"``).
    """

    wavelength: float
    power: float = 1.0
    spectrum: Optional[SpectralDistribution] = None
    label: Optional[str] = None

    def __post_init__(self):
        if self.spectrum is None:
            self.spectrum = MonochromaticSpectrum(wavelength=self.wavelength)


class MultiSpectralSource:
    """Generates a stack of :class:`LightField` objects at multiple wavelengths.

    Uses a shared :class:`LightSource` template for all channels,
    overriding the wavelength, power, and spectrum per channel.

    Parameters
    ----------
    channels : list of ChannelConfig
        Spectral channel configurations.
    source_template : LightSource
        Base source whose parameters (beam profile, polarisation,
        divergence, etc.) are shared across all channels.  The
        template's ``wavelength`` and ``power`` are overridden.
    """

    def __init__(
        self,
        channels: List[ChannelConfig],
        source_template: Optional[LightSource] = None,
    ):
        self.channels = channels
        self.source_template = source_template or LightSource()

    @property
    def n_channels(self) -> int:
        return len(self.channels)

    @property
    def wavelengths(self) -> np.ndarray:
        return np.array([c.wavelength for c in self.channels])

    def generate_light_field(self, shape: Tuple[int, int], spacing: float = 1.0) -> MultiChannelLightField:
        """Generate a :class:`MultiChannelLightField` over a 2D grid.

        Parameters
        ----------
        shape : tuple of int
            Grid dimensions ``(height, width)``.
        spacing : float
            Physical distance between adjacent grid points.

        Returns
        -------
        MultiChannelLightField
            One :class:`LightField` per channel.
        """
        fields = []
        for channel in self.channels:
            src = self.source_template
            lf = LightSource(
                wavelength=channel.wavelength,
                power=channel.power,
                polarization=src.polarization,
                coherence_length=src.coherence_length,
                beam_profile=src.beam_profile,
                propagation_direction=src.propagation_direction,
                origin=src.origin,
                divergence=src.divergence,
                wavefront=src.wavefront,
                waist_position=src.waist_position,
                focal_distance=src.focal_distance,
                spectrum=channel.spectrum,
            ).generate_light_field(shape=shape, spacing=spacing)
            fields.append(lf)
        return MultiChannelLightField(fields=fields)


class FilterWheelSource:
    """Programmable filter-wheel / AOTF source.

    Cycles through a sequence of spectral channels, producing one
    :class:`LightField` at a time.  Useful for simulating sequential
    multi-spectral acquisition.

    Parameters
    ----------
    channels : list of ChannelConfig
        Spectral channels to cycle through.
    source_template : LightSource or None
        Shared source parameters.
    """

    def __init__(
        self,
        channels: List[ChannelConfig],
        source_template: Optional[LightSource] = None,
    ):
        self._multi = MultiSpectralSource(channels, source_template)
        self._index = 0

    @property
    def n_channels(self) -> int:
        return self._multi.n_channels

    @property
    def wavelengths(self) -> np.ndarray:
        return self._multi.wavelengths

    @property
    def current_channel(self) -> ChannelConfig:
        return self._multi.channels[self._index]

    def next_channel(self) -> ChannelConfig:
        """Advance to the next channel and return its config."""
        self._index = (self._index + 1) % self.n_channels
        return self.current_channel

    def reset(self):
        """Reset the channel index to 0."""
        self._index = 0

    def generate_light_field(self, shape: Tuple[int, int], spacing: float = 1.0) -> LightField:
        """Generate a light field for the *current* channel.

        Returns
        -------
        LightField
            Single-channel light field.
        """
        multi = self._multi.generate_light_field(shape, spacing)
        return multi.fields[self._index]

    def generate_all(self, shape: Tuple[int, int], spacing: float = 1.0) -> MultiChannelLightField:
        """Generate light fields for *all* channels.

        Returns
        -------
        MultiChannelLightField
        """
        return self._multi.generate_light_field(shape, spacing)

    def capture_band(self, band_index: int, shape: Tuple[int, int], spacing: float = 1.0) -> LightField:
        """Generate a light field for a specific band index."""
        self._index = band_index % self.n_channels
        return self.generate_light_field(shape, spacing)
