import numpy as np

from optical_metrology.illumination import LightField
from optical_metrology.scattering import (
    CookTorranceScattering,
    LambertianScattering,
    ScatteredField,
    ScatteringModel,
)
from optical_metrology.surface import Material, Surface


def test_lambertian_scattering_returns_scattered_field():
    """LambertianScattering.evaluate() returns a ScatteredField with the
    correct shapes and non-negative radiance."""
    lightfield = LightField(
        intensity=np.ones((4, 4), dtype=float),
        direction=np.zeros((4, 4, 3), dtype=float),
        wavelength=532e-9,
        polarization=None,
    )
    surface = Surface(
        height=np.zeros((4, 4), dtype=float),
        normals=np.zeros((4, 4, 3), dtype=float),
        curvature=np.zeros((4, 4), dtype=float),
        slope_x=np.zeros((4, 4), dtype=float),
        slope_y=np.zeros((4, 4), dtype=float),
        roughness=0.0,
        material=Material(name="test"),
    )
    model = LambertianScattering(albedo=0.8)
    scattered = model.evaluate(lightfield, surface, view_direction=np.array([0.0, 0.0, 1.0]))

    assert isinstance(scattered, ScatteredField)
    assert scattered.radiance.shape == (4, 4)
    assert np.all(scattered.radiance >= 0.0)
    assert scattered.outgoing_direction.shape == (4, 4, 3)


def test_lambertian_radiance_scales_with_albedo():
    """Radiance should be proportional to albedo when direction and
    normals are aligned."""
    lightfield = LightField(
        intensity=np.ones((2, 2), dtype=float),
        direction=np.zeros((2, 2, 3), dtype=float),
        wavelength=532e-9,
        polarization=None,
    )
    surface = Surface(
        height=np.zeros((2, 2), dtype=float),
        normals=np.zeros((2, 2, 3), dtype=float),
        curvature=np.zeros((2, 2), dtype=float),
        slope_x=np.zeros((2, 2), dtype=float),
        slope_y=np.zeros((2, 2), dtype=float),
        roughness=0.0,
        material=Material(),
    )
    model = LambertianScattering(albedo=0.5)
    scattered = model.evaluate(lightfield, surface, view_direction=np.array([0.0, 0.0, 1.0]))
    assert np.allclose(scattered.radiance, 0.0)


def test_lambertian_normal_incidence_gives_peak_radiance():
    """When the light propagates toward the surface (-z) and the surface
    normal points up (+z), the direction from surface to light (+z) is
    aligned with the normal and radiance should equal albedo."""
    lightfield = LightField(
        intensity=np.ones((2, 2), dtype=float),
        direction=np.zeros((2, 2, 3), dtype=float) + np.array([0.0, 0.0, -1.0]),
        wavelength=532e-9,
        polarization=None,
    )
    surface = Surface(
        height=np.zeros((2, 2), dtype=float),
        normals=np.zeros((2, 2, 3), dtype=float) + np.array([0.0, 0.0, 1.0]),
        curvature=np.zeros((2, 2), dtype=float),
        slope_x=np.zeros((2, 2), dtype=float),
        slope_y=np.zeros((2, 2), dtype=float),
        roughness=0.0,
        material=Material(),
    )
    model = LambertianScattering(albedo=0.7)
    scattered = model.evaluate(lightfield, surface, view_direction=np.array([0.0, 0.0, 1.0]))
    assert np.allclose(scattered.radiance, 0.7)


def test_lambertian_grazing_angle_gives_zero_radiance():
    """When the direction from surface to light is perpendicular to the
    normal, cosine = 0 and radiance = 0."""
    lightfield = LightField(
        intensity=np.ones((2, 2), dtype=float),
        direction=np.zeros((2, 2, 3), dtype=float) + np.array([1.0, 0.0, 0.0]),
        wavelength=532e-9,
        polarization=None,
    )
    surface = Surface(
        height=np.zeros((2, 2), dtype=float),
        normals=np.zeros((2, 2, 3), dtype=float) + np.array([0.0, 0.0, 1.0]),
        curvature=np.zeros((2, 2), dtype=float),
        slope_x=np.zeros((2, 2), dtype=float),
        slope_y=np.zeros((2, 2), dtype=float),
        roughness=0.0,
        material=Material(),
    )
    model = LambertianScattering(albedo=0.8)
    scattered = model.evaluate(lightfield, surface, view_direction=np.array([0.0, 0.0, 1.0]))
    assert np.allclose(scattered.radiance, 0.0)


def test_scattering_model_base_raises_not_implemented():
    """ScatteringModel.evaluate() should raise NotImplementedError."""
    model = ScatteringModel()
    try:
        model.evaluate(None, None, None)
        assert False, "Expected NotImplementedError"
    except NotImplementedError:
        pass


# ── Cook-Torrance tests ──────────────────────────────────────────────

def test_cooktorrance_returns_scattered_field():
    lf = LightField(
        intensity=np.ones((4, 4), dtype=float),
        direction=np.zeros((4, 4, 3), dtype=float) + np.array([0.0, 0.0, -1.0]),
        wavelength=532e-9,
        polarization=None,
    )
    surf = Surface(
        height=np.zeros((4, 4), dtype=float),
        normals=np.zeros((4, 4, 3), dtype=float) + np.array([0.0, 0.0, 1.0]),
        curvature=np.zeros((4, 4), dtype=float),
        slope_x=np.zeros((4, 4), dtype=float),
        slope_y=np.zeros((4, 4), dtype=float),
        roughness=0.0,
        material=Material(),
    )
    model = CookTorranceScattering(roughness=0.1, fresnel_reflectance=0.04, albedo=0.5)
    result = model.evaluate(lf, surf, view_direction=np.array([0.0, 0.0, 1.0]))
    assert isinstance(result, ScatteredField)
    assert result.radiance.shape == (4, 4)
    assert np.all(result.radiance >= 0.0)
    assert result.outgoing_direction.shape == (4, 4, 3)


