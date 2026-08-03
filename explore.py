#!/usr/bin/env python3
"""
Interactive exploration script for the optical scattering sensor simulation.

Usage
-----
    python explore.py                        # interactive illumination mode
    python explore.py --surface              # interactive surface-geometry mode
    python explore.py --scattering           # interactive scattering mode
    python explore.py --list                 # list illumination scenarios
    python explore.py --list --surface       # list surface scenarios
    python explore.py --list --scattering    # list scattering scenarios
    python explore.py --run 1                # run illumination scenario 1
    python explore.py --surface --run 2      # run surface scenario 2
    python explore.py --scattering --run 1   # run scattering scenario 1
    python explore.py --all                  # run all illumination scenarios
    python explore.py --surface --all        # run all surface scenarios
    python explore.py --scattering --all     # run all scattering scenarios
"""

import argparse
import sys
import textwrap

import numpy as np

from optical_metrology.illumination import (
    BroadbandLamp,
    LED,
    Laser,
    Sunlight,
    GaussianBeamProfile,
    TopHatBeamProfile,
    UniformBeamProfile,
    PolarizationState,
)

from optical_metrology.surface import (
    FlatSurface,
    RoughSurface,
    ScratchedSurface,
    ParticleSurface,
    Material,
)

from optical_metrology.scattering import (
    LambertianScattering,
)

# ---------------------------------------------------------------------------
# Illumination scenarios
# ---------------------------------------------------------------------------

ILLUM_SCENARIOS = [
    {
        "name": "Green laser pointer",
        "desc": "5 mW, 532 nm, Gaussian beam (w0=2), +z propagation",
        "src": Laser(wavelength=532e-9, power=5e-3, beam_profile=GaussianBeamProfile(w0=2.0)),
    },
    {
        "name": "Green LED",
        "desc": "10 mW, 530 nm peak, 25 nm FWHM, Gaussian profile, 0.5 rad divergence",
        "src": LED(peak_wavelength=530e-9, width=25e-9, power=10e-3),
    },
    {
        "name": "Sunlight",
        "desc": "Solar black-body at 5778 K, 1 W, uniform profile",
        "src": Sunlight(temperature=5778.0, power=1.0),
    },
    {
        "name": "Broadband lamp",
        "desc": "10 W, 400-700 nm flat spectrum, uniform profile",
        "src": BroadbandLamp(wavelength_range=(400e-9, 700e-9), power=10.0),
    },
    {
        "name": "High-power blue laser",
        "desc": "1 W, 445 nm, Gaussian beam (w0=0.5), linear polarization",
        "src": Laser(
            wavelength=445e-9,
            power=1.0,
            beam_profile=GaussianBeamProfile(w0=0.5),
            polarization=PolarizationState("linear"),
        ),
    },
    {
        "name": "Custom LED (red, wide)",
        "desc": "5 mW, 650 nm peak, 50 nm FWHM, top-hat profile",
        "src": LED(
            peak_wavelength=650e-9,
            width=50e-9,
            power=5e-3,
            beam_profile=TopHatBeamProfile(),
        ),
    },
]

# ---------------------------------------------------------------------------
# Surface-geometry scenarios
# ---------------------------------------------------------------------------

SURFACE_SCENARIOS = [
    {
        "name": "Flat surface",
        "desc": "Perfectly level reference (zero height, zero roughness)",
        "gen": FlatSurface,
        "kwargs": {"material": Material(name="glass")},
    },
    {
        "name": "Rough surface",
        "desc": "Correlated Gaussian noise (sigma=6, amplitude=0.5)",
        "gen": RoughSurface,
        "kwargs": {"sigma": 6.0, "amplitude": 0.5, "material": Material(name="silicon")},
    },
    {
        "name": "Scratched surface",
        "desc": "Diagonal groove (depth=0.3, width=3)",
        "gen": ScratchedSurface,
        "kwargs": {"scratch_depth": 0.3, "scratch_width": 3, "material": Material(name="aluminium")},
    },
    {
        "name": "Particle surface",
        "desc": "8 Gaussian bumps (amplitude=0.8, sigma=2)",
        "gen": ParticleSurface,
        "kwargs": {"particle_count": 8, "amplitude": 0.8, "sigma": 2.0, "material": Material(name="gold")},
    },
]

# ---------------------------------------------------------------------------
# Scattering scenarios  (combine a light source, a surface, and a model)
# ---------------------------------------------------------------------------

