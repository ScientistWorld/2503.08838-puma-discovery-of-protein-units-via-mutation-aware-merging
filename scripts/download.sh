#!/bin/bash
# Download all data and models needed for this environment.
#
# Estimated total download size: ~120 MB
# Estimated disk usage after extraction: ~120 MB

set -euo pipefail

cd /home/user

mkdir -p data/downloads/proteingym_clinical_substitutions
mkdir -p data/downloads/proteingym_dms_substitutions

if [ ! -e data/downloads/proteingym_clinical_substitutions/train-00000-of-00001.parquet ]; then
  curl -L --fail \
    https://huggingface.co/datasets/OATML-Markslab/ProteinGym_v1/resolve/main/clinical_substitutions/train-00000-of-00001.parquet \
    -o data/downloads/proteingym_clinical_substitutions/train-00000-of-00001.parquet
fi

for shard in 0 1 2 3 4; do
  file=$(printf "train-%05d-of-00005.parquet" "$shard")
  if [ ! -e "data/downloads/proteingym_dms_substitutions/$file" ]; then
    curl -L --fail \
      "https://huggingface.co/datasets/OATML-Markslab/ProteinGym_v1/resolve/main/DMS_substitutions/$file" \
      -o "data/downloads/proteingym_dms_substitutions/$file"
  fi
done
