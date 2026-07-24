import numpy as np

from optics import AiryPSF


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
