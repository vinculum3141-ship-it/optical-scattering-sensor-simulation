"""Tiled acquisition and multi-FOV stitching helper (UC1).

Provides :class:`TiledAcquisition` for scanning a large surface in
overlapping tiles and merging the results.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

import numpy as np


class TiledAcquisition:
    """Scan a large surface in overlapping field-of-view tiles.

    The user provides a *pipeline_fn* that accepts ``(row_offset,
    col_offset, height, width)`` and returns a 2D numpy array
    (e.g. the captured image for that tile).  This class iterates
    over tile positions and stitches the results.

    Parameters
    ----------
    tile_height : int
        Height of each tile in pixels.
    tile_width : int
        Width of each tile in pixels.
    overlap : float
        Fractional overlap between adjacent tiles (0 to 1).
        Default 0.1 (10% overlap).
    """

    def __init__(self, tile_height: int, tile_width: int, overlap: float = 0.1):
        self.tile_height = tile_height
        self.tile_width = tile_width
        self.overlap = overlap

    def tile_grid(self, surface_height: int, surface_width: int) -> List[Tuple[int, int, int, int]]:
        """Generate tile positions covering a surface of given size.

        Parameters
        ----------
        surface_height, surface_width : int
            Dimensions of the surface in pixels.

        Returns
        -------
        list of (row, col, tile_height, tile_width)
        """
        stride_h = int(self.tile_height * (1.0 - self.overlap))
        stride_w = int(self.tile_width * (1.0 - self.overlap))
        stride_h = max(1, stride_h)
        stride_w = max(1, stride_w)

        tiles = []
        r = 0
        while r < surface_height:
            c = 0
            while c < surface_width:
                th = min(self.tile_height, surface_height - r)
                tw = min(self.tile_width, surface_width - c)
                tiles.append((r, c, th, tw))
                c += stride_w
            r += stride_h
        return tiles

    def acquire(
        self,
        pipeline_fn: Callable,
        surface_height: int,
        surface_width: int,
    ) -> np.ndarray:
        """Acquire all tiles and stitch them into a single image.

        Parameters
        ----------
        pipeline_fn : callable
            ``pipeline_fn(row, col, height, width) -> np.ndarray``
            that returns a 2D image array for the given tile region.
        surface_height, surface_width : int
            Full surface dimensions in pixels.

        Returns
        -------
        np.ndarray
            Stitched image with shape ``(surface_height, surface_width)``.
        """
        stitched = np.zeros((surface_height, surface_width), dtype=float)
        weight = np.zeros((surface_height, surface_width), dtype=float)

        tiles = self.tile_grid(surface_height, surface_width)
        for r, c, th, tw in tiles:
            tile_image = pipeline_fn(r, c, th, tw)
            if tile_image.shape != (th, tw):
                tile_image = tile_image[:th, :tw]
            stitched[r : r + th, c : c + tw] += tile_image
            weight[r : r + th, c : c + tw] += 1.0

        weight = np.where(weight > 0, weight, 1.0)
        return (stitched / weight).astype(np.float32)
