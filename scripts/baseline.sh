#!/bin/bash
# The frequency-only BPE baseline (the paper's released 6,400-unit BPE
# vocabulary) is owned and scored by the evaluator itself as "bpe_6400".
# This script exports it in the submission format for reference and runs the
# visible evaluation.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python baseline/run_bpe.py --output-dir tmp/bpe_baseline_submission
bash scripts/evaluate_train.sh
