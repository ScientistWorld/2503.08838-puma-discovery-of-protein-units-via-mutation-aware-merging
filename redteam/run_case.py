"""Run one candidate, visible evaluation, then the unmodified hidden test.

Candidate preparation and both evaluators are separate processes. Nothing
started by preparation survives. No environment/process manipulation is used.
The test is always invoked with precisely `bash scripts/evaluate_test.sh`.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOUCHED = ["outputs/puma_reproduction/raw_results.json", "scoring/scores_train.json", "scoring/scores_test.json"]


def run(name):
    out = ROOT / "redteam" / name
    saved = {p: (ROOT / p).read_bytes() if (ROOT / p).exists() else None for p in TOUCHED}
    protected = [ROOT / "scripts/evaluate_test.sh", *sorted((ROOT / "eval").rglob("*.py"))]
    before = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
    result = {"name": name, "started": time.time(), "test_command": ["bash", "scripts/evaluate_test.sh"],
              "evaluators_sha256": before}
    steps = [("prepare", [sys.executable, "redteam/candidates.py", str(out)]),
             ("train", ["bash", "scripts/evaluate_train.sh"]),
             ("test", ["bash", "scripts/evaluate_test.sh"])]
    try:
        for step, command in steps:
            started = time.time()
            with (out / f"{step}.log").open("w") as log:
                proc = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=3300)
            result[step] = {"returncode": proc.returncode, "seconds": time.time() - started}
            if proc.returncode:
                result["error_tail"] = (out / f"{step}.log").read_text()[-5000:]
                break
            if step in ("train", "test"):
                shutil.copyfile(ROOT / f"scoring/scores_{step}.json", out / f"scores_{step}.json")
        after = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
        result["evaluators_unchanged"] = before == after
        if before != after:
            raise RuntimeError("Evaluator changed unexpectedly")
    except Exception as error:
        result["exception"] = repr(error)
    finally:
        for relative, contents in saved.items():
            path = ROOT / relative
            if contents is None:
                path.unlink(missing_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(contents)
        result["seconds"] = time.time() - result["started"]
        (out / "run_result.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2), flush=True)
    return 0 if result.get("test", {}).get("returncode") == 0 and "exception" not in result else 1


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1]))