def _downward_source(cls, **kwargs):
    src = cls(**kwargs)
    src.propagation_direction = np.array([0.0, 0.0, -1.0])
    return src


SCATTERING_SCENARIOS = [
    {
        "name": "Laser on flat surface",
        "desc": "532 nm laser (Gaussian beam, w0=2)  Lambertian (albedo=0.8)  flat glass",
        "src": _downward_source(Laser, wavelength=532e-9, power=5e-3, beam_profile=GaussianBeamProfile(w0=2.0)),
        "surface_gen": FlatSurface,
        "surface_kwargs": {"material": Material(name="glass")},
        "model": LambertianScattering(albedo=0.8),
    },
    {
        "name": "Laser on rough surface",
        "desc": "532 nm laser (Gaussian beam, w0=2)  Lambertian (albedo=0.8)  rough silicon",
        "src": _downward_source(Laser, wavelength=532e-9, power=5e-3, beam_profile=GaussianBeamProfile(w0=2.0)),
        "surface_gen": RoughSurface,
        "surface_kwargs": {"sigma": 6.0, "amplitude": 0.5, "material": Material(name="silicon")},
        "model": LambertianScattering(albedo=0.8),
    },
    {
        "name": "Laser on scratched surface",
        "desc": "532 nm laser (Gaussian beam, w0=2)  Lambertian (albedo=0.8)  scratched aluminium",
        "src": _downward_source(Laser, wavelength=532e-9, power=5e-3, beam_profile=GaussianBeamProfile(w0=2.0)),
        "surface_gen": ScratchedSurface,
        "surface_kwargs": {"scratch_depth": 0.3, "scratch_width": 3, "material": Material(name="aluminium")},
        "model": LambertianScattering(albedo=0.8),
    },
    {
        "name": "Laser on particle surface",
        "desc": "532 nm laser (Gaussian beam, w0=2)  Lambertian (albedo=0.8)  gold particles",
        "src": _downward_source(Laser, wavelength=532e-9, power=5e-3, beam_profile=GaussianBeamProfile(w0=2.0)),
        "surface_gen": ParticleSurface,
        "surface_kwargs": {"particle_count": 8, "amplitude": 0.8, "sigma": 2.0, "material": Material(name="gold")},
        "model": LambertianScattering(albedo=0.8),
    },
    {
        "name": "LED on rough surface",
        "desc": "Green LED  Lambertian (albedo=0.5)  rough silicon",
        "src": _downward_source(LED, peak_wavelength=530e-9, width=25e-9, power=10e-3),
        "surface_gen": RoughSurface,
        "surface_kwargs": {"sigma": 6.0, "amplitude": 0.5, "material": Material(name="silicon")},
        "model": LambertianScattering(albedo=0.5),
    },
]

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _heatmap(arr: np.ndarray, max_width: int = 80, color: bool = True) -> str:
    """Render a 2D array as a terminal heatmap (same style as LightField.visualize)."""
    SHADES = [" ", "\u2591", "\u2592", "\u2593", "\u2588"]
    h, w = arr.shape
    scale = min(1.0, max_width / w)
    if scale < 1.0:
        nh, nw = max(1, int(h * scale)), max_width
        ir, jc = np.mgrid[0:h:nh * 1j, 0:w:nw * 1j]
        vals = arr[
            ir.astype(np.intp).clip(0, h - 1),
            jc.astype(np.intp).clip(0, w - 1),
        ]
    else:
        nh, nw, vals = h, w, arr

    vmin, vmax = float(vals.min()), float(vals.max())
    if vmax == vmin:
        norm = np.zeros_like(vals)
    else:
        norm = (vals - vmin) / (vmax - vmin)

    n_shades = len(SHADES) - 1
    shade_idx = (norm * n_shades).astype(np.intp).clip(0, n_shades)

    if not color:
        lines = ["".join(SHADES[idx] for idx in row) for row in shade_idx]
    else:
        lines = []
        for row in shade_idx:
            buf = []
            for idx in row:
                intensity = idx / n_shades
                if intensity < 0.25:
                    colour = 36
                elif intensity < 0.5:
                    colour = 32
                elif intensity < 0.75:
                    colour = 33
                else:
                    colour = 31
                buf.append(f"\033[1;{colour}m{SHADES[idx]}\033[0m")
            lines.append("".join(buf))

    header = (
        f"  ({nh}\u00d7{nw})  "
        f"min={vmin:.4g}  max={vmax:.4g}  "
        f"(scale factor = {1/scale:.2f}x)"
    )
    sep = "\u2500" * min(len(header), max_width)
    return f"{header}\n{sep}\n" + "\n".join(lines)


