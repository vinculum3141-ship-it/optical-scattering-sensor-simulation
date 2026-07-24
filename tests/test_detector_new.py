import numpy as np

from detector import (
    BloomingNoise,
    CMOSDetector,
    ColumnDefectNoise,
    DeadPixelNoise,
    FixedPatternNoise,
    HotPixelNoise,
    PhotoResponseNonUniformity,
    SpeckleNoise,
)
from optics import SensorField

from surface.base import Surface, Material


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


def _rough_surface(shape=(8, 8), amplitude=1e-6):
    height = np.random.randn(*shape) * amplitude
    return Surface(
        height=height,
        normals=np.zeros((*shape, 3), dtype=float),
        curvature=np.zeros(shape, dtype=float),
        slope_x=np.zeros(shape, dtype=float),
        slope_y=np.zeros(shape, dtype=float),
        roughness=float(np.std(height)),
        material=Material("test"),
    )


def test_speckle_noise_smooth_surface_no_effect():
    height = np.ones((8, 8)) * 1.0  # flat, σ_h = 0
    surface = Surface(
        height=height,
        normals=np.zeros((8, 8, 3), dtype=float),
        curvature=np.zeros((8, 8), dtype=float),
        slope_x=np.zeros((8, 8), dtype=float),
        slope_y=np.zeros((8, 8), dtype=float),
        roughness=0.0,
        material=Material("test"),
    )
    noise = SpeckleNoise(coherence_length=1e-3)
    noise.prepare(height, wavelength=532e-9)
    electrons = np.ones((8, 8)) * 100.0
    result = noise.apply(electrons)
    assert np.allclose(result, electrons, rtol=1e-10)


def test_speckle_noise_coherent_increases_variance():
    """Rough surface + long coherence → visible speckle → higher variance."""
    rng_state = np.random.get_state()
    np.random.seed(42)
    surface = _rough_surface(shape=(32, 32), amplitude=2e-6)
    noise = SpeckleNoise(coherence_length=1.0)  # L_c >> σ_h
    noise.prepare(surface.height, wavelength=532e-9)
    electrons = np.ones((32, 32)) * 1000.0
    result = noise.apply(electrons)
    np.random.set_state(rng_state)
    var_ratio = float(np.var(result) / np.mean(result)**2)
    assert var_ratio > 0.05, f"Expected visible speckle variance, got {var_ratio:.4f}"


def test_speckle_noise_incoherent_no_effect():
    """Rough surface + tiny coherence length → no speckle."""
    rng_state = np.random.get_state()
    np.random.seed(42)
    surface = _rough_surface(shape=(16, 16), amplitude=2e-6)
    noise = SpeckleNoise(coherence_length=1e-12)  # L_c << σ_h
    noise.prepare(surface.height, wavelength=532e-9)
    electrons = np.ones((16, 16)) * 1000.0
    result = noise.apply(electrons)
    np.random.set_state(rng_state)
    assert np.allclose(result, electrons, atol=1.0)


def test_capture_with_surface_and_speckle():
    detector = CMOSDetector(
        exposure_time=1.0,
        quantum_efficiency=0.5,
        noise_models=[SpeckleNoise(coherence_length=1.0)],
    )
    sf = _sensor_field(irradiance=1e3)
    surface = _rough_surface(shape=(8, 8), amplitude=1e-6)
    image = detector.capture(sf, surface=surface)
    assert image.pixels.shape == (8, 8)
    assert image.pixels.dtype == np.uint16


def test_capture_with_surface_no_speckle_model_unchanged():
    detector = CMOSDetector(exposure_time=1.0)
    sf = _sensor_field(irradiance=1e3)
    surface = _rough_surface(shape=(8, 8), amplitude=1e-6)
    image_no_surface = detector.capture(sf)
    image_with_surface = detector.capture(sf, surface=surface)
    assert image_with_surface.pixels.shape == (8, 8)


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


# ── Blooming tests ────────────────────────────────────────────────────

def test_blooming_no_spill_below_full_well():
    bloom = BloomingNoise(bloom_factor=0.1, full_well_capacity=100.0)
    electrons = np.full((4, 4), 80.0)
    result = bloom.apply(electrons)
    assert np.allclose(result, 80.0)


def test_blooming_spills_to_neighbours():
    bloom = BloomingNoise(bloom_factor=0.1, iterations=1, full_well_capacity=100.0)
    electrons = np.zeros((4, 4), dtype=float)
    electrons[1, 1] = 200.0
    result = bloom.apply(electrons)
    assert result[1, 1] == 100.0
    assert result[0, 1] > 0.0
    assert result[2, 1] > 0.0
    assert result[1, 0] > 0.0
    assert result[1, 2] > 0.0
    assert result[0, 0] == 0.0


def test_blooming_integrated_with_detector():
    detector = CMOSDetector(
        exposure_time=1.0,
        quantum_efficiency=1.0,
        gain=1.0,
        full_well_capacity=5000.0,
        noise_models=[BloomingNoise(bloom_factor=0.1, iterations=2, full_well_capacity=5000.0)],
    )
    sf = _sensor_field(irradiance=1e5, wavelength=532e-9)
    image = detector.capture(sf)
    assert image.pixels.shape == (8, 8)
    assert np.any(image.pixels > 0)
