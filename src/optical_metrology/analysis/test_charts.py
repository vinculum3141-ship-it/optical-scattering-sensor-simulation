"""Standard test chart generators for sensor characterisation (UC3).

Provides factory functions that produce DigitalImage instances
of common calibration targets:

- Siemens star (modulation vs. frequency)
- Slanted edge (MTF measurement)
- Greyscale wedge (linearity, dynamic range)
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from optical_metrology.detector import DigitalImage


def siemens_star(
    size: int = 256,
    spokes: int = 36,
    bit_depth: int = 12,
) -> DigitalImage:
    """Generate a Siemens star test chart.

    Parameters
    ----------
    size : int
        Width and height in pixels (square).
    spokes : int
        Number of black/white spoke pairs.
    bit_depth : int
        Bit depth of the output image.

    Returns
    -------
    DigitalImage
    """
    max_val = 2 ** bit_depth - 1
    cx = cy = (size - 1) / 2.0
    y, x = np.ogrid[:size, :size]
    angle = np.arctan2(y - cy, x - cx)
    radius = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)

    pattern = (np.sin(angle * spokes / 2.0) + 1.0) / 2.0
    pattern[radius > cx] = 0.5

    pixels = (pattern * max_val).astype(np.uint16)
    return DigitalImage(pixels=pixels, metadata={"bit_depth": bit_depth})


def slanted_edge(
    height: int = 256,
    width: int = 256,
    angle_deg: float = 5.0,
    bit_depth: int = 12,
) -> DigitalImage:
    """Generate a slanted-edge test chart for MTF measurement.

    Parameters
    ----------
    height, width : int
        Image dimensions in pixels.
    angle_deg : float
        Edge angle in degrees from vertical (default 5°).
    bit_depth : int
        Bit depth of the output image.

    Returns
    -------
    DigitalImage
    """
    max_val = 2 ** bit_depth - 1
    y, x = np.mgrid[:height, :width]
    angle_rad = np.radians(angle_deg)
    edge = x * np.cos(angle_rad) + y * np.sin(angle_rad)
    centre = (width * np.cos(angle_rad) + height * np.sin(angle_rad)) / 2.0
    pixels = np.where(edge < centre, max_val, 0).astype(np.uint16)
    return DigitalImage(pixels=pixels, metadata={"bit_depth": bit_depth})


def greyscale_wedge(
    height: int = 64,
    width: int = 256,
    bit_depth: int = 12,
    reverse: bool = False,
) -> DigitalImage:
    """Generate a horizontal greyscale wedge (linear ramp).

    Parameters
    ----------
    height : int
        Image height in pixels.
    width : int
        Image width in pixels.
    bit_depth : int
        Bit depth of the output image.
    reverse : bool
        If ``True``, ramp from max to 0 (right to left).

    Returns
    -------
    DigitalImage
    """
    max_val = 2 ** bit_depth - 1
    ramp = np.linspace(0, max_val, width, dtype=np.uint16)
    if reverse:
        ramp = ramp[::-1]
    pixels = np.tile(ramp, (height, 1))
    return DigitalImage(pixels=pixels, metadata={"bit_depth": bit_depth})