def fmt(val, unit=""):
    """Format a numeric value for display with optional unit."""
    if isinstance(val, float):
        if abs(val) < 1e-6:
            return f"{val:.3e} {unit}".strip()
        if val >= 1e3:
            return f"{val:.4g} {unit}".strip()
        return f"{val:.4g} {unit}".strip()
    return str(val)


# ---------------------------------------------------------------------------
# Illumination runner
# ---------------------------------------------------------------------------


def describe_source(src):
    """Return a multi-line string summarising a light source."""
    pol = src.polarization.kind if hasattr(src.polarization, "kind") else str(src.polarization)
    profile_name = type(src.beam_profile).__name__
    spec = src.spectral_distribution()
    spec_desc = f"{type(spec).__name__}"
    if hasattr(spec, "wavelength") and spec.wavelength:
        spec_desc += f" ({fmt(spec.wavelength, 'm')})"
    if hasattr(spec, "peak_wavelength") and spec.peak_wavelength:
        spec_desc += f" (peak {fmt(spec.peak_wavelength, 'm')})"
    if hasattr(spec, "temperature") and spec.temperature:
        spec_desc += f" ({fmt(spec.temperature, 'K')})"

    lines = [
        f"  Type:               {type(src).__name__}",
        f"  Wavelength:         {fmt(src.wavelength, 'm')}",
        f"  Power:              {fmt(src.power, 'W')}",
        f"  Polarization:       {pol}",
        f"  Coherence length:   {fmt(src.coherence_length, 'm')}",
        f"  Divergence:         {fmt(src.divergence, 'rad')}",
        f"  Beam profile:       {profile_name}",
        f"  Spectrum:           {spec_desc}",
        f"  Direction:          {np.array2string(src.propagation_direction, precision=3)}",
    ]
    return "\n".join(lines)


def run_illum_scenario(idx, shape=(32, 32), spacing=0.5):
    """Generate and display a light field for illumination scenario *idx* (1-based)."""
    if idx < 1 or idx > len(ILLUM_SCENARIOS):
        print(f"Invalid scenario {idx}. Choose 1\u2013{len(ILLUM_SCENARIOS)}.")
        return
    sc = ILLUM_SCENARIOS[idx - 1]
    src = sc["src"]

    header = f"  Scenario {idx}: {sc['name']}"
    print(f"\n{'=' * len(header)}")
    print(header)
    print(f"{'=' * len(header)}")
    print()
    print(describe_source(src))
    print()

    field = src.generate_light_field(shape=shape, spacing=spacing)
    print(f"  Light field ({shape[0]}\u00d7{shape[1]} grid, spacing={spacing}):")
    print(f"    Intensity shape:  {field.intensity.shape}")
    print(f"    Intensity range:  {field.intensity.min():.4g} \u2013 {field.intensity.max():.4g}")
    print(f"    Direction shape:  {field.direction.shape}")
    print(f"    Wavelength:       {fmt(field.wavelength, 'm')}")
    print(f"    Polarization:     {field.polarization.kind}")
    print(f"    Phase:            {'None' if field.phase is None else field.phase.shape}")
    print()
    print(field.visualize(max_width=80, color=True))
    print()


def print_illum_scenarios():
    """Print the predefined illumination scenarios."""
    print(f"\n{'=' * 60}")
    print(f"  Illumination scenarios ({len(ILLUM_SCENARIOS)} total)")
    print(f"{'=' * 60}")
    for i, sc in enumerate(ILLUM_SCENARIOS, 1):
        print(f"\n  [{i}] {sc['name']}")
        print(f"       {sc['desc']}")


# ---------------------------------------------------------------------------
# Surface runner
# ---------------------------------------------------------------------------


def describe_surface(surf):
    """Return a multi-line string summarising a surface."""
    lines = [
        f"  Type:               {type(surf).__name__}",
        f"  Shape:              {surf.height.shape}",
        f"  Height range:       {surf.height.min():.4g} \u2013 {surf.height.max():.4g}",
        f"  Roughness (RMS):    {surf.roughness:.4g}",
        f"  Curvature range:    {surf.curvature.min():.4g} \u2013 {surf.curvature.max():.4g}",
        f"  Material:           {surf.material.name} (n={surf.material.refractive_index})",
        f"  Slope_x range:      {surf.slope_x.min():.4g} \u2013 {surf.slope_x.max():.4g}",
        f"  Slope_y range:      {surf.slope_y.min():.4g} \u2013 {surf.slope_y.max():.4g}",
    ]
    return "\n".join(lines)


