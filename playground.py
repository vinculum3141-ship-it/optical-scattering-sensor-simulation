#!/usr/bin/env python3
"""
Interactive playground for the optical-scattering-sensor-simulation framework.

Run with::

    python playground.py                  # menu-based exploration
    python playground.py --script         # run a batch of examples non-interactively

This script provides a convenient REPL for constructing light sources,
surfaces, scattering models, and optical systems — and inspecting the
results — without leaving the terminal.

Dependencies: numpy (required), robot (optional, for test validation).
"""

import argparse
import sys
import textwrap

import numpy as np

from illumination import (
    BroadbandLamp,
    LED,
    Laser,
    Sunlight,
    GaussianBeamProfile,
    TopHatBeamProfile,
    UniformBeamProfile,
    PolarizationState,
    LightField,
    LightSource,
)
from surface import (
    FlatSurface,
    RoughSurface,
    ScratchedSurface,
    ParticleSurface,
    Material,
    GeometryAnalyzer,
)
from scattering import (
    LambertianScattering,
    ScatteredField,
    ScatteringModel,
)
from optics import (
    GaussianPSF,
    OpticalPropagator,
    OpticalSystem,
    SensorField,
)
from detector import (
    CMOSDetector,
    DigitalImage,
)

# ---------------------------------------------------------------------------
# Utility: compact terminal heatmap (same style as LightField.visualize)
# ---------------------------------------------------------------------------

_SHADES = [" ", "\u2591", "\u2592", "\u2593", "\u2588"]


def heatmap(arr: np.ndarray, max_width: int = 72) -> str:
    h, w = arr.shape
    scale = min(1.0, max_width / w)
    if scale < 1.0:
        nh, nw = max(1, int(h * scale)), max_width
        ir, jc = np.mgrid[0:h:nh * 1j, 0:w:nw * 1j]
        vals = arr[ir.astype(np.intp).clip(0, h - 1), jc.astype(np.intp).clip(0, w - 1)]
    else:
        nh, nw, vals = h, w, arr

    vmin, vmax = float(vals.min()), float(vals.max())
    norm = np.zeros_like(vals) if vmax == vmin else (vals - vmin) / (vmax - vmin)
    shade_idx = (norm * (len(_SHADES) - 1)).astype(np.intp).clip(0, len(_SHADES) - 1)

    lines = []
    for row in shade_idx:
        buf = []
        for idx in row:
            colour = [36, 32, 33, 31][min(idx, 3)]
            buf.append(f"\033[1;{colour}m{_SHADES[idx]}\033[0m")
        lines.append("".join(buf))

    header = f"({nh}\u00d7{nw})  min={vmin:.4g}  max={vmax:.4g}"
    return f"{header}\n" + "\n".join(lines)


# ---------------------------------------------------------------------------
# Example recipes
# ---------------------------------------------------------------------------

def demo_illumination():
    """Create various light sources and inspect their light fields."""
    print("=" * 60)
    print("  ILLUMINATION DEMO")
    print("=" * 60)

    # Laser
    laser = Laser(wavelength=532e-9, power=5e-3, beam_profile=GaussianBeamProfile(w0=2.0))
    field = laser.generate_light_field(shape=(16, 16), spacing=0.5)
    print(f"\n  Laser (532 nm, 5 mW, Gaussian beam)")
    print(f"    Intensity: {field.intensity.min():.4g} - {field.intensity.max():.4g}")
    print(heatmap(field.intensity))
    print()

    # LED
    led = LED(peak_wavelength=530e-9, width=25e-9, power=10e-3)
    field = led.generate_light_field(shape=(16, 16), spacing=0.5)
    print(f"  LED (530 nm, 10 mW, Gaussian spectrum)")
    print(f"    Intensity: {field.intensity.min():.4g} - {field.intensity.max():.4g}")
    print(heatmap(field.intensity))
    print()

    # Sunlight
    sun = Sunlight(temperature=5778.0, power=1.0)
    field = sun.generate_light_field(shape=(8, 8), spacing=1.0)
    print(f"  Sunlight (5778 K black-body, 1 W)")
    print(f"    Intensity (uniform): {field.intensity.min():.4g} - {field.intensity.max():.4g}")
    print()

    # Custom source: blue laser with linear polarization
    blue = Laser(
        wavelength=445e-9,
        power=1.0,
        beam_profile=GaussianBeamProfile(w0=0.5),
        polarization=PolarizationState("linear"),
    )
    field = blue.generate_light_field(shape=(16, 16), spacing=0.5)
    print(f"  Blue laser (445 nm, 1 W, linear polarization)")
    print(f"    Polarization: {field.polarization.kind}")
    print(f"    Intensity: {field.intensity.min():.4g} - {field.intensity.max():.4g}")
    print(heatmap(field.intensity))
    print()


