import numpy as np

from optical_metrology.optics import AiryPSF, Wavefront, ZernikePolynomials, ZernikePSF


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
    wf_aberr = Wavefront({5: 0.5})  # defocus
    ideal = ZernikePSF(wf_ideal, wavelength=532e-9, numerical_aperture=0.25)
    aberr = ZernikePSF(wf_aberr, wavelength=532e-9, numerical_aperture=0.25)
    k_ideal = ideal.kernel(size=31)
    k_aberr = aberr.kernel(size=31)
    assert k_ideal[15, 15] > k_aberr[15, 15], \
        "aberration should reduce peak intensity"


def test_zernike_psf_odd_size_auto():
    wf = Wavefront({})
    psf = ZernikePSF(wf, wavelength=532e-9, numerical_aperture=0.25)
    kernel = psf.kernel(size=20)
    assert kernel.shape[0] % 2 == 1
