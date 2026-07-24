import numpy as np

from detector import (
    CMOSDetector,
    ColumnDefectNoise,
    DeadPixelNoise,
    FixedPatternNoise,
    HotPixelNoise,
    PhotoResponseNonUniformity,
)
from optics import SensorField


def _sensor_field(shape=(8, 8), irradiance=1e3, wavelength=532e-9):
    return SensorField(
        irradiance=np.ones(shape, dtype=float) * irradiance,
        wavelength=wavelength,
        polarization=None,
        optical_path_length=0.1,
    )


def test_fixed_pattern_noise_adds_offset():
    detector = CMOSDetector(
        exposure_time=0.1, noise_models=[FixedPatternNoise(pattern=10.0)],
    )
    sf = _sensor_field()
    image = detector.capture(sf)
    assert image.pixels.shape == (8, 8)
    assert image.pixels.dtype == np.uint16


def test_fixed_pattern_noise_with_array():
    pattern = np.ones((8, 8)) * 5.0
    detector = CMOSDetector(
        exposure_time=0.1, noise_models=[FixedPatternNoise(pattern=pattern)],
    )
    sf = _sensor_field()
    image = detector.capture(sf)
    assert image.pixels.shape == (8, 8)


def test_hot_pixel_noise_adds_bright_spots():
    detector = CMOSDetector(
        exposure_time=0.1,
        noise_models=[HotPixelNoise(density=0.5, hot_current=100.0, exposure_time=0.1)],
    )
    sf = _sensor_field()
    image = detector.capture(sf)
    assert image.pixels.shape == (8, 8)


def test_column_defect_noise_affects_column():
    detector = CMOSDetector(
        exposure_time=0.1,
        noise_models=[ColumnDefectNoise(column_index=0, scale_factor=0.0)],
    )
    sf = _sensor_field()
    image = detector.capture(sf)
    # Column 0 should be all zeros (scale_factor=0)
    assert np.all(image.pixels[:, 0] == 0)


def test_photo_response_non_uniformity():
    detector = CMOSDetector(
        exposure_time=0.1,
        noise_models=[PhotoResponseNonUniformity(magnitude=0.1)],
    )
    sf = _sensor_field()
    image = detector.capture(sf)
    assert image.pixels.shape == (8, 8)


def test_dead_pixel_noise():
    detector = CMOSDetector(
        exposure_time=0.1,
        noise_models=[DeadPixelNoise(density=0.2, stuck_value=0.0)],
    )
    sf = _sensor_field()
    image = detector.capture(sf)
    assert image.pixels.shape == (8, 8)
    # At least some pixels should be zero (stuck_value)
    assert np.any(image.pixels == 0)


def test_multiple_noise_models_chain():
    noise_models = [
        FixedPatternNoise(pattern=5.0),
        PhotoResponseNonUniformity(magnitude=0.05),
    ]
    detector = CMOSDetector(
        exposure_time=0.1, noise_models=noise_models,
    )
    sf = _sensor_field()
    image = detector.capture(sf)
    assert image.pixels.shape == (8, 8)


def test_noise_model_raises_on_shape_mismatch():
    pattern = np.ones((4, 4)) * 5.0
    noise = FixedPatternNoise(pattern=pattern)
    detector = CMOSDetector(
        exposure_time=0.1, noise_models=[noise],
    )
    sf = _sensor_field(shape=(8, 8))
    try:
        detector.capture(sf)
        assert False, "Expected ValueError"
    except ValueError:
        pass
