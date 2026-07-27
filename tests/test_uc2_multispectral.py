"""Unit tests for UC2 Multi-Spectral Material Identification components."""

import numpy as np
import pytest

from optical_metrology.illumination import (
    ChannelConfig,
    FilterWheelSource,
    LightField,
    LightSource,
    MultiChannelLightField,
    MultiSpectralSource,
)
from optical_metrology.analysis.spectral import ReferenceSpectrum, SpectralAnalyzer
from optical_metrology.detector.cfa import CFAConfig, CFADetector
from optical_metrology.detector import CMOSDetector, DigitalImage

# ─── Multi-Channel Light Field ───────────────────────────────────────


def test_multichannel_lightfield_creation():
    lf1 = LightField(intensity=np.ones((4, 4)), direction=np.zeros((4, 4, 3)),
                     wavelength=450e-9, polarization=None)
    lf2 = LightField(intensity=np.ones((4, 4)), direction=np.zeros((4, 4, 3)),
                     wavelength=550e-9, polarization=None)
    mclf = MultiChannelLightField(fields=[lf1, lf2])
    assert mclf.n_channels == 2
    assert mclf.shape == (4, 4, 2)
    np.testing.assert_allclose(mclf.wavelengths, [450e-9, 550e-9])


def test_multichannel_lightfield_intensity_stack():
    lf1 = LightField(intensity=np.full((3, 3), 1.0), direction=np.zeros((3, 3, 3)),
                     wavelength=450e-9, polarization=None)
    lf2 = LightField(intensity=np.full((3, 3), 2.0), direction=np.zeros((3, 3, 3)),
                     wavelength=550e-9, polarization=None)
    mclf = MultiChannelLightField(fields=[lf1, lf2])
    stack = mclf.intensity_stack()
    assert stack.shape == (3, 3, 2)
    assert np.allclose(stack[:, :, 0], 1.0)
    assert np.allclose(stack[:, :, 1], 2.0)


def test_multichannel_lightfield_wavelength_indexing():
    lf1 = LightField(intensity=np.ones((2, 2)), direction=np.zeros((2, 2, 3)),
                     wavelength=450e-9, polarization=None)
    lf2 = LightField(intensity=np.ones((2, 2)), direction=np.zeros((2, 2, 3)),
                     wavelength=550e-9, polarization=None)
    mclf = MultiChannelLightField(fields=[lf1, lf2])
    assert mclf[0].wavelength == 450e-9
    assert mclf[1].wavelength == 550e-9
    # nearest wavelength lookup
    assert mclf[449e-9].wavelength == 450e-9
    assert mclf[600e-9].wavelength == 550e-9


def test_multichannel_lightfield_iteration():
    lf1 = LightField(intensity=np.ones((2, 2)), direction=np.zeros((2, 2, 3)),
                     wavelength=450e-9, polarization=None)
    lf2 = LightField(intensity=np.ones((2, 2)), direction=np.zeros((2, 2, 3)),
                     wavelength=550e-9, polarization=None)
    mclf = MultiChannelLightField(fields=[lf1, lf2])
    assert len(mclf) == 2
    wavelengths = [f.wavelength for f in mclf]
    assert wavelengths == [450e-9, 550e-9]


# ─── Multi-Spectral Source ───────────────────────────────────────────


def test_multispectral_source_generates_correct_channels():
    channels = [
        ChannelConfig(wavelength=450e-9, power=1.0, label="blue"),
        ChannelConfig(wavelength=550e-9, power=2.0, label="green"),
        ChannelConfig(wavelength=650e-9, power=1.5, label="red"),
    ]
    mss = MultiSpectralSource(channels)
    mclf = mss.generate_light_field(shape=(8, 8))
    assert mclf.n_channels == 3
    np.testing.assert_allclose(mclf.wavelengths, [450e-9, 550e-9, 650e-9])


