import numpy as np
import pytest

from optical_metrology.optics import (
    AiryPSF,
    OpticalPropagator,
    OpticalSystem,
    SensorField,
    Wavefront,
    ZernikePolynomials,
    ZernikePSF,
    defocus_coefficient,
)
from optical_metrology.optics.airy import _j1


class _MockScatteredField:
    def __init__(self, radiance, polarization=None):
        self.radiance = radiance
        self.polarization = polarization or "unpolarized"


class _MockImage:
    def __init__(self, pixels):
        self.pixels = pixels


def test_airy_psf_kernel_normalised():
    psf = AiryPSF(wavelength=532e-9, numerical_aperture=0.25, pixel_size=5e-6)
    kernel = psf.kernel(size=31)
    assert kernel.shape == (31, 31)
    assert np.allclose(kernel.sum(), 1.0)


def test_airy_psf_centre_peak():
    psf = AiryPSF()
    kernel = psf.kernel(size=31)
    centre = kernel[15, 15]
    # Centre should be the brightest point
    assert centre == kernel.max()


def test_airy_psf_symmetric():
    psf = AiryPSF()
    kernel = psf.kernel(size=21)
    assert np.allclose(kernel, kernel.T, atol=1e-10)
    assert np.allclose(kernel, np.flip(kernel), atol=1e-10)


def test_airy_psf_odd_size_auto():
    psf = AiryPSF()
    kernel = psf.kernel(size=20)
    assert kernel.shape[0] % 2 == 1


def test_airy_psf_invalid_size():
    psf = AiryPSF()
    try:
        psf.kernel(size=0)
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_zernike_polynomial_piston():
    rho = np.array([[0.0, 0.5], [0.8, 1.0]])
    theta = np.zeros_like(rho)
    Z = ZernikePolynomials.evaluate(1, rho, theta)
    assert np.allclose(Z, np.ones_like(rho))


def test_zernike_polynomial_defocus_centre():
    rho = np.linspace(0, 1, 10)
    theta = np.zeros_like(rho)
    Z = ZernikePolynomials.evaluate(5, rho, theta)
    assert np.allclose(Z[0], -np.sqrt(3)), "defocus at centre (rho=0)"
    assert np.allclose(Z[-1], np.sqrt(3)), "defocus at edge (rho=1)"


def test_zernike_polynomial_tilt():
    rho = np.array([[0.0, 0.5], [0.8, 1.0]])
    theta = np.zeros_like(rho)  # along +x
    Z = ZernikePolynomials.evaluate(3, rho, theta)
    # tilt x varies linearly with rho
    assert np.allclose(Z[0, 0], 0.0)
    assert Z[0, 1] > 0
    assert Z[1, 0] > Z[0, 1]


def test_wavefront_map_builds_from_coefficients():
    wf = Wavefront({1: 1.0, 5: 0.5})
    rho = np.array([[0.0, 0.5], [0.8, 1.0]])
    theta = np.zeros_like(rho)
    m = wf.map(rho, theta)
    assert m.shape == (2, 2)
    assert not np.allclose(m, 0.0)


def test_zernike_psf_kernel_normalised():
    wf = Wavefront({})
    psf = ZernikePSF(wavefront=wf, wavelength=532e-9, numerical_aperture=0.25)
    kernel = psf.kernel(size=31)
    assert kernel.shape == (31, 31)
    assert np.allclose(kernel.sum(), 1.0)


def test_zernike_psf_centre_peak():
    wf = Wavefront({})
    psf = ZernikePSF(wavefront=wf, wavelength=532e-9, numerical_aperture=0.25)
    kernel = psf.kernel(size=31)
    centre = kernel[15, 15]
    assert centre == kernel.max()


def test_zernike_psf_aberration_broadens():
    wf_ideal = Wavefront({})
    wf_aberr = Wavefront({5: 0.25e-6})  # defocus, ~0.5 waves at 532 nm
    ideal = ZernikePSF(wf_ideal, wavelength=532e-9, numerical_aperture=0.25)
    aberr = ZernikePSF(wf_aberr, wavelength=532e-9, numerical_aperture=0.25)
    k_ideal = ideal.kernel(size=31)
    k_aberr = aberr.kernel(size=31)
    assert k_ideal[15, 15] > k_aberr[15, 15], \
        "aberration should reduce peak intensity"


