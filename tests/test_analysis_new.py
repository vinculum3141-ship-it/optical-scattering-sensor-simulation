import numpy as np

from optical_metrology.analysis import (
    ContrastAnalyzer,
    EdgeDetectionAnalyzer,
    ErrorMapAnalyzer,
    FFTAnalyzer,
    FocusAnalyzer,
    ImageAnalyzer,
    IntensityProfileAnalyzer,
    MTFAnalyzer,
    SNRAnalyzer,
    SaturationAnalyzer,
    SpeckleRoughnessEstimator,
)
from optical_metrology.detector import DigitalImage


def _image(pixels=None, bit_depth=12):
    if pixels is None:
        pixels = np.random.randint(0, 2**bit_depth, size=(8, 8), dtype=np.uint16)
    return DigitalImage(pixels=pixels, metadata={"bit_depth": bit_depth})


def test_contrast_analyzer_returns_measurements():
    image = _image()
    analyzer = ContrastAnalyzer()
    report = analyzer.analyze(image)
    assert "rms_contrast" in report.measurements
    assert "michelson_contrast" in report.measurements
    assert "mean_intensity" in report.measurements


def test_contrast_uniform_image_gives_zero():
    pixels = np.ones((8, 8), dtype=np.uint16) * 2048
    image = _image(pixels=pixels)
    analyzer = ContrastAnalyzer()
    report = analyzer.analyze(image)
    assert report.measurements["rms_contrast"] == 0.0
    assert report.measurements["michelson_contrast"] == 0.0


def test_contrast_high_contrast_image():
    pixels = np.zeros((8, 8), dtype=np.uint16)
    pixels[:, :4] = 0
    pixels[:, 4:] = 4095
    image = _image(pixels=pixels)
    analyzer = ContrastAnalyzer()
    report = analyzer.analyze(image)
    assert report.measurements["michelson_contrast"] > 0.9


def test_saturation_analyzer_detects_saturated():
    pixels = np.zeros((8, 8), dtype=np.uint16)
    pixels[0, 0] = 4095
    image = _image(pixels=pixels)
    analyzer = SaturationAnalyzer(threshold=0.99)
    report = analyzer.analyze(image)
    assert report.measurements["saturated_pixels"] >= 1
    assert report.measurements["saturation_fraction"] > 0.0


def test_saturation_analyzer_no_saturation():
    pixels = np.ones((8, 8), dtype=np.uint16) * 100
    image = _image(pixels=pixels, bit_depth=12)
    analyzer = SaturationAnalyzer(threshold=0.99)
    report = analyzer.analyze(image)
    assert report.measurements["saturated_pixels"] == 0


def test_image_analyzer_with_multiple_analysis_modules():
    pixels = np.random.randint(0, 4095, size=(8, 8), dtype=np.uint16)
    image = _image(pixels=pixels)
    analyzer = ImageAnalyzer(modules=[ContrastAnalyzer(), SaturationAnalyzer()])
    report = analyzer.analyze(image)
    assert "rms_contrast" in report.measurements
    assert "saturated_pixels" in report.measurements


def test_intensity_profile_returns_profile():
    image = _image()
    analyzer = IntensityProfileAnalyzer(start=(0, 0), end=(7, 7))
    report = analyzer.analyze(image)
    assert "profile" in report.measurements
    assert len(report.measurements["profile"]) == 256


def test_intensity_profile_horizontal_line():
    pixels = np.zeros((8, 8), dtype=np.uint16)
    pixels[4, :] = 1000
    image = _image(pixels=pixels)
    analyzer = IntensityProfileAnalyzer(start=(4, 0), end=(4, 7))
    report = analyzer.analyze(image)
    assert np.allclose(report.measurements["profile"], 1000.0)


def test_intensity_profile_contrast_on_step():
    pixels = np.zeros((8, 8), dtype=np.uint16)
    pixels[:, 4:] = 4000
    image = _image(pixels=pixels)
    m = IntensityProfileAnalyzer(start=(4, 0), end=(4, 7)).analyze(image).measurements
    assert m["profile_contrast"] > 0.9
    assert m["profile_min"] < 1.0
    assert m["profile_max"] > 3990.0


def test_intensity_profile_linewidth_averages():
    pixels = np.zeros((16, 16), dtype=np.uint16)
    pixels[6:10, :] = 2000
    image = _image(pixels=pixels)
    narrow = IntensityProfileAnalyzer(start=(7, 0), end=(7, 15), linewidth=1)
    wide = IntensityProfileAnalyzer(start=(7, 0), end=(7, 15), linewidth=5)
    r_narrow = narrow.analyze(image).measurements
    r_wide = wide.analyze(image).measurements
    assert r_narrow["profile_max"] > r_wide["profile_max"], \
        "wider linewidth should smooth the profile peak"


