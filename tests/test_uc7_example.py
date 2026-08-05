from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_uc7_wafer_alignment_example_runs() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root / "src") + os.pathsep + env.get("PYTHONPATH", "")

    result = subprocess.run(
        [
            sys.executable,
            "notebooks/07_wafer_metrology/alignment/run_alignment.py",
            "--shift",
            "3",
            "--rotation",
            "2.0",
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert "UC7 wafer alignment" in result.stdout
    assert "match_score=" in result.stdout
    assert "match_score=0.0000" not in result.stdout
