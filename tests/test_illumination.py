"""Unit tests for the illumination package."""

import numpy as np

from illumination import (
    BroadbandLamp,
    LED,
    Laser,
    LightField,
    LightSource,
    MonochromaticSpectrum,
    Sunlight,
    GaussianBeamProfile,
)


def test_laser_defaults_and_spectrum():
    laser = Laser(wavelength=532e-9, power=5e-3)

    assert laser.wavelength == 532e-9
    assert laser.power == 5e-3
    assert laser.polarization.kind == "unpolarized"

    spectrum = laser.spectral_distribution()
    assert isinstance(spectrum, MonochromaticSpectrum)
    assert spectrum.wavelength == 532e-9


def test_lightfield_generation_uses_beam_profile():
    laser = Laser(wavelength=532e-9, beam_profile=GaussianBeamProfile(w0=1.0))
    field = laser.generate_light_field(shape=(3, 3), spacing=1.0)

    assert isinstance(field, LightField)
    assert field.intensity.shape == (3, 3)
    assert field.direction.shape == (3, 3, 3)
    assert field.wavelength == 532e-9
    assert np.allclose(field.intensity[1, 1], 1.0)


def test_source_direction_is_normalized():
    direction = np.array([0.2, 0.1, -0.97], dtype=float)
    source = LightSource(wavelength=450e-9, propagation_direction=direction)

    assert np.allclose(source.propagation_direction, direction / np.linalg.norm(direction))


def test_subclasses_expose_expected_spectral_models():
    led = LED(peak_wavelength=530e-9, width=25e-9)
    sunlight = Sunlight(temperature=5778.0)
    lamp = BroadbandLamp(wavelength_range=(400e-9, 700e-9))

    assert led.spectral_distribution().kind == "gaussian"
    assert sunlight.spectral_distribution().kind == "blackbody"
    assert lamp.spectral_distribution().kind == "broadband"


def test_planar_wavefront_uniform_direction():
    src = LightSource(wavelength=532e-9, propagation_direction=[0, 0, -1])
    lf = src.generate_light_field(shape=(8, 8), spacing=0.5)
    assert lf.direction.shape == (8, 8, 3)
    assert np.allclose(lf.direction, [0, 0, -1])


def test_spherical_wavefront_center_direction():
    src = LightSource(wavelength=532e-9, wavefront="spherical", origin=[0, 0, 1.0])
    lf = src.generate_light_field(shape=(5, 5), spacing=1.0)
    assert np.allclose(lf.direction[2, 2], [0, 0, -1], atol=1e-10)


def test_spherical_wavefront_corner_has_transverse_components():
    src = LightSource(wavelength=532e-9, wavefront="spherical", origin=[0, 0, 1.0])
    lf = src.generate_light_field(shape=(5, 5), spacing=1.0)
    corner = lf.direction[0, 0]
    assert abs(corner[0]) > 0.1
    assert abs(corner[1]) > 0.1
    assert corner[2] < 0  # pointing toward grid


def test_spherical_wavefront_all_normalised():
    src = LightSource(wavelength=532e-9, wavefront="spherical", origin=[0, 0, 1.0])
    lf = src.generate_light_field(shape=(8, 8), spacing=0.5)
    norms = np.linalg.norm(lf.direction, axis=2)
    assert np.allclose(norms, 1.0)


def test_spherical_wavefront_asymmetric_origin():
    src = LightSource(wavelength=532e-9, wavefront="spherical", origin=[2.0, 0, 1.0])
    lf = src.generate_light_field(shape=(3, 3), spacing=1.0)
    assert lf.direction[1, 0, 0] < lf.direction[1, 2, 0], \
        "left pixels should point more leftward (more negative x)"


def test_wavefront_default_is_planar():
    src = LightSource(wavelength=532e-9)
    assert src.wavefront == "planar"


def test_invalid_wavefront_raises():
    import pytest
    with pytest.raises(ValueError, match="Unsupported wavefront"):
        LightSource(wavelength=532e-9, wavefront="diverging")
