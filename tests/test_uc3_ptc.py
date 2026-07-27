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


def test_ptc_gain_approx_one_from_poisson_images():
    rng = np.random.default_rng(42)
    images = []
    for level in np.linspace(50, 500, 20):
        pixels = rng.poisson(level, size=(64, 64)).astype(np.uint16)
        images.append(DigitalImage(pixels=pixels, metadata={"bit_depth": 12}))
    report = PTCAnalyzer().analyze(images)
    gain = report.measurements["gain"]
    assert 0.8 < gain < 1.2, f"Expected gain ≈ 1.0, got {gain}"


def test_ptc_read_noise_extracted():
    rng = np.random.default_rng(42)
    images = []
    for level in np.linspace(50, 500, 20):
        noise = rng.normal(0, 5, size=(64, 64))
        pixels = (rng.poisson(level, size=(64, 64)) + noise).astype(np.uint16)
        images.append(DigitalImage(pixels=pixels, metadata={"bit_depth": 12}))
    report = PTCAnalyzer().analyze(images)
    assert report.measurements["gain"] > 0
    assert "read_noise_electrons" in report.measurements


def test_ptc_returns_all_keys():
    rng = np.random.default_rng(42)
    images = []
    for level in np.linspace(50, 500, 20):
        pixels = rng.poisson(level, size=(32, 32)).astype(np.uint16)
        images.append(DigitalImage(pixels=pixels, metadata={"bit_depth": 12}))
    m = PTCAnalyzer().analyze(images).measurements
    for key in ("gain", "read_noise_electrons", "full_well_signal", "dynamic_range_db", "mean_signal", "variance"):
        assert key in m, f"Missing key: {key}"


def test_ptc_fit_region_respected():
    rng = np.random.default_rng(42)
    images = []
    for level in np.linspace(50, 500, 20):
        pixels = rng.poisson(level, size=(32, 32)).astype(np.uint16)
        images.append(DigitalImage(pixels=pixels, metadata={"bit_depth": 12}))
    m1 = PTCAnalyzer(fit_region=(0.0, 1.0)).analyze(images).measurements
    m2 = PTCAnalyzer(fit_region=(0.2, 0.8)).analyze(images).measurements
    assert m1["gain"] > 0
    assert m2["gain"] > 0


def test_ptc_few_images_returns_zero():
    rng = np.random.default_rng(42)
    pixels = rng.poisson(100, size=(8, 8)).astype(np.uint16)
    img = DigitalImage(pixels=pixels, metadata={"bit_depth": 12})
    m = PTCAnalyzer().analyze([img]).measurements
    assert m["gain"] == 0.0


def test_dynamic_range_uniform_image_is_zero():
    pixels = np.ones((8, 8), dtype=np.uint16) * 2048
    image = DigitalImage(pixels=pixels, metadata={"bit_depth": 12})
    m = DynamicRangeAnalyzer().analyze(image).measurements
    assert m["dynamic_range_db"] == 0.0


def test_dynamic_range_varied_image_positive():
    pixels = np.zeros((8, 8), dtype=np.uint16)
    pixels[0, 0] = 1
    pixels[1, 1] = 4095
    image = DigitalImage(pixels=pixels, metadata={"bit_depth": 12})
    m = DynamicRangeAnalyzer().analyze(image).measurements
    assert m["dynamic_range_db"] >= 0.0
    assert m["max_signal"] == 4095.0
    assert m["min_signal"] == 0.0


def test_dynamic_range_with_nonzero_min():
    pixels = np.full((8, 8), 100, dtype=np.uint16)
    pixels[0, 0] = 4000
    image = DigitalImage(pixels=pixels, metadata={"bit_depth": 12})
    m = DynamicRangeAnalyzer().analyze(image).measurements
    assert m["dynamic_range_db"] > 0.0


def test_dynamic_range_returns_all_keys():
    pixels = np.random.randint(0, 4095, size=(8, 8), dtype=np.uint16)
    image = DigitalImage(pixels=pixels, metadata={"bit_depth": 12})
    m = DynamicRangeAnalyzer().analyze(image).measurements
    for key in ("dynamic_range_db", "max_signal", "min_signal", "mean_signal", "std_signal", "snr_ratio_db"):
        assert key in m


