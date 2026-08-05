# Module 2 — The Six Layers

> **Goal:** understand what each of the six layers computes, the data
> contract each produces, and how to inspect a field at every stage.
>
> **Prerequisites:** [Module 1](module-1-first-pipeline.md).

The pipeline is a chain of *independent* packages. Each layer produces a
well-defined data container consumed by the next:

```
illumination → LightField
surface      → Surface
scattering   → ScatteredField
optics       → SensorField
detector     → DigitalImage
analysis     → AnalysisReport
```

The key design idea: **the layers do not import each other**. They talk
through these containers, so any layer can be swapped, skipped, or
replaced independently.

## 1. Illumination — `LightField`

Sources: `Laser`, `LED`, `Sunlight`, `BroadbandLamp`. They differ only
in their spectral model — everything else comes from the `LightSource`
base class.

```python
from optical_metrology.illumination import Laser, GaussianBeamProfile
laser = Laser(532e-9, power=5e-3, beam_profile=GaussianBeamProfile(w0=2.0))
lf = laser.generate_light_field(shape=(16, 16), spacing=0.5)
print(lf.intensity.shape, lf.direction.shape, lf.wavelength)
```

Try `laser.incidence_angle_degrees = 30` and regenerate — the direction
array changes, the intensity does not.

## 2. Surface — `Surface`

Height maps and their derived geometry: normals, curvature, roughness.
Generators include `FlatSurface`, `RoughSurface`, `DentSurface`,
`WaferSurface`, `MisalignedSurface`.

```python
from optical_metrology.surface import RoughSurface, Material
surf = RoughSurface((16, 16), sigma=4.0, amplitude=0.3, material=Material("silicon"))
print(surf.height.shape, surf.normals.shape, surf.roughness)
```

**Note:** the constructor does the geometry analysis — the object you
get *is* the finished surface.

## 3. Scattering — `ScatteredField`

BRDF models evaluate how much light goes toward the observer:
`LambertianScattering`, `PhongScattering`, `BeckmannScattering`,
`GGXScattering`, `CookTorranceScattering`, `OrenNayarScattering`, plus
particle models `RayleighScattering` / `MieScattering`.

```python
from optical_metrology.scattering import LambertianScattering
scattered = LambertianScattering(albedo=0.7).evaluate(lf, surf, view=[0, 0, 1])
print(scattered.radiance.shape, scattered.radiance.max())
```

## 4. Optics — `SensorField`

PSF convolution models the imaging system: `GaussianPSF`, `AiryPSF`,
`ZernikePSF` (with `defocus`). The `OpticalSystem` describes focal
length and aperture; the `OpticalPropagator` applies the PSF.

```python
from optical_metrology.optics import OpticalSystem, GaussianPSF, OpticalPropagator
optics = OpticalSystem(focal_length=0.05, aperture_diameter=0.008, wavelength=532e-9)
sensor = OpticalPropagator(GaussianPSF(sigma=1.0)).propagate(scattered, optics)
print(sensor.irradiance.shape)
```

**Try this:** increase `sigma` (a larger PSF blur) and watch the
irradiance smooth out.

## 5. Detector — `DigitalImage`

The CMOS pipeline converts irradiance → electrons → digital counts,
adding noise: shot noise, dark current, read noise, fixed-pattern noise,
hot pixels, and more.

```python
from optical_metrology.detector import CMOSDetector
image = CMOSDetector(exposure_time=1e-5).capture(sensor)
print(image.pixels.shape, image.pixels.min(), image.pixels.max())
```

Run it twice — the digital image differs each time, because the noise
stage is stochastic. That is the *only* stochastic stage by design.

## 6. Analysis — `AnalysisReport`

Pluggable `AnalysisModule`s compute metrics on the image:

```python
from optical_metrology.analysis import ImageAnalyzer, HistogramAnalyzer, ContrastAnalyzer
report = ImageAnalyzer(modules=[HistogramAnalyzer(), ContrastAnalyzer()]).analyze(image)
print(report.measurements)
```

## Putting It Together

Each layer is optional. You can skip optics and feed a hand-built
`ScatteredField` straight to the detector — that is what makes the
framework usable at any stage in isolation. See
[Architecture](../../engineering/architecture.md) for the full data
contracts table.

## Exercises

1. Print the `direction` array of a spherical-wavefront source
   (`Laser(..., wavefront="spherical")`) — verify it varies per pixel.
2. Compare `BeckmannScattering(roughness=0.05)` vs
   `roughness=0.5` on the same surface. Which looks more specular?
3. Add `HotPixelNoise()` to the detector and inspect the image for the
   bright isolated pixels (hint: `image.pixels.max()`).

## Check Your Understanding

- Which layers do *not* depend on the layers after them?
- Name the container produced by each layer.
- Why is detector noise the only stochastic stage?
- How can you run only the illumination stage of the pipeline?

## Next

[Module 3 — Running the Example Projects](module-3-running-the-examples.md)
— explore the seven use cases as notebook units and CLI scripts.
