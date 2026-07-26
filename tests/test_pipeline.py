import numpy as np

from optical_metrology.analysis import HistogramAnalyzer
from optical_metrology.detector import CMOSDetector
from optical_metrology.illumination import Laser, GaussianBeamProfile
from optical_metrology.optics import GaussianPSF, OpticalPropagator, OpticalSystem
from optical_metrology.scattering import LambertianScattering
from optical_metrology.pipeline import SimulationPipeline
from optical_metrology.surface import Material, RoughSurface


def test_pipeline_run_returns_all_stages():
    pipeline = SimulationPipeline(
        source=Laser(532e-9, power=5e-3, beam_profile=GaussianBeamProfile(w0=2.0)),
        surface=RoughSurface((16, 16), sigma=4.0, amplitude=0.3, material=Material("silicon")),
        scattering=LambertianScattering(albedo=0.7),
        optics=OpticalSystem(focal_length=0.05, aperture_diameter=0.008),
        propagator=OpticalPropagator(GaussianPSF(sigma=1.0)),
        detector=CMOSDetector(exposure_time=1e-5, gain=1.0),
        analysers=[HistogramAnalyzer()],
    )
    result = pipeline.run(shape=(16, 16), spacing=0.5, view_direction=[0, 0, 1])
    assert result.light_field is not None
    assert result.surface is not None
    assert result.scattered_field is not None
    assert result.sensor_field is not None
    assert result.digital_image is not None
    assert result.report is not None
    assert result.digital_image.pixels.shape == (16, 16)
    assert "mean_intensity" in result.report.measurements


def test_pipeline_partial_illumination_only():
    pipeline = SimulationPipeline(
        source=Laser(532e-9, power=5e-3),
    )
    result = pipeline.run(shape=(8, 8))
    assert result.light_field is not None
    assert result.surface is None
    assert result.digital_image is None


def test_pipeline_partial_detector_only():
    from optical_metrology.optics import SensorField
    pipeline = SimulationPipeline(
        detector=CMOSDetector(exposure_time=0.1),
    )
    # Manually inject a sensor field
    result = pipeline.run(shape=(8, 8))
    assert result.digital_image is None  # no sensor field input


def test_pipeline_describe_returns_string():
    pipeline = SimulationPipeline(
        source=Laser(532e-9, power=5e-3),
        detector=CMOSDetector(),
        analysers=[HistogramAnalyzer()],
    )
    desc = pipeline.describe()
    assert "Laser" in desc
    assert "CMOSDetector" in desc
    assert "HistogramAnalyzer" in desc


def test_pipeline_with_surface_generator():
    pipeline = SimulationPipeline(
        source=Laser(532e-9, power=5e-3, beam_profile=GaussianBeamProfile(w0=2.0)),
        surface=RoughSurface,
        scattering=LambertianScattering(albedo=0.7),
        surface_material=Material("glass"),
    )
    pipeline.source.propagation_direction = np.array([0.0, 0.0, -1.0])
    result = pipeline.run(shape=(8, 8), spacing=1.0, view_direction=[0, 0, 1])
    assert result.light_field is not None
    assert result.surface is not None
    assert result.scattered_field is not None
