#!/usr/bin/env python3
"""Evaluate PUMA reproduction artifacts without importing method code."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def clinical_metric_block(method_result: dict) -> dict[str, float]:
    labels = method_result["labels"]
    benign = labels.get("benign") or labels.get("Benign")
    pathogenic = labels.get("pathogenic") or labels.get("Pathogenic")
    if benign is None or pathogenic is None:
        raise ValueError(f"Expected benign/pathogenic labels, got {sorted(labels)}")
    benign_rate = float(benign["same_sibling_rate"])
    pathogenic_rate = float(pathogenic["same_sibling_rate"])
    return {
        "benign_same_sibling_rate": benign_rate,
        "pathogenic_same_sibling_rate": pathogenic_rate,
        "benign_pathogenic_gap": benign_rate - pathogenic_rate,
        "benign_same_idx": float(benign["same_idx"]),
        "pathogenic_same_idx": float(pathogenic["same_idx"]),
        "family_coverage": float(method_result["family_coverage"]),
        "vocab_size": float(method_result["vocab_size"]),
    }


def structure_metric_block(method_result: dict) -> dict[str, float]:
    vocab_size = float(method_result["vocab_size"])
    return {
        "family_coverage": float(method_result["family_coverage"]),
        "mutated_vocab_fraction": float(method_result["mutated_count"]) / vocab_size,
        "parent_vocab_fraction": float(method_result["parent_count"]) / vocab_size,
        "vocab_size": vocab_size,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", default="outputs/puma_reproduction/raw_results.json")
    parser.add_argument("--scores", default="scoring/scores.json")
    args = parser.parse_args()

    with (ROOT / args.raw).open() as handle:
        raw = json.load(handle)

    scores = {
        "experiments": {
            "clinical_sibling_association": {"results": {}},
            "vocabulary_structure": {"results": {}},
        }
    }
    for name, result in raw["methods"].items():
        scores["experiments"]["clinical_sibling_association"]["results"][name] = clinical_metric_block(result)
        scores["experiments"]["vocabulary_structure"]["results"][name] = structure_metric_block(result)

    scores_path = ROOT / args.scores
    scores_path.parent.mkdir(parents=True, exist_ok=True)
    with scores_path.open("w") as handle:
        json.dump(scores, handle, indent=2)
    print(f"Wrote {scores_path}")


if __name__ == "__main__":
    main()
