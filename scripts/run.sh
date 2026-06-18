#!/bin/bash
# Compute-node job script for train/test evaluation scoring.

set -euo pipefail

cd /home/user

bash scripts/evaluate_train.sh outputs/puma_reproduction/raw_results.json
bash scripts/evaluate_test.sh outputs/puma_reproduction/raw_results.json
