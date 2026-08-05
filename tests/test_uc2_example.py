from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_uc2_multispectral_classification_example_runs() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root / "src") + os.pathsep + env.get("PYTHONPATH", "")

    result = subprocess.run(
        [
            sys.executable,
            "notebooks/02_multispectral_identification/run_classification.py",
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert "UC2 multispectral classification" in result.stdout
    assert "dominant_label=" in result.stdout
