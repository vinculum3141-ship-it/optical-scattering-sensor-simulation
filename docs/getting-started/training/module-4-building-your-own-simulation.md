# Module 4 — Building Your Own Simulation

> **Goal:** assemble a custom pipeline for your own problem, extend the
> framework with a custom model, and know how to carry the result toward
> production.
>
> **Prerequisites:** [Module 3](module-3-running-the-examples.md),
> [Design Patterns](../../engineering/design-patterns.md) (skim section 3).

## 1. Start From a Question

A good simulation starts from a measurable question:

> "Can a camera see a 2 µm dent on a rough silicon wafer in dark-field?"

Write it down, then pick the layers that matter for it. Everything else
can be left at defaults or skipped.

## 2. Assemble a Custom Pipeline

```python
from optical_metrology.pipeline import SimulationPipeline
from optical_metrology.illumination import Laser, TopHatBeamProfile
from optical_metrology.surface import DentSurface, Material
from optical_metrology.scattering import BeckmannScattering
from optical_metrology.optics import OpticalSystem, ZernikePSF, OpticalPropagator
from optical_metrology.detector import CMOSDetector, HotPixelNoise
from optical_metrology.analysis import ImageAnalyzer, HistogramAnalyzer, DefectAnalyzer

pipeline = SimulationPipeline(
    source=Laser(532e-9, power=5e-3, beam_profile=TopHatBeamProfile()),
    surface=DentSurface(radius=3.0, depth=2.0, material=Material("silicon")),
    scattering=BeckmannScattering(roughness=0.1),
    optics=OpticalSystem(focal_length=0.05, aperture_diameter=0.008),
    propagator=OpticalPropagator(ZernikePSF()),
    detector=CMOSDetector(exposure_time=1e-5, noise_models=[HotPixelNoise()]),
    analysers=[HistogramAnalyzer(), DefectAnalyzer(threshold=0.08)],
    surface_material=Material("silicon"),
)
result = pipeline.run(shape=(64, 64), spacing=0.5)
print(result.report.measurements)
```

Every piece is a *strategy* — swap `BeckmannScattering` for
`LambertianScattering` and the rest of the pipeline is untouched. That
is the [Strategy pattern](../../engineering/design-patterns.md#31-strategy-pattern)
doing its job.

## 3. Extend the Framework

Custom models implement a single method. A custom scattering model:

```python
import numpy as np
from optical_metrology.scattering import ScatteringModel, ScatteredField

class MyModel(ScatteringModel):
    """Diffuse + a sharp specular spike."""
    def __init__(self, diffuse=0.6, specular=0.4):
        self.diffuse = diffuse
        self.specular = specular

    def evaluate(self, lightfield, surface, view_direction):
        normals = np.asarray(surface.normals, dtype=float)
        view = np.asarray(view_direction, dtype=float)
        view = view / np.linalg.norm(view)
        to_light = -np.asarray(lightfield.direction, dtype=float)
        cos_i = np.clip(np.einsum("...i,...i->...", to_light, normals), 0.0, None)
        radiance = self.diffuse * cos_i
        if cos_i.max() > 0.99:            # near-normal incidence → spike
            radiance = radiance + self.specular
        H, W = radiance.shape
        return ScatteredField(
            radiance=radiance,
            outgoing_direction=np.broadcast_to(view, (H, W, 3)).copy(),
            polarization=lightfield.polarization,
        )
```

Drop it into the pipeline above and rerun. The same pattern applies to
light sources (`default_spectrum`), surfaces (`generate(shape)`), noise
(`apply(electrons)`), and analysis (`analyze(image)`) — see
[Extending the Framework](../../engineering/extending.md).

## 4. Sweep and Compare

Turn the single run into a comparison. The built-in sweeps do the
bookkeeping for you:

```python
from optical_metrology.analysis import ScatteringSweep, BRDFFitter

sweep = ScatteringSweep(
    model_class=BeckmannScattering,
    params={"roughness": [0.05, 0.2, 0.5]},
)
data = sweep.run(lightfield, surface)
```

Or iterate yourself — but **change one parameter at a time** and record
every result. This is the discipline that makes a prototype a study
(see [Research Workflows](../../science/research-workflows.md)).

## 5. Protect Your Work (Toward Production)

1. **Parameterise** — turn your pipeline into a script with flags
   (mirror the unit scripts in `notebooks/`).
2. **Assert the known answers** — add pytest cases for invariants you
   rely on (see [Testing](../../quality-assurance/testing.md)).
3. **Write an acceptance test** — a Robot test case that states the
   expected behaviour in plain language (see
   [Test Strategy](../../quality-assurance/test-strategy.md)).
4. **Document assumptions** — note which model validities your
   simulation depends on (each layer doc lists them).

## Exercises

1. Swap `ZernikePSF()` for `GaussianPSF(sigma=1.0)` in the pipeline and
   compare `report.measurements`. Which model is "blurrier"?
2. Add `defocus=5e-6` to the `OpticalSystem` (or the propagator's PSF)
   and observe the effect on a defect's visibility.
3. Write a custom `AnalysisModule` that reports the mean of the top 1%
   of pixels, add it to `analysers`, and run.

## Check Your Understanding

- Why can you swap models without touching the rest of the pipeline?
- What is the single method a custom scattering model must implement?
- What is the difference between a `Surface` instance and a
  `SurfaceGenerator` in the pipeline?
- Name three things you should do before calling a prototype "done".

## Where Next?

- [Research Workflows: Prototyping to Production](../../science/research-workflows.md)
  — the full path from notebook to hand-off.
- [Design Patterns & Software Principles](../../engineering/design-patterns.md)
  — why the framework is built this way.
- [Use Cases](../../use-cases/index.md) — seven full scenarios to model
  your problem on.
