# Module 1 — First Pipeline

> **Goal:** get a complete simulation running in minutes and understand
> what "end to end" means.
>
> **Prerequisites:** framework installed (see [training index](index.md)).

## 1. Run the Demo

The fastest way to see every layer in action:

```bash
python playground.py --demo
```

You will see terminal heatmaps at each stage — illumination, surface,
scattering, optics, detector, analysis. You do not need to understand
them yet; just notice that **data flows from one stage to the next**.

## 2. Build a Six-Line Pipeline

Now build the same thing yourself, by hand. Create a file `first.py`:

```python
from optical_metrology.illumination import Laser, GaussianBeamProfile
from optical_metrology.surface import RoughSurface, Material
from optical_metrology.scattering import LambertianScattering
from optical_metrology.optics import OpticalSystem, GaussianPSF, OpticalPropagator
from optical_metrology.detector import CMOSDetector

laser = Laser(532e-9, power=5e-3, beam_profile=GaussianBeamProfile(w0=2.0))
laser.propagation_direction = [0, 0, -1]
lf = laser.generate_light_field(shape=(16, 16), spacing=0.5)
surface = RoughSurface((16, 16), sigma=4.0, amplitude=0.3, material=Material("silicon"))
scattered = LambertianScattering(albedo=0.7).evaluate(lf, surface, view=[0, 0, 1])
optics = OpticalSystem(focal_length=0.05, aperture_diameter=0.008, wavelength=532e-9)
sensor = OpticalPropagator(GaussianPSF(sigma=1.0)).propagate(scattered, optics)
image = CMOSDetector(exposure_time=1e-5, gain=1.0).capture(sensor)
print(image.pixels.min(), "-", image.pixels.max(), "ADU")
```

Run it:

```bash
python first.py
```

Six objects, six steps — each line is one layer of the pipeline.

## 3. Render a Heatmap

Every data container has a `visualize()` method — no plotting library
needed:

```python
print(lf.visualize())              # the light field intensity
print(image.visualize(max_width=72, color=True))   # the digital image
```

**Notice:** the light field is smooth (Gaussian beam), the digital image
is not (the surface roughness and detector noise have been added).

## 4. Use the Pipeline Orchestrator

The six manual steps can be wrapped in a single `SimulationPipeline`:

```python
from optical_metrology.pipeline import SimulationPipeline

pipeline = SimulationPipeline(
    source=Laser(532e-9, power=5e-3, beam_profile=GaussianBeamProfile(w0=2.0)),
    surface=RoughSurface,
    scattering=LambertianScattering(albedo=0.7),
    optics=OpticalSystem(focal_length=0.05, aperture_diameter=0.008),
    propagator=OpticalPropagator(GaussianPSF(sigma=1.0)),
    detector=CMOSDetector(exposure_time=1e-5),
)
result = pipeline.run(shape=(16, 16), spacing=0.5)
print(result.digital_image.pixels.min(), "-", result.digital_image.pixels.max(), "ADU")
```

Note the difference: here `surface` is the **class** `RoughSurface`
(not an instance), and the pipeline calls it with `(shape, material)`.
Every component is optional — set any to `None` to skip that stage.

## Exercises

1. Change the beam profile to `UniformBeamProfile()` and rerun. How does
   the light-field heatmap change?
2. Change `albedo` from `0.7` to `0.3`. What happens to the digital
   image range?
3. Set `detector=None` in the pipeline. What does `result.digital_image`
   become? Why?

## Check Your Understanding

- What are the six layers, in order?
- What object does each layer produce?
- What is the difference between passing `RoughSurface` (class) and a
  `RoughSurface(...)` (instance) to `SimulationPipeline.surface`?
- Name one way to visualise a field without matplotlib.

## Next

[Module 2 — The Six Layers](module-2-the-six-layers.md) — dig into what
each layer actually computes, and the data contracts that connect them.