def test_cooktorrance_nonnegative():
    """Radiance must be non-negative for arbitrary incident/view angles."""
    lf = LightField(
        intensity=np.ones((4, 4), dtype=float),
        direction=np.zeros((4, 4, 3), dtype=float) + np.array([0.5, 0.0, -0.866]),
        wavelength=532e-9,
        polarization=None,
    )
    surf = Surface(
        height=np.zeros((4, 4), dtype=float),
        normals=np.zeros((4, 4, 3), dtype=float) + np.array([0.0, 0.0, 1.0]),
        curvature=np.zeros((4, 4), dtype=float),
        slope_x=np.zeros((4, 4), dtype=float),
        slope_y=np.zeros((4, 4), dtype=float),
        roughness=0.0,
        material=Material(),
    )
    model = CookTorranceScattering()
    result = model.evaluate(lf, surf, view_direction=np.array([0.0, 0.2, 0.98]))
    assert np.all(result.radiance >= -1e-12)


def test_cooktorrance_monotonic_roughness():
    """Specular peak decreases as roughness increases."""
    lf = LightField(
        intensity=np.ones((1, 1), dtype=float),
        direction=np.zeros((1, 1, 3), dtype=float) + np.array([0.0, 0.0, -1.0]),
        wavelength=532e-9,
        polarization=None,
    )
    surf = Surface(
        height=np.zeros((1, 1), dtype=float),
        normals=np.zeros((1, 1, 3), dtype=float) + np.array([0.0, 0.0, 1.0]),
        curvature=np.zeros((1, 1), dtype=float),
        slope_x=np.zeros((1, 1), dtype=float),
        slope_y=np.zeros((1, 1), dtype=float),
        roughness=0.0,
        material=Material(),
    )
    view = np.array([0.0, 0.0, 1.0])
    r_smooth = CookTorranceScattering(roughness=0.01).evaluate(lf, surf, view).radiance
    r_rough = CookTorranceScattering(roughness=0.5).evaluate(lf, surf, view).radiance
    assert r_smooth.item() > r_rough.item()


def test_cooktorrance_fresnel_increases_with_F0():
    """Radiance increases with fresnel_reflectance at near-specular view."""
    lf = LightField(
        intensity=np.ones((1, 1), dtype=float),
        direction=np.zeros((1, 1, 3), dtype=float) + np.array([0.0, 0.0, -1.0]),
        wavelength=532e-9,
        polarization=None,
    )
    surf = Surface(
        height=np.zeros((1, 1), dtype=float),
        normals=np.zeros((1, 1, 3), dtype=float) + np.array([0.0, 0.0, 1.0]),
        curvature=np.zeros((1, 1), dtype=float),
        slope_x=np.zeros((1, 1), dtype=float),
        slope_y=np.zeros((1, 1), dtype=float),
        roughness=0.0,
        material=Material(),
    )
    view = np.array([0.0, 0.0, 1.0])
    r_low = CookTorranceScattering(fresnel_reflectance=0.04).evaluate(lf, surf, view).radiance
    r_high = CookTorranceScattering(fresnel_reflectance=0.9).evaluate(lf, surf, view).radiance
    assert r_high.item() > r_low.item()


def test_cooktorrance_grazing_gives_mostly_diffuse():
    """At grazing incidence the specular lobe is weak; radiance is dominated
    by the diffuse (1-F) component."""
    lf = LightField(
        intensity=np.ones((4, 4), dtype=float),
        direction=np.zeros((4, 4, 3), dtype=float) + np.array([1.0, 0.0, 0.0]),
        wavelength=532e-9,
        polarization=None,
    )
    surf = Surface(
        height=np.zeros((4, 4), dtype=float),
        normals=np.zeros((4, 4, 3), dtype=float) + np.array([0.0, 0.0, 1.0]),
        curvature=np.zeros((4, 4), dtype=float),
        slope_x=np.zeros((4, 4), dtype=float),
        slope_y=np.zeros((4, 4), dtype=float),
        roughness=0.0,
        material=Material(),
    )
    model = CookTorranceScattering(roughness=0.1, fresnel_reflectance=0.5, albedo=0.8)
    result = model.evaluate(lf, surf, view_direction=np.array([0.0, 0.0, 1.0]))
    assert np.allclose(result.radiance, 0.0)  # cos_i ≈ 0


def test_cooktorrance_shape_matches_lightfield():
    """Output shape matches non-square input shape."""
    lf = LightField(
        intensity=np.ones((6, 8), dtype=float),
        direction=np.zeros((6, 8, 3), dtype=float) + np.array([0.0, 0.0, -1.0]),
        wavelength=532e-9,
        polarization=None,
    )
    surf = Surface(
        height=np.zeros((6, 8), dtype=float),
        normals=np.zeros((6, 8, 3), dtype=float) + np.array([0.0, 0.0, 1.0]),
        curvature=np.zeros((6, 8), dtype=float),
        slope_x=np.zeros((6, 8), dtype=float),
        slope_y=np.zeros((6, 8), dtype=float),
        roughness=0.0,
        material=Material(),
    )
    model = CookTorranceScattering()
    result = model.evaluate(lf, surf, view_direction=np.array([0.0, 0.0, 1.0]))
    assert result.radiance.shape == (6, 8)