"""Robot Framework test library for the surface package."""

import sys
from pathlib import Path

_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import numpy as np

from surface import (
    FlatSurface,
    RoughSurface,
    ScratchedSurface,
    ParticleSurface,
    Material,
    Surface,
    GeometryAnalyzer,
)


class SurfaceLibrary:
    """Test library providing keywords for surface geometry model verification."""

    def create_flat_surface(self, height_str, width_str, material_name="default"):
        shape = (int(height_str), int(width_str))
        mat = Material(name=material_name)
        self._surface = FlatSurface(shape, material=mat)
        return self._surface

    def create_rough_surface(self, height_str, width_str, sigma, amplitude):
        shape = (int(height_str), int(width_str))
        self._surface = RoughSurface(shape, sigma=float(sigma), amplitude=float(amplitude))
        return self._surface

    def create_scratched_surface(self, height_str, width_str, depth, width):
        shape = (int(height_str), int(width_str))
        self._surface = ScratchedSurface(shape, scratch_depth=float(depth), scratch_width=int(width))
        return self._surface

    def create_particle_surface(self, height_str, width_str, count, amplitude, sigma):
        shape = (int(height_str), int(width_str))
        self._surface = ParticleSurface(
            shape, particle_count=int(count), amplitude=float(amplitude), sigma=float(sigma)
        )
        return self._surface

    def surface_type_should_be(self, expected_type):
        actual = type(self._surface).__name__
        if actual != expected_type:
            raise AssertionError(f"Expected surface type {expected_type}, got {actual}")

    def height_shape_should_be(self, expected_str):
        expected = tuple(int(x) for x in expected_str.split(","))
        if self._surface.height.shape != expected:
            raise AssertionError(f"Height shape {self._surface.height.shape} != {expected}")

    def normals_shape_should_be(self, expected_str):
        expected = tuple(int(x) for x in expected_str.split(","))
        if self._surface.normals.shape != expected:
            raise AssertionError(f"Normals shape {self._surface.normals.shape} != {expected}")

    def roughness_should_be(self, expected, tolerance=1e-6):
        diff = abs(self._surface.roughness - float(expected))
        if diff > float(tolerance):
            raise AssertionError(
                f"Roughness {self._surface.roughness} != {expected} (±{tolerance})"
            )

    def roughness_should_be_greater_than(self, threshold):
        if self._surface.roughness <= float(threshold):
            raise AssertionError(
                f"Roughness {self._surface.roughness} is not > {threshold}"
            )

    def height_range_should_contain_zero(self):
        if not (self._surface.height.min() <= 0.0 <= self._surface.height.max()):
            raise AssertionError("Height range does not contain zero")

    def max_height_should_be_positive(self):
        if self._surface.height.max() <= 0.0:
            raise AssertionError(f"Max height {self._surface.height.max()} is not positive")

    def min_height_should_be_negative(self):
        if self._surface.height.min() >= 0.0:
            raise AssertionError(f"Min height {self._surface.height.min()} is not negative")

    def height_should_be_all_close_to(self, expected, tolerance=1e-6):
        if not np.allclose(self._surface.height, float(expected), atol=float(tolerance)):
            raise AssertionError("Height values are not all close to expected")

    def material_name_should_be(self, expected):
        if self._surface.material.name != expected:
            raise AssertionError(
                f"Material name '{self._surface.material.name}' != '{expected}'"
            )

    def slopes_should_be_all_close_to(self, expected, tolerance=1e-6):
        exp = float(expected)
        if not np.allclose(self._surface.slope_x, exp, atol=float(tolerance)):
            raise AssertionError("slope_x not all close to expected")
        if not np.allclose(self._surface.slope_y, exp, atol=float(tolerance)):
            raise AssertionError("slope_y not all close to expected")

    def curvature_should_be_all_close_to(self, expected, tolerance=1e-6):
        if not np.allclose(self._surface.curvature, float(expected), atol=float(tolerance)):
            raise AssertionError("curvature not all close to expected")

    def height_range_should_be_non_zero(self):
        if np.ptp(self._surface.height) == 0.0:
            raise AssertionError("Height range is zero (expected variation)")