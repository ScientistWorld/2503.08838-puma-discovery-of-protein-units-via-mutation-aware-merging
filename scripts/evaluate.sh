#!/bin/bash
# Default development evaluation: the visible train slice, written to
# scoring/scores.json (same evaluator and protocol as scripts/evaluate_train.sh).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python eval/train/evaluate.py --scores scoring/scores.json
