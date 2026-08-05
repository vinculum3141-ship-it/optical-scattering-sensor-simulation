import numpy as np

from optical_metrology.illumination import LightField
from optical_metrology.scattering import (
    BeckmannScattering,
    GGXScattering,
    OrenNayarScattering,
    PhongScattering,
    ScatteredField,
    ScatteringModel,
)
from optical_metrology.surface import Material, Surface


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


# ── Beckmann tests ────────────────────────────────────────────────────

def test_beckmann_scattering_returns_scattered_field():
    lf = _make_lightfield()
    surf = _make_surface()
    model = BeckmannScattering(roughness=0.1, fresnel_reflectance=0.04)
    result = model.evaluate(lf, surf, view_direction=np.array([0.0, 0.0, 1.0]))
    assert isinstance(result, ScatteredField)
    assert result.radiance.shape == (4, 4)
    assert np.all(result.radiance >= 0.0)
    assert result.outgoing_direction.shape == (4, 4, 3)


def test_beckmann_specular_peak_decreases_with_roughness():
    lf = _make_lightfield(shape=(1, 1))
    surf = _make_surface(shape=(1, 1))
    view = np.array([0.0, 0.0, 1.0])
    r_smooth = BeckmannScattering(roughness=0.01).evaluate(lf, surf, view).radiance
    r_rough = BeckmannScattering(roughness=0.5).evaluate(lf, surf, view).radiance
    assert r_smooth.item() > r_rough.item()


def test_beckmann_fresnel_increases_with_F0():
    lf = _make_lightfield(shape=(1, 1))
    surf = _make_surface(shape=(1, 1))
    view = np.array([0.0, 0.0, 1.0])
    r_low = BeckmannScattering(fresnel_reflectance=0.04).evaluate(lf, surf, view).radiance
    r_high = BeckmannScattering(fresnel_reflectance=0.9).evaluate(lf, surf, view).radiance
    assert r_high.item() > r_low.item()


def test_beckmann_grazing_gives_zero_radiance():
    lf = _make_lightfield(direction=(1.0, 0.0, 0.0))
    surf = _make_surface(normal=(0.0, 0.0, 1.0))
    model = BeckmannScattering(roughness=0.1)
    result = model.evaluate(lf, surf, view_direction=np.array([0.0, 0.0, 1.0]))
    assert np.allclose(result.radiance, 0.0)


# ── GGX tests ─────────────────────────────────────────────────────────

def test_ggx_scattering_returns_scattered_field():
    lf = _make_lightfield()
    surf = _make_surface()
    model = GGXScattering(roughness=0.1, fresnel_reflectance=0.04)
    result = model.evaluate(lf, surf, view_direction=np.array([0.0, 0.0, 1.0]))
    assert isinstance(result, ScatteredField)
    assert result.radiance.shape == (4, 4)
    assert np.all(result.radiance >= 0.0)
    assert result.outgoing_direction.shape == (4, 4, 3)


def test_ggx_specular_peak_decreases_with_roughness():
    lf = _make_lightfield(shape=(1, 1))
    surf = _make_surface(shape=(1, 1))
    view = np.array([0.0, 0.0, 1.0])
    r_smooth = GGXScattering(roughness=0.01).evaluate(lf, surf, view).radiance
    r_rough = GGXScattering(roughness=0.5).evaluate(lf, surf, view).radiance
    assert r_smooth.item() > r_rough.item()


def test_ggx_fresnel_increases_with_F0():
    lf = _make_lightfield(shape=(1, 1))
    surf = _make_surface(shape=(1, 1))
    view = np.array([0.0, 0.0, 1.0])
    r_low = GGXScattering(fresnel_reflectance=0.04).evaluate(lf, surf, view).radiance
    r_high = GGXScattering(fresnel_reflectance=0.9).evaluate(lf, surf, view).radiance
    assert r_high.item() > r_low.item()


def test_ggx_grazing_gives_zero_radiance():
    lf = _make_lightfield(direction=(1.0, 0.0, 0.0))
    surf = _make_surface(normal=(0.0, 0.0, 1.0))
    model = GGXScattering(roughness=0.1)
    result = model.evaluate(lf, surf, view_direction=np.array([0.0, 0.0, 1.0]))
    assert np.allclose(result.radiance, 0.0)
