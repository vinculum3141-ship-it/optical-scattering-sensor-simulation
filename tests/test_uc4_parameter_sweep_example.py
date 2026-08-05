from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_parameter_sweep_example_runs() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root / "src") + os.pathsep + env.get("PYTHONPATH", "")

    result = subprocess.run(
        [
            sys.executable,
            "examples/run_parameter_sweep.py",
            "--roughness",
            "0.05",
            "0.3",
            "--theta-i",
            "0.0",
            "--wavelength",
            "450e-9",
            "650e-9",
            "--refractive-index",
            "1.5",
            "3.5",
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert "Multi-parameter scattering sweep" in result.stdout
    assert "n_cases:" in result.stdout
