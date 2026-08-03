"""Robot Framework test library for the analysis package."""

import numpy as np

from optical_metrology.analysis import (
    AnalysisReport,
    ContrastAnalyzer,
    HistogramAnalyzer,
    ImageAnalyzer,
    SaturationAnalyzer,
)
from optical_metrology.detector import DigitalImage


class AnalysisLibrary:
    """Test library providing keywords for analysis model verification."""

    def create_histogram_analyzer(self):
        self._analyzer = HistogramAnalyzer()
        return self._analyzer

    def create_image_analyzer(self):
        self._analyzer = ImageAnalyzer(modules=[HistogramAnalyzer()])
        return self._analyzer

    def analyze_image(self, height, width, bit_depth):
        shape = (int(height), int(width))
        pixels = np.random.randint(0, 2**int(bit_depth), size=shape, dtype=np.uint16)
        image = DigitalImage(pixels=pixels, metadata={"bit_depth": int(bit_depth)})
        self._report = self._analyzer.analyze(image)
        return self._report

    def analyze_known_image(self):
        pixels = np.array([[0, 1, 2], [3, 4, 5]], dtype=np.uint16)
        image = DigitalImage(pixels=pixels, metadata={"bit_depth": 8})
        self._report = self._analyzer.analyze(image)
        return self._report

    def result_should_be_analysis_report(self):
        if not isinstance(self._report, AnalysisReport):
            raise AssertionError(
                f"Expected AnalysisReport, got {type(self._report)}"
            )

    def histogram_should_exist(self):
        if self._report.histogram is None:
            raise AssertionError("Histogram is None")

    def measurement_should_exist(self, name):
        if name not in self._report.measurements:
            raise AssertionError(
                f"Measurement '{name}' not found. Keys: {list(self._report.measurements.keys())}"
            )

    def measurement_should_be_close(self, name, expected, tolerance=1e-6):
        actual = self._report.measurements.get(name)
        if actual is None:
            raise AssertionError(f"Measurement '{name}' not found")
        diff = abs(float(actual) - float(expected))
        if diff > float(tolerance):
            raise AssertionError(
                f"Measurement '{name}' = {actual} != {expected} (±{tolerance})"
            )

    def histogram_length_should_be(self, expected):
        length = len(self._report.histogram)
        if length != int(expected):
            raise AssertionError(
                f"Histogram length {length} != {expected}"
            )

    def analyzer_type_should_be(self, expected_type):
        actual = type(self._analyzer).__name__
        if actual != expected_type:
            raise AssertionError(f"Expected {expected_type}, got {actual}")

    def create_contrast_analyzer(self):
        self._analyzer = ContrastAnalyzer()
        return self._analyzer

    def create_saturation_analyzer(self, threshold):
        self._analyzer = SaturationAnalyzer(threshold=float(threshold))
        return self._analyzer

    def create_combined_analyzer(self):
        self._analyzer = ImageAnalyzer(modules=[ContrastAnalyzer(), SaturationAnalyzer()])
        return self._analyzer

    def analyze_uniform_image(self, height, width, value, bit_depth):
        shape = (int(height), int(width))
        pixels = np.ones(shape, dtype=np.uint16) * int(value)
        image = DigitalImage(pixels=pixels, metadata={"bit_depth": int(bit_depth)})
        self._report = self._analyzer.analyze(image)
        return self._report

    def analyze_image_with_saturation(self, height, width, saturation_fraction, bit_depth):
        shape = (int(height), int(width))
        total = shape[0] * shape[1]
        n_sat = int(total * float(saturation_fraction))
        pixels = np.random.randint(0, 100, size=shape, dtype=np.uint16)
        sat_level = 2**int(bit_depth) - 1
        sat_indices = np.random.choice(total, n_sat, replace=False)
        pixels.flat[sat_indices] = sat_level
        image = DigitalImage(pixels=pixels, metadata={"bit_depth": int(bit_depth)})
        self._report = self._analyzer.analyze(image)
        return self._report
