#!/bin/bash
# Train the paper's method, PUMA(BLOSUM62, a=0.7, f=0.05, lengths 3-12), with the
# official implementation on the full UniRef50-human corpus at the 6,400-unit
# budget, and write the submission to outputs/puma_6400/. Extra arguments are
# passed to method/run_puma.py (e.g. --output-dir, --min-freq, --cutoff).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python method/run_puma.py --output-dir outputs/puma_6400 "$@"
