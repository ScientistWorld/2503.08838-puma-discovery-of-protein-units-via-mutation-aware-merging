#!/bin/bash
# Visible train slice: score every method on disk (outputs/<method>/tokenizer.json
# + vocab.json) plus the evaluator-owned BPE baseline with the same protocol as
# the hidden test. Takes no arguments; writes scoring/scores_train.json.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python eval/train/evaluate.py --scores scoring/scores_train.json
