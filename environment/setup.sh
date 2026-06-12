#!/bin/bash
# Install Python packages into the container overlay.

set -euo pipefail

if ! command -v uv >/dev/null 2>&1; then
  python -m pip install uv
fi

uv pip install --system \
  biopython \
  more-itertools \
  numpy \
  pandas \
  pyarrow \
  scipy \
  tokenizers \
  tqdm
