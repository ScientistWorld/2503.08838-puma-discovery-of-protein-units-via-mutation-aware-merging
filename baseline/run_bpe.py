#!/usr/bin/env python3
"""Baseline entry point.

The baseline is frequency-only BPE using the official vocabulary released with
the paper. It is evaluated by method/run_puma.py in the same artifact format as
PUMA so scripts/evaluate.sh can score both methods consistently.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    subprocess.run(
        [
            "python",
            str(ROOT / "method" / "run_puma.py"),
            "--output",
            "outputs/puma_reproduction/raw_results.json",
            "--max-per-label",
            "4000",
        ],
        check=True,
    )