def run_surface_scenario(idx, shape=(32, 32)):
    """Generate and display a surface for surface scenario *idx* (1-based)."""
    if idx < 1 or idx > len(SURFACE_SCENARIOS):
        print(f"Invalid scenario {idx}. Choose 1\u2013{len(SURFACE_SCENARIOS)}.")
        return
    sc = SURFACE_SCENARIOS[idx - 1]
    gen = sc["gen"]
    surf = gen(shape, **sc["kwargs"])
    surface_type = type(surf).__name__

    header = f"  Scenario {idx}: {sc['name']}"
    print(f"\n{'=' * len(header)}")
    print(header)
    print(f"{'=' * len(header)}")
    print()
    print(describe_surface(surf))
    print()

    print(f"  Height map ({shape[0]}\u00d7{shape[1]}):")
    print(_heatmap(surf.height, max_width=80, color=True))
    print()

    mid = shape[0] // 2
    row = surf.height[mid, :]
    print(f"  Horizontal slice (row {mid}):")
    print(f"    {np.array2string(row, precision=4, suppress_small=True)}")
    print()


def print_surface_scenarios():
    """Print the predefined surface scenarios."""
    print(f"\n{'=' * 60}")
    print(f"  Surface scenarios ({len(SURFACE_SCENARIOS)} total)")
    print(f"{'=' * 60}")
    for i, sc in enumerate(SURFACE_SCENARIOS, 1):
        print(f"\n  [{i}] {sc['name']}")
        print(f"       {sc['desc']}")


# ---------------------------------------------------------------------------
# Scattering runner
# ---------------------------------------------------------------------------


def describe_scattering_setup(src, surf, model):
    """Return a multi-line string summarising the scattering setup."""
    lines = [
        f"  Light source:       {type(src).__name__} ({fmt(src.wavelength, 'm')}, {fmt(src.power, 'W')})",
        f"  Light direction:    {np.array2string(src.propagation_direction, precision=3)}",
        f"  Surface:            {type(surf).__name__} ({surf.material.name}, RMS={surf.roughness:.4g})",
        f"  Scattering model:   {type(model).__name__} (albedo={model.albedo})",
    ]
    return "\n".join(lines)


def run_scattering_scenario(idx, shape=(32, 32), spacing=0.5):
    """Generate and display a scattering evaluation for scenario *idx* (1-based)."""
    if idx < 1 or idx > len(SCATTERING_SCENARIOS):
        print(f"Invalid scenario {idx}. Choose 1\u2013{len(SCATTERING_SCENARIOS)}.")
        return
    sc = SCATTERING_SCENARIOS[idx - 1]
    src = sc["src"]
    surf = sc["surface_gen"](shape, **sc["surface_kwargs"])
    model = sc["model"]

    header = f"  Scenario {idx}: {sc['name']}"
    print(f"\n{'=' * len(header)}")
    print(header)
    print(f"{'=' * len(header)}")
    print()
    print(describe_scattering_setup(src, surf, model))
    print()

    lightfield = src.generate_light_field(shape=shape, spacing=spacing)
    view_dir = np.array([0.0, 0.0, 1.0])
    result = model.evaluate(lightfield, surf, view_direction=view_dir)

    print(f"  Scattered field ({shape[0]}\u00d7{shape[1]} grid, view={np.array2string(view_dir, precision=1)}):")
    print(f"    Radiance shape:   {result.radiance.shape}")
    print(f"    Radiance range:   {result.radiance.min():.4g} \u2013 {result.radiance.max():.4g}")
    print(f"    Outgoing dir:     {result.outgoing_direction.shape}")
    print(f"    Polarization:     {result.polarization}")
    print()
    print("  Scattered radiance heatmap:")
    print(_heatmap(result.radiance, max_width=80, color=True))
    print()


def print_scattering_scenarios():
    """Print the predefined scattering scenarios."""
    print(f"\n{'=' * 60}")
    print(f"  Scattering scenarios ({len(SCATTERING_SCENARIOS)} total)")
    print(f"{'=' * 60}")
    for i, sc in enumerate(SCATTERING_SCENARIOS, 1):
        print(f"\n  [{i}] {sc['name']}")
        print(f"       {sc['desc']}")


# ---------------------------------------------------------------------------
# Interactive menu
# ---------------------------------------------------------------------------


