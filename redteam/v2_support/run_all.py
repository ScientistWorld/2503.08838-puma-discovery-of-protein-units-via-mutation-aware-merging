"""Single compute-node job, resumable per case, preserving each test receipt."""
import json
import subprocess
import sys
import time
from pathlib import Path

root = Path('/home/user')
cases = json.loads((root / 'redteam/v2_support/cases.json').read_text())
status = {}
for name in cases:
    folder = root / 'redteam' / name
    receipt = folder / 'run_receipt.json'
    if receipt.exists() and json.loads(receipt.read_text()).get('success'):
        print('Already completed', name, flush=True)
        continue
    print(time.strftime('%H:%M:%S'), 'Running', name, flush=True)
    try:
        rc = subprocess.run(['bash', str(folder / 'run.sh')], cwd=root, timeout=5200).returncode
    except subprocess.TimeoutExpired:
        rc = 'timeout'
    status[name] = rc
    (root / 'redteam/v2_support/job_progress.json').write_text(json.dumps(status, indent=2))
subprocess.run([sys.executable, 'redteam/v2_support/summarize.py'], cwd=root, check=True)
