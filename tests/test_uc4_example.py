from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_uc4_brdf_sweep_example_runs() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root / "src") + os.pathsep + env.get("PYTHONPATH", "")

    result = subprocess.run(
        [
            sys.executable,
            "notebooks/04_angle_resolved_scattering/run_brdf_sweep.py",
            "--theta-i-range",
            "0.0",
            "0.4",
            "3",
            "--theta-r-range",
            "0.0",
            "0.4",
            "3",
            "--phi-range",
            "0.0",
            "0.0",
            "1",
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert "UC4 BRDF sweep" in result.stdout
    assert "n_measurements=" in result.stdout
