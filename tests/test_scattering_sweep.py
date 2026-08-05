import numpy as np

from optical_metrology.analysis import ScatteringSweep, SweepCase
from optical_metrology.illumination import Laser
from optical_metrology.scattering import BeckmannScattering, GGXScattering, LambertianScattering
from optical_metrology.surface import FlatSurface, Material, RoughSurface


def _source_factory(wavelength=550e-9):
    src = Laser(wavelength=wavelength, power=1.0)
    src.propagation_direction = np.array([0.0, 0.0, -1.0])
    return src


def _flat_surface_factory(refractive_index=1.5):
    return FlatSurface(
        (16, 16),
        material=Material(refractive_index=refractive_index),
    )


def _rough_surface_factory(refractive_index=1.5):
    return RoughSurface(
        shape=(16, 16),
        sigma=2.0,
        amplitude=0.2,
        material=Material(refractive_index=refractive_index),
    )


def test_sweep_single_parameter_roughness():
    sweep = ScatteringSweep()
    cases = sweep.sweep(
        models={"beckmann": BeckmannScattering},
        source_factory=_source_factory,
        surface_factory=_rough_surface_factory,
        roughness=[0.02, 0.3],
    )
    assert len(cases) == 2
    assert all(isinstance(c, SweepCase) for c in cases)
    assert cases[0].parameters["roughness"] == 0.02
    assert cases[1].parameters["roughness"] == 0.3
    assert cases[0].radiance.shape == cases[0].theta_r.shape
    assert cases[1].radiance.shape == cases[1].theta_r.shape
    assert np.all(cases[0].radiance >= 0.0)


def test_sweep_all_five_parameters_cartesian_product():
    sweep = ScatteringSweep()
    cases = sweep.sweep(
        models={"beckmann": BeckmannScattering, "ggx": GGXScattering},
        source_factory=_source_factory,
        surface_factory=_rough_surface_factory,
        roughness=[0.05, 0.3],
        incident_angle=[0.0, 0.4],
        wavelength=[450e-9, 650e-9],
        refractive_index=[1.5, 3.5],
    )
    assert len(cases) == 2 * 2 * 2 * 2 * 2  # models × 4 swept dims
    swept_combos = {(c.model, tuple(sorted(c.parameters.items()))) for c in cases}
    assert len(swept_combos) == len(cases)


def test_roughness_broadens_distribution():
    sweep = ScatteringSweep()
    cases = sweep.sweep(
        models={"beckmann": BeckmannScattering},
        source_factory=_source_factory,
        surface_factory=_rough_surface_factory,
        roughness=[0.05, 0.3],
    )
    smoother, rougher = cases
    assert rougher.half_width > smoother.half_width
    assert rougher.peak < smoother.peak


def test_incident_angle_changes_distribution():
    sweep = ScatteringSweep(theta_r_range=(0.0, 1.2, 60))
    cases = sweep.sweep(
        models={"beckmann": lambda **kw: BeckmannScattering(roughness=0.3)},
        source_factory=_source_factory,
        surface_factory=_rough_surface_factory,
        incident_angle=[0.0, 0.4],
    )
    normal, tilted = cases
    # Tilting the incidence moves the scattering lobe; the backscatter
    # toward a fixed normal observer weakens.
    assert tilted.peak < normal.peak
    assert not np.isclose(normal.radiance, tilted.radiance).all()


def test_refractive_index_increases_fresnel_peak():
    sweep = ScatteringSweep()
    cases = sweep.sweep(
        # fresnel_reflectance=None makes the model derive F0 from the
        # surface material, so the refractive index actually matters.
        models={"beckmann": lambda **kw: BeckmannScattering(roughness=0.2, fresnel_reflectance=None)},
        source_factory=_source_factory,
        surface_factory=_flat_surface_factory,
        refractive_index=[1.0, 3.0],
    )
    low_n, high_n = cases
    assert high_n.peak > low_n.peak


def test_models_parameter_is_optional_and_model_ignores_extra_kwargs():
    sweep = ScatteringSweep()
    cases = sweep.sweep(
        models={"lambertian": LambertianScattering},
        source_factory=_source_factory,
        surface_factory=_flat_surface_factory,
        roughness=[0.1, 0.4],
    )
    assert len(cases) == 2
    assert cases[0].peak > 0.0
    # Lambertian ignores the roughness kwarg (filtered out) and the flat
    # surface is deterministic, so the two cases are identical.
    assert np.isclose(cases[0].radiance, cases[1].radiance).all()


def test_analyze_report_summary():
    sweep = ScatteringSweep()
    cases = sweep.sweep(
        models={"beckmann": BeckmannScattering},
        source_factory=_source_factory,
        surface_factory=_rough_surface_factory,
        roughness=[0.05, 0.2],
    )
    report = sweep.analyze(cases)
    assert report.measurements["n_cases"] == 2
    assert report.measurements["swept_parameters"] == ["roughness"]
    first = report.measurements["cases"][0]
    assert set(first) >= {
        "model", "roughness", "peak", "peak_angle", "total_power", "half_width", "radiance",
    }
    assert len(first["radiance"]) == len(report.measurements["theta_r"])


def test_analyze_empty_returns_zero_cases():
    report = ScatteringSweep().analyze([])
    assert report.measurements["n_cases"] == 0


def test_invalid_metric_raises():
    try:
        ScatteringSweep(metric="bogus")
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_empty_models_raises():
    try:
        ScatteringSweep().sweep(models={}, source_factory=_source_factory, surface_factory=_flat_surface_factory)
        assert False, "Expected ValueError"
    except ValueError:
        pass
