import numpy as np

from analysis import ContrastAnalyzer, ImageAnalyzer, SaturationAnalyzer
from detector import DigitalImage


def _image(pixels=None, bit_depth=12):
    if pixels is None:
        pixels = np.random.randint(0, 2**bit_depth, size=(8, 8), dtype=np.uint16)
    return DigitalImage(pixels=pixels, metadata={"bit_depth": bit_depth})


def test_contrast_analyzer_returns_measurements():
    image = _image()
    analyzer = ContrastAnalyzer()
    report = analyzer.analyze(image)
    assert "rms_contrast" in report.measurements
    assert "michelson_contrast" in report.measurements
    assert "mean_intensity" in report.measurements


def test_contrast_uniform_image_gives_zero():
    pixels = np.ones((8, 8), dtype=np.uint16) * 2048
    image = _image(pixels=pixels)
    analyzer = ContrastAnalyzer()
    report = analyzer.analyze(image)
    assert report.measurements["rms_contrast"] == 0.0
    assert report.measurements["michelson_contrast"] == 0.0


def test_contrast_high_contrast_image():
    pixels = np.zeros((8, 8), dtype=np.uint16)
    pixels[:, :4] = 0
    pixels[:, 4:] = 4095
    image = _image(pixels=pixels)
    analyzer = ContrastAnalyzer()
    report = analyzer.analyze(image)
    assert report.measurements["michelson_contrast"] > 0.9


def test_saturation_analyzer_detects_saturated():
    pixels = np.zeros((8, 8), dtype=np.uint16)
    pixels[0, 0] = 4095
    image = _image(pixels=pixels)
    analyzer = SaturationAnalyzer(threshold=0.99)
    report = analyzer.analyze(image)
    assert report.measurements["saturated_pixels"] >= 1
    assert report.measurements["saturation_fraction"] > 0.0


def test_saturation_analyzer_no_saturation():
    pixels = np.ones((8, 8), dtype=np.uint16) * 100
    image = _image(pixels=pixels, bit_depth=12)
    analyzer = SaturationAnalyzer(threshold=0.99)
    report = analyzer.analyze(image)
    assert report.measurements["saturated_pixels"] == 0


def test_image_analyzer_with_multiple_analysis_modules():
    pixels = np.random.randint(0, 4095, size=(8, 8), dtype=np.uint16)
    image = _image(pixels=pixels)
    analyzer = ImageAnalyzer(modules=[ContrastAnalyzer(), SaturationAnalyzer()])
    report = analyzer.analyze(image)
    assert "rms_contrast" in report.measurements
    assert "saturated_pixels" in report.measurements
