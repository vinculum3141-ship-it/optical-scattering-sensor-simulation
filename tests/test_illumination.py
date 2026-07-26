"""Unit tests for the illumination package."""

import re

import numpy as np
import pytest

from optical_metrology.illumination import (
    BroadbandLamp,
    BroadbandSpectrum,
    FlatFieldSource,
    GaussianBeamProfile,
    LED,
    Laser,
    LightField,
    LightSource,
    MonochromaticSpectrum,
    SourceExtent,
    Sunlight,
    TemporalEnvelope,
    bright_field,
    dark_field,
    ring_light,
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


def test_converging_wavefront_center_points_forward():
    src = LightSource(wavelength=532e-9, wavefront="converging", focal_distance=1.0)
    lf = src.generate_light_field(shape=(5, 5), spacing=1.0)
    centre = lf.direction[2, 2]
    assert centre[2] > 0, "centre should point in +z toward focal point"
    assert np.allclose(centre, [0, 0, 1], atol=1e-6)


def test_converging_wavefront_corner_points_inward():
    src = LightSource(wavelength=532e-9, wavefront="converging", focal_distance=1.0)
    lf = src.generate_light_field(shape=(5, 5), spacing=1.0)
    corner = lf.direction[0, 0]
    assert corner[0] > 0, "top-left should point rightward toward centre focal point (+x)"
    assert corner[1] < 0, "top-left should point downward toward centre focal point (-y)"
    assert corner[2] > 0, "top-left should point forward (+z)"


def test_converging_wavefront_all_normalised():
    src = LightSource(wavelength=532e-9, wavefront="converging", focal_distance=2.0)
    lf = src.generate_light_field(shape=(8, 8), spacing=0.5)
    norms = np.linalg.norm(lf.direction, axis=2)
    assert np.allclose(norms, 1.0)


def test_converging_default_focal_distance():
    src = LightSource(wavelength=532e-9, wavefront="converging")
    lf = src.generate_light_field(shape=(5, 5), spacing=1.0)
    assert np.allclose(lf.direction[2, 2], [0, 0, 1], atol=1e-6)
    norms = np.linalg.norm(lf.direction, axis=2)
    assert np.allclose(norms, 1.0)


def test_gaussian_beam_waist_at_grid_no_scaling():
    src = LightSource(wavelength=1.0, waist_position=0.0,
                      beam_profile=GaussianBeamProfile(w0=2.0))
    lf = src.generate_light_field(shape=(5, 5), spacing=1.0)
    assert np.allclose(lf.intensity[2, 2], src.power)


def test_gaussian_beam_waist_off_grid_reduces_peak():
    src = LightSource(wavelength=1.0, waist_position=1.5,
                      beam_profile=GaussianBeamProfile(w0=1.0))
    lf = src.generate_light_field(shape=(3, 3), spacing=0.5)
    peak = lf.intensity[1, 1]
    assert peak < src.power, "beam should be wider away from waist, reducing peak"
    assert peak > 0, "peak should still be positive"


def test_flat_field_source_uses_uniform_profile():
    src = FlatFieldSource(power=2.0)
    lf = src.generate_light_field(shape=(8, 8))
    assert np.allclose(lf.intensity, 2.0, rtol=1e-10)


def test_flat_field_source_default_spectrum_is_broadband():
    src = FlatFieldSource()
    assert isinstance(src.spectrum, BroadbandSpectrum)


def test_flat_field_source_intensity_levels_validation():
    src = FlatFieldSource(power=1.0, intensity_levels=[0.0, 0.25, 0.5, 1.0])
    assert src.intensity_levels == [0.0, 0.25, 0.5, 1.0]

    with pytest.raises(ValueError, match=re.escape("intensity_levels must be in [0, 1]")):
        FlatFieldSource(power=1.0, intensity_levels=[-0.1, 0.5])

    with pytest.raises(ValueError, match=re.escape("intensity_levels must be in [0, 1]")):
        FlatFieldSource(power=1.0, intensity_levels=[0.5, 1.5])


def test_flat_field_intensity_sweep_returns_correct_number():
    levels = [0.0, 0.1, 0.5, 0.8, 1.0]
    src = FlatFieldSource(power=10.0, intensity_levels=levels)
    fields = src.generate_intensity_sweep(shape=(4, 4))
    assert len(fields) == len(levels)
    for field, level in zip(fields, levels):
        assert np.allclose(field.intensity, 10.0 * level, rtol=1e-10)
        assert np.allclose(field.power, 10.0 * level, rtol=1e-10)


def test_flat_field_intensity_sweep_preserves_direction():
    levels = [0.0, 0.5, 1.0]
    src = FlatFieldSource(power=1.0, intensity_levels=levels)
    fields = src.generate_intensity_sweep(shape=(4, 4))
    for f in fields:
        assert np.allclose(f.direction, np.array([0.0, 0.0, 1.0]))


def test_flat_field_source_default_intensity_level():
    src = FlatFieldSource(power=5.0)
    lf = src.generate_light_field(shape=(4, 4))
    assert np.allclose(lf.intensity, 5.0, rtol=1e-10)


def test_gaussian_beam_waist_farther_reduces_peak_more():
    src_near = LightSource(wavelength=1.0, waist_position=0.5,
                           beam_profile=GaussianBeamProfile(w0=1.0))
    src_far = LightSource(wavelength=1.0, waist_position=5.0,
                          beam_profile=GaussianBeamProfile(w0=1.0))
    lf_near = src_near.generate_light_field(shape=(3, 3), spacing=0.5)
    lf_far = src_far.generate_light_field(shape=(3, 3), spacing=0.5)
    assert lf_far.intensity[1, 1] < lf_near.intensity[1, 1], \
        "farther from waist should have lower peak intensity"


def test_temporal_envelope_gaussian_defaults():
    te = TemporalEnvelope(pulse_energy=1e-6, pulse_duration=1e-9, repetition_rate=1e6)
    assert te.shape == "gaussian"
    assert np.isclose(te.average_power, 1.0)
    assert te.peak_power > 0


def test_temporal_envelope_rectangular():
    te = TemporalEnvelope(shape="rectangular", pulse_energy=1e-6, pulse_duration=1e-9, repetition_rate=1e6)
    t = np.linspace(-2e-9, 2e-9, 5)
    env = te.envelope(t)
    assert env[0] == 0.0
    assert env[2] == 1.0


def test_temporal_envelope_invalid_shape_raises():
    with pytest.raises(ValueError, match="Unsupported pulse shape"):
        TemporalEnvelope(shape="sawtooth", pulse_energy=1e-6)


def test_temporal_envelope_peak_power_from_energy():
    te = TemporalEnvelope(pulse_energy=1e-6, pulse_duration=1e-9, repetition_rate=1e6)
    assert np.isclose(te.peak_power, 1e-6 / te.effective_pulse_width)


def test_temporal_envelope_energy_from_peak_power():
    te = TemporalEnvelope(peak_power=1e3, pulse_duration=1e-9, repetition_rate=1e6)
    assert np.isclose(te.pulse_energy, 1e3 * te.effective_pulse_width)


def test_source_extent_uniform_disk():
    se = SourceExtent(shape="uniform_disk", radius=1e-3)
    x = np.linspace(-2e-3, 2e-3, 5)
    y = np.linspace(-2e-3, 2e-3, 5)
    xx, yy = np.meshgrid(x, y)
    ap = se.aperture_function(xx, yy)
    assert ap[2, 2] == 1.0
    assert ap[0, 0] == 0.0


def test_source_extent_gaussian():
    se = SourceExtent(shape="gaussian", radius=1e-3)
    x = np.array([0.0, 1e-3])
    y = np.array([0.0, 0.0])
    xx, yy = np.meshgrid(x, y)
    ap = se.aperture_function(xx, yy)
    assert ap[0, 0] == 1.0
    assert ap[0, 1] == pytest.approx(np.exp(-0.5), rel=1e-6)


def test_source_extent_invalid_shape_raises():
    with pytest.raises(ValueError, match="Unsupported source shape"):
        SourceExtent(shape="triangle")


def test_bright_field_normal_incidence():
    src = bright_field(incidence_angle=0.0)
    assert np.allclose(src.propagation_direction, [0, 0, -1])


def test_dark_field_nonzero_incidence():
    src = dark_field(incidence_angle=0.785, azimuth=0.0)
    assert src.incidence_angle > 0.1


def test_ring_light_returns_tuple():
    rings = ring_light(n_segments=4)
    assert len(rings) == 4
    assert all(isinstance(s, LightSource) for s in rings)
