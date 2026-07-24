"""Robot Framework test library for the detector package."""

import sys
from pathlib import Path

_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import numpy as np

from detector import (
    CMOSDetector,
    ColumnDefectNoise,
    DigitalImage,
    FixedPatternNoise,
    HotPixelNoise,
)
from optics import SensorField


class DetectorLibrary:
    """Test library providing keywords for detector model verification."""

    def create_detector(self, exposure_time, quantum_efficiency, dark_current,
                        read_noise_sigma, full_well_capacity, gain, bit_depth):
        self._detector = CMOSDetector(
            exposure_time=float(exposure_time),
            quantum_efficiency=float(quantum_efficiency),
            dark_current=float(dark_current),
            read_noise_sigma=float(read_noise_sigma),
            full_well_capacity=float(full_well_capacity),
            gain=float(gain),
            bit_depth=int(bit_depth),
        )
        return self._detector

    def create_default_detector(self):
        self._detector = CMOSDetector()
        return self._detector

    def capture_with_detector(self, height, width, wavelength):
        shape = (int(height), int(width))
        irradiance = np.ones(shape, dtype=float) * 1e3
        sensor_field = SensorField(
            irradiance=irradiance,
            wavelength=float(wavelength),
            polarization=None,
            optical_path_length=0.1,
        )
        self._image = self._detector.capture(sensor_field)
        return self._image

    def image_should_be_digital_image(self):
        if not isinstance(self._image, DigitalImage):
            raise AssertionError(
                f"Expected DigitalImage, got {type(self._image)}"
            )

    def pixel_shape_should_be(self, expected_str):
        expected = tuple(int(x) for x in expected_str.split(","))
        if self._image.pixels.shape != expected:
            raise AssertionError(
                f"Pixel shape {self._image.pixels.shape} != {expected}"
            )

    def pixel_dtype_should_be_uint16(self):
        if self._image.pixels.dtype != np.uint16:
            raise AssertionError(
                f"Pixel dtype {self._image.pixels.dtype} != uint16"
            )

    def pixel_range_should_be_within(self, min_val, max_val):
        actual_min = int(self._image.pixels.min())
        actual_max = int(self._image.pixels.max())
        if actual_min < int(min_val):
            raise AssertionError(f"Pixel min {actual_min} < {min_val}")
        if actual_max > int(max_val):
            raise AssertionError(f"Pixel max {actual_max} > {max_val}")

    def metadata_should_contain_key(self, key):
        if key not in self._image.metadata:
            raise AssertionError(
                f"Metadata missing key '{key}'. Keys: {list(self._image.metadata.keys())}"
            )

    def metadata_value_should_be(self, key, expected):
        actual = self._image.metadata.get(key)
        if actual is None:
            raise AssertionError(f"Metadata key '{key}' not found")
        if str(actual) != str(expected):
            raise AssertionError(
                f"Metadata['{key}'] = {actual} != {expected}"
            )

    def detector_type_should_be(self, expected_type):
        actual = type(self._detector).__name__
        if actual != expected_type:
            raise AssertionError(f"Expected {expected_type}, got {actual}")

    def add_fixed_pattern_noise(self, magnitude):
        noise = FixedPatternNoise(pattern=float(magnitude))
        self._detector.noise_models.append(noise)
        return noise

    def add_column_defect(self, column, scale):
        noise = ColumnDefectNoise(column_index=int(column), scale_factor=float(scale))
        self._detector.noise_models.append(noise)
        return noise

    def add_hot_pixel_noise(self, density, hot_current, exposure_time):
        noise = HotPixelNoise(
            density=float(density),
            hot_current=float(hot_current),
            exposure_time=float(exposure_time),
        )
        self._detector.noise_models.append(noise)
        return noise

    def column_should_be_zero(self, column):
        col = int(column)
        if not np.all(self._image.pixels[:, col] == 0):
            raise AssertionError(f"Column {col} is not all zeros")