def interactive_menu(mode="illumination"):
    """Present an interactive menu for exploring scenarios.

    Parameters
    ----------
    mode : str
        One of ``"illumination"``, ``"surface"``, or ``"scattering"``.
    """
    if mode == "surface":
        scenarios = SURFACE_SCENARIOS
        run_fn = lambda i: run_surface_scenario(i, shape=(16, 16))
        printer = print_surface_scenarios
    elif mode == "scattering":
        scenarios = SCATTERING_SCENARIOS
        run_fn = lambda i: run_scattering_scenario(i, shape=(16, 16), spacing=0.5)
        printer = print_scattering_scenarios
    else:
        scenarios = ILLUM_SCENARIOS
        run_fn = lambda i: run_illum_scenario(i, shape=(16, 16), spacing=0.5)
        printer = print_illum_scenarios

    mode_label = mode.upper()
    mode_choices = {
        "illumination": "illumination (l)",
        "surface": "surface (s)",
        "scattering": "scattering (c)",
    }
    next_modes = {
        "illumination": "surface",
        "surface": "scattering",
        "scattering": "illumination",
    }

    while True:
        print(f"\n{'─' * 60}")
        print(f"  OPTICAL SCATTERING SIMULATION \u2014 Interactive Explorer [{mode_label}]")
        print(f"{'─' * 60}")
        print(f"  Scenarios available: {len(scenarios)}")
        for i, sc in enumerate(scenarios, 1):
            print(f"    [{i}] {sc['name']}")
        print(f"    [l] List all {mode_label.lower()} scenarios with details")
        print(f"    [i] Switch to illumination mode")
        print(f"    [s] Switch to surface mode")
        print(f"    [c] Switch to scattering mode")
        print(f"    [q] Quit")
        print(f"{'─' * 60}")
        choice = input(
            "  Choose (1\u2013{}, l, i, s, c, q): ".format(len(scenarios))
        ).strip().lower()

        if choice == "q":
            print("\n  Goodbye!")
            break
        if choice == "l":
            printer()
            continue
        if choice in ("i", "s", "c"):
            if choice == "c":
                return interactive_menu("scattering")
            elif choice == "s":
                return interactive_menu("surface")
            else:
                return interactive_menu("illumination")

        try:
            idx = int(choice)
        except ValueError:
            print(f"  Invalid input '{choice}'.")
            continue

        run_fn(idx)

        input("\n  Press Enter to continue...")

    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Explore the optical scattering sensor simulation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python explore.py                         # illumination menu
              python explore.py --surface               # surface menu
              python explore.py --scattering             # scattering menu
              python explore.py --run 1                 # illumination scenario 1
              python explore.py --surface --run 2       # surface scenario 2
              python explore.py --scattering --run 1    # scattering scenario 1
        """),
    )
    parser.add_argument("--scattering", action="store_true", help="operate on scattering scenarios")
    parser.add_argument("--surface", action="store_true", help="operate on surface scenarios")
    parser.add_argument("--list", action="store_true", help="list all scenarios")
    parser.add_argument("--run", type=int, metavar="N", help="run scenario N (1-based)")
    parser.add_argument("--all", action="store_true", help="run all scenarios")
    parser.add_argument("--shape", type=int, nargs=2, default=(16, 16), metavar=("H", "W"),
                        help="grid dimensions (default 16 16)")
    parser.add_argument("--spacing", type=float, default=0.5, help="grid spacing (default 0.5)")

    args = parser.parse_args()

    if args.scattering:
        scenarios = SCATTERING_SCENARIOS
        runner = lambda idx: run_scattering_scenario(idx, shape=tuple(args.shape), spacing=args.spacing)
        printer = print_scattering_scenarios
        menu_mode = "scattering"
    elif args.surface:
        scenarios = SURFACE_SCENARIOS
        runner = lambda idx: run_surface_scenario(idx, shape=tuple(args.shape))
        printer = print_surface_scenarios
        menu_mode = "surface"
    else:
        scenarios = ILLUM_SCENARIOS
        runner = lambda idx: run_illum_scenario(idx, shape=tuple(args.shape), spacing=args.spacing)
        printer = print_illum_scenarios
        menu_mode = "illumination"

    if args.list:
        printer()
        return 0

    if args.run is not None:
        runner(args.run)
        return 0

    if args.all:
        for i in range(1, len(scenarios) + 1):
            runner(i)
        return 0

    return interactive_menu(mode=menu_mode)


if __name__ == "__main__":
    sys.exit(main())