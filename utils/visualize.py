"""Centralised terminal heatmap rendering.

Replaces duplicated ``_SHADES`` / ``heatmap()`` / ``visualize()``
implementations previously spread across ``illumination/lightfield.py``,
``detector/base.py``, ``explore.py``, and ``playground.py``.

All four original locations now import from here for consistent
rendering.
"""

import numpy as np

_SHADES = [" ", "\u2591", "\u2592", "\u2593", "\u2588"]


def heatmap(arr, max_width=72, color=True):
    """Render a 2D array as a terminal block-character heatmap.

    Parameters
    ----------
    arr : np.ndarray
        2D array of values to visualise.
    max_width : int
        Maximum character width for the output grid.  Larger fields
        are down-sampled to fit.
    color : bool
        If True, use ANSI 8-colour escape codes: blue (low) →
        green → yellow → red (high).

    Returns
    -------
    str
        Multi-line string ready to ``print()``.
    """
    arr = np.asarray(arr, dtype=float)
    h, w = arr.shape
    scale = min(1.0, max_width / w)
    if scale < 1.0:
        nh, nw = max(1, int(h * scale)), max_width
        ir, jc = np.mgrid[0:h:nh * 1j, 0:w:nw * 1j]
        vals = arr[
            ir.astype(np.intp).clip(0, h - 1),
            jc.astype(np.intp).clip(0, w - 1),
        ]
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

    header = (
        f"({nh}\u00d7{nw})  min={vmin:.4g}  max={vmax:.4g}"
    )
    return f"{header}\n" + "\n".join(lines)
