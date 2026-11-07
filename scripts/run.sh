#!/bin/bash
# Compute-node job: hardening verification run. Builds the split, trains the
# reference PUMA submission (scripts/method.sh), trains/builds variants and
# shortcut probes, scores them before/after, then regenerates the gym's score
# files from the reference alone and validates.

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

python hardening/run_hardening.py
