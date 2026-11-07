#!/bin/bash
# Temporary audit dispatch; restored from the starting commit after the job.
set -euo pipefail
cd /home/user
bash redteam/run_all.sh
