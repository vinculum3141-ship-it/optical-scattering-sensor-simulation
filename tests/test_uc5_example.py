from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_uc5_structured_light_example_runs() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root / "src") + os.pathsep + env.get("PYTHONPATH", "")

    result = subprocess.run(
        [
            sys.executable,
            "notebooks/05_structured_light_3d/run_structured_light.py",
            "--period",
            "16.0",
            "--projection-angle",
            "0.5",
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert "UC5 structured light" in result.stdout
    assert "reconstructed_rms=" in result.stdout
