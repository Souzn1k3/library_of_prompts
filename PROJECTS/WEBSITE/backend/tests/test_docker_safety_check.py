from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_docker_safety_check_static_mode() -> None:
    backend_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "scripts/docker_safety_check.py", "--mode", "static"],
        cwd=backend_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
