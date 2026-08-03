"""Robot Framework test library for UC3 Sensor Characterization."""

import numpy as np

from optical_metrology.analysis import (
    DynamicRangeAnalyzer,
    LinearityTestAnalyzer,
    PTCAnalyzer,
    greyscale_wedge,
    siemens_star,
    slanted_edge,
)
from optical_metrology.detector import DigitalImage


class SensorCharLibrary:
    """Test library for UC3 sensor performance characterization."""

    def __init__(self):
        self._results = {}

    def create_poisson_images(self, count: str = "10", size: str = "32", low: str = "50", high: str = "500", seed: str = "42"):
        n = int(count)
        s = int(size)
        lo = float(low)
        hi = float(high)
        rng = np.random.default_rng(int(seed))
        self._images = []
        for level in np.linspace(lo, hi, n):
            pixels = rng.poisson(level, size=(s, s)).astype(np.uint16)
            self._images.append(DigitalImage(pixels=pixels, metadata={"bit_depth": 12}))

    def create_linear_response_images(self, count: str = "5"):
        n = int(count)
        self._images = []
        for m in np.linspace(100, 1000, n):
            pixels = np.full((8, 8), int(m), dtype=np.uint16)
            self._images.append(DigitalImage(pixels=pixels, metadata={"bit_depth": 12}))

    def create_uniform_image(self, value: str = "2048", size: str = "8"):
        v = int(value)
        s = int(size)
        pixels = np.full((s, s), v, dtype=np.uint16)
        self._image = DigitalImage(pixels=pixels, metadata={"bit_depth": 12})

    def create_varied_image(self):
        pixels = np.full((8, 8), 100, dtype=np.uint16)
        pixels[0, 0] = 1
        pixels[1, 1] = 4095
        self._image = DigitalImage(pixels=pixels, metadata={"bit_depth": 12})

    def run_ptc_analysis(self):
        analyzer = PTCAnalyzer()
        self._report = analyzer.analyze(self._images)
        self._results = self._report.measurements

    def run_dynamic_range_analysis(self):
        analyzer = DynamicRangeAnalyzer()
        self._report = analyzer.analyze(self._image)
        self._results = self._report.measurements

    def run_linearity_analysis(self):
        analyzer = LinearityTestAnalyzer()
        self._report = analyzer.analyze(self._images)
        self._results = self._report.measurements

    def generate_siemens_star(self, size: str = "64", spokes: str = "36", bit_depth: str = "12"):
        self._image = siemens_star(size=int(size), spokes=int(spokes), bit_depth=int(bit_depth))

    def generate_slanted_edge(self, height: str = "64", width: str = "64", angle: str = "5.0", bit_depth: str = "12"):
        self._image = slanted_edge(height=int(height), width=int(width), angle_deg=float(angle), bit_depth=int(bit_depth))

    def generate_greyscale_wedge(self, height: str = "16", width: str = "64", bit_depth: str = "12", reverse: str = "False"):
        self._image = greyscale_wedge(height=int(height), width=int(width), bit_depth=int(bit_depth), reverse=reverse.lower() == "true")

    def gain_should_be_positive(self):
        gain = self._results.get("gain", 0.0)
        if gain <= 0:
            raise AssertionError(f"Expected positive gain, got {gain}")

    def gain_should_be_approx(self, expected: str, tolerance: str = "0.2"):
        gain = self._results.get("gain", 0.0)
        exp = float(expected)
        tol = float(tolerance)
        if abs(gain - exp) > tol:
            raise AssertionError(f"Expected gain ≈ {exp}, got {gain}")

    def dynamic_range_should_be_zero(self):
        dr = self._results.get("dynamic_range_db", -1)
        if dr != 0.0:
            raise AssertionError(f"Expected dynamic range 0 dB, got {dr} dB")

    def dynamic_range_should_be_positive(self):
        dr = self._results.get("dynamic_range_db", 0.0)
        if dr <= 0:
            raise AssertionError(f"Expected positive dynamic range, got {dr} dB")

    def linearity_r_squared_should_be_high(self):
        r2 = self._results.get("r_squared", 0.0)
        if r2 < 0.99:
            raise AssertionError(f"Expected R² > 0.99, got {r2}")

    def linearity_error_should_be_low(self):
        err = self._results.get("linearity_error_pct", 100.0)
        if err > 5.0:
            raise AssertionError(f"Expected linearity error < 5%, got {err}%")

    def image_shape_should_be(self, expected: str):
        h, w = [int(s) for s in expected.split("x")]
        if self._image.pixels.shape != (h, w):
            raise AssertionError(f"Expected shape ({h}, {w}), got {self._image.pixels.shape}")

    def max_value_should_be(self, expected: str):
        exp = int(expected)
        actual = int(np.max(self._image.pixels))
        if actual != exp:
            raise AssertionError(f"Expected max value {exp}, got {actual}")

    def image_should_have_both_halves(self):
        unique = np.unique(self._image.pixels)
        if 0 not in unique or 4095 not in unique:
            raise AssertionError(f"Expected both 0 and 4095 in image, got {unique}")

    def greyscale_wedge_should_be_linear(self):
        row = self._image.pixels[0, :].astype(float)
        diffs = np.diff(row)
        if not np.all(diffs >= 0):
            raise AssertionError("Greyscale wedge is not monotonically increasing")
