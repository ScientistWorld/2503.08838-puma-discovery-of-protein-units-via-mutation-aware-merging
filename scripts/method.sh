#!/bin/bash
# Run the paper's proposed PUMA method and score it.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

mkdir -p outputs/puma_reproduction checkpoints

python method/run_puma.py \
  --train-small \
  --train-sequences "${PUMA_TRAIN_SEQUENCES:-1200}" \
  --train-vocab-size "${PUMA_TRAIN_VOCAB_SIZE:-900}" \
  --max-per-label "${PUMA_MAX_PER_LABEL:-4000}" \
  --output outputs/puma_reproduction/raw_results.json

bash scripts/evaluate.sh outputs/puma_reproduction/raw_results.json
