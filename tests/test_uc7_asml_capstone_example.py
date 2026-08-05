from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_uc7_asml_capstone_example_runs() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root / "src") + os.pathsep + env.get("PYTHONPATH", "")

    result = subprocess.run(
        [
            sys.executable,
            "notebooks/07_wafer_metrology/defect_capstone/run_asml_capstone.py",
            "--coherence",
            "1e-4",
            "--exposure",
            "0.001",
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert "ASML-style wafer defect inspection capstone" in result.stdout
    assert "defect_count=" in result.stdout
    assert "snr_db=" in result.stdout
