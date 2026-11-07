"""Rerun the actual supplied PUMA trainer under explicit RNG/hash seeds."""
import argparse
import json
import random
import runpy
import sys
from pathlib import Path

import numpy as np

p = argparse.ArgumentParser()
p.add_argument("--seed", type=int, required=True)
p.add_argument("--output-dir", required=True)
p.add_argument("--cutoff", type=float, default=0.7)
a = p.parse_args()
random.seed(a.seed)
np.random.seed(a.seed)
sys.argv = ["method/run_puma.py", "--output-dir", a.output_dir, "--cutoff", str(a.cutoff)]
runpy.run_path("method/run_puma.py", run_name="__main__")
Path(a.output_dir, "audit_seed.json").write_text(json.dumps({"seed": a.seed, "cutoff": a.cutoff,
    "note": "Full corpus, actual official training algorithm; no resampling or labels."}, indent=2))