def test_focus_laplacian_sharp_image_scores_higher():
    sharp = np.random.randn(16, 16).astype(np.float32) * 100
    blurry = np.ones((16, 16), dtype=np.float32) * 128
    s_img = DigitalImage(pixels=sharp, metadata={"bit_depth": 12})
    b_img = DigitalImage(pixels=blurry, metadata={"bit_depth": 12})
    s_score = FocusAnalyzer(method="laplacian_variance").analyze(s_img).measurements["focus_score"]
    b_score = FocusAnalyzer(method="laplacian_variance").analyze(b_img).measurements["focus_score"]
    assert s_score > b_score


def test_focus_tenengrad_sharp_image_scores_higher():
    sharp = np.random.randn(16, 16).astype(np.float32) * 100
    blurry = np.ones((16, 16), dtype=np.float32) * 128
    s_img = DigitalImage(pixels=sharp, metadata={"bit_depth": 12})
    b_img = DigitalImage(pixels=blurry, metadata={"bit_depth": 12})
    s_score = FocusAnalyzer(method="tenengrad").analyze(s_img).measurements["focus_score"]
    b_score = FocusAnalyzer(method="tenengrad").analyze(b_img).measurements["focus_score"]
    assert s_score > b_score


def test_focus_brenner_sharp_image_scores_higher():
    sharp = np.random.randn(16, 16).astype(np.float32) * 100
    blurry = np.ones((16, 16), dtype=np.float32) * 128
    s_img = DigitalImage(pixels=sharp, metadata={"bit_depth": 12})
    b_img = DigitalImage(pixels=blurry, metadata={"bit_depth": 12})
    s_score = FocusAnalyzer(method="brenner").analyze(s_img).measurements["focus_score"]
    b_score = FocusAnalyzer(method="brenner").analyze(b_img).measurements["focus_score"]
    assert s_score > b_score


def test_focus_uniform_image_gives_zero():
    pixels = np.ones((16, 16), dtype=np.uint16) * 2048
    image = DigitalImage(pixels=pixels, metadata={"bit_depth": 12})
    for method in ("laplacian_variance", "tenengrad", "brenner"):
        score = FocusAnalyzer(method=method).analyze(image).measurements["focus_score"]
        assert score == 0.0, f"{method} should be 0 for uniform image"


def test_focus_invalid_method_raises():
    import pytest
    with pytest.raises(ValueError, match="Unknown focus method"):
        FocusAnalyzer(method="invalid")


def test_error_map_identical_images():
    pixels = np.random.randint(0, 4095, size=(8, 8), dtype=np.uint16)
    ref = DigitalImage(pixels=pixels.copy(), metadata={"bit_depth": 12})
    img = DigitalImage(pixels=pixels.copy(), metadata={"bit_depth": 12})
    m = ErrorMapAnalyzer(ref).analyze(img).measurements
    assert m["mae"] == 0.0
    assert m["rmse"] == 0.0
    assert m["max_error"] == 0.0
    assert m["psnr_db"] == 120.0


def test_error_map_constant_offset():
    ref_pixels = np.zeros((4, 4), dtype=np.uint16)
    img_pixels = np.full((4, 4), 100, dtype=np.uint16)
    ref = DigitalImage(pixels=ref_pixels, metadata={"bit_depth": 12})
    img = DigitalImage(pixels=img_pixels, metadata={"bit_depth": 12})
    m = ErrorMapAnalyzer(ref).analyze(img).measurements
    assert m["mae"] == 100.0
    assert m["rmse"] == 100.0
    assert m["max_error"] == 100.0


def test_error_map_shape_mismatch_raises():
    ref_pixels = np.zeros((4, 4), dtype=np.uint16)
    img_pixels = np.zeros((8, 8), dtype=np.uint16)
    ref = DigitalImage(pixels=ref_pixels, metadata={"bit_depth": 12})
    img = DigitalImage(pixels=img_pixels, metadata={"bit_depth": 12})
    import pytest
    with pytest.raises(ValueError, match="Shape mismatch"):
        ErrorMapAnalyzer(ref).analyze(img)


def test_error_map_accepts_raw_array():
    ref = np.zeros((4, 4), dtype=np.uint16)
    img = DigitalImage(pixels=np.ones((4, 4), dtype=np.uint16) * 50, metadata={"bit_depth": 12})
    m = ErrorMapAnalyzer(ref).analyze(img).measurements
    assert m["mae"] == 50.0


def test_speckle_roughness_uniform_image_not_valid():
    pixels = np.ones((8, 8), dtype=np.uint16) * 2048
    image = DigitalImage(pixels=pixels, metadata={"bit_depth": 12})
    m = SpeckleRoughnessEstimator(coherence_length=1e-3, wavelength=532e-9).analyze(image).measurements
    assert m["valid"] is False


def test_speckle_roughness_high_contrast_gives_high_roughness():
    rng = np.random.default_rng(42)
    pixels = rng.exponential(scale=1.0, size=(32, 32)).astype(np.float32)
    image = DigitalImage(pixels=pixels, metadata={"bit_depth": 12})
    m = SpeckleRoughnessEstimator(coherence_length=1e-3, wavelength=532e-9).analyze(image).measurements
    assert m["speckle_contrast"] > 0.1
    assert m["estimated_roughness_rms"] > 0


