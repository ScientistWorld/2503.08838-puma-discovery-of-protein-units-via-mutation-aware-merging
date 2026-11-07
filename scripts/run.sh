#!/bin/bash
# Compute-node job: end-to-end reproduction of the reference.
#   1. build the fixed train / hidden-test populations (eval/test/prepare_split.py)
#   2. train PUMA(BLOSUM62, 0.7, 0.05) on the full corpus -> outputs/puma_6400/
#   3. score train slice, hidden test and default scores; validate.
# The hardening study (variants + shortcut probes, before/after scoring) is
# reproduced separately with: python hardening/run_hardening.py

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ ! -s eval/test/downloads/raw/clinical_substitutions/train-00000-of-00001.parquet ]; then
  echo "Missing raw ProteinGym data. Run scripts/download.sh on an internet-enabled node first." >&2
  exit 1
fi
for shard in 0 1 2 3 4; do
  file=$(printf "eval/test/downloads/raw/DMS_substitutions/train-%05d-of-00005.parquet" "$shard")
  [ -s "$file" ] || { echo "Missing $file. Run scripts/download.sh first." >&2; exit 1; }
done

bash scripts/reproduce.sh
