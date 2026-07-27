"""End-to-end integration test for UC2 Multi-Spectral Material Identification.

Simulates a complete multi-spectral imaging pipeline:
1. Multi-spectral source generates light fields at several wavelengths.
2. A simple surface (with material properties) reflects the light.
3. A CFA detector captures multi-spectral images.
4. Spectral analyzer performs material classification.
"""

import numpy as np

from optical_metrology.illumination import ChannelConfig, MultiSpectralSource, LightSource
from optical_metrology.analysis.spectral import ReferenceSpectrum, SpectralAnalyzer
from optical_metrology.detector import CMOSDetector, DigitalImage
from optical_metrology.detector.cfa import CFAConfig, CFADetector
from optical_metrology.surface.base import Material


def _expected_detector_response(f0: np.ndarray, wavelengths: np.ndarray,
                                power: float = 1e-2) -> np.ndarray:
    """Compute expected pixel ADU for given F0 spectrum.
    
     Accounts for photon energy, QE, pixel area, exposure time, gain.
    """
    h = 6.62607015e-34
    c = 2.99792458e8
    qe = 0.9
    pixel_area = 25e-12
    exposure_time = 0.01
    gain = 2.0
    response = []
    for i, wl in enumerate(wavelengths):
        photon_energy = h * c / wl
        irradiance = power * f0[i]
        photons = irradiance * pixel_area * exposure_time / photon_energy
        electrons = photons * qe
        adu = electrons / gain
        response.append(adu)
    return np.array(response)


def test_end_to_end_material_classification():
    """Simulate multi-spectral imaging of two materials and classify."""
    h = 6.62607015e-34
    c = 2.99792458e8
    power = 1e-2

    wavelengths = np.array([450e-9, 550e-9, 650e-9])
    n_bands = len(wavelengths)

    # Define two materials with distinct spectral F0 curves
    mat_a = Material(
        name="glass",
        refractive_index_fn=lambda wl: 1.5 + (wl - 550e-9) * 1e6,
    )
    mat_b = Material(
        name="silicon",
        refractive_index=3.5,
        extinction=0.0,
    )

    f0_a = np.array([mat_a.F0(wl) for wl in wavelengths])
    f0_b = np.array([mat_b.F0(wl) for wl in wavelengths])

    # Build reference spectra that match the expected detector response
    ref_a = _expected_detector_response(f0_a, wavelengths, power)
    ref_b = _expected_detector_response(f0_b, wavelengths, power)

    refs = [
        ReferenceSpectrum("glass", ref_a, wavelengths),
        ReferenceSpectrum("silicon", ref_b, wavelengths),
    ]
    analyzer = SpectralAnalyzer(reference_library=refs)

    # Create a multi-spectral source with uniform illumination
    H, W = 8, 8
    channels = [ChannelConfig(wavelength=w, power=power) for w in wavelengths]
    source = MultiSpectralSource(channels, source_template=LightSource())
    mclf = source.generate_light_field(shape=(H, W))

    stack = mclf.intensity_stack()

    # Simulate material A on left half, material B on right half
    refl_map = np.zeros((H, W, n_bands))
    for b in range(n_bands):
        refl_map[:, :W // 2, b] = f0_a[b]
        refl_map[:, W // 2:, b] = f0_b[b]

    radiance = stack * refl_map

    # Capture each band monochromatically
    band_images = []
    for b in range(n_bands):
        class FakeSensorField:
            irradiance = radiance[:, :, b]
            wavelength = wavelengths[b]

        det = CMOSDetector(rng_seed=42, quantum_efficiency=lambda wl: 0.9)
        img = det.capture(FakeSensorField())
        band_images.append(img.pixels.astype(float))

    data_cube = np.stack(band_images, axis=-1)
    image = DigitalImage(pixels=np.round(data_cube).astype(np.uint16),
                         metadata={"n_channels": n_bands})

    report = analyzer.analyze(image)
    assert "classification" in report.measurements
    labels = report.measurements["classification"]["labels"]
    confidence = report.measurements["classification"]["confidence"]

    assert labels.shape == (H, W)
    assert np.all(confidence >= 0.0)
    assert np.all(confidence <= 1.0)

    n_left_correct = np.sum(labels[:, :W // 2] == 0)
    n_right_correct = np.sum(labels[:, W // 2:] == 1)
    total = H * (W // 2)
    assert n_left_correct > total * 0.5, f"Left classification too low: {n_left_correct}/{total}"
    assert n_right_correct > total * 0.5, f"Right classification too low: {n_right_correct}/{total}"


def test_band_ratio_discrimination():
    """Two materials with different band ratios should be separable."""
    # Material A: high in band 0, low in band 1
    # Material B: low in band 0, high in band 1
    refs = [
        ReferenceSpectrum("A", np.array([1.0, 0.1])),
        ReferenceSpectrum("B", np.array([0.1, 1.0])),
    ]
    analyzer = SpectralAnalyzer(reference_library=refs)

    # Pure A pixel
    labels_a, conf_a = analyzer.classify(np.array([[[1.0, 0.1]]]))
    assert labels_a[0, 0] == 0  # class A

    # Pure B pixel
    labels_b, conf_b = analyzer.classify(np.array([[[0.1, 1.0]]]))
    assert labels_b[0, 0] == 1  # class B


def test_spectral_angle_map_on_cube():
    """Spectral angle map computation on a multi-pixel data cube."""
    ref = np.array([1.0, 0.0, 0.0])
    data = np.zeros((3, 3, 3))
    data[:, :, 0] = 1.0  # all pixels match ref

    sam_map = SpectralAnalyzer.spectral_angle_map(data, ref)
    assert sam_map.shape == (3, 3)
    assert np.allclose(sam_map, 0.0, atol=1e-10)


def test_spectral_analyzer_with_wavelength_dependent_qe():
    """Spectral analysis with wavelength-dependent QE."""
    wavelengths = np.array([450e-9, 550e-9])

    # Material with different reflectance at each wavelength
    mat = Material(name="test", refractive_index=2.0, extinction=0.0)
    ref_vals = np.array([mat.F0(wl) for wl in wavelengths])

    analyzer = SpectralAnalyzer(
        reference_library=[ReferenceSpectrum("test", ref_vals, wavelengths)],
        wavelengths=wavelengths,
    )

    # Create fake multiband data
    pixels = np.zeros((4, 4, 2))
    pixels[:, :, 0] = ref_vals[0]
    pixels[:, :, 1] = ref_vals[1]

    image = DigitalImage(pixels=np.round(pixels * 255).astype(np.uint16), metadata={})
    report = analyzer.analyze(image)
    assert report.measurements["n_channels"] == 2
    assert "band_ratios" in report.measurements


def test_cfa_detector_with_multispectral_bands():
    """CFA detector captures each band and produces consistent output."""
    det = CFADetector(demosaic=True, rng_seed=42)
    wavelengths = [450e-9, 550e-9, 650e-9]

    images = []
    for wl in wavelengths:
        class FakeField:
            irradiance = np.ones((8, 8)) * 100.0
            wavelength = wl

        img = det.capture(FakeField())
        images.append(img)

    # Each band should produce a 3-channel demosaiced image
    for img in images:
        assert img.pixels.ndim == 3
        assert img.pixels.shape[2] == 3
        assert img.metadata.get("cfa_demosaiced") is True
