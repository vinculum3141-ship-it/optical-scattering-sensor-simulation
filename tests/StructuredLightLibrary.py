"""Robot Framework test library for UC5 Structured Light 3D Scanning."""

import numpy as np

from optical_metrology.analysis.phase import PhaseExtractor, PhaseUnwrapper
from optical_metrology.analysis.reconstruction import HeightReconstructor, SurfaceComparator
from optical_metrology.illumination.structured import FringeProjector


class StructuredLightLibrary:
    """Test library providing keywords for structured light verification."""

    def create_fringe_projector(self, period, orientation="vertical"):
        self._projector = FringeProjector(period=float(period), orientation=orientation)
        return self._projector

    def generate_patterns(self, height, width):
        shape = (int(height), int(width))
        self._patterns = self._projector.generate_patterns(shape)
        return self._patterns

    def pattern_count_should_be(self, expected):
        actual = len(self._patterns)
        if actual != int(expected):
            raise AssertionError(f"Expected {expected} patterns, got {actual}")

    def pattern_shape_should_be(self, expected_height, expected_width):
        shape = self._patterns[0].intensity.shape
        expected = (int(expected_height), int(expected_width))
        if shape != expected:
            raise AssertionError(f"Pattern shape {shape} != {expected}")

    def extract_phase(self):
        images = [lf.intensity for lf in self._patterns]
        shifts = self._projector.phase_shifts
        self._extractor = PhaseExtractor(phase_shifts=shifts)
        self._wrapped_phase = self._extractor.extract(images)
        return self._wrapped_phase

    def unwrap_phase(self):
        self._unwrapper = PhaseUnwrapper()
        self._unwrapped_phase = self._unwrapper.unwrap(self._wrapped_phase)
        return self._unwrapped_phase

    def reconstruct_height(self, period, projection_angle):
        self._reconstructor = HeightReconstructor()
        reference = np.zeros_like(self._unwrapped_phase)
        self._height = self._reconstructor.reconstruct(
            self._unwrapped_phase, reference,
            period=float(period), projection_angle=float(projection_angle),
        )
        return self._height

    def height_should_be_finite(self):
        if not np.all(np.isfinite(self._height)):
            raise AssertionError("Height map contains non-finite values")

    def height_should_have_shape(self, expected_height, expected_width):
        expected = (int(expected_height), int(expected_width))
        if self._height.shape != expected:
            raise AssertionError(
                f"Height map shape {self._height.shape} != {expected}"
            )

    def phase_map_should_have_shape(self, expected_height, expected_width):
        expected = (int(expected_height), int(expected_width))
        if self._wrapped_phase.shape != expected:
            raise AssertionError(
                f"Phase map shape {self._wrapped_phase.shape} != {expected}"
            )
