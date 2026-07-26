import numpy as np

from optical_metrology.surface import (
    AnisotropicRoughSurface,
    FlatSurface,
    ImportedSurface,
    Material,
    SinusoidalSurface,
    Surface,
)


def test_sinusoidal_surface_has_periodic_structure():
    surface = SinusoidalSurface(shape=(32, 32), period=16.0, amplitude=0.5)
    assert isinstance(surface, Surface)
    assert surface.height.shape == (32, 32)
    assert abs(surface.height.max()) > 0.0
    assert abs(surface.height.min()) > 0.0
    assert abs(surface.height.max() - surface.height.min()) > 0.0


def test_sinusoidal_surface_roughness_zero_mean():
    surface = SinusoidalSurface(shape=(32, 32), period=16.0, amplitude=0.5)
    assert abs(float(np.mean(surface.height))) < 1e-10


def test_sinusoidal_surface_amplitude_matches():
    surface = SinusoidalSurface(shape=(16, 16), period=8.0, amplitude=0.3)
    assert abs(surface.height.max()) <= 0.3 + 1e-10
    assert abs(surface.height.min()) <= 0.3 + 1e-10


def test_anisotropic_rough_surface_has_nonzero_roughness():
    surface = AnisotropicRoughSurface(
        shape=(32, 32), sigma_x=8.0, sigma_y=2.0, amplitude=0.5,
    )
    assert isinstance(surface, Surface)
    assert surface.height.shape == (32, 32)
    assert surface.roughness > 0.0


def test_imported_surface_from_array():
    heights = np.array([[0.0, 0.5, 0.0], [0.5, 1.0, 0.5], [0.0, 0.5, 0.0]])
    surf = ImportedSurface(heights)
    assert surf.height.shape == (3, 3)
    assert np.allclose(surf.height, heights)
    assert surf.roughness > 0.0
    assert surf.normals.shape == (3, 3, 3)


def test_imported_surface_rejects_non_2d():
    import pytest
    with pytest.raises(ValueError, match="Height map must be 2D"):
        ImportedSurface(np.array([1.0, 2.0, 3.0]))


def test_anisotropic_rough_surface_material():
    material = Material("aluminium")
    surface = AnisotropicRoughSurface(
        shape=(16, 16), sigma_x=4.0, sigma_y=1.0, amplitude=0.3,
        material=material,
    )
    assert surface.material.name == "aluminium"


def test_flat_surface_phase_screen_zero():
    surface = FlatSurface(shape=(16, 16))
    phase = surface.phase_screen(wavelength=532e-9)
    assert phase.shape == (16, 16)
    assert np.all(phase == 0.0)


def test_phase_screen_formula():
    surface = SinusoidalSurface(shape=(32, 32), period=16.0, amplitude=0.5)
    phase = surface.phase_screen(wavelength=532e-9)
    expected = 4.0 * np.pi * surface.height / 532e-9
    assert np.allclose(phase, expected)


def test_phase_screen_scales_with_inverse_wavelength():
    surface = SinusoidalSurface(shape=(16, 16), period=8.0, amplitude=0.3)
    phase_red = surface.phase_screen(wavelength=650e-9)
    phase_blue = surface.phase_screen(wavelength=450e-9)
    ratio = phase_blue / phase_red
    assert np.allclose(ratio, 650.0 / 450.0, rtol=1e-10)
