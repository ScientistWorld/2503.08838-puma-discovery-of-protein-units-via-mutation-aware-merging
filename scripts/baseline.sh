#!/bin/bash
# Run the frequency-only BPE baseline released with the paper.

set -euo pipefail

cd /home/user

mkdir -p outputs/bpe_baseline
python baseline/run_bpe.py
bash scripts/evaluate.sh outputs/bpe_baseline/raw_results.json
