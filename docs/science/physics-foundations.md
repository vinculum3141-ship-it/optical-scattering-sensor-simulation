# Physics Foundations

> **Target audience:** Physics scientists, optical engineers, modellers.

This document describes the physical models, governing equations, and
assumptions used in each layer of the simulation framework.

## 1. Illumination Physics

### Radiometric Quantities

The framework uses standard radiometric quantities:

- **Radiant flux (power)** Φ — total optical power in watts (W).
- **Irradiance** E — power per unit area incident on a surface (W/m^2).
- **Radiant intensity** I — power per unit solid angle (W/sr).
- **Radiance** L — power per unit area per unit solid angle
  (W/(m^2 sr)).

The `LightField` stores **irradiance** at each grid point, computed as
the product of the source power and the beam profile:

    E(x, y) = P_total × P_profile(x, y)

where P_profile is normalised so that its sum over the grid equals 1
(or equivalently, the total power is the sum of irradiance values times
the pixel area).

### Beam Profiles

- **Uniform** — E(x, y) = constant across the grid. Represents an
  idealised collimated beam with no spatial variation.
- **Gaussian (TEM00)** — E(x, y) ∝ exp(-2 r^2 / w0^2), where w0 is the
  1/e^2 beam-waist radius. This is the fundamental transverse mode of
  a laser resonator.
- **TopHat** — uniform over a circular aperture, zero outside. The
  current implementation is a placeholder returning uniform over the
  full grid.

### Spectral Models

- **Monochromatic** — a delta-function at a single wavelength.
  Appropriate for narrow-linewidth lasers where Δλ ≪ λ.
- **Gaussian** — Gaussian line shape centred at λ_peak with FWHM width σ.
  Typical for LEDs where the emission spectrum is approximately Gaussian.
- **Blackbody** — Planck distribution B(λ, T) = (2hc^2/λ^5) /
  [exp(hc/λkT) - 1]. Used for sunlight (T_eff = 5778 K) and
  incandescent sources.
- **Broadband** — flat (constant) spectral power over a finite range
  [λ_min, λ_max]. A simple model for white-light lamps.

### Polarisation States

Supported idealised states: unpolarized, linear, circular, elliptical.
The `PolarizationState` is a validated label; polarisation-dependent
effects (Fresnel reflection, polarising optics) are not yet implemented
in the scattering or optics layers.

### Divergence

Beam divergence is a scalar parameter (full-angle in radians). It is
recorded but not currently used to modify the direction array — the
generated light field is always perfectly collimated at the grid
resolution.

## 2. Surface Geometry Physics

### Height Map Representation

A surface is represented as a 2D height map h(x, y) on a regular grid.
This is a Monge parameterisation: the surface is assumed to be a
function z = h(x, y) that is single-valued (no overhangs or folds).

### Surface Normals

For a surface z = h(x, y), the surface normal is:

    n = (-∂h/∂x, -∂h/∂y, 1) normalised to unit length

The partial derivatives ∂h/∂x and ∂h/∂y are approximated with
second-order finite differences via `numpy.gradient`.

### Curvature

Curvature is approximated as the Laplacian of the height field:

    κ ≈ ∇^2 h = ∂^2h/∂x^2 + ∂^2h/∂y^2

This is a scalar measure of local bending. Positive values indicate
concave-up (valley), negative indicate concave-down (ridge).

### Roughness

RMS roughness is defined as:

    R_q = sqrt( (1/N) Σ (h_i - ⟨h⟩)^2 )

where ⟨h⟩ is the mean height. This is the standard deviation of the
height distribution and matches the ISO 25178 definition of Sq
(areal surface roughness).

### Material Model

`Material` is a simple label with a refractive index. No dispersive
(n(λ)) or temperature-dependent effects are modelled. The refractive
index is available for future Fresnel-based scattering models but
is not used by the current Lambertian implementation.

## 3. Scattering Physics

### Lambert's Cosine Law

The baseline scattering model is the Lambertian diffuse model
(see `layer-scattering.md` for the full set of implemented models:
Lambertian, Phong, Oren-Nayar, Cook-Torrance, Beckmann, GGX,
Rayleigh, Mie):

    L_r(x) = (ρ/π) × E_i(x) × max( n(x) · ω_i , 0 )

where:

- L_r is the reflected radiance (W/(m^2 sr)) — but since we work in
  2D per-pixel terms and ignore the 1/π factor, the radiance stored
  is proportional to irradiance × cos θ_i.