def test_zernike_polynomial_astigmatism():
    """Astigmatism (Noll j=6, cos 2θ) changes sign between the x and y
    axes; j=4 (sin 2θ) vanishes along both axes."""
    rho = np.array([0.5, 0.8])
    z6x = ZernikePolynomials.evaluate(6, rho, np.zeros_like(rho))
    z6y = ZernikePolynomials.evaluate(6, rho, np.full_like(rho, np.pi / 2.0))
    assert np.allclose(z6x, np.sqrt(6) * rho ** 2)
    assert np.allclose(z6y, -np.sqrt(6) * rho ** 2)
    assert np.allclose(ZernikePolynomials.evaluate(4, rho, np.zeros_like(rho)), 0.0)


def test_zernike_psf_astigmatism_broadens():
    """Astigmatism (Noll j=6) reduces the peak and spreads the PSF."""
    kw = dict(wavelength=532e-9, numerical_aperture=0.5, pixel_size=0.1e-6)
    ideal = ZernikePSF(Wavefront({}), **kw).kernel(63)
    astig = ZernikePSF(Wavefront({6: 0.1e-6}), **kw).kernel(63)
    c = 63 // 2
    y, x = np.mgrid[-c:c + 1, -c:c + 1]
    second_moment = lambda k: (k * (x ** 2 + y ** 2)).sum()
    assert astig[c, c] < ideal[c, c]
    assert second_moment(astig) > second_moment(ideal)


def test_zernike_psf_matches_airy_when_aberration_free():
    """The aberration-free ZernikePSF reproduces the Airy disk at the same
    physical parameters (the diffraction scale is tied to NA/pixel_size)."""
    kw = dict(wavelength=532e-9, numerical_aperture=0.5, pixel_size=0.1e-6)
    zern = ZernikePSF(Wavefront({}), **kw).kernel(63)
    airy = AiryPSF(**kw).kernel(63)
    corr = np.corrcoef(airy.ravel(), zern.ravel())[0, 1]
    assert corr > 0.999
    assert np.isclose(zern[31, 31] / airy[31, 31], 1.0, rtol=0.05)


def test_zernike_psf_diffraction_scale_tracks_pixel_size():
    """Smaller pixels give a wider diffraction spot (more pixels across
    the Airy disk) — the PSF scale follows 1/(NA * pixel_size)."""
    c = 63 // 2
    y, x = np.mgrid[-c:c + 1, -c:c + 1]
    second_moment = lambda k: (k * (x ** 2 + y ** 2)).sum()
    wide = ZernikePSF(Wavefront({}), wavelength=532e-9, numerical_aperture=0.5, pixel_size=0.1e-6).kernel(63)
    narrow = ZernikePSF(Wavefront({}), wavelength=532e-9, numerical_aperture=0.5, pixel_size=0.2e-6).kernel(63)
    assert second_moment(wide) > second_moment(narrow)


def test_j1_accuracy():
    """_j1 matches tabulated values of J1 to ~1e-8 across series and
    asymptotic regimes (previously the asymptotic form was used down to
    |x| = 0.5, giving errors up to ~0.6)."""
    x = np.array([0.0, 1.0, 3.0, 8.0, 20.0])
    ref = np.array([0.0, 0.44005058574493355, 0.33905895852593646,
                    0.23463634685391462, 0.06683312417585005])
    assert np.allclose(_j1(x), ref, atol=1e-8)


def test_propagator_accepts_diffraction_psf_models():
    """OpticalPropagator works with PSF models that do not expose
    ``sigma`` (AiryPSF, ZernikePSF), not just GaussianPSF."""
    opt = OpticalSystem(wavelength=532e-9, numerical_aperture=0.25)
    field = _MockScatteredField(radiance=np.ones((8, 8)))
    for model in (AiryPSF(), ZernikePSF(Wavefront({}), wavelength=532e-9, numerical_aperture=0.25)):
        sf = OpticalPropagator(psf_model=model, throughput_enabled=False).propagate(field, opt)
        assert sf.irradiance.shape == (8, 8)
        assert np.all(sf.irradiance >= 0.0)


