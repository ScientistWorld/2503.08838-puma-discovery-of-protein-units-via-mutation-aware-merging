#!/bin/bash
# Run the frequency-only BPE baseline released with the paper.

set -euo pipefail

cd /home/user

mkdir -p outputs/puma_reproduction
python baseline/run_bpe.py
bash scripts/evaluate.sh outputs/puma_reproduction/raw_results.json