def test_speckle_roughness_zero_coherence_not_valid():
    rng = np.random.default_rng(42)
    pixels = rng.exponential(scale=1.0, size=(16, 16)).astype(np.float32)
    image = DigitalImage(pixels=pixels, metadata={"bit_depth": 12})
    m = SpeckleRoughnessEstimator(coherence_length=0.0, wavelength=532e-9).analyze(image).measurements
    assert m["valid"] is False


def test_speckle_roughness_roi_selection():
    pixels = np.zeros((16, 16), dtype=np.float32)
    pixels[4:12, 4:12] = np.random.default_rng(42).exponential(scale=1.0, size=(8, 8))
    image = DigitalImage(pixels=pixels, metadata={"bit_depth": 12})
    full = SpeckleRoughnessEstimator(coherence_length=1e-3, wavelength=532e-9).analyze(image).measurements
    roi = SpeckleRoughnessEstimator(coherence_length=1e-3, wavelength=532e-9, roi=(4, 4, 8, 8)).analyze(image).measurements
    assert "speckle_contrast" in roi
    assert roi["estimated_roughness_rms"] > 0


def test_snr_single_image_returns_measurements():
    pixels = np.ones((8, 8), dtype=np.uint16) * 2048
    image = DigitalImage(pixels=pixels, metadata={"bit_depth": 12})
    m = SNRAnalyzer(method="single_image").analyze(image).measurements
    assert "snr_db" in m
    assert "signal_mean" in m


def test_snr_high_signal_gives_high_snr():
    rng = np.random.default_rng(42)
    pixels = (1000 + rng.normal(0, 10, size=(32, 32))).astype(np.uint16)
    image = DigitalImage(pixels=pixels, metadata={"bit_depth": 12})
    m = SNRAnalyzer(method="single_image").analyze(image).measurements
    assert m["snr_db"] > 20  # 1000/10 = 100 → 40 dB


def test_snr_flat_field_pair_returns_measurements():
    rng = np.random.default_rng(42)
    im1 = DigitalImage(pixels=rng.poisson(1000, size=(16, 16)).astype(np.uint16), metadata={"bit_depth": 12})
    im2 = DigitalImage(pixels=rng.poisson(1000, size=(16, 16)).astype(np.uint16), metadata={"bit_depth": 12})
    m = SNRAnalyzer(method="flat_field_pair", second_image=im2).analyze(im1).measurements
    assert "snr_db" in m


def test_snr_invalid_method_raises():
    import pytest
    with pytest.raises(ValueError, match="Unknown SNR method"):
        SNRAnalyzer(method="invalid")


def test_edge_detection_returns_counts():
    pixels = np.zeros((16, 16), dtype=np.uint16)
    pixels[:, 8:] = 4095
    image = DigitalImage(pixels=pixels, metadata={"bit_depth": 12})
    m = EdgeDetectionAnalyzer().analyze(image).measurements
    assert m["edge_count"] > 0
    assert 0 < m["edge_density"] < 1


def test_edge_detection_uniform_image_no_edges():
    pixels = np.ones((8, 8), dtype=np.uint16) * 2048
    image = DigitalImage(pixels=pixels, metadata={"bit_depth": 12})
    m = EdgeDetectionAnalyzer().analyze(image).measurements
    assert m["edge_count"] == 0


def test_fft_analyzer_returns_measurements():
    rng = np.random.default_rng(42)
    pixels = rng.random((16, 16)).astype(np.float32) * 4095
    image = DigitalImage(pixels=pixels, metadata={"bit_depth": 12})
    m = FFTAnalyzer().analyze(image).measurements
    assert "dc_fraction" in m
    assert "radial_profile" in m
    assert "peak_spatial_frequency" in m
    assert "power_spectrum_slope" in m


def test_fft_analyzer_dc_removal():
    pixels = np.ones((8, 8), dtype=np.uint16) * 2048
    image = DigitalImage(pixels=pixels, metadata={"bit_depth": 12})
    m = FFTAnalyzer(dc_removal=True).analyze(image).measurements
    assert m["dc_fraction"] < 0.5


def test_mtf_sinusoidal_returns_mtf():
    pixels = np.zeros((16, 16), dtype=np.uint16)
    x = np.arange(16)
    pattern = (np.sin(2 * np.pi * x / 4) + 1) * 2047
    pixels[:] = pattern.astype(np.uint16)
    image = DigitalImage(pixels=pixels, metadata={"bit_depth": 12})
    m = MTFAnalyzer(target_type="sinusoidal", lp_per_mm=10.0).analyze(image).measurements
    assert "mtf" in m
    assert "measured_modulation" in m


def test_mtf_sinusoidal_no_frequency_raises():
    import pytest
    pixels = np.ones((8, 8), dtype=np.uint16) * 2048
    image = DigitalImage(pixels=pixels, metadata={"bit_depth": 12})
    with pytest.raises(ValueError, match="lp_per_mm must be provided"):
        MTFAnalyzer(target_type="sinusoidal").analyze(image)