def test_zernike_psf_odd_size_auto():
    wf = Wavefront({})
    psf = ZernikePSF(wf, wavelength=532e-9, numerical_aperture=0.25)
    kernel = psf.kernel(size=20)
    assert kernel.shape[0] % 2 == 1


def test_propagator_throughput_scales_irradiance():
    opt = OpticalSystem(wavelength=532e-9, numerical_aperture=0.5, focal_length=50e-3, magnification=1.0)
    field = _MockScatteredField(radiance=np.ones((5, 5)))
    prop_on = OpticalPropagator(throughput_enabled=True)
    prop_off = OpticalPropagator(throughput_enabled=False)
    sf_on = prop_on.propagate(field, opt)
    sf_off = prop_off.propagate(field, opt)
    expected = np.pi * 0.5 ** 2
    assert np.allclose(sf_on.irradiance, sf_off.irradiance * expected)


def test_propagator_throughput_disabled():
    opt = OpticalSystem(wavelength=532e-9, numerical_aperture=0.5, focal_length=50e-3, magnification=1.0)
    field = _MockScatteredField(radiance=np.ones((5, 5)))
    prop = OpticalPropagator(throughput_enabled=False)
    sf = prop.propagate(field, opt)
    assert np.isclose(sf.irradiance[2, 2], 1.0)


def test_propagator_magnification_resamples():
    opt = OpticalSystem(wavelength=532e-9, numerical_aperture=0.25, focal_length=50e-3, magnification=0.5)
    field = _MockScatteredField(radiance=np.eye(10))
    prop = OpticalPropagator(magnification_enabled=True, throughput_enabled=False)
    sf = prop.propagate(field, opt)
    assert sf.irradiance.shape == (5, 5)


def test_propagator_magnification_unity_no_change():
    opt = OpticalSystem(wavelength=532e-9, numerical_aperture=0.25, focal_length=50e-3, magnification=1.0)
    rad = np.ones((5, 5))
    field = _MockScatteredField(radiance=rad)
    prop = OpticalPropagator(magnification_enabled=True, throughput_enabled=False)
    sf = prop.propagate(field, opt)
    assert sf.irradiance.shape == (5, 5)


def test_propagator_magnification_disabled():
    opt = OpticalSystem(wavelength=532e-9, numerical_aperture=0.25, focal_length=50e-3, magnification=0.5)
    field = _MockScatteredField(radiance=np.eye(10))
    prop = OpticalPropagator(magnification_enabled=False, throughput_enabled=False)
    sf = prop.propagate(field, opt)
    assert sf.irradiance.shape == (10, 10)


def test_defocus_coefficient_formula():
    """c5 = defocus · NA² / (4·√3) metres of RMS wavefront error."""
    assert np.isclose(defocus_coefficient(1e-3, 0.5), 1e-3 * 0.25 / (4 * np.sqrt(3)))
    assert np.isclose(defocus_coefficient(0.0, 0.5), 0.0)


def test_defocus_coefficient_sign_and_scaling():
    assert defocus_coefficient(1e-4, 0.5) > 0.0
    assert defocus_coefficient(-1e-4, 0.5) < 0.0
    # Doubling NA quadruples the coefficient (NA² dependence).
    assert np.isclose(defocus_coefficient(1e-4, 0.5), 4 * defocus_coefficient(1e-4, 0.25))


def test_optical_system_defocus_defaults_to_zero():
    assert OpticalSystem().defocus == 0.0


def test_zernike_psf_with_defocus_broadens():
    """Axial defocus widens the PSF and lowers the peak (via a Zernike
    j=5 coefficient), closing the loop with sharpness metrics."""
    kw = dict(wavelength=532e-9, numerical_aperture=0.5, pixel_size=0.1e-6)
    ideal = ZernikePSF(Wavefront({}), **kw).kernel(63)
    defoc = ZernikePSF(Wavefront({}), **kw).with_defocus(1.4e-6).kernel(63)
    c = 63 // 2
    y, x = np.mgrid[-c:c + 1, -c:c + 1]
    second_moment = lambda k: (k * (x ** 2 + y ** 2)).sum()
    assert defoc[c, c] < ideal[c, c]
    assert second_moment(defoc) > second_moment(ideal)


