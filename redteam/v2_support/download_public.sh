#!/bin/bash
# Independent downloads from URLs disclosed in the scientist-visible download.sh.
# Never copy or read the hidden evaluator's raw data or split.
set -euo pipefail
cd /home/user
base=https://huggingface.co/datasets/OATML-Markslab/ProteinGym_v1/resolve/main
fetch() {
  mkdir -p "$(dirname "$2")"
  if [ ! -s "$2" ]; then
    curl -L --fail --retry 3 "$1" -o "$2.part"
    mv "$2.part" "$2"
  fi
}
fetch "$base/clinical_substitutions/train-00000-of-00001.parquet" redteam/downloads/clinical.parquet
for shard in 0 1 2 3 4; do
  name=$(printf 'train-%05d-of-00005.parquet' "$shard")
  fetch "$base/DMS_substitutions/$name" "redteam/downloads/dms/$name"
done