def demo_surfaces():
    """Create and inspect surface geometries."""
    print("=" * 60)
    print("  SURFACE GEOMETRY DEMO")
    print("=" * 60)

    shape = (16, 16)

    # Flat
    flat = FlatSurface(shape, material=Material("glass"))
    print(f"\n  Flat surface (glass)")
    print(f"    Height range: {flat.height.min():.4g} - {flat.height.max():.4g}")
    print(f"    Roughness:    {flat.roughness:.4g}")
    print(f"    Normals:      {flat.normals[0, 0]}")
    print(heatmap(flat.height))
    print()

    # Rough
    rough = RoughSurface(shape, sigma=4.0, amplitude=0.5, material=Material("silicon"))
    print(f"  Rough surface (silicon)")
    print(f"    Height range: {rough.height.min():.4g} - {rough.height.max():.4g}")
    print(f"    Roughness:    {rough.roughness:.4g}")
    print(heatmap(rough.height))
    print()

    # Scratched
    scratch = ScratchedSurface(shape, scratch_depth=0.3, scratch_width=3, material=Material("aluminium"))
    print(f"  Scratched surface (aluminium)")
    print(f"    Height range: {scratch.height.min():.4g} - {scratch.height.max():.4g}")
    print(f"    Roughness:    {scratch.roughness:.4g}")
    print(heatmap(scratch.height))
    print()

    # Particle
    particles = ParticleSurface(shape, particle_count=6, amplitude=0.8, sigma=2.0, material=Material("gold"))
    print(f"  Particle surface (gold, 6 particles)")
    print(f"    Height range: {particles.height.min():.4g} - {particles.height.max():.4g}")
    print(f"    Roughness:    {particles.roughness:.4g}")
    print(heatmap(particles.height))
    print()


def demo_scattering():
    """Run scattering simulations for different source+surface combinations."""
    print("=" * 60)
    print("  SCATTERING DEMO")
    print("=" * 60)

    shape = (16, 16)
    view_dir = np.array([0.0, 0.0, 1.0])

    scenarios = [
        ("Laser + Flat (glass)", Laser(wavelength=532e-9, power=5e-3, beam_profile=GaussianBeamProfile(w0=2.0)),
         FlatSurface(shape, material=Material("glass")), LambertianScattering(albedo=0.8)),
        ("Laser + Rough (silicon)", Laser(wavelength=532e-9, power=5e-3, beam_profile=GaussianBeamProfile(w0=2.0)),
         RoughSurface(shape, sigma=4.0, amplitude=0.5, material=Material("silicon")), LambertianScattering(albedo=0.8)),
        ("LED + Scratched (aluminium)", LED(peak_wavelength=530e-9, power=10e-3),
         ScratchedSurface(shape, scratch_depth=0.3, scratch_width=3, material=Material("aluminium")),
         LambertianScattering(albedo=0.6)),
    ]

    for label, src, surf, model in scenarios:
        src.propagation_direction = np.array([0.0, 0.0, -1.0])

        lf = src.generate_light_field(shape=shape, spacing=0.5)
        result = model.evaluate(lf, surf, view_direction=view_dir)

        print(f"\n  {label}")
        print(f"    Radiance:   {result.radiance.min():.4g} - {result.radiance.max():.4g}")
        print(f"    Outgoing:   {result.outgoing_direction[0, 0]}")
        print(f"    Polarization: {result.polarization}")
        print(heatmap(result.radiance))
        print()


def demo_optics():
    """Propagate a scattered field through an optical system."""
    print("=" * 60)
    print("  OPTICS DEMO")
    print("=" * 60)

    shape = (16, 16)
    lf_in = LightField(
        intensity=np.ones(shape, dtype=float),
        direction=np.zeros(shape + (3,), dtype=float) + np.array([0.0, 0.0, -1.0]),
        wavelength=532e-9,
        polarization=None,
    )
    flat = FlatSurface(shape, material=Material("glass"))
    model = LambertianScattering(albedo=0.8)
    scattered = model.evaluate(lf_in, flat, view_direction=np.array([0.0, 0.0, 1.0]))

    # Without PSF (box-filter default)
    optics = OpticalSystem(focal_length=0.1, aperture_diameter=0.01, wavelength=532e-9)
    prop = OpticalPropagator()
    sensor = prop.propagate(scattered, optics)
    print(f"\n  Flat-field propagation (default 3x3 box PSF)")
    print(f"    Irradiance: {sensor.irradiance.min():.4g} - {sensor.irradiance.max():.4g}")
    print(heatmap(sensor.irradiance))
    print()

    # With Gaussian PSF (sigma=1.5)
    prop2 = OpticalPropagator(psf_model=GaussianPSF(sigma=1.5))
    sensor2 = prop2.propagate(scattered, optics)
    print(f"  Flat-field propagation (Gaussian PSF, sigma=1.5)")
    print(f"    Irradiance: {sensor2.irradiance.min():.4g} - {sensor2.irradiance.max():.4g}")
    print(heatmap(sensor2.irradiance))
    print()


