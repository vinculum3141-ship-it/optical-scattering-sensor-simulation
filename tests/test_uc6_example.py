from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_uc6_lidar_example_runs() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root / "src") + os.pathsep + env.get("PYTHONPATH", "")

    result = subprocess.run(
        [
            sys.executable,
            "examples/run_uc6_lidar.py",
            "--range-m",
            "12.0",
            "--backscatter",
            "1e-4",
            "--pulse-duration",
            "1e-9",
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert "UC6 LiDAR ranging" in result.stdout
    assert "received_power=" in result.stdout
