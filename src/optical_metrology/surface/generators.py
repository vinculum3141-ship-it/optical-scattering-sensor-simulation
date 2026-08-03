"""Concrete surface generators for common test geometries.

Each class inherits from both :class:`~surface.base.Surface` (as a data
container) and :class:`~surface.base.SurfaceGenerator` (as a factory),
providing a ready-to-use surface object on construction:

    - :class:`FlatSurface` — zero height everywhere (ideal reference)
    - :class:`RoughSurface` — Gaussian-correlated noise with configurable
      correlation length and RMS amplitude
    - :class:`ScratchedSurface` — a diagonal groove with programmable
      depth and width
    - :class:`ParticleSurface` — localised Gaussian bumps at random
      (seeded) grid locations
    - :class:`ImportedSurface` — load a height map from an external file
      or NumPy array

All classes use :class:`~surface.base.GeometryAnalyzer` to automatically
compute normals, slopes, curvature, and roughness from the generated
height map on construction.

The helper :func:`_gaussian_filter` provides a pure-NumPy separable
Gaussian blur to avoid a SciPy dependency.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple, Union

import numpy as np

from .base import Material, Surface, SurfaceGenerator, GeometryAnalyzer


def _gaussian_filter(image: np.ndarray, sigma: float) -> np.ndarray:
    """Apply a separable Gaussian blur using convolution.

    This is a pure-NumPy replacement for ``scipy.ndimage.gaussian_filter``
    that avoids adding a SciPy dependency.  It convolves the image with a
    1D Gaussian kernel along each axis independently.

    Parameters
    ----------
    image : np.ndarray
        2D input array.
    sigma : float
        Standard deviation of the Gaussian kernel in pixels.
        Values ≤ 0 return the input unchanged.

    Returns
    -------
    np.ndarray
        Smoothed array of the same shape as *image*.
    """
    if sigma <= 0.0:
        return image

    radius = int(np.ceil(3.0 * sigma))
    coords = np.arange(-radius, radius + 1, dtype=float)
    kernel = np.exp(-(coords**2) / (2.0 * sigma**2))
    kernel /= kernel.sum()

    out = image.astype(float, copy=True)
    h, w = out.shape

    # Blur along axis=1 (horizontal) — convolve each row.
    padded = np.pad(out, ((0, 0), (radius, radius)), mode="edge")
    row_result = np.empty_like(out)
    for i in range(h):
        conv = np.convolve(padded[i, :], kernel, mode="same")
        row_result[i, :] = conv[radius:radius + w]

    # Blur along axis=0 (vertical) — convolve each column.
    padded = np.pad(row_result, ((radius, radius), (0, 0)), mode="edge")
    col_result = np.empty_like(row_result)
    for j in range(w):
        conv = np.convolve(padded[:, j], kernel, mode="same")
        col_result[:, j] = conv[radius:radius + h]

    return col_result


class FlatSurface(Surface):
    """A perfectly flat reference surface.

    All height values are zero, giving zero slope, normals pointing
    straight up (+z), and zero roughness.

    Parameters
    ----------
    shape : tuple of int
        Grid dimensions ``(height, width)``.
    material : Material or None
        Material to attach to the surface.
    """

    def __init__(self, shape: Tuple[int, int], material: Optional[Material] = None):
        self.shape = shape
        surface = GeometryAnalyzer.analyze(np.zeros(shape, dtype=float), material=material)
        self.__dict__.update(surface.__dict__)

    def generate(self, shape: Tuple[int, int]) -> np.ndarray:
        """Return a zero-filled height map."""
        return np.zeros(shape, dtype=float)


class RoughSurface(Surface):
    """A randomly textured surface with correlated noise.

    The height map starts as white Gaussian noise and is then blurred
    with a Gaussian kernel to introduce spatial correlation.  The
    result is scaled by *amplitude*.

    Parameters
    ----------
    shape : tuple of int
        Grid dimensions ``(height, width)``.
    sigma : float
        Correlation length (std-dev of the blur kernel) in pixels.
        Larger values produce longer-wavelength surface undulations.
    amplitude : float
        RMS amplitude scaling factor for the height map.
    material : Material or None
        Material to attach to the surface.
    """

    def __init__(self, shape: Tuple[int, int], sigma: float = 8.0, amplitude: float = 0.5, material: Optional[Material] = None):
        self.sigma = sigma
        self.amplitude = amplitude
        self.shape = shape
        height = self.generate(shape)
        surface = GeometryAnalyzer.analyze(height, material=material)
        self.__dict__.update(surface.__dict__)

    def generate(self, shape: Tuple[int, int]) -> np.ndarray:
        """Generate a rough height map from filtered Gaussian noise."""
        height = np.random.randn(*shape)
        height = _gaussian_filter(height, sigma=self.sigma)
        return self.amplitude * height


class ScratchedSurface(Surface):
    """A surface with a diagonal groove-like scratch.

    The scratch runs from the upper-left quadrant to the right edge,
    with a programmable depth and width.  The groove profile is a
    simple step — each pixel in the scratch path is lowered by
    *scratch_depth*.

    Parameters
    ----------
    shape : tuple of int
        Grid dimensions ``(height, width)``.
    scratch_depth : float
        Depth of the scratch (positive value subtracted from height).
    scratch_width : int
        Approximate width of the scratch in pixels.
    material : Material or None
        Material to attach to the surface.
    """

    def __init__(self, shape: Tuple[int, int], scratch_depth: float = 0.3, scratch_width: int = 3, material: Optional[Material] = None):
        self.scratch_depth = scratch_depth
        self.scratch_width = scratch_width
        self.shape = shape
        height = self.generate(shape)
        surface = GeometryAnalyzer.analyze(height, material=material)
        self.__dict__.update(surface.__dict__)

    def generate(self, shape: Tuple[int, int]) -> np.ndarray:
        """Generate a height map with a diagonal scratch."""
        height = np.zeros(shape, dtype=float)
        h, w = shape
        start_y = h // 4
        start_x = w // 4
        end_x = 3 * w // 4
        for x in range(start_x, end_x):
            y = start_y + (x - start_x) // max(1, self.scratch_width)
            y = int(np.clip(y, 0, h - 1))
            height[y, x] -= self.scratch_depth
        return height


class SinusoidalSurface(Surface):
    """A surface with a sinusoidal wave pattern along the x-axis.

    Useful for modelling diffraction gratings, periodic textures,
    or wavy substrates.

    Parameters
    ----------
    shape : tuple of int
        Grid dimensions ``(height, width)``.
    period : float
        Wavelength of the sinusoid in pixels.
    amplitude : float
        Peak-to-peak amplitude of the sinusoid.
    phase : float
        Phase offset in radians (default 0).
    material : Material or None
        Material to attach to the surface.
    """

    def __init__(self, shape, period=16.0, amplitude=0.5, phase=0.0, material=None):
        self.period = period
        self.amplitude = amplitude
        self.phase = phase
        self.shape = shape
        height = self.generate(shape)
        surface = GeometryAnalyzer.analyze(height, material=material)
        self.__dict__.update(surface.__dict__)

    def generate(self, shape):
        h, w = shape
        x = np.arange(w, dtype=float) - (w - 1) / 2.0
        return self.amplitude * np.sin(2.0 * np.pi * x / self.period + self.phase)[None, :] * np.ones((h, 1))


class AnisotropicRoughSurface(Surface):
    """A randomly textured surface with different correlation lengths
    in the x and y directions.

    Useful for modelling surfaces with directional roughness
    (e.g. ground glass, machined metal, brushed surfaces).

    Parameters
    ----------
    shape : tuple of int
        Grid dimensions ``(height, width)``.
    sigma_x : float
        Correlation length in the x-direction (pixels).
    sigma_y : float
        Correlation length in the y-direction (pixels).
    amplitude : float
        RMS amplitude scaling factor for the height map.
    material : Material or None
        Material to attach to the surface.
    """

    def __init__(self, shape, sigma_x=8.0, sigma_y=2.0, amplitude=0.5, material=None):
        self.sigma_x = sigma_x
        self.sigma_y = sigma_y
        self.amplitude = amplitude
        self.shape = shape
        height = self.generate(shape)
        surface = GeometryAnalyzer.analyze(height, material=material)
        self.__dict__.update(surface.__dict__)

    def generate(self, shape):
        height = np.random.randn(*shape)
        height = _gaussian_filter(height, sigma=self.sigma_x)
        height = _gaussian_filter(height.T, sigma=self.sigma_y).T
        return self.amplitude * height


class DentSurface(Surface):
    """A surface with a smooth Gaussian dent (circular depression).

    Parameters
    ----------
    shape : tuple of int
        Grid dimensions ``(height, width)``.
    depth : float
        Maximum depth of the dent at its centre (positive value).
    radius : float
        Standard deviation of the Gaussian profile in pixels.
        The dent extends approximately 3× *radius* from centre.
    centre : tuple of float or None
        ``(row, col)`` centre of the dent.  If ``None``, the dent is
        centred on the grid.
    material : Material or None
        Material to attach to the surface.
    """

    def __init__(self, shape: Tuple[int, int], depth: float = 0.5, radius: float = 4.0, centre: Optional[Tuple[float, float]] = None, material: Optional[Material] = None):
        self.depth = depth
        self.radius = radius
        self.centre = centre
        self.shape = shape
        height = self.generate(shape)
        surface = GeometryAnalyzer.analyze(height, material=material)
        self.__dict__.update(surface.__dict__)

    def generate(self, shape: Tuple[int, int]) -> np.ndarray:
        height = np.zeros(shape, dtype=float)
        h, w = shape
        cy, cx = self.centre if self.centre is not None else (h / 2.0, w / 2.0)
        yy, xx = np.ogrid[:h, :w]
        dist_sq = (xx - cx) ** 2 + (yy - cy) ** 2
        height -= self.depth * np.exp(-dist_sq / (2.0 * self.radius ** 2))
        return height


class PitSurface(Surface):
    """A surface with a step-like circular pit.

    Parameters
    ----------
    shape : tuple of int
        Grid dimensions ``(height, width)``.
    depth : float
        Depth of the pit (positive value subtracted from height).
    radius : float
        Radius of the pit in pixels.
    centre : tuple of float or None
        ``(row, col)`` centre of the pit.  If ``None``, centred on grid.
    material : Material or None
        Material to attach to the surface.
    """

    def __init__(self, shape: Tuple[int, int], depth: float = 0.5, radius: float = 4.0, centre: Optional[Tuple[float, float]] = None, material: Optional[Material] = None):
        self.depth = depth
        self.radius = radius
        self.centre = centre
        self.shape = shape
        height = self.generate(shape)
        surface = GeometryAnalyzer.analyze(height, material=material)
        self.__dict__.update(surface.__dict__)

    def generate(self, shape: Tuple[int, int]) -> np.ndarray:
        height = np.zeros(shape, dtype=float)
        h, w = shape
        cy, cx = self.centre if self.centre is not None else (h / 2.0, w / 2.0)
        yy, xx = np.ogrid[:h, :w]
        dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
        height[dist <= self.radius] -= self.depth
        return height


class CrackSurface(Surface):
    """A surface with a thin branching crack-like feature.

    The crack traces a path of connected pixels with random lateral
    deviations, producing a jagged line.

    Parameters
    ----------
    shape : tuple of int
        Grid dimensions ``(height, width)``.
    depth : float
        Depth of the crack (positive value subtracted from height).
    width : int
        Width of the crack in pixels.
    length : int
        Approximate length of the crack in pixels.
    jaggedness : float
        Amplitude of random lateral deviations (pixels).
        Default 1.0 produces mild waviness.
    material : Material or None
        Material to attach to the surface.
    """

    def __init__(self, shape: Tuple[int, int], depth: float = 0.4, width: int = 1, length: int = 20, jaggedness: float = 1.0, material: Optional[Material] = None):
        self.depth = depth
        self.width = width
        self.length = length
        self.jaggedness = jaggedness
        self.shape = shape
        height = self.generate(shape)
        surface = GeometryAnalyzer.analyze(height, material=material)
        self.__dict__.update(surface.__dict__)

    def generate(self, shape: Tuple[int, int]) -> np.ndarray:
        height = np.zeros(shape, dtype=float)
        h, w = shape
        rng = np.random.default_rng(42)
        y = float(h // 2)
        x = float(w // 4)
        for _ in range(self.length):
            ix, iy = int(round(x)), int(round(y))
            if 0 <= iy < h and 0 <= ix < w:
                for dw in range(-self.width // 2, self.width // 2 + 1):
                    for dh in range(-self.width // 2, self.width // 2 + 1):
                        py, px = iy + dh, ix + dw
                        if 0 <= py < h and 0 <= px < w:
                            height[py, px] -= self.depth
            x += 1.0
            y += rng.uniform(-self.jaggedness, self.jaggedness)
        return height


class StainSurface(Surface):
    """A surface with a shallow, diffuse stain-like region.

    The stain is modelled as a smooth Gaussian depression with a
    large radius relative to depth, simulating a contamination
    residue.

    Parameters
    ----------
    shape : tuple of int
        Grid dimensions ``(height, width)``.
    depth : float
        Maximum depth at the centre (positive value).
    radius : float
        Standard deviation of the Gaussian profile in pixels.
        Typically larger than for a dent (diffuse edge).
    centre : tuple of float or None
        ``(row, col)`` centre.  If ``None``, centred on grid.
    asymmetry : float
        Stretch factor > 1 makes the stain elliptical along the
        y-axis.  Default 1.0 (circular).
    material : Material or None
        Material to attach to the surface.
    """

    def __init__(self, shape: Tuple[int, int], depth: float = 0.15, radius: float = 8.0, centre: Optional[Tuple[float, float]] = None, asymmetry: float = 1.0, material: Optional[Material] = None):
        self.depth = depth
        self.radius = radius
        self.centre = centre
        self.asymmetry = asymmetry
        self.shape = shape
        height = self.generate(shape)
        surface = GeometryAnalyzer.analyze(height, material=material)
        self.__dict__.update(surface.__dict__)

    def generate(self, shape: Tuple[int, int]) -> np.ndarray:
        height = np.zeros(shape, dtype=float)
        h, w = shape
        cy, cx = self.centre if self.centre is not None else (h / 2.0, w / 2.0)
        yy, xx = np.ogrid[:h, :w]
        dist_sq = (xx - cx) ** 2 + (yy - cy) ** 2 / self.asymmetry ** 2
        height -= self.depth * np.exp(-dist_sq / (2.0 * self.radius ** 2))
        return height


class ParticleSurface(Surface):
    """A surface with localized Gaussian bumps simulating particles.

    Each particle is placed at a random grid location and modelled as
    a 2D Gaussian bump.  The particle positions are deterministic
    (seeded with ``rng = np.random.default_rng(0)``) for reproducibility.

    Parameters
    ----------
    shape : tuple of int
        Grid dimensions ``(height, width)``.
    particle_count : int
        Number of particles to place.
    amplitude : float
        Peak height of each particle bump.
    sigma : float
        Standard deviation of each Gaussian bump in pixels.
    material : Material or None
        Material to attach to the surface.
    """

    def __init__(self, shape: Tuple[int, int], particle_count: int = 4, amplitude: float = 0.8, sigma: float = 2.0, material: Optional[Material] = None):
        self.particle_count = particle_count
        self.amplitude = amplitude
        self.sigma = sigma
        self.shape = shape
        height = self.generate(shape)
        surface = GeometryAnalyzer.analyze(height, material=material)
        self.__dict__.update(surface.__dict__)

    def generate(self, shape: Tuple[int, int]) -> np.ndarray:
        """Generate a height map with Gaussian particle bumps."""
        height = np.zeros(shape, dtype=float)
        h, w = shape
        rng = np.random.default_rng(0)
        for _ in range(self.particle_count):
            cx = rng.integers(0, w)
            cy = rng.integers(0, h)
            yy, xx = np.ogrid[:h, :w]
            radius_sq = (xx - cx) ** 2 + (yy - cy) ** 2
            height += self.amplitude * np.exp(-radius_sq / (2 * self.sigma**2))
        return height


def _load_height_map(source: Union[str, Path, np.ndarray]) -> np.ndarray:
    """Load a 2D height array from *source*.

    Supported formats
    -----------------
    * ``.npy``  — NumPy binary (``np.load``).  Must contain a 2D array.
    * ``.csv``  — comma-separated values (``np.loadtxt`` with delimiter ``,``).
    * ``.txt``  — whitespace-delimited text (``np.loadtxt``).
    * ``np.ndarray`` — used directly if already a NumPy array.

    Parameters
    ----------
    source : str, Path, or np.ndarray
        File path or existing array.

    Returns
    -------
    np.ndarray
        2D float64 height map.
    """
    if isinstance(source, np.ndarray):
        arr = source
    else:
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Height map file not found: {path}")
        suffix = path.suffix.lower()
        if suffix == ".npy":
            arr = np.load(str(path))
        elif suffix == ".csv":
            arr = np.loadtxt(str(path), delimiter=",")
        elif suffix == ".txt":
            arr = np.loadtxt(str(path))
        else:
            raise ValueError(
                f"Unsupported file format: {suffix}.  "
                f"Use .npy, .csv, or .txt."
            )
    arr = np.asarray(arr, dtype=float)
    if arr.ndim != 2:
        raise ValueError(
            f"Height map must be 2D, got shape {arr.shape}.  "
            f"Ensure your file contains a 2D grid of height values."
        )
    return arr


class ImportedSurface(Surface):
    """Load an external height map from a file or a NumPy array.

    Use this generator to bring in real measurement data (AFM, profilometry)
    or height maps created outside the framework.  The geometry (normals,
    slopes, curvature, roughness) is derived automatically.

    Parameters
    ----------
    source : str, Path, or np.ndarray
        One of:

        * Path to a ``.npy`` file (NumPy binary)
        * Path to a ``.csv`` file (comma-separated, no header)
        * Path to a ``.txt`` file (whitespace-delimited)
        * A 2D :class:`np.ndarray` directly

    spacing : float, optional
        Physical grid spacing in metres.  Used only if the surface
        needs to be re-sampled or visualised with correct aspect ratio.
        Default 1.0 (arbitrary units).
    material : Material or None
        Material to attach to the surface.

    Input requirements
    ------------------
    1. The file or array must contain a **rectangular 2D grid** of
       height values (rows = Y, columns = X).
    2. All values must be numeric (``int`` or ``float``).
    3. No header rows or index columns — pure data only.
    4. For CSV files, use comma delimiters and no quoting.
    5. Height units are arbitrary but should be **consistent with
       the illumination wavelengths** used in the simulation
       (typically micrometres or nanometres for optical work).

    Example file content (CSV, 3×3 grid)::

        0.0, 0.1, 0.0
        0.1, 0.5, 0.1
        0.0, 0.1, 0.0

    Examples
    --------
    >>> # From a NumPy array
    >>> heights = np.random.randn(64, 64) * 0.3
    >>> surf = ImportedSurface(heights, material=Material("silicon"))
    >>> surf.shape
    (64, 64)
    >>> surf.roughness > 0
    True

    >>> # From a .npy file
    >>> surf = ImportedSurface("measurement.npy")

    >>> # From a CSV file
    >>> surf = ImportedSurface("profile.csv", spacing=1e-6)
    """

    def __init__(
        self,
        source: Union[str, Path, np.ndarray],
        spacing: float = 1.0,
        material: Optional[Material] = None,
    ):
        self.source = source
        self.spacing = spacing
        height = _load_height_map(source)
        self.shape = height.shape
        surface = GeometryAnalyzer.analyze(height, material=material)
        self.__dict__.update(surface.__dict__)

    def generate(self, shape: Tuple[int, int]) -> np.ndarray:
        """Return the loaded height map (``shape`` is ignored).

        Parameters
        ----------
        shape : tuple of int
            Ignored — the shape is fixed by the imported data.
            Accepted for interface compatibility.

        Returns
        -------
        np.ndarray
            2D height array.
        """
        return self.height


class WaferSurface(Surface):
    """A rectangular wafer surface with a grid of chip dies and fiducial marks.

    Dies are arranged in a regular grid separated by scribe streets.
    Fiducial crosses (+) are placed at the four corners of the wafer.

    Parameters
    ----------
    shape : tuple of int
        Grid dimensions ``(height, width)``.
    die_rows : int
        Number of die rows in the grid.
    die_cols : int
        Number of die columns in the grid.
    street_width : int
        Width of scribe streets between dies in pixels.
    fiducial_size : int
        Half-arm length of each fiducial cross in pixels.
    fiducial_height : float
        Height of fiducial marks (relative to die surface).
    die_height_val : float
        Height of each die surface.
    material : Material or None
        Material to attach to the surface.
    """

    def __init__(
        self,
        shape,
        die_rows=4,
        die_cols=4,
        street_width=4,
        fiducial_size=3,
        fiducial_height=2.0,
        die_height_val=1.0,
        material=None,
    ):
        self.die_rows = die_rows
        self.die_cols = die_cols
        self.street_width = street_width
        self.fiducial_size = fiducial_size
        self.fiducial_height = fiducial_height
        self.die_height_val = die_height_val
        self.shape = shape
        height = self.generate(shape)
        surface = GeometryAnalyzer.analyze(height, material=material)
        self.__dict__.update(surface.__dict__)

    def generate(self, shape):
        h, w = shape
        height = np.zeros((h, w), dtype=float)

        usable_h = h - (self.die_rows + 1) * self.street_width
        usable_w = w - (self.die_cols + 1) * self.street_width
        die_h = max(1, usable_h // self.die_rows)
        die_w = max(1, usable_w // self.die_cols)

        self._die_height_px = die_h
        self._die_width_px = die_w

        for row in range(self.die_rows):
            for col in range(self.die_cols):
                y0 = self.street_width + row * (die_h + self.street_width)
                x0 = self.street_width + col * (die_w + self.street_width)
                y1 = min(y0 + die_h, h)
                x1 = min(x0 + die_w, w)
                height[y0:y1, x0:x1] = self.die_height_val

        fs = self.fiducial_size
        corners = [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)]
        for cy, cx in corners:
            for dy in range(-fs, fs + 1):
                for dx in range(-1, 2):
                    py, px = cy + dy, cx + dx
                    if 0 <= py < h and 0 <= px < w:
                        height[py, px] = self.fiducial_height
            for dy in range(-1, 2):
                for dx in range(-fs, fs + 1):
                    py, px = cy + dy, cx + dx
                    if 0 <= py < h and 0 <= px < w:
                        height[py, px] = self.fiducial_height

        return height


class MisalignedSurface(Surface):
    """A wafer surface with configurable translation, rotation, and scale errors.

    Wraps :class:`WaferSurface` and applies an affine transformation to
    simulate chip misalignment.

    Parameters
    ----------
    shape : tuple of int
        Grid dimensions ``(height, width)``.
    dx : float
        Horizontal translation offset in pixels.
    dy : float
        Vertical translation offset in pixels.
    rotation_deg : float
        Rotation angle in degrees (counter-clockwise).
    scale : float
        Uniform scale factor.
    kwds
        Additional keyword arguments forwarded to :class:`WaferSurface`
        (die_rows, die_cols, street_width, fiducial_size, etc.).
    """

    def __init__(
        self,
        shape,
        dx=0.0,
        dy=0.0,
        rotation_deg=0.0,
        scale=1.0,
        material=None,
        **kwds,
    ):
        self.dx = dx
        self.dy = dy
        self.rotation_deg = rotation_deg
        self.scale = scale
        self._wafer_kwds = kwds
        self.shape = shape
        height = self.generate(shape)
        surface = GeometryAnalyzer.analyze(height, material=material)
        self.__dict__.update(surface.__dict__)

    def generate(self, shape):
        base = WaferSurface(shape, **self._wafer_kwds)
        height = base.height.copy()

        theta = np.radians(self.rotation_deg)
        cos_t, sin_t = np.cos(theta), np.sin(theta)
        transform = np.array([[cos_t * self.scale, -sin_t * self.scale, self.dx],
                               [sin_t * self.scale, cos_t * self.scale, self.dy]])

        from scipy.ndimage import affine_transform
        return affine_transform(height, transform, order=1, mode='constant', cval=0.0)