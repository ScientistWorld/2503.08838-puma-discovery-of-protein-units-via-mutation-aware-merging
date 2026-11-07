#!/bin/bash
# Shortcut: fit clinical answers while forcing zero DMS sibling signal.
set -euo pipefail
cd /home/user
python redteam/v2_support/run_case.py v2_shortcut_abandon_dms
