#!/bin/bash
# Run the frequency-only BPE baseline released with the paper.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

mkdir -p outputs/bpe_baseline
python baseline/run_bpe.py
bash scripts/evaluate.sh outputs/bpe_baseline/raw_results.json
