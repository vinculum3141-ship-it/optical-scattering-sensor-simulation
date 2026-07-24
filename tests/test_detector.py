import numpy as np

from detector import CMOSDetector, DigitalImage, DetectorNoiseModel
from optics import SensorField


def test_detector_pipeline_creates_digital_image():
    sensor_field = SensorField(
        irradiance=np.ones((8, 8), dtype=float) * 1e3,
        wavelength=532e-9,
        polarization=None,
        optical_path_length=0.1,
    )
    detector = CMOSDetector(
        exposure_time=0.1,
        quantum_efficiency=0.9,
        dark_current=5.0,
        read_noise_sigma=2.0,
        full_well_capacity=80000.0,
        gain=2.0,
        bit_depth=12,
    )

    image = detector.capture(sensor_field)

    assert isinstance(image, DigitalImage)
    assert image.pixels.shape == (8, 8)
    assert image.pixels.dtype == np.uint16
    assert image.metadata["bit_depth"] == 12
