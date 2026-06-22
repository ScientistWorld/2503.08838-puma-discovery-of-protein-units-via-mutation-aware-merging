#!/bin/bash
# End-to-end compact reproduction. Run scripts/download.sh first on an
# internet-enabled node; compute nodes are expected to start with data present.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ ! -e data/downloads/proteingym_clinical_substitutions/train-00000-of-00001.parquet ]; then
  echo "Missing ProteinGym clinical parquet. Run bash scripts/download.sh before reproduce.sh." >&2
  exit 1
fi
for shard in 0 1 2 3 4; do
  file=$(printf "data/downloads/proteingym_dms_substitutions/train-%05d-of-00005.parquet" "$shard")
  if [ ! -e "$file" ]; then
    echo "Missing ProteinGym DMS shard $file. Run bash scripts/download.sh before reproduce.sh." >&2
    exit 1
  fi
done

bash scripts/method.sh
python validate.py --compare