def test_linearity_perfect_linear():
    images = []
    for m in np.linspace(100, 1000, 5):
        pixels = np.full((8, 8), int(m), dtype=np.uint16)
        images.append(DigitalImage(pixels=pixels, metadata={"bit_depth": 12}))
    m = LinearityTestAnalyzer().analyze(images).measurements
    assert m["r_squared"] > 0.99
    assert m["linearity_error_pct"] < 1.0


def test_linearity_known_exposures():
    exposures = [0.1, 0.3, 0.5, 0.7, 1.0]
    images = []
    for e in exposures:
        pixels = np.full((8, 8), int(e * 1000), dtype=np.uint16)
        images.append(DigitalImage(pixels=pixels, metadata={"bit_depth": 12}))
    m = LinearityTestAnalyzer(ideal_exposures=exposures).analyze(images).measurements
    assert m["r_squared"] > 0.99


def test_linearity_nonlinear_high_error():
    images = []
    for m in np.linspace(100, 1000, 5):
        val = int(m ** 1.5 / 30)
        pixels = np.full((8, 8), val, dtype=np.uint16)
        images.append(DigitalImage(pixels=pixels, metadata={"bit_depth": 12}))
    m = LinearityTestAnalyzer().analyze(images).measurements
    assert m["linearity_error_pct"] > 0.0


def test_linearity_single_image_returns_zero():
    pixels = np.full((8, 8), 500, dtype=np.uint16)
    img = DigitalImage(pixels=pixels, metadata={"bit_depth": 12})
    m = LinearityTestAnalyzer().analyze([img]).measurements
    assert m["linearity_error_pct"] == 0.0


def test_linearity_returns_all_keys():
    images = []
    for m in np.linspace(100, 1000, 5):
        pixels = np.full((8, 8), int(m), dtype=np.uint16)
        images.append(DigitalImage(pixels=pixels, metadata={"bit_depth": 12}))
    m = LinearityTestAnalyzer().analyze(images).measurements
    for key in ("linearity_error_pct", "r_squared", "slope", "intercept"):
        assert key in m


def test_siemens_star_shape():
    img = siemens_star(size=128, spokes=36, bit_depth=12)
    assert img.pixels.shape == (128, 128)
    assert img.pixels.dtype == np.uint16


def test_siemens_star_max_value():
    img = siemens_star(size=64, spokes=36, bit_depth=12)
    max_val = 2 ** 12 - 1
    assert np.max(img.pixels) <= max_val


def test_siemens_star_variable_size():
    img = siemens_star(size=256, spokes=36, bit_depth=8)
    assert img.pixels.shape == (256, 256)
    max_val = 2 ** 8 - 1
    assert np.max(img.pixels) <= max_val


def test_slanted_edge_shape():
    img = slanted_edge(height=128, width=128, angle_deg=5.0, bit_depth=12)
    assert img.pixels.shape == (128, 128)


def test_slanted_edge_two_halves():
    img = slanted_edge(height=64, width=64, angle_deg=5.0, bit_depth=12)
    max_val = 2 ** 12 - 1
    unique = np.unique(img.pixels)
    assert max_val in unique
    assert 0 in unique


def test_slanted_edge_angle_variation():
    img = slanted_edge(height=64, width=64, angle_deg=10.0, bit_depth=12)
    mid = img.pixels[:, 32]
    assert np.any(mid == 0) and np.any(mid == 4095)


def test_greyscale_wedge_shape():
    img = greyscale_wedge(height=32, width=128, bit_depth=12)
    assert img.pixels.shape == (32, 128)


def test_greyscale_wedge_linear_ramp():
    img = greyscale_wedge(height=16, width=64, bit_depth=12)
    max_val = 2 ** 12 - 1
    assert np.min(img.pixels) == 0
    assert np.max(img.pixels) == max_val
    row = img.pixels[0, :].astype(float)
    diffs = np.diff(row)
    assert np.all(diffs >= 0)


def test_greyscale_wedge_reverse():
    img = greyscale_wedge(height=16, width=64, bit_depth=12, reverse=True)
    row = img.pixels[0, :].astype(float)
    diffs = np.diff(row)
    assert np.all(diffs <= 0)


def test_greyscale_wedge_all_rows_identical():
    img = greyscale_wedge(height=32, width=64, bit_depth=12)
    for i in range(1, 32):
        assert np.array_equal(img.pixels[0, :], img.pixels[i, :])


def test_greyscale_wedge_bit_depth_8():
    img = greyscale_wedge(height=8, width=32, bit_depth=8)
    max_val = 2 ** 8 - 1
    assert np.max(img.pixels) == max_val
