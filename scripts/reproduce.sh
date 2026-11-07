#!/bin/bash
# End-to-end reproduction of the reference: build the split, train PUMA, score
# train / hidden test / default, validate. Run scripts/download.sh first on an
# internet-enabled node.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

bash scripts/prepare_data.sh
bash scripts/method.sh
bash scripts/evaluate_train.sh
bash scripts/evaluate_test.sh
bash scripts/evaluate.sh
python validate.py --compare
