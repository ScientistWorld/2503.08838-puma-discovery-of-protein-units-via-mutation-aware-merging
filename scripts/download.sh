#!/bin/bash
# Download everything this environment needs from public sources, then build
# the fixed train / hidden-test variant populations.
#
#   ProteinGym v1 clinical substitutions (~9 MB) and DMS substitutions (~110 MB)
#   are fetched from Hugging Face into eval/test/downloads/raw/. The labelled
#   raw files belong to the hidden test; eval/test/prepare_split.py writes the
#   agent-visible TRAIN populations to data/downloads/proteingym_train/ and the
#   held-out TEST populations to eval/test/downloads/split/.
#
# The UniRef50-human training corpus (data/uniref50_human.fasta), the released
# PUMA/BPE vocabularies (method/PUMA_official/RSRC/) and the evaluator's fixed
# BPE baseline (eval/*/baseline_bpe_6400_tokenizer.json) are tracked in git.
# They originate from https://github.com/boun-tabi-lifelu/PUMA (RSRC/).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

RAW=eval/test/downloads/raw
HF=https://huggingface.co/datasets/OATML-Markslab/ProteinGym_v1/resolve/main
mkdir -p "$RAW/clinical_substitutions" "$RAW/DMS_substitutions"

fetch() {  # fetch <url> <dest>  (idempotent)
  if [ ! -s "$2" ]; then
    curl -L --fail --retry 3 "$1" -o "$2.tmp"
    mv "$2.tmp" "$2"
  fi
}

fetch "$HF/clinical_substitutions/train-00000-of-00001.parquet" \
  "$RAW/clinical_substitutions/train-00000-of-00001.parquet"
for shard in 0 1 2 3 4; do
  file=$(printf "train-%05d-of-00005.parquet" "$shard")
  fetch "$HF/DMS_substitutions/$file" "$RAW/DMS_substitutions/$file"
done

# Re-fetch the tracked PUMA artifacts only if they are missing (e.g. a sparse clone).
PUMA_RAW=https://raw.githubusercontent.com/boun-tabi-lifelu/PUMA/main
for f in RSRC/vocabs/uniref50_mutbpe_0.7_3_12_0.05_6400.json RSRC/vocabs/hf_uniref50_mutbpe_0.7_3_12_0.05_6400.json \
         RSRC/vocabs/uniref50_bpe_6400.json RSRC/vocabs/hf_uniref50_bpe_6400.json; do
  mkdir -p "$(dirname "method/PUMA_official/$f")"
  fetch "$PUMA_RAW/$f" "method/PUMA_official/$f"
done
if [ ! -s data/uniref50_human.fasta ]; then
  fetch "$PUMA_RAW/RSRC/dataset/uniref_50.fasta" data/uniref50_human.fasta
fi
for side in train test; do
  [ -s "eval/$side/baseline_bpe_6400_tokenizer.json" ] || cp method/PUMA_official/RSRC/vocabs/hf_uniref50_bpe_6400.json "eval/$side/baseline_bpe_6400_tokenizer.json"
done

# Build the split now if the Python stack is available; otherwise
# scripts/prepare_data.sh (or the first hidden-test run) builds it in the container.
if python -c "import pandas, pyarrow" >/dev/null 2>&1; then
  bash scripts/prepare_data.sh
else
  echo "pandas/pyarrow not available here: run 'bash scripts/prepare_data.sh' inside the container to build the split."
fi
