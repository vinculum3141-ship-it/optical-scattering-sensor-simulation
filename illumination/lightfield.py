"""Data structure that holds the illumination field over a spatial grid.

A :class:`LightField` is the output of
:meth:`LightSource.generate_light_field`.  It is intentionally kept
as a plain container so that downstream modules (scattering, optics,
detector) can consume it without depending on the source details.
"""

from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class LightField:
    """Structured description of illumination over a 2D spatial grid.

    Attributes
    ----------
    intensity : np.ndarray
        2D array of intensity values (W/m²) at each grid point.
        Shape ``(height, width)``.
    direction : np.ndarray
        3D array of unit propagation vectors at each grid point.
        Shape ``(height, width, 3)``.
    wavelength : float
        Centre wavelength of the illumination in metres.
    polarization : PolarizationState
        Polarisation state of the field.
    phase : np.ndarray | None
        2D array of relative optical phase (radians) at each grid
        point.  ``None`` means the phase is undefined or irrelevant
        for the application.
    """

    intensity: np.ndarray
    direction: np.ndarray
    wavelength: float
    polarization: object
    phase: Optional[np.ndarray] = None

    _SHADES = [" ", "\u2591", "\u2592", "\u2593", "\u2588"]

    def visualize(self, max_width: int = 80, color: bool = True) -> str:
        """Render the intensity as a 2D terminal heatmap.

        Parameters
        ----------
        max_width : int
            Maximum character width for the output grid.  Large fields
            are down-sampled to fit.
        color : bool
            If True, use ANSI 8-colour escape codes to tint the blocks
            from blue (low) through green/yellow to red (high).

        Returns
        -------
        str
            Multi-line string ready to ``print()``.
        """
        h, w = self.intensity.shape
        scale = min(1.0, max_width / w)
        if scale < 1.0:
            nh, nw = max(1, int(h * scale)), max_width
            ir, jc = np.mgrid[0:h:nh * 1j, 0:w:nw * 1j]
            vals = self.intensity[
                ir.astype(np.intp).clip(0, h - 1),
                jc.astype(np.intp).clip(0, w - 1),
            ]
        else:
            nh, nw, vals = h, w, self.intensity

        vmin, vmax = float(vals.min()), float(vals.max())
        if vmax == vmin:
            norm = np.zeros_like(vals)
        else:
            norm = (vals - vmin) / (vmax - vmin)

        n_shades = len(self._SHADES) - 1
        shade_idx = (norm * n_shades).astype(np.intp).clip(0, n_shades)

        if not color:
            lines = ["".join(self._SHADES[idx] for idx in row) for row in shade_idx]
        else:
            lines = []
            for row in shade_idx:
                buf = []
                for idx in row:
                    intensity = idx / n_shades
                    if intensity < 0.25:
                        colour = 36  # cyan
                    elif intensity < 0.5:
                        colour = 32  # green
                    elif intensity < 0.75:
                        colour = 33  # yellow
                    else:
                        colour = 31  # red
                    ch = self._SHADES[idx]
                    buf.append(f"\033[1;{colour}m{ch}\033[0m")
                lines.append("".join(buf))

        header = (
            f"Intensity  ({nh}×{nw})  "
            f"min={vmin:.4g}  max={vmax:.4g}  "
            f"(scale factor = {1/scale:.2f}x)"
        )
        sep = "─" * min(len(header), max_width)
        return f"{header}\n{sep}\n" + "\n".join(lines)
