"""Lightweight checks of saved audit evidence; does not run a method."""
from __future__ import annotations

import hashlib
import json
import math
import statistics
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "redteam"
METHOD = "puma_official_6400"


def read(path):
    return json.loads(path.read_text())


def main():
    summary = read(AUDIT / "summary.json")
    definitions = read(AUDIT / "reference_definition.json")["experiments"]
    reference = read(AUDIT / "initial_scores_test.json")["experiments"]
    checks = []
    for name, entry in summary.items():
        folder = AUDIT / name
        run = read(folder / "run_result.json")
        assert (folder / "run.sh").is_file(), name
        assert run["test_command"] == ["bash", "scripts/evaluate_test.sh"], name
        assert all(run[step]["returncode"] == 0 for step in ("prepare", "train", "test")), name
        assert run["evaluators_unchanged"], name
        assert "exception" not in run, name
        for relative, digest in run["evaluators_sha256"].items():
            assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest, relative
        scores = read(folder / "scores_test.json")["experiments"]
        for method, ranked in entry["methods"].items():
            terms, absolute = [], []
            for experiment, spec in definitions.items():
                actual = scores[experiment]["results"][method]
                expected = reference[experiment]["results"][method]
                for metric, description in spec["metrics"].items():
                    assert math.isfinite(actual[metric]), (name, experiment, metric)
                    coefficient = spec["weight"] * description["coefficient"]
                    terms.append(coefficient * (actual[metric] - expected[metric]))
                    absolute.append(coefficient * actual[metric])
            assert math.isclose(math.fsum(terms), ranked["delta_vs_reference_test"], abs_tol=1e-10), name
            assert math.isclose(math.fsum(absolute), ranked["absolute_weighted_score"], abs_tol=1e-10), name
        checks.append({"name": name, "successful_steps": 3, "evaluator_hashes_match": True,
                       "finite_scores_and_independent_rank_arithmetic": True})
    assert len(checks) == 19
    assert read(AUDIT / "reference_seed7/scores_test.json") == read(AUDIT / "initial_scores_test.json")
    start = (AUDIT / "start_commit.txt").read_text().strip()
    # Explicit paths avoid pre-existing non-regular root files and system logs.
    protected = ["scripts", "scoring", "eval", "method", "baseline", "environment", "briefing", "data"]
    diff = subprocess.check_output(["git", "diff", "--name-only", start, "--", *protected], cwd=ROOT, text=True)
    assert not diff.strip(), diff
    samples = [summary[f"reference_seed{seed}"]["methods"][METHOD]["absolute_weighted_score"]
               for seed in (7, 17, 29)]
    result = {"successful_cases": checks, "case_count": len(checks),
              "reference_matches_initial_hidden_scores": True,
              "gym_source_and_scoring_match_start_commit": start,
              "seed_mean": statistics.mean(samples), "seed_sample_sd": statistics.stdev(samples),
              "seed_peak_to_peak_spread": max(samples) - min(samples)}
    (AUDIT / "validation.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "successful_cases"}, indent=2))


if __name__ == "__main__":
    main()
