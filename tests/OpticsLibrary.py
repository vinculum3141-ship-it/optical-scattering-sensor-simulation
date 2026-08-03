"""Robot Framework test library for the optics package (new models)."""

import numpy as np

from optical_metrology.optics import AiryPSF


class OpticsLibrary:
    """Test library providing keywords for optics model verification."""

    def create_airy_psf(self, wavelength, na, pixel_size):
        self._psf = AiryPSF(
            wavelength=float(wavelength),
            numerical_aperture=float(na),
            pixel_size=float(pixel_size),
        )
        return self._psf

    def generate_kernel(self, size):
        self._kernel = self._psf.kernel(size=int(size))
        return self._kernel

    def kernel_should_be_normalised(self):
        if not np.allclose(self._kernel.sum(), 1.0):
            raise AssertionError(
                f"Kernel sum = {self._kernel.sum()}, expected 1.0"
            )

    def kernel_shape_should_be(self, expected_str):
        expected = tuple(int(x) for x in expected_str.split(","))
        if self._kernel.shape != expected:
            raise AssertionError(
                f"Kernel shape {self._kernel.shape} != {expected}"
            )

    def centre_should_be_maximum(self):
        h, w = self._kernel.shape
        centre = self._kernel[h // 2, w // 2]
        if centre != self._kernel.max():
            raise AssertionError(
                f"Centre value {centre} is not the maximum ({self._kernel.max()})"
            )

    def kernel_should_be_symmetric(self):
        if not np.allclose(self._kernel, self._kernel.T, atol=1e-10):
            raise AssertionError("Kernel is not symmetric about the transpose")
        if not np.allclose(self._kernel, np.flip(self._kernel), atol=1e-10):
            raise AssertionError("Kernel is not symmetric about the centre")
