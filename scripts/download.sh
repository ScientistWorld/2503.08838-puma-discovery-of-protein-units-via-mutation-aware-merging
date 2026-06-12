#!/bin/bash
# Download all data and models needed for this environment.
#
# Estimated total download size: ~9 MB
# Estimated disk usage after extraction: ~9 MB

set -euo pipefail

cd /home/user

mkdir -p data/downloads/proteingym_clinical_substitutions

if [ ! -e data/downloads/proteingym_clinical_substitutions/train-00000-of-00001.parquet ]; then
  curl -L --fail \
    https://huggingface.co/datasets/OATML-Markslab/ProteinGym_v1/resolve/main/clinical_substitutions/train-00000-of-00001.parquet \
    -o data/downloads/proteingym_clinical_substitutions/train-00000-of-00001.parquet
fi
