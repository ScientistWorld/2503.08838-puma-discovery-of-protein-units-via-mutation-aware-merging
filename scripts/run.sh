#!/bin/bash
# Compute-node job script for end-to-end compact PUMA verification.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ ! -e data/downloads/proteingym_clinical_substitutions/train-00000-of-00001.parquet ]; then
  echo "Missing ProteinGym clinical data. Run scripts/download.sh on an internet-enabled node before submitting." >&2
  exit 1
fi
if [ ! -e data/uniref50_human.fasta ]; then
  echo "Missing tracked UniRef50-human FASTA at data/uniref50_human.fasta." >&2
  exit 1
fi
for shard in 0 1 2 3 4; do
  file=$(printf "data/downloads/proteingym_dms_substitutions/train-%05d-of-00005.parquet" "$shard")
  if [ ! -e "$file" ]; then
    echo "Missing ProteinGym DMS shard $file. Run scripts/download.sh on an internet-enabled node before submitting." >&2
    exit 1
  fi
done

bash scripts/method.sh
bash scripts/evaluate_train.sh outputs/puma_reproduction/raw_results.json
bash scripts/evaluate_test.sh outputs/puma_reproduction/raw_results.json
python validate.py --compare
