#!/bin/bash
# End-to-end compact reproduction.

set -euo pipefail

cd /home/user

bash scripts/download.sh
bash scripts/method.sh
python validate.py --compare