def demo_detector():
    """Run the full pipeline including the CMOS detector model."""
    print("=" * 60)
    print("  DETECTOR DEMO")
    print("=" * 60)

    shape = (16, 16)

    # Generate a scattered field (laser on rough surface)
    laser = Laser(wavelength=532e-9, power=5e-3, beam_profile=GaussianBeamProfile(w0=2.0))
    laser.propagation_direction = np.array([0.0, 0.0, -1.0])
    lf = laser.generate_light_field(shape=shape, spacing=0.5)
    surface = RoughSurface(shape, sigma=4.0, amplitude=0.3, material=Material("silicon"))
    model = LambertianScattering(albedo=0.7)
    scattered = model.evaluate(lf, surface, view_direction=np.array([0.0, 0.0, 1.0]))

    # Propagate through optics
    optics = OpticalSystem(focal_length=0.05, aperture_diameter=0.008, wavelength=532e-9)
    propagator = OpticalPropagator(psf_model=GaussianPSF(sigma=1.0))
    sensor = propagator.propagate(scattered, optics)

    # Capture with CMOS detector
    detector = CMOSDetector(
        exposure_time=0.1,
        quantum_efficiency=0.9,
        dark_current=5.0,
        read_noise_sigma=2.0,
        full_well_capacity=80000.0,
        gain=2.0,
        bit_depth=12,
    )
    image = detector.capture(sensor)

    print(f"\n  Detector: CMOS")
    print(f"    Exposure:    {detector.exposure_time} s")
    print(f"    QE:          {detector.quantum_efficiency}")
    print(f"    Bit depth:   {detector.bit_depth}-bit")
    print(f"    Gain:        {detector.gain} e⁻/ADU")
    print(f"    FWC:         {detector.full_well_capacity} e⁻")
    print(f"    Dark curr:   {detector.dark_current} e⁻/s")
    print(f"    Read noise:  {detector.read_noise_sigma} e⁻")
    print(f"\n    Pixel shape:  {image.pixels.shape}")
    print(f"    Pixel dtype:  {image.pixels.dtype}")
    print(f"    Pixel range:  {image.pixels.min()} - {image.pixels.max()} ADU")
    print(f"    Metadata:     {image.metadata}")
    print()
    print(heatmap(image.pixels.astype(float)))
    print()


def demo_custom_pipeline():
    """Build a custom source-surface-scattering-optics pipeline from scratch."""
    print("=" * 60)
    print("  CUSTOM PIPELINE")
    print("=" * 60)

    # 1. Create a red laser (power = 2 mW, Gaussian beam, waist = 1.5)
    laser = Laser(wavelength=635e-9, power=2e-3, beam_profile=GaussianBeamProfile(w0=1.5))
    laser.propagation_direction = np.array([0.0, 0.0, -1.0])

    # 2. Generate the light field on a 24x24 grid
    lf = laser.generate_light_field(shape=(24, 24), spacing=0.4)
    print(f"  1. Light source: {type(laser).__name__} at {laser.wavelength*1e9:.0f} nm")
    print(f"     Intensity range: {lf.intensity.min():.4g} - {lf.intensity.max():.4g}")
    print(heatmap(lf.intensity))

    # 3. Create a rough gold surface
    gold = Material("gold", refractive_index=0.47)  # approx. @ 635 nm
    surface = RoughSurface(shape=(24, 24), sigma=5.0, amplitude=0.3, material=gold)
    print(f"\n  2. Surface: {type(surface).__name__} ({surface.material.name})")
    print(f"     Height range: {surface.height.min():.4g} - {surface.height.max():.4g}")
    print(f"     Roughness: {surface.roughness:.4g}")

    # 4. Scatter (Lambertian, albedo = 0.7)
    model = LambertianScattering(albedo=0.7)
    view = np.array([0.3, 0.2, 0.93])  # slightly off-axis viewer
    view = view / np.linalg.norm(view)
    result = model.evaluate(lf, surface, view_direction=view)
    print(f"\n  3. Scattering model: {type(model).__name__} (albedo = {model.albedo})")
    print(f"     View direction: {view}")
    print(f"     Radiance range: {result.radiance.min():.4g} - {result.radiance.max():.4g}")
    print(heatmap(result.radiance))

    # 5. Propagate through optics
    optics = OpticalSystem(aperture_diameter=0.008, focal_length=0.05, wavelength=635e-9)
    propagator = OpticalPropagator(psf_model=GaussianPSF(sigma=1.2))
    sensor = propagator.propagate(result, optics)
    print(f"\n  4. Optical propagation")
    print(f"     NA = {optics.numerical_aperture:.4f}")
    print(f"     Sensor irradiance: {sensor.irradiance.min():.4g} - {sensor.irradiance.max():.4g}")
    print(heatmap(sensor.irradiance))

    # 6. Capture with CMOS detector
    detector = CMOSDetector(exposure_time=0.05, quantum_efficiency=0.85, bit_depth=12)
    image = detector.capture(sensor)
    print(f"\n  5. CMOS capture (12-bit)")
    print(f"     Digital image: {image.pixels.shape}, range {image.pixels.min()} - {image.pixels.max()} ADU")
    print(heatmap(image.pixels.astype(float)))
    print()


