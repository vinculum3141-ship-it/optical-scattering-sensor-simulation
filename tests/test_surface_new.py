import numpy as np

from optical_metrology.surface import (
    AnisotropicRoughSurface,
    FlatSurface,
    ImportedSurface,
    Material,
    RoughSurface,
    SellmeierCoefficients,
    SinusoidalSurface,
    Surface,
)
from optical_metrology.illumination import Laser
from optical_metrology.scattering import CookTorranceScattering


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


def test_rotation_matrix_x_properties():
    angle = np.pi / 4
    R = Surface.rotation_matrix_x(angle)
    assert R.shape == (3, 3)
    assert np.allclose(R @ R.T, np.eye(3))
    assert np.allclose(np.linalg.det(R), 1.0)


def test_rotation_matrix_y_properties():
    angle = np.pi / 6
    R = Surface.rotation_matrix_y(angle)
    assert np.allclose(R @ R.T, np.eye(3))
    assert np.allclose(np.linalg.det(R), 1.0)


def test_rotation_matrix_z_properties():
    angle = np.pi / 3
    R = Surface.rotation_matrix_z(angle)
    assert np.allclose(R @ R.T, np.eye(3))
    assert np.allclose(np.linalg.det(R), 1.0)


def test_transform_rotates_normals():
    surf = FlatSurface(shape=(8, 8), material=Material("test"))
    assert np.allclose(surf.normals, [0, 0, 1])

    angle = np.pi / 6
    surf.rotate_x(angle)
    expected_z = np.cos(angle)
    assert np.allclose(surf.normals[:, :, 2], expected_z, atol=1e-10)


def test_transform_identity_leaves_normals_unchanged():
    surf = RoughSurface(shape=(8, 8), sigma=4.0, amplitude=0.3, material=Material("test"))
    orig_normals = surf.normals.copy()
    surf.transform(np.eye(3))
    assert np.allclose(surf.normals, orig_normals)


def test_rotate_x_changes_normals():
    surf = FlatSurface(shape=(4, 4), material=Material("test"))
    surf.rotate_x(np.pi / 4)
    norms = np.linalg.norm(surf.normals, axis=2)
    assert np.allclose(norms, 1.0)
    assert np.allclose(surf.normals[:, :, 0], 0.0, atol=1e-10)
    assert np.allclose(surf.normals[:, :, 1], -np.sin(np.pi / 4), atol=1e-10)
    assert np.allclose(surf.normals[:, :, 2], np.cos(np.pi / 4), atol=1e-10)


def test_rotate_y_changes_normals():
    surf = FlatSurface(shape=(4, 4), material=Material("test"))
    surf.rotate_y(np.pi / 4)
    norms = np.linalg.norm(surf.normals, axis=2)
    assert np.allclose(norms, 1.0)
    assert np.allclose(surf.normals[:, :, 0], np.sin(np.pi / 4), atol=1e-10)
    assert np.allclose(surf.normals[:, :, 2], np.cos(np.pi / 4), atol=1e-10)


def test_chained_rotations_equivalent_to_single():
    surf1 = FlatSurface(shape=(4, 4), material=Material("test"))
    surf1.rotate_x(np.pi / 6).rotate_y(np.pi / 4)

    surf2 = FlatSurface(shape=(4, 4), material=Material("test"))
    Rx = Surface.rotation_matrix_x(np.pi / 6)
    Ry = Surface.rotation_matrix_y(np.pi / 4)
    surf2.transform(Ry @ Rx)

    assert np.allclose(surf1.normals, surf2.normals)


def test_material_constant_refractive_index():
    mat = Material("test", refractive_index=1.5)
    assert mat.refractive_index_at(500e-9) == 1.5
    assert mat.F0(500e-9) == ((1.0 - 1.5) / (1.0 + 1.5)) ** 2


def test_material_sellmeier_dispersion():
    """BK7 glass Sellmeier coefficients from refractiveindex.info."""
    bk7 = SellmeierCoefficients(B1=1.03961212, B2=0.231792344, B3=1.01046945,
                                C1=0.00600069867, C2=0.0200179144, C3=103.560653)
    mat = Material("BK7", sellmeier=bk7)
    n_500 = mat.refractive_index_at(500e-9)
    assert 1.50 < n_500 < 1.55, f"n(500nm) = {n_500}"
    n_633 = mat.refractive_index_at(633e-9)
    assert 1.50 < n_633 < 1.55, f"n(633nm) = {n_633}"
    assert n_500 > n_633, "BK7 should have higher n at shorter wavelength (normal dispersion)"


def test_material_F0_from_sellmeier():
    bk7 = SellmeierCoefficients(B1=1.03961212, B2=0.231792344, B3=1.01046945,
                                C1=0.00600069867, C2=0.0200179144, C3=103.560653)
    mat = Material("BK7", sellmeier=bk7)
    F0_633 = mat.F0(633e-9)
    expected = ((1.0 - mat.refractive_index_at(633e-9)) / (1.0 + mat.refractive_index_at(633e-9))) ** 2
    assert np.allclose(F0_633, expected)


def test_material_nk_table():
    """Gold n,k data (approx) at two wavelengths."""
    table = {500e-9: (0.62, 2.0), 600e-9: (0.33, 3.2)}
    mat = Material("gold", nk_table=table)
    n = mat.refractive_index_at(550e-9)
    k = mat.extinction_at(550e-9)
    assert 0.33 <= n <= 0.62
    assert 2.0 <= k <= 3.2


def test_material_F0_with_extinction():
    """Gold F0 at 633nm should be high (~0.8-0.9) due to large k."""
    table = {633e-9: (0.33, 3.2)}
    mat = Material("gold", nk_table=table)
    F0 = mat.F0(633e-9)
    assert 0.8 < F0 < 0.95, f"gold F0 @ 633nm = {F0}"


def test_material_refractive_index_fn():
    mat = Material("custom", refractive_index_fn=lambda wl: 2.0 + wl * 0)
    assert mat.refractive_index_at(400e-9) == 2.0
    assert mat.refractive_index_at(700e-9) == 2.0


def test_material_default_F0():
    mat = Material("default")
    expected = ((1.0 - 1.5) / (1.0 + 1.5)) ** 2
    assert mat.F0(550e-9) == expected


def test_cooktorrance_auto_F0_from_material():
    mat = Material("glass", refractive_index=1.5)
    surf = FlatSurface(shape=(4, 4), material=mat)
    lf = Laser(wavelength=550e-9).generate_light_field(shape=(4, 4))
    view = np.array([0.0, 0.0, 1.0])

    model_auto = CookTorranceScattering(fresnel_reflectance=None)
    model_explicit = CookTorranceScattering(fresnel_reflectance=0.04)

    result_auto = model_auto.evaluate(lf, surf, view)
    result_explicit = model_explicit.evaluate(lf, surf, view)

    assert np.allclose(result_auto.radiance, result_explicit.radiance, rtol=1e-6)
