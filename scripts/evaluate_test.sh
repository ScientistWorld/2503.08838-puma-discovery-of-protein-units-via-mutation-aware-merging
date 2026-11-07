#!/bin/bash
# Hidden test: score every method on disk (outputs/<method>/tokenizer.json +
# vocab.json) plus the evaluator-owned BPE baseline on held-out proteins.
# Takes no arguments; writes scoring/scores_test.json.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python eval/test/evaluate.py --scores scoring/scores_test.json