def test_multispectral_source_power_per_channel():
    channels = [
        ChannelConfig(wavelength=450e-9, power=5.0),
        ChannelConfig(wavelength=550e-9, power=10.0),
    ]
    mss = MultiSpectralSource(channels)
    mclf = mss.generate_light_field(shape=(4, 4))
    stack = mclf.intensity_stack()
    # uniform profile → each pixel = channel power
    assert np.allclose(stack[:, :, 0], 5.0, rtol=1e-10)
    assert np.allclose(stack[:, :, 1], 10.0, rtol=1e-10)


def test_multispectral_source_with_template():
    template = LightSource(polarization="linear", divergence=0.1)
    channels = [
        ChannelConfig(wavelength=450e-9, power=1.0),
        ChannelConfig(wavelength=550e-9, power=1.0),
    ]
    mss = MultiSpectralSource(channels, source_template=template)
    mclf = mss.generate_light_field(shape=(4, 4))
    for f in mclf:
        assert f.polarization.kind == "linear"


# ─── Filter Wheel Source ─────────────────────────────────────────────


def test_filter_wheel_cycles_through_channels():
    channels = [
        ChannelConfig(wavelength=450e-9, power=1.0),
        ChannelConfig(wavelength=550e-9, power=1.0),
        ChannelConfig(wavelength=650e-9, power=1.0),
    ]
    fws = FilterWheelSource(channels)
    assert fws.n_channels == 3
    assert fws.current_channel.wavelength == 450e-9
    fws.next_channel()
    assert fws.current_channel.wavelength == 550e-9
    fws.next_channel()
    assert fws.current_channel.wavelength == 650e-9
    fws.next_channel()
    assert fws.current_channel.wavelength == 450e-9  # wraps


def test_filter_wheel_generate_light_field():
    channels = [
        ChannelConfig(wavelength=450e-9, power=2.0),
        ChannelConfig(wavelength=550e-9, power=3.0),
    ]
    fws = FilterWheelSource(channels)
    lf = fws.generate_light_field(shape=(4, 4))
    assert isinstance(lf, LightField)
    assert lf.wavelength == 450e-9
    assert np.allclose(lf.intensity, 2.0, rtol=1e-10)

    fws.next_channel()
    lf2 = fws.generate_light_field(shape=(4, 4))
    assert lf2.wavelength == 550e-9
    assert np.allclose(lf2.intensity, 3.0, rtol=1e-10)


def test_filter_wheel_generate_all():
    channels = [
        ChannelConfig(wavelength=450e-9, power=1.0),
        ChannelConfig(wavelength=550e-9, power=1.0),
    ]
    fws = FilterWheelSource(channels)
    mclf = fws.generate_all(shape=(4, 4))
    assert isinstance(mclf, MultiChannelLightField)
    assert mclf.n_channels == 2


def test_filter_wheel_reset():
    channels = [
        ChannelConfig(wavelength=450e-9, power=1.0),
        ChannelConfig(wavelength=550e-9, power=1.0),
    ]
    fws = FilterWheelSource(channels)
    fws.next_channel()
    assert fws.current_channel.wavelength == 550e-9
    fws.reset()
    assert fws.current_channel.wavelength == 450e-9


# ─── Spectral Analyzer ───────────────────────────────────────────────


def test_spectral_angle_identical_vectors():
    r = np.array([1.0, 2.0, 3.0])
    t = np.array([1.0, 2.0, 3.0])
    angle = SpectralAnalyzer.spectral_angle(r, t)
    assert angle == pytest.approx(0.0, abs=1e-10)


def test_spectral_angle_orthogonal_vectors():
    r = np.array([1.0, 0.0])
    t = np.array([0.0, 1.0])
    angle = SpectralAnalyzer.spectral_angle(r, t)
    assert angle == pytest.approx(np.pi / 2, abs=1e-10)


def test_spectral_angle_zero_vector():
    r = np.array([0.0, 0.0])
    t = np.array([1.0, 2.0])
    angle = SpectralAnalyzer.spectral_angle(r, t)
    assert angle == 0.0


def test_band_ratio():
    analyzer = SpectralAnalyzer()
    spectrum = np.array([2.0, 1.0, 4.0])
    ratio = analyzer.band_ratio(spectrum, 0, 1)
    assert ratio == 2.0
    ratio2 = analyzer.band_ratio(spectrum, 2, 1)
    assert ratio2 == 4.0


