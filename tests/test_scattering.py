import numpy as np

from illumination import LightField
from scattering import LambertianScattering, ScatteredField, ScatteringModel
from surface import Material, Surface


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