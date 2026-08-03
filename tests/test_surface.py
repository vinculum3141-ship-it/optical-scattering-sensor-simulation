import numpy as np

from optical_metrology.surface import FlatSurface, Material, ParticleSurface, RoughSurface, ScratchedSurface, Surface


def test_flat_surface_has_zero_height_and_zero_derived_geometry():
    material = Material(name="silicon")
    surface = FlatSurface(shape=(16, 16), material=material)

    assert isinstance(surface, Surface)
    assert surface.height.shape == (16, 16)
    assert np.allclose(surface.height, 0.0)
    assert surface.normals.shape == (16, 16, 3)
    assert np.allclose(surface.slope_x, 0.0)
    assert np.allclose(surface.slope_y, 0.0)
    assert np.allclose(surface.curvature, 0.0)
    assert surface.roughness == 0.0
    assert surface.material.name == "silicon"


def test_rough_surface_has_nonzero_roughness_and_shape():
    surface = RoughSurface(shape=(32, 32), sigma=4.0, amplitude=0.5)

    assert surface.height.shape == (32, 32)
    assert surface.roughness > 0.0
    assert np.any(np.abs(surface.height) > 0.0)


def test_scratched_surface_creates_a_visible_groove():
    surface = ScratchedSurface(shape=(32, 32), scratch_depth=0.3, scratch_width=3)

    assert np.min(surface.height) < 0.0
    assert np.max(surface.height) >= 0.0


def test_particle_surface_creates_localized_bumps():
    surface = ParticleSurface(shape=(32, 32), particle_count=4, amplitude=0.8, sigma=2.0)

    assert np.max(surface.height) > 0.0
    assert np.ptp(surface.height) > 0.0
