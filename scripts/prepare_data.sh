#!/bin/bash
# Build the fixed train / hidden-test variant populations from the raw
# ProteinGym downloads (idempotent; run inside the gym container).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
python eval/test/prepare_split.py "$@"
