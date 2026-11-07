#!/bin/bash
# Temporary audit job launcher; restored to the initial version at completion.
set -euo pipefail
cd /home/user
python redteam/v2_support/run_all.py
