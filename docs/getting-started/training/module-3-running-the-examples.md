# Module 3 — Running the Example Projects

> **Goal:** navigate the notebook units, run the CLI scripts, and pick a
> use case to explore in depth.
>
> **Prerequisites:** [Module 2](module-2-the-six-layers.md).

The example projects live in `notebooks/` as **units** — one folder per
use case, each containing a tutorial notebook, a CLI script, and a
README.

## 1. The Units

| Unit | Folder | What it demonstrates |
|---|---|---|
| 00 | `notebooks/00_getting_started/` | Full pipeline, end to end |
| 01 | `notebooks/01_surface_defect_inspection/` | Defect inspection, bright/dark-field |
| 02 | `notebooks/02_multispectral_identification/` | Spectral material ID |
| 03 | `notebooks/03_sensor_characterization/` | PTC, dynamic range, linearity |
| 04 | `notebooks/04_angle_resolved_scattering/` | BRDF sweeps and fitting |
| 05 | `notebooks/05_structured_light_3d/` | Fringe-projection 3D scanning |
| 06 | `notebooks/06_lidar_ranging/` | LiDAR range finding |
| 07 | `notebooks/07_wafer_metrology/` | Die alignment + defect capstone |

The full index is at `notebooks/README.md`.

## 2. Run a CLI Script

Every unit ships a script that takes parameters as command-line
arguments. No notebook needed:

```bash
python notebooks/01_surface_defect_inspection/run_inspection.py \
    --defect dent --illumination darkfield --threshold 0.08
```

```bash
python notebooks/06_lidar_ranging/run_lidar.py --target-range 10.0 --reflectance 0.8
```

```bash
python notebooks/04_angle_resolved_scattering/run_brdf_sweep.py
```

Try changing one flag at a time and observe how the reported metrics
move.

## 3. Run a Tutorial Notebook

Notebooks require Jupyter (`pip install -e ".[visualisation]"`):

```bash
jupyter notebook notebooks/06_lidar_ranging/lidar_tutorial.ipynb
```

Every notebook follows the same pattern:

1. **Intro** — objective and what you will see.
2. **Editable parameters** — one cell where the inputs live.
3. **Pipeline cells** — the simulation, step by step.
4. **Try next** — one-parameter-at-a-time experiments.

Change one parameter, re-run the notebook, compare.

## 4. Choose a Use Case

Start with the one closest to your interest:

- Hardware / camera people → [UC3 sensor characterisation](../../use-cases/uc3-sensor-characterization.md)
- Materials / coatings → [UC4 BRDF sweep](../../use-cases/uc4-angle-resolved-scattering.md)
- Metrology / inspection → [UC1 defect inspection](../../use-cases/uc1-surface-defect-inspection.md) or [UC7 wafer](../../use-cases/uc7-alignment.md)
- 3D / range sensing → [UC5 structured light](../../use-cases/uc5-structured-light-3d.md) or [UC6 LiDAR](../../use-cases/uc6-lidar-ranging.md)

Each use-case page ([`docs/use-cases/`](../../use-cases/index.md)) explains
the objective, workflow, what it demonstrates, and links to the notebook
unit.

## Exercises

1. Run `run_lidar.py` with `--target-range 5`, `10`, `20`. What trend do
   you see in received power? (This is the inverse-square law in action.)
2. Run `run_inspection.py` with `--illumination brightfield` and then
   `darkfield`. Which one highlights a dent better, and why?
3. Open one notebook and change exactly one parameter. Does the result
   match your intuition?

## Check Your Understanding

- How is a notebook unit structured?
- What is the difference between running a CLI script and a notebook?
- Which unit would you use to measure a camera's dynamic range?

## Next

[Module 4 — Building Your Own Simulation](module-4-building-your-own-simulation.md)
— assemble a custom pipeline and extend the framework.
