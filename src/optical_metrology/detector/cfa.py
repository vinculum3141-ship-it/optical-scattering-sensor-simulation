"""Colour filter array (CFA) model for multi-spectral and colour imaging.

Provides:
- :class:`CFAConfig` — defines a Bayer-style colour filter array pattern.
- :class:`CFADetector` — :class:`CMOSDetector` subclass that applies a
  CFA during capture and optionally demosaics the result.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple, Union

import numpy as np

from .base import CMOSDetector, DigitalImage

# Typical Bayer patterns: each entry maps (row % 2, col % 2) → channel index
BAYER_RGGB = {(0, 0): 0, (0, 1): 1, (1, 0): 1, (1, 1): 2}
BAYER_GRBG = {(0, 0): 1, (0, 1): 0, (1, 0): 2, (1, 1): 1}
BAYER_BGGR = {(0, 0): 2, (0, 1): 1, (1, 0): 1, (1, 1): 0}
BAYER_GBRG = {(0, 0): 1, (0, 1): 2, (1, 0): 0, (1, 1): 1}


@dataclass
class CFAConfig:
    """Configuration for a colour filter array.

    Parameters
    ----------
    pattern : dict
        Mapping from ``(row_mod_2, col_mod_2)`` to channel index.
        Pre-defined patterns: ``RGGB``, ``GRBG``, ``BGGR``, ``GBRG``.
    channel_labels : list of str
        Human-readable names for each channel (e.g. ``["R", "G", "B"]``).
    channel_wavelengths : list of float or None
        Centre wavelengths for each channel (metres).  Used for
        wavelength-dependent QE lookup.
    """

    pattern: Dict[Tuple[int, int], int] = field(default_factory=lambda: BAYER_RGGB)
    channel_labels: List[str] = field(default_factory=lambda: ["R", "G", "B"])
    channel_wavelengths: Optional[List[float]] = None

    @property
    def n_channels(self) -> int:
        return len(self.channel_labels)

    def channel_at(self, row: int, col: int) -> int:
        """Return the channel index for pixel *(row, col)*."""
        return self.pattern[(row % 2, col % 2)]

    def mask_for_channel(self, shape: Tuple[int, int], channel: int) -> np.ndarray:
        """Return a boolean mask for all pixels of *channel* in a *shape* grid."""
        H, W = shape
        mask = np.zeros((H, W), dtype=bool)
        for (rm, cm), ch in self.pattern.items():
            if ch == channel:
                mask[rm::2, cm::2] = True
        return mask


class CFADetector(CMOSDetector):
    """CMOS detector with a colour filter array.

    Extends :class:`CMOSDetector` by applying a CFA pattern during
    capture.  When *demosaic* is ``True``, the raw bayer image is
    demosaiced via bilinear interpolation to produce a full-resolution
    RGB image.

    Parameters
    ----------
    cfa_config : CFAConfig
        Colour filter array pattern configuration.
    demosaic : bool
        If ``True``, perform bilinear demosaicing after capture
        (default ``True``).
    **kwargs
        All other arguments are passed to :class:`CMOSDetector`.
    """

    def __init__(
        self,
        cfa_config: Optional[CFAConfig] = None,
        demosaic: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.cfa_config = cfa_config or CFAConfig()
        self.demosaic = demosaic

    def _apply_cfa(self, full_res: np.ndarray) -> np.ndarray:
        """Apply the CFA mask to a full-resolution image.

        Only the pixel values at CFA-pass positions are retained;
        other pixels are set to 0.
        """
        H, W = full_res.shape
        raw = np.zeros((H, W), dtype=full_res.dtype)
        for (rm, cm), ch in self.cfa_config.pattern.items():
            raw[rm::2, cm::2] = full_res[rm::2, cm::2]
        return raw

    @staticmethod
    def _bilinear_demosaic(raw: np.ndarray, cfa: CFAConfig) -> np.ndarray:
        """Bilinear demosaicing from raw CFA to full RGB.

        Parameters
        ----------
        raw : np.ndarray
            Raw CFA image ``(H, W)``.
        cfa : CFAConfig
            CFA pattern configuration.

        Returns
        -------
        np.ndarray
            Demosaiced image ``(H, W, C)`` where ``C = cfa.n_channels``.
        """
        H, W = raw.shape
        C = cfa.n_channels
        result = np.zeros((H, W, C), dtype=float)

        for ch in range(C):
            mosaic = np.zeros((H, W), dtype=float)
            for (rm, cm), ch_idx in cfa.pattern.items():
                if ch_idx == ch:
                    mosaic[rm::2, cm::2] = raw[rm::2, cm::2]

            full = mosaic.copy()

            kernel = np.array([[0.25, 0.5, 0.25],
                               [0.5,  1.0, 0.5],
                               [0.25, 0.5, 0.25]], dtype=float)

            from scipy.ndimage import convolve
            full = convolve(full, kernel, mode="reflect")

            result[:, :, ch] = full

        return result

    def capture(self, sensor_field, surface=None) -> DigitalImage:
        """Capture with CFA applied.

        Returns
        -------
        DigitalImage
            If *demosaic* is ``True``, ``.pixels`` is ``(H, W, C)``.
            Otherwise it is ``(H, W)`` with zeros at non-CFA positions.
        """
        image = super().capture(sensor_field, surface)
        raw_pixels = image.pixels.astype(float)

        raw_cfa = self._apply_cfa(raw_pixels)

        if self.demosaic:
            rgb = self._bilinear_demosaic(raw_cfa, self.cfa_config)
            rgb = np.round(rgb).clip(0, 2 ** self.bit_depth - 1).astype(np.uint16)
            image.pixels = rgb
            image.metadata["cfa_demosaiced"] = True
        else:
            image.pixels = np.round(raw_cfa).clip(0, 2 ** self.bit_depth - 1).astype(np.uint16)
            image.metadata["cfa_demosaiced"] = False

        image.metadata["cfa_pattern"] = str(self.cfa_config.pattern)
        return image
