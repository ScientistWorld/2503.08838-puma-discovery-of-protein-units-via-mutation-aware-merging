#!/bin/bash
# Evaluate the held-out test slice from the same artifacts scored on train.
#
# Usage:
#   bash scripts/evaluate_test.sh [raw_results_json]

set -euo pipefail

cd /home/user

RAW_PATH="${1:-outputs/puma_reproduction/raw_results.json}"
python eval/test/evaluate_puma.py \
  --raw "$RAW_PATH" \
  --scores scoring/scores_test.json \
  --train-scores scoring/scores_train.json \
  --require-train-scores
