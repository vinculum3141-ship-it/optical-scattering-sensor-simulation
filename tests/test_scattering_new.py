import numpy as np

from illumination import LightField
from scattering import (
    OrenNayarScattering,
    PhongScattering,
    ScatteredField,
    ScatteringModel,
)
from surface import Material, Surface


def _make_lightfield(shape=(4, 4), direction=(0, 0, -1)):
    return LightField(
        intensity=np.ones(shape, dtype=float),
        direction=np.zeros(shape + (3,), dtype=float) + np.array(direction),
        wavelength=532e-9,
        polarization=None,
    )


def _make_surface(shape=(4, 4), normal=(0, 0, 1)):
    return Surface(
        height=np.zeros(shape, dtype=float),
        normals=np.zeros(shape + (3,), dtype=float) + np.array(normal),
        curvature=np.zeros(shape, dtype=float),
        slope_x=np.zeros(shape, dtype=float),
        slope_y=np.zeros(shape, dtype=float),
        roughness=0.0,
        material=Material("test"),
    )


def test_phong_scattering_returns_scattered_field():
    lf = _make_lightfield()
    surf = _make_surface()
    model = PhongScattering(diffuse_albedo=0.6, specular_albedo=0.4, shininess=32)
    result = model.evaluate(lf, surf, view_direction=np.array([0.0, 0.0, 1.0]))
    assert isinstance(result, ScatteredField)
    assert result.radiance.shape == (4, 4)
    assert np.all(result.radiance >= 0.0)
    assert result.outgoing_direction.shape == (4, 4, 3)


def test_phong_combines_diffuse_and_specular():
    lf = _make_lightfield()
    surf = _make_surface()
    # With normal incidence and on-axis view, both diffuse and specular contribute
    model = PhongScattering(diffuse_albedo=0.5, specular_albedo=0.5, shininess=32)
    result = model.evaluate(lf, surf, view_direction=np.array([0.0, 0.0, 1.0]))
    # Diffuse = 0.5 * 1, specular ≈ 0.5 * 1 = 1.0 total
    assert np.allclose(result.radiance, 1.0, atol=1e-6)


def test_phong_grazing_gives_diffuse_only():
    lf = _make_lightfield(direction=(1.0, 0.0, 0.0))
    surf = _make_surface(normal=(0.0, 0.0, 1.0))
    model = PhongScattering(diffuse_albedo=0.5, specular_albedo=0.5, shininess=32)
    result = model.evaluate(lf, surf, view_direction=np.array([0.0, 0.0, 1.0]))
    # cos_i = 0, so both diffuse and specular = 0
    assert np.allclose(result.radiance, 0.0)


def test_orennayar_scattering_returns_scattered_field():
    lf = _make_lightfield()
    surf = _make_surface()
    model = OrenNayarScattering(albedo=0.8, roughness=0.5)
    result = model.evaluate(lf, surf, view_direction=np.array([0.0, 0.0, 1.0]))
    assert isinstance(result, ScatteredField)
    assert result.radiance.shape == (4, 4)
    assert np.all(result.radiance >= 0.0)
    assert result.outgoing_direction.shape == (4, 4, 3)


def test_orennayar_smooth_approaches_lambertian():
    lf = _make_lightfield()
    surf = _make_surface()
    # With roughness → 0, should approach Lambertian: radiance ≈ albedo * cos_i
    model = OrenNayarScattering(albedo=0.8, roughness=0.01)
    result = model.evaluate(lf, surf, view_direction=np.array([0.0, 0.0, 1.0]))
    # Lambertian reference: 0.8 * 1.0 = 0.8
    assert np.allclose(result.radiance, 0.8, atol=0.02)


def test_orennayar_base_class_enforced():
    model = ScatteringModel()
    try:
        model.evaluate(None, None, None)
        assert False, "Expected NotImplementedError"
    except NotImplementedError:
        pass