- ρ is the albedo (fraction of incident power diffusely reflected).
- E_i is the incident irradiance from the `LightField`.
- n is the unit surface normal.
- ω_i is the direction from the surface toward the light source
  (the negative of the light propagation direction).

Key properties of Lambertian scattering:

- **View-independent** — radiance is the same in all directions
  (perfectly diffuse).
- **Cosine falloff** — radiance decreases as cos θ_i where θ_i is
  the angle between the surface normal and the incident light.
- **No wavelength dependence** — albedo is a single scalar, not a
  spectral function.
- **No polarisation** — the outgoing field carries the incident
  polarisation state unchanged.

### Sign Convention

```
lightfield.direction  =  unit vector from source → surface  (illumination direction)
to_light              = -lightfield.direction               (direction from surface to source)
Lambert's law:         radiance ∝ max(dot(to_light, normal), 0)
```

### Physical Validity

The Lambertian model is a good approximation for:

- Matte surfaces (paper, chalk, rough plastics).
- Low-angle scattering where multiple scattering dominates.
- Reference cases and baseline comparisons.

It is **not** valid for:

- Specular (mirror-like) surfaces.
- Glossy or semi-glossy materials.
- Wavelength-dependent scattering (colour shifts).
- Surfaces with significant subsurface scattering.

## 4. Optics Physics

### Imaging Model

The optics layer transforms scattered radiance into sensor-plane
irradiance via convolution with a point-spread function (PSF):

    E_sensor(x, y) = (L_scattered ∗ PSF)(x, y)

where ∗ denotes 2D convolution. This models a spatially invariant,
incoherent imaging system under the paraxial approximation.

### Optical System Parameters

- **Aperture diameter D** — entrance pupil diameter (m).
- **Focal length f** — effective focal length (m).
- **Numerical aperture** — NA = D/(2f), auto-computed.
- **Magnification M** — lateral magnification (defaults to 1.0).

### Gaussian PSF Model

The current PSF is an isotropic 2D Gaussian:

    PSF(x, y) = (1 / (2πσ²)) exp(-(x² + y²) / (2σ²))

The kernel is normalised to unit sum for energy conservation.

### Limitations

- No diffraction (Airy disk, MTF).
- No aberrations (spherical, coma, astigmatism, etc.).
- No wavelength-dependent effects (chromatic aberration).
- No polarisation dependence in the optical system.
- Spatially invariant PSF (no field-dependent aberrations).
- Paraxial approximation only.

## 5. Detector Physics

### Photon Conversion

The conversion from irradiance to photoelectrons follows:

    N_photons = (E × A_pixel × t_exp) / (hc/λ)

where:

- E = irradiance (W/m^2)
- A_pixel = pixel area (m^2)
- t_exp = exposure time (s)
- hc/λ = photon energy (J)

### Quantum Efficiency

A fraction QE of incident photons generate photoelectrons:

    N_e = QE × N_photons

### Noise Sources

| Noise type | Distribution | Origin | Model |
|---|---|---|---|
| Shot noise | Poisson(μ = N_e) | Photon arrival statistics | √N variance |
| Dark current | Poisson(μ = I_d × t) | Thermal generation | Temperature-independent |
| Read noise | Gaussian(0, σ_read) | Readout electronics | Additive |

### Full-Well Capacity

Electrons are clipped to the full-well capacity FWC:

    N_e_clipped = min(N_e, FWC)

This models pixel saturation.

### ADC Quantisation

Electron counts are converted to digital numbers (ADU):

    DN = round(N_e / gain)

then clipped to [0, 2^bit_depth - 1]. The gain is in units of
electrons per ADU.

## 6. Analysis Physics

### Histogram

The histogram bin i counts the number of pixels with value v_i:

    H(v_i) = count of pixels where pixel = v_i

This is the full-resolution histogram (one bin per unique pixel value),
not a binned approximation.

### Statistics

- **Mean intensity** — ⟨I⟩ = (1/N) Σ I_i
- **Max intensity** — max(I)
- **Min intensity** — min(I)

## Units Summary

| Layer | Input quantity | Units | Output quantity | Units |
|---|---|---|---|---|
| Illumination | Power, profile | W, dimensionless | Irradiance | W/m^2 |
| Surface | Height map | m | Roughness, normals | m, dimensionless |
| Scattering | Irradiance + normals | W/m^2 | Radiance | W/(m^2 sr) |
| Optics | Radiance | W/(m^2 sr) | Irradiance | W/m^2 |
| Detector | Irradiance | W/m^2 | Digital counts | ADU |
| Analysis | Digital counts | ADU | Statistics | dimensionless |
