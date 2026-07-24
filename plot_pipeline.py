"""Standalone pipeline script — runs the full simulation and saves matplotlib plots.

Usage:
    pip install matplotlib    # first install
    python plot_pipeline.py

Output files written to the current directory:
    pipeline_01_illumination.png   — laser intensity over the grid
    pipeline_02_surface.png        — surface height map
    pipeline_03_scattering.png     — scattered radiance
    pipeline_04_optics.png         — sensor-plane irradiance
    pipeline_05_detector.png       — digital image (ADU counts)
    pipeline_06_analysis.png       — histogram and statistics
"""

import os

import numpy as np

from illumination import Laser, GaussianBeamProfile
from surface import RoughSurface, Material
from scattering import LambertianScattering
from optics import OpticalSystem, GaussianPSF, OpticalPropagator
from detector import CMOSDetector
from analysis import ImageAnalyzer, HistogramAnalyzer


def main():
    np.random.seed(42)

    save_dir = "."
    shape = (64, 64)

    # ---- Layer 1: Illumination -------------------------------------------
    print("[1/6] Illumination …")
    laser = Laser(
        wavelength=532e-9,
        power=5e-3,
        beam_profile=GaussianBeamProfile(w0=3.0),
    )
    laser.propagation_direction = np.array([0.0, 0.0, -1.0])
    lf = laser.generate_light_field(shape=shape, spacing=0.4)

    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize

    fig, axes = plt.subplots(2, 3, figsize=(14, 9))
    fig.suptitle("Optical Scattering Sensor — Pipeline", fontsize=14, y=0.98)

    ax = axes[0, 0]
    im = ax.imshow(lf.intensity, cmap="inferno", aspect="equal")
    ax.set_title("1  Illumination (laser intensity)")
    ax.set_xlabel("pixel x"); ax.set_ylabel("pixel y")
    plt.colorbar(im, ax=ax, label="W / m²")

    # ---- Layer 2: Surface ------------------------------------------------
    print("[2/6] Surface geometry …")
    surface = RoughSurface(
        shape, sigma=6.0, amplitude=0.5,
        material=Material("silicon"),
    )

    ax = axes[0, 1]
    vlim = max(abs(surface.height.min()), abs(surface.height.max()))
    im = ax.imshow(surface.height, cmap="RdBu_r", norm=Normalize(-vlim, vlim), aspect="equal")
    ax.set_title("2  Surface height")
    ax.set_xlabel("pixel x"); ax.set_ylabel("pixel y")
    plt.colorbar(im, ax=ax, label="µm")
    ax.annotate(f"roughness = {surface.roughness:.4f}", (0.02, 0.93),
                xycoords="axes fraction", fontsize=9, color="white",
                bbox=dict(boxstyle="round,pad=0.3", fc="black", alpha=0.5))

    # ---- Layer 3: Scattering ---------------------------------------------
    print("[3/6] Scattering …")
    model = LambertianScattering(albedo=0.7)
    scattered = model.evaluate(
        lf, surface,
        view_direction=np.array([0.0, 0.0, 1.0]),
    )

    ax = axes[0, 2]
    im = ax.imshow(scattered.radiance, cmap="plasma", aspect="equal")
    ax.set_title("3  Scattered radiance")
    ax.set_xlabel("pixel x"); ax.set_ylabel("pixel y")
    plt.colorbar(im, ax=ax, label="W / sr / m²")

    # ---- Layer 4: Optics -------------------------------------------------
    print("[4/6] Optics …")
    optics = OpticalSystem(
        focal_length=0.05, aperture_diameter=0.008, wavelength=532e-9,
    )
    propagator = OpticalPropagator(psf_model=GaussianPSF(sigma=1.5))
    sensor = propagator.propagate(scattered, optics)

    ax = axes[1, 0]
    im = ax.imshow(sensor.irradiance, cmap="viridis", aspect="equal")
    ax.set_title("4  Sensor-plane irradiance")
    ax.set_xlabel("pixel x"); ax.set_ylabel("pixel y")
    plt.colorbar(im, ax=ax, label="W / m²")

    # ---- Layer 5: Detector -----------------------------------------------
    print("[5/6] Detector …")
    detector = CMOSDetector(
        exposure_time=2e-5,
        quantum_efficiency=0.9,
        dark_current=5.0,
        read_noise_sigma=2.0,
        full_well_capacity=80000.0,
        gain=1.0,
        bit_depth=12,
    )
    image = detector.capture(sensor)

    ax = axes[1, 1]
    im = ax.imshow(image.pixels, cmap="gray", aspect="equal")
    ax.set_title(f"5  Digital image ({detector.bit_depth}-bit)")
    ax.set_xlabel("pixel x"); ax.set_ylabel("pixel y")
    plt.colorbar(im, ax=ax, label="ADU")
    ax.annotate(f"range {image.pixels.min()}–{image.pixels.max()} ADU",
                (0.02, 0.93), xycoords="axes fraction", fontsize=9,
                color="white",
                bbox=dict(boxstyle="round,pad=0.3", fc="black", alpha=0.5))

    # ---- Layer 6: Analysis -----------------------------------------------
    print("[6/6] Analysis …")
    analyzer = ImageAnalyzer(modules=[HistogramAnalyzer()])
    report = analyzer.analyze(image)
    hist = report.histogram

    ax = axes[1, 2]
    values = np.unique(image.pixels)
    ax.bar(values, hist, width=1.0, color="steelblue", edgecolor="none")
    for key, val in sorted(report.measurements.items()):
        label = key.replace("_", " ").title()
        ax.text(0.96, 0.93 - 0.08 * list(report.measurements.keys()).index(key),
                f"{label}: {val:.1f}", transform=ax.transAxes,
                fontsize=9, ha="right", va="top",
                bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.7))
    ax.set_xlabel("Pixel value (ADU)")
    ax.set_ylabel("Count")
    ax.set_title("6  Histogram & statistics")

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    path = os.path.join(save_dir, "pipeline_full.png")
    fig.savefig(path, dpi=150)
    print(f"\nSaved → {path}  ({fig.get_size_inches()})")
    plt.close(fig)

    # ---- Individual layer plots -----------------------------------------------
    figures = [
        ("pipeline_01_illumination.png", lf.intensity, "Illumination (laser intensity)", "W / m²", "inferno"),
        ("pipeline_02_surface.png",      surface.height, "Surface height", "µm", "RdBu_r"),
        ("pipeline_03_scattering.png",   scattered.radiance, "Scattered radiance", "W / sr / m²", "plasma"),
        ("pipeline_04_optics.png",       sensor.irradiance, "Sensor-plane irradiance", "W / m²", "viridis"),
        ("pipeline_05_detector.png",     image.pixels.astype(float), "Digital image (ADU)", "ADU", "gray"),
    ]
    for fname, data, title, label, cmap in figures:
        fig, ax = plt.subplots(figsize=(5, 4.5))
        im = ax.imshow(data, cmap=cmap, aspect="equal")
        ax.set_title(title)
        plt.colorbar(im, ax=ax, label=label)
        fig.tight_layout()
        fig.savefig(os.path.join(save_dir, fname), dpi=150)
        print(f"  → {fname}")
        plt.close(fig)

    print("\nDone — all plots saved to", os.path.abspath(save_dir))


if __name__ == "__main__":
    main()