def test_band_ratio_zero_denominator():
    analyzer = SpectralAnalyzer()
    spectrum = np.array([2.0, 0.0])
    ratio = analyzer.band_ratio(spectrum, 0, 1)
    assert ratio == float("inf")


def test_spectral_angle_map_homogeneous():
    data = np.ones((4, 4, 3))
    ref = np.ones(3)
    sam_map = SpectralAnalyzer.spectral_angle_map(data, ref)
    assert sam_map.shape == (4, 4)
    assert np.allclose(sam_map, 0.0)


def test_classify_with_references():
    refs = [
        ReferenceSpectrum("A", np.array([1.0, 0.0, 0.0])),
        ReferenceSpectrum("B", np.array([0.0, 1.0, 0.0])),
    ]
    analyzer = SpectralAnalyzer(reference_library=refs)
    data = np.array([
        [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
        [[0.5, 0.5, 0.0], [1.0, 0.0, 0.0]],
    ])
    labels, confidence = analyzer.classify(data)
    assert labels.shape == (2, 2)
    assert labels[0, 0] == 0  # matches A
    assert labels[0, 1] == 1  # matches B
    assert np.all(confidence >= 0.0)
    assert np.all(confidence <= 1.0)


def test_classify_no_references():
    analyzer = SpectralAnalyzer()
    data = np.ones((4, 4, 3))
    labels, confidence = analyzer.classify(data)
    assert np.all(labels == -1)
    assert np.all(confidence == 0.0)


# ─── CFA ─────────────────────────────────────────────────────────────


def test_cfa_config_pattern():
    cfa = CFAConfig()
    assert cfa.channel_at(0, 0) == 0  # R
    assert cfa.channel_at(0, 1) == 1  # G
    assert cfa.channel_at(1, 0) == 1  # G
    assert cfa.channel_at(1, 1) == 2  # B


def test_cfa_mask_for_channel():
    cfa = CFAConfig()
    mask = cfa.mask_for_channel((4, 4), 0)  # R
    assert mask[0, 0]
    assert not mask[0, 1]
    assert not mask[1, 0]
    assert not mask[1, 1]


def test_cfa_detector_capture_raw():
    """Test CFA detector produces raw output with pattern."""
    det = CFADetector(cfa_config=CFAConfig(), demosaic=False, rng_seed=42)

    class FakeSensorField:
        irradiance = np.ones((4, 4))
        wavelength = 550e-9

    image = det.capture(FakeSensorField())
    assert image.pixels.shape == (4, 4)
    # Bayer RGGB: R at (0,0), G at (0,1), G at (1,0), B at (1,1)
    assert image.pixels[0, 0] > 0  # R channel
    assert image.pixels[1, 1] > 0  # B channel


def test_cfa_detector_demosaic():
    """Test CFA detector produces 3-channel output when demosaicing."""
    det = CFADetector(cfa_config=CFAConfig(), demosaic=True, rng_seed=42)

    class FakeSensorField:
        irradiance = np.ones((6, 6))
        wavelength = 550e-9

    image = det.capture(FakeSensorField())
    assert image.pixels.ndim == 3
    assert image.pixels.shape[2] == 3  # R, G, B


# ─── Integration-style: SpectralAnalyzer + DigitalImage ──────────────


def test_spectral_analyzer_analyze_image():
    refs = [
        ReferenceSpectrum("mat_A", np.array([1.0, 0.0])),
        ReferenceSpectrum("mat_B", np.array([0.0, 1.0])),
    ]
    analyzer = SpectralAnalyzer(reference_library=refs)

    pixels = np.zeros((4, 4, 2))
    pixels[:, :, 0] = 1.0  # strong in band 0 → mat_A
    pixels[:, :, 1] = 0.0
    image = DigitalImage(pixels=pixels, metadata={"bands": 2})

    report = analyzer.analyze(image)
    assert report.measurements["n_channels"] == 2
    assert "classification" in report.measurements
    labels = report.measurements["classification"]["labels"]
    assert np.all(labels == 0)
