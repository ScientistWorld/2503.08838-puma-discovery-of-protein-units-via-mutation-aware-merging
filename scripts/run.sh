#!/bin/bash
# Compute-node job script for the compact PUMA reproduction with DMS scoring.

set -euo pipefail

cd /home/user

bash scripts/reproduce.sh
