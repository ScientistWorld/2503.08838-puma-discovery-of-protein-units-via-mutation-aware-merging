"""Lightweight evidence/restore consistency check; no training or inference."""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUPPORT = ROOT / "redteam/v2_support"


def load(path):
    return json.loads(path.read_text())


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


cases = load(SUPPORT / "cases.json")
summary = load(SUPPORT / "summary.json")
definition = load(SUPPORT / "reference_definition.json")
reference = load(SUPPORT / "initial_reference_scores_test.json")
assert len(cases) == 20 and set(cases) == set(summary["cases"])
protected = None
for name in cases:
    folder = ROOT / "redteam" / name
    receipt = load(folder / "run_receipt.json")
    scores = load(folder / "scores_test.json")
    rank = load(folder / "rank.json")
    assert receipt["success"] and receipt["evaluators_unchanged"], name
    assert receipt["test_command"] == ["bash", "scripts/evaluate_test.sh"], name
    assert receipt["steps"][-1]["command"] == receipt["test_command"], name
    assert all(step["returncode"] == 0 for step in receipt["steps"]), name
    assert protected is None or protected == receipt["evaluator_hashes"], name
    protected = receipt["evaluator_hashes"]
    assert rank == summary["cases"][name], name
    assert (folder / "run.sh").is_file() and (folder / "scores_train.json").is_file(), name
    actual = ref = 0.0
    for experiment, spec in definition["experiments"].items():
        for metric, setting in spec["metrics"].items():
            scale = spec["weight"] * setting.get("coefficient", 0)
            if not scale:
                continue
            assert setting["higher_is_better"], (experiment, metric)
            actual += scale * scores["experiments"][experiment]["results"][receipt["submitted_name"]][metric]
            ref += scale * reference["experiments"][experiment]["results"]["puma_6400"][metric]
    assert math.isclose(actual, rank["absolute_score"], abs_tol=1e-15), name
    assert math.isclose(actual - ref, rank["rank_delta"], abs_tol=1e-15), name
    for experiment in definition["experiments"]:
        assert scores["experiments"][experiment]["results"]["bpe_6400"] == reference["experiments"][experiment]["results"]["bpe_6400"], name

for path, expected in protected.items():
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected, path

for seed in (7, 17, 29):
    training = load(ROOT / f"redteam/v2_reference_seed{seed}/training_summary.json")
    assert training["n_sequences"] == 70692 and training["labels_used"] is False
assert summary["seed_summary"]["spread"] == 0
s = summary["cases"]
assert s["v2_better_chemical_families"]["absolute_score"] > s["v2_reference_seed7"]["absolute_score"] > s["v2_weaker_no_genealogy"]["absolute_score"]
assert s["v2_better_cutoff060"]["rank_delta"] > 0
for name in ("visible_label_fitting", "public_answer_fitting", "abandon_dms"):
    assert s["v2_shortcut_" + name]["rank_delta"] > 0
assert s["v2_shortcut_abandon_dms"]["metrics"]["dms_sibling_association.positive_negative_gap"] == 0
assert all(v["sibling"] == 0 for v in s["v2_shortcut_abandon_dms"]["validation"]["counts"]["dms"].values())
assert s["v2_shortcut_identical_artifact"]["rank_delta"] == 0

start = (SUPPORT / "start_commit.txt").read_text().strip()
restored_trees = ["scripts", "method", "baseline", "data", "eval", "scoring", "environment", "briefing"]
assert not git("diff", "--name-only", start, "--", *restored_trees), "Source/score restoration failed"
initial = {line[3:] for line in (SUPPORT / "initial_git_status.txt").read_text().splitlines() if line and not line.startswith("??")}
external = git("diff", "--name-only", start, "--", ".", ":(exclude)redteam", ":(exclude)REDTEAM.md").splitlines()
classified = {"pre_existing_setup_changes": [], "system_job_records": [], "required_action_protocol": [], "unexpected": []}
for path in external:
    if path == "action.yaml":
        category = "required_action_protocol"
    elif path in initial:
        category = "pre_existing_setup_changes"
    elif path.startswith("jobs/"):
        category = "system_job_records"
    else:
        category = "unexpected"
    classified[category].append(path)
assert not classified["unexpected"], classified["unexpected"]
result = {"cases_checked": len(cases), "all_evaluations_completed": True,
          "all_ranks_recomputed_from_original_coefficients": True,
          "all_evaluator_hashes_unchanged": True, "fixed_baseline_results_unchanged": True,
          "seed_trainings_use_full_corpus": True,
          "start_commit": start, "source_and_score_trees_restored": restored_trees,
          "external_changes": classified}
(SUPPORT / "validation.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
