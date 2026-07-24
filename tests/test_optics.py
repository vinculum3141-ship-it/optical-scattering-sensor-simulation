import numpy as np

from optics import GaussianPSF, OpticalPropagator, OpticalSystem, SensorField
from scattering import ScatteredField


def test_optical_propagator_returns_sensor_field():
    scattered = ScatteredField(
        radiance=np.ones((8, 8), dtype=float),
        outgoing_direction=np.zeros((8, 8, 3), dtype=float),
        polarization=None,
    )
    optics = OpticalSystem(focal_length=0.1, aperture_diameter=0.01, wavelength=532e-9)
    propagator = OpticalPropagator(psf_model=GaussianPSF(sigma=1.0))
    sensor_field = propagator.propagate(scattered, optics)

    assert isinstance(sensor_field, SensorField)
    assert sensor_field.irradiance.shape == (8, 8)
    assert sensor_field.wavelength == 532e-9
    assert sensor_field.optical_path_length >= 0.0
