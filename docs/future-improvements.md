# Future Improvements — Deferred Architectural Notes

> **Purpose:** Track design ideas explicitly **not** in the current
> roadmap (see `docs/roadmap-todo.md` for planned work).  Items here
> are deferred because no use case requires them yet, not because they
> lack priority.

---

## 1. Separate BeamGenerator from LightSource

**What:** Split `LightSource.generate_light_field()` into a standalone
`BeamGenerator` class that samples a physical source onto a grid.

**Why excluded:** No use case needs multiple beam models per source.
The current method is convenient and blocks nothing.  This is a pure
architectural refactor.

**Trigger:** UC5 (structured light) — projecting different fringe
patterns from the same projector, or composing a segmented ring-light
from multiple beam profiles.

**Sketch:**
```python
class BeamGenerator:
    def generate(self, source: LightSource, shape, spacing) -> LightField: ...

# LightSource becomes a pure parameter container:
laser = Laser(532e-9, power=5e-3)
gen = PlanarBeamGenerator(beam_profile=GaussianBeamProfile(w0=2.0))
lf = gen.generate(laser, shape=(32, 32), spacing=0.5)
```

---

## 2. Spatially Varying LightField Properties

**What:** Promote `wavelength`, `polarization`, and `coherence_length`
from scalar to per-pixel arrays on `LightField`.

**Why excluded:** No use case demands it.  Keeping them scalar keeps
the interface simple.

**Trigger:** UC2 (multi-spectral) — wavelength stack; or modelling a
spatially varying polariser / colour filter array.

**Sketch:**
```python
@dataclass
class LightField:
    intensity: np.ndarray           # (H, W)
    direction: np.ndarray           # (H, W, 3)
    wavelength: np.ndarray          # (H, W)
    polarization: np.ndarray        # (H, W)
    coherence_length: float | np.ndarray
    power: float
    phase: np.ndarray | None
```
Backwards compatible if scalar inputs are broadcast to full grid.

---

## 3. Holography / Coherent Imaging

**What:** Full complex-amplitude propagation through the optical chain
(not just intensity PSF convolution).  Requires coherent illumination
and phase-retrieval / digital holography reconstruction.

**Why excluded:** None of the 7 use cases require it.  It would be a
new physics engine rather than an extension of the current radiometric
pipeline.

**Trigger:** A future use case involving digital holographic
microscopy or interferometric surface profiling.