def test_zernike_psf_with_defocus_zero_unchanged():
    kw = dict(wavelength=532e-9, numerical_aperture=0.5, pixel_size=0.1e-6)
    psf = ZernikePSF(Wavefront({}), **kw)
    assert np.allclose(psf.with_defocus(0.0).kernel(63), psf.kernel(63))


def test_zernike_psf_with_defocus_preserves_aberrations():
    kw = dict(wavelength=532e-9, numerical_aperture=0.5, pixel_size=0.1e-6)
    psf = ZernikePSF(Wavefront({6: 0.1e-6}), **kw).with_defocus(1.4e-6)
    assert np.isclose(psf.wavefront.coefficients[6], 0.1e-6)
    assert psf.wavefront.coefficients[5] > 0.0


def test_defocus_kernel_size_covers_geometric_blur():
    """The kernel grows to hold the geometric circle of confusion."""
    psf = ZernikePSF(Wavefront({}), wavelength=532e-9, numerical_aperture=0.5, pixel_size=5e-6)
    small = psf.defocus_kernel_size(1e-4, base_size=31)  # radius 10 px
    large = psf.defocus_kernel_size(5e-4, base_size=31)  # radius 50 px
    assert small >= 31 and small % 2 == 1
    assert large >= 101
    assert large > small


def test_propagator_defocus_broadens_point_image():
    """An OpticalSystem with axial defocus spreads a point source over a
    wider blur than the same system in focus."""
    model = ZernikePSF(Wavefront({}), wavelength=532e-9, numerical_aperture=0.25)
    field = _MockScatteredField(radiance=np.zeros((41, 41)))
    field.radiance[20, 20] = 1.0
    opt = OpticalSystem(wavelength=532e-9, numerical_aperture=0.25, defocus=0.0)
    in_focus = OpticalPropagator(psf_model=model, throughput_enabled=False).propagate(field, opt)
    opt.defocus = 2e-4
    blurred = OpticalPropagator(psf_model=model, throughput_enabled=False).propagate(field, opt)
    c = 20
    y, x = np.mgrid[-c:c + 1, -c:c + 1]
    second_moment = lambda img: (img * (x ** 2 + y ** 2)).sum()
    assert blurred.irradiance[c, c] < in_focus.irradiance[c, c]
    assert second_moment(blurred.irradiance) > second_moment(in_focus.irradiance)


def test_propagator_defocus_through_focus_sharpness():
    """Focus scores fall as defocus grows — in-focus is sharpest, the
    signature of a through-focus scan closing the defocus -> blur loop."""
    from optical_metrology.analysis.focus import FocusAnalyzer

    model = ZernikePSF(Wavefront({}), wavelength=532e-9, numerical_aperture=0.25, pixel_size=2e-6)
    field = _MockScatteredField(radiance=np.zeros((49, 49)))
    field.radiance[24, 24] = 1.0
    scores = []
    for defocus in (0.0, 1e-4, 2e-4, 4e-4):
        opt = OpticalSystem(wavelength=532e-9, numerical_aperture=0.25, defocus=defocus)
        sf = OpticalPropagator(psf_model=model, throughput_enabled=False).propagate(field, opt)
        score = FocusAnalyzer(method="laplacian_variance").analyze(_MockImage(sf.irradiance)).measurements["focus_score"]
        scores.append(score)
    assert all(scores[i] > scores[i + 1] for i in range(len(scores) - 1))


def test_propagator_defocus_ignored_without_defocus_capable_psf():
    """Systems without a defocus-capable PSF (e.g. no psf_model) ignore
    the defocus setting without error."""
    opt = OpticalSystem(wavelength=532e-9, numerical_aperture=0.25, defocus=1e-3)
    field = _MockScatteredField(radiance=np.ones((5, 5)))
    sf = OpticalPropagator(psf_model=None, throughput_enabled=False).propagate(field, opt)
    assert sf.irradiance.shape == (5, 5)
