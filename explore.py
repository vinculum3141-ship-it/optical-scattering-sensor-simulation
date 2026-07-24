#!/usr/bin/env python3
"""
Interactive exploration script for the illumination simulation.

Usage
-----
    python explore.py               # interactive menu-driven mode
    python explore.py --list        # list predefined scenarios
    python explore.py --run N       # run scenario N and print results
    python explore.py --all         # run all scenarios
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
)


SCENARIOS = [
    {
        "name": "Green laser pointer",
        "desc": "5 mW, 532 nm, Gaussian beam (w0=2), +z propagation",
        "source": Laser(wavelength=532e-9, power=5e-3, beam_profile=GaussianBeamProfile(w0=2.0)),
    },
    {
        "name": "Green LED",
        "desc": "10 mW, 530 nm peak, 25 nm FWHM, Gaussian profile, 0.5 rad divergence",
        "source": LED(peak_wavelength=530e-9, width=25e-9, power=10e-3),
    },
    {
        "name": "Sunlight",
        "desc": "Solar black-body at 5778 K, 1 W, uniform profile",
        "source": Sunlight(temperature=5778.0, power=1.0),
    },
    {
        "name": "Broadband lamp",
        "desc": "10 W, 400-700 nm flat spectrum, uniform profile",
        "source": BroadbandLamp(wavelength_range=(400e-9, 700e-9), power=10.0),
    },
    {
        "name": "High-power blue laser",
        "desc": "1 W, 445 nm, Gaussian beam (w0=0.5), linear polarization",
        "source": Laser(
            wavelength=445e-9,
            power=1.0,
            beam_profile=GaussianBeamProfile(w0=0.5),
            polarization=PolarizationState("linear"),
        ),
    },
    {
        "name": "Custom LED (red, wide)",
        "desc": "5 mW, 650 nm peak, 50 nm FWHM, top-hat profile",
        "source": LED(
            peak_wavelength=650e-9,
            width=50e-9,
            power=5e-3,
            beam_profile=TopHatBeamProfile(),
        ),
    },
]


def fmt(val, unit=""):
    """Format a numeric value for display with optional unit."""
    if isinstance(val, float):
        if abs(val) < 1e-6:
            return f"{val:.3e} {unit}".strip()
        if val >= 1e3:
            return f"{val:.4g} {unit}".strip()
        return f"{val:.4g} {unit}".strip()
    return str(val)


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


def print_scenario_list():
    """Print the predefined scenarios."""
    print(f"\n{'=' * 60}")
    print(f"  Predefined scenarios ({len(SCENARIOS)} total)")
    print(f"{'=' * 60}")
    for i, sc in enumerate(SCENARIOS, 1):
        print(f"\n  [{i}] {sc['name']}")
        print(f"       {sc['desc']}")


def run_scenario(idx, shape=(32, 32), spacing=0.5):
    """Generate and display a light field for scenario *idx* (1-based)."""
    if idx < 1 or idx > len(SCENARIOS):
        print(f"Invalid scenario {idx}. Choose 1–{len(SCENARIOS)}.")
        return
    sc = SCENARIOS[idx - 1]
    src = sc["source"]

    header = f"  Scenario {idx}: {sc['name']}"
    print(f"\n{'=' * len(header)}")
    print(header)
    print(f"{'=' * len(header)}")
    print()
    print(describe_source(src))
    print()

    field = src.generate_light_field(shape=shape, spacing=spacing)
    print(f"  Light field ({shape[0]}×{shape[1]} grid, spacing={spacing}):")
    print(f"    Intensity shape:  {field.intensity.shape}")
    print(f"    Intensity range:  {field.intensity.min():.4g} – {field.intensity.max():.4g}")
    print(f"    Direction shape:  {field.direction.shape}")
    print(f"    Wavelength:       {fmt(field.wavelength, 'm')}")
    print(f"    Polarization:     {field.polarization.kind}")
    print(f"    Phase:            {'None' if field.phase is None else field.phase.shape}")

    peak_row = shape[0] // 2
    centre = field.intensity[peak_row, :]
    if centre.size <= 32:
        print(f"\n  Horizontal slice at row {peak_row}:")
        print(f"    {np.array2string(centre, precision=4, suppress_small=True)}")
    print()


def interactive_menu():
    """Present an interactive menu for exploring scenarios."""
    while True:
        print(f"\n{'─' * 60}")
        print("  OPTICAL SCATTERING SIMULATION — Interactive Explorer")
        print(f"{'─' * 60}")
        print(f"  Scenarios available: {len(SCENARIOS)}")
        for i, sc in enumerate(SCENARIOS, 1):
            print(f"    [{i}] {sc['name']}")
        print(f"    [l] List all scenarios with details")
        print(f"    [q] Quit")
        print(f"{'─' * 60}")
        choice = input("  Choose scenario (1–{}, l, q): ".format(len(SCENARIOS))).strip().lower()

        if choice == "q":
            print("\n  Goodbye!")
            break
        if choice == "l":
            print_scenario_list()
            continue

        try:
            idx = int(choice)
        except ValueError:
            print(f"  Invalid input '{choice}'.")
            continue

        run_scenario(idx, shape=(16, 16), spacing=0.5)

        input("\n  Press Enter to continue...")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Explore the illumination simulation interactively.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python explore.py --list
              python explore.py --run 1
              python explore.py --all
              python explore.py          # interactive mode
        """),
    )
    parser.add_argument("--list", action="store_true", help="list all predefined scenarios")
    parser.add_argument("--run", type=int, metavar="N", help="run scenario N (1-based)")
    parser.add_argument("--all", action="store_true", help="run all scenarios")
    parser.add_argument("--shape", type=int, nargs=2, default=(16, 16), metavar=("H", "W"),
                        help="grid dimensions (default 16 16)")
    parser.add_argument("--spacing", type=float, default=0.5, help="grid spacing (default 0.5)")

    args = parser.parse_args()

    if args.list:
        print_scenario_list()
        return 0

    if args.run is not None:
        run_scenario(args.run, shape=tuple(args.shape), spacing=args.spacing)
        return 0

    if args.all:
        for i in range(1, len(SCENARIOS) + 1):
            run_scenario(i, shape=tuple(args.shape), spacing=args.spacing)
        return 0

    return interactive_menu()


if __name__ == "__main__":
    sys.exit(main())
