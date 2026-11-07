"""Post-run audit arithmetic, never imported by a candidate."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "redteam"
PUMA = "puma_official_6400"
BPE = "bpe_official_6400"


def load(path):
    return json.loads(path.read_text())


def main():
    definitions = load(AUDIT / "reference_definition.json")["experiments"]
    reference = load(AUDIT / "reference_seed7/scores_test.json")["experiments"]
    summary = {}
    for folder in sorted(AUDIT.iterdir()):
        scorefile = folder / "scores_test.json"
        if not scorefile.exists():
            continue
        scores = load(scorefile)["experiments"]
        methods = scores["clinical_sibling_association"]["results"]
        entry = {"methods": {}}
        for name in methods:
            detail = {}
            absolute = 0.0
            delta = 0.0
            for exp, spec in definitions.items():
                actual = scores[exp]["results"][name]
                expected = reference[exp]["results"][name]
                contributions = {}
                for metric, metadata in spec["metrics"].items():
                    coefficient = metadata["coefficient"] * spec["weight"]
                    contributions[metric] = coefficient * (actual[metric] - expected[metric])
                    absolute += coefficient * actual[metric]
                subtotal = sum(contributions.values())
                delta += subtotal
                detail[exp] = {"delta": subtotal, "metric_contributions": contributions}
            entry["methods"][name] = {"absolute_weighted_score": absolute,
                                       "delta_vs_reference_test": delta, "by_experiment": detail}
        entry["delta_summed_over_present_methods"] = sum(x["delta_vs_reference_test"] for x in entry["methods"].values())
        (folder / "rank.json").write_text(json.dumps(entry, indent=2))
        summary[folder.name] = entry
    (AUDIT / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps({k: {m: v["delta_vs_reference_test"] for m, v in x["methods"].items()}
                      for k, x in summary.items()}, indent=2))


if __name__ == "__main__":
    main()