def demo_tinker():
    """Simple REPL for tinkering with raw arrays."""
    print("=" * 60)
    print("  TINKER MODE")
    print("=" * 60)
    print("""
  Create a light field from scratch (no LightSource needed):

    lf = LightField(
        intensity=np.ones((8, 8)),
        direction=np.zeros((8, 8, 3)) + np.array([0, 0, -1]),
        wavelength=532e-9,
        polarization=None,
    )

  Create a surface from a custom height map:

    height = np.random.randn(8, 8) * 0.2
    surf = GeometryAnalyzer.analyze(height, material=Material("custom"))

  Evaluate scattering:

    model = LambertianScattering(albedo=0.5)
    result = model.evaluate(lf, surf, view_direction=np.array([0, 0, 1]))
    print("Radiance:", result.radiance.min(), "-", result.radiance.max())

  Propagate through optics:

    optics = OpticalSystem()
    prop = OpticalPropagator(GaussianPSF(sigma=1.0))
    sensor = prop.propagate(result, optics)

  Capture with a CMOS detector:

    from detector import CMOSDetector
    detector = CMOSDetector(exposure_time=0.1, bit_depth=12)
    image = detector.capture(sensor)
    print("Digital image:", image.pixels.shape, image.pixels.dtype)
""")
    print("  (Copy-paste the commands above into a Python shell.)")


# ---------------------------------------------------------------------------
# Menu
# ---------------------------------------------------------------------------

def interactive_menu():
    items = [
        ("Illumination demo", demo_illumination),
        ("Surface geometry demo", demo_surfaces),
        ("Scattering demo", demo_scattering),
        ("Optics demo", demo_optics),
        ("Detector demo", demo_detector),
        ("Custom pipeline (end-to-end)", demo_custom_pipeline),
        ("Tinker mode (code snippets)", demo_tinker),
    ]

    while True:
        print("\n" + "=" * 60)
        print("  OPTICAL SCATTERING SIMULATION — Playground")
        print("=" * 60)
        for i, (label, _) in enumerate(items, 1):
            print(f"    [{i}] {label}")
        print("    [q] Quit")
        print("-" * 60)

        choice = input("  Choose (1-{}, q): ".format(len(items))).strip().lower()
        if choice == "q":
            print("\n  Goodbye!")
            break

        try:
            idx = int(choice)
            if 1 <= idx <= len(items):
                items[idx - 1][1]()
                input("\n  Press Enter to continue...")
            else:
                print(f"  Invalid choice {idx}.")
        except ValueError:
            print(f"  Invalid input '{choice}'.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Playground for the optical scattering sensor simulation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python playground.py         # interactive menu
              python playground.py --demo  # run all demos
        """),
    )
    parser.add_argument("--demo", action="store_true", help="Run all demos non-interactively and exit")
    args = parser.parse_args()

    if args.demo:
        demo_illumination()
        demo_surfaces()
        demo_scattering()
        demo_optics()
        demo_detector()
        demo_custom_pipeline()
        demo_tinker()
        return 0

    return interactive_menu()


if __name__ == "__main__":
    sys.exit(main())
