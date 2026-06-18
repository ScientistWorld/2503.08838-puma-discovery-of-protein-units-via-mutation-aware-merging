#!/usr/bin/env python3
"""Train-slice evaluator for PUMA artifacts.

This script is intentionally method-agnostic: it reads the same raw artifact
JSON as ``scripts/evaluate.sh`` and scores tokenizer/vocabulary outputs without
importing from ``method/``. The train slice is a deterministic, label-stratified
half of the original evaluation pool.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd
from tokenizers import Tokenizer

ROOT = Path(__file__).resolve().parents[2]
SLICE_NAME = "train"


def resolve_workspace_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else ROOT / path


def parse_single_mutant(mutant: str) -> tuple[int, str, str] | None:
    if not isinstance(mutant, str) or ":" in mutant or len(mutant) < 3:
        return None
    try:
        return int(mutant[1:-1]) - 1, mutant[0], mutant[-1]
    except ValueError:
        return None


def stable_variant_hash(row: pd.Series) -> str:
    key = "\x1f".join(
        str(row.get(column, ""))
        for column in ("annotation", "mutant", "target_seq", "mutated_sequence")
    )
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def select_slice(variants: pd.DataFrame) -> pd.DataFrame:
    if variants.empty:
        return variants.copy()
    df = variants.copy()
    df["_split_hash"] = df.apply(stable_variant_hash, axis=1)
    parts = []
    for _label, group in df.sort_values("_split_hash").groupby("annotation", sort=True):
        ranked = group.reset_index(drop=True)
        parts.append(ranked[ranked.index % 2 == 0])
    return (
        pd.concat(parts, ignore_index=True)
        .drop(columns=["_split_hash"])
        .sample(frac=1.0, random_state=17)
        .reset_index(drop=True)
    )


def load_clinical_variants(path: Path, max_per_label: int | None, seed: int) -> pd.DataFrame:
    df = pd.read_parquet(path)
    required = {"mutated_sequence", "target_seq", "mutant", "annotation"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"ProteinGym clinical file missing columns: {sorted(missing)}")
    df = df[list(required)].copy()
    df["parsed_mutation"] = df["mutant"].map(parse_single_mutant)
    df = df[df["parsed_mutation"].notna()]
    df = df[df["target_seq"].str.len() == df["mutated_sequence"].str.len()]
    df = df[df["target_seq"].str.len() <= 3000]
    if max_per_label:
        parts = []
        for _, group in df.groupby("annotation"):
            parts.append(group.sample(n=min(max_per_label, len(group)), random_state=seed))
        df = pd.concat(parts).sample(frac=1.0, random_state=seed).reset_index(drop=True)
    return select_slice(df.reset_index(drop=True))


def load_dms_variants(path: Path, max_per_bin: int | None, seed: int) -> pd.DataFrame:
    files = sorted(path.glob("*.parquet")) if path.is_dir() else [path]
    if not files:
        raise FileNotFoundError(f"No DMS parquet files found under {path}")
    df = pd.concat((pd.read_parquet(file) for file in files), ignore_index=True)
    required = {"mutated_sequence", "mutant", "DMS_score", "DMS_score_bin"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"ProteinGym DMS file missing columns: {sorted(missing)}")

    human_columns = [column for column in ("DMS_id", "assay_name", "target_name") if column in df.columns]
    if human_columns:
        mask = False
        for column in human_columns:
            mask = mask | df[column].astype(str).str.contains("HUMAN", case=False, na=False)
        df = df[mask].copy()

    df = df[list(required)].copy()
    df = df[~df["mutant"].astype(str).str.contains(":", na=False)]
    df = df[(df["DMS_score"] <= 5) & (df["DMS_score"] >= -5)]
    df["parsed_mutation"] = df["mutant"].map(parse_single_mutant)
    df = df[df["parsed_mutation"].notna()]

    def reverse_mutation(row: pd.Series) -> str | None:
        pos, ref, _alt = row["parsed_mutation"]
        seq = row["mutated_sequence"]
        if not isinstance(seq, str) or pos < 0 or pos >= len(seq):
            return None
        return seq[:pos] + ref + seq[pos + 1 :]

    df["target_seq"] = df.apply(reverse_mutation, axis=1)
    df = df[df["target_seq"].notna()]
    df["annotation"] = df["DMS_score_bin"].map(lambda x: "Positive" if int(x) == 1 else "Negative")
    if max_per_bin:
        parts = []
        for _, group in df.groupby("annotation"):
            parts.append(group.sample(n=min(max_per_bin, len(group)), random_state=seed))
        df = pd.concat(parts).sample(frac=1.0, random_state=seed).reset_index(drop=True)
    return select_slice(df[["mutated_sequence", "target_seq", "mutant", "parsed_mutation", "annotation"]].reset_index(drop=True))


def build_family_dictionary(vocab: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    parent_to_members: dict[str, list[str]] = {}
    for token, entry in vocab.items():
        if "is_parent" in entry:
            parent_to_members.setdefault(token, [token])
    for token, entry in vocab.items():
        parent = entry.get("parent")
        if parent is not None:
            parent_to_members.setdefault(parent, [parent]).append(token)

    families = {token: [] for token in vocab}
    for members in parent_to_members.values():
        for token in members:
            families[token] = members
    return families


def family_statistics(vocab: dict[str, dict[str, Any]]) -> dict[str, float]:
    parent_to_members: dict[str, set[str]] = {}
    for token, entry in vocab.items():
        if "is_parent" in entry:
            parent_to_members.setdefault(token, {token})
    for token, entry in vocab.items():
        parent = entry.get("parent")
        if parent is not None:
            parent_to_members.setdefault(parent, {parent}).add(token)

    multi_member_sizes = [len(members) for members in parent_to_members.values() if len(members) > 1]
    if not multi_member_sizes:
        return {
            "family_count": 0.0,
            "mean_family_size": 0.0,
            "largest_family_fraction": 0.0,
        }

    family_member_total = sum(multi_member_sizes)
    return {
        "family_count": float(len(multi_member_sizes)),
        "mean_family_size": family_member_total / len(multi_member_sizes),
        "largest_family_fraction": max(multi_member_sizes) / len(vocab),
    }


def score_artifact(method_result: dict[str, Any], variants: pd.DataFrame) -> dict[str, Any]:
    tokenizer_path = resolve_workspace_path(method_result["tokenizer_path"])
    vocab_path = resolve_workspace_path(method_result["vocab_path"])
    tokenizer = Tokenizer.from_file(str(tokenizer_path))
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    with vocab_path.open() as handle:
        vocab = json.load(handle)
    families = build_family_dictionary(vocab)
    family_stats = family_statistics(vocab)

    label_counts: Counter[str] = Counter()
    same_counts: Counter[str] = Counter()
    sibling_counts: Counter[str] = Counter()
    usable = 0

    for row in variants.itertuples(index=False):
        pos, ref, alt = row.parsed_mutation
        if pos < 0 or pos >= len(row.target_seq):
            continue
        if row.target_seq[pos] != ref or row.mutated_sequence[pos] != alt:
            continue
        label = str(row.annotation)
        label_counts[label] += 1
        usable += 1
        original = tokenizer.encode(row.target_seq)
        mutated = tokenizer.encode(row.mutated_sequence)
        if original.offsets != mutated.offsets:
            continue
        same_counts[label] += 1
        token_index = None
        for i, (start, end) in enumerate(original.offsets):
            if start <= pos < end:
                token_index = i
                break
        if token_index is None:
            continue
        original_token = original.tokens[token_index]
        mutated_token = mutated.tokens[token_index]
        if original_token in families.get(mutated_token, []):
            sibling_counts[label] += 1

    labels = {}
    for label, count in sorted(label_counts.items()):
        same = same_counts[label]
        sibling = sibling_counts[label]
        labels[label] = {
            "variant_count": count,
            "same_count": same,
            "sibling_count": sibling,
            "same_idx": same / count if count else 0.0,
            "same_sibling_rate": sibling / same if same else 0.0,
        }

    vocab_size = len(vocab)
    parent_count = sum("is_parent" in entry for entry in vocab.values())
    mutated_count = sum("parent" in entry for entry in vocab.values())
    return {
        "labels": labels,
        "vocab_size": float(vocab_size),
        "parent_count": parent_count,
        "mutated_count": mutated_count,
        "family_coverage": (parent_count + mutated_count) / vocab_size,
        "usable_variant_count": usable,
        **family_stats,
    }


def clinical_metric_block(scored: dict[str, Any]) -> dict[str, float]:
    labels = scored["labels"]
    benign = labels.get("benign") or labels.get("Benign")
    pathogenic = labels.get("pathogenic") or labels.get("Pathogenic")
    if benign is None or pathogenic is None:
        raise ValueError(f"Expected benign/pathogenic labels, got {sorted(labels)}")
    benign_rate = float(benign["same_sibling_rate"])
    pathogenic_rate = float(pathogenic["same_sibling_rate"])
    eps = 1e-9
    return {
        "benign_same_sibling_rate": benign_rate,
        "pathogenic_same_sibling_rate": pathogenic_rate,
        "benign_pathogenic_gap": benign_rate - pathogenic_rate,
        "benign_pathogenic_log_ratio": math.log((benign_rate + eps) / (pathogenic_rate + eps)),
        "benign_same_idx": float(benign["same_idx"]),
        "pathogenic_same_idx": float(pathogenic["same_idx"]),
        "minimum_same_idx": min(float(benign["same_idx"]), float(pathogenic["same_idx"])),
        "family_coverage": float(scored["family_coverage"]),
        "vocab_size": float(scored["vocab_size"]),
    }


def dms_metric_block(scored: dict[str, Any]) -> dict[str, float]:
    labels = scored["labels"]
    positive = labels.get("Positive") or labels.get("positive")
    negative = labels.get("Negative") or labels.get("negative")
    if positive is None or negative is None:
        raise ValueError(f"Expected Positive/Negative DMS labels, got {sorted(labels)}")
    positive_rate = float(positive["same_sibling_rate"])
    negative_rate = float(negative["same_sibling_rate"])
    eps = 1e-9
    return {
        "positive_same_sibling_rate": positive_rate,
        "negative_same_sibling_rate": negative_rate,
        "positive_negative_gap": positive_rate - negative_rate,
        "positive_negative_log_ratio": math.log((positive_rate + eps) / (negative_rate + eps)),
        "positive_same_idx": float(positive["same_idx"]),
        "negative_same_idx": float(negative["same_idx"]),
        "minimum_same_idx": min(float(positive["same_idx"]), float(negative["same_idx"])),
        "family_coverage": float(scored["family_coverage"]),
        "vocab_size": float(scored["vocab_size"]),
    }


def structure_metric_block(scored: dict[str, Any]) -> dict[str, float]:
    vocab_size = float(scored["vocab_size"])
    return {
        "family_coverage": float(scored["family_coverage"]),
        "mutated_vocab_fraction": float(scored["mutated_count"]) / vocab_size,
        "parent_vocab_fraction": float(scored["parent_count"]) / vocab_size,
        "family_count": float(scored["family_count"]),
        "mean_family_size": float(scored["mean_family_size"]),
        "largest_family_fraction": float(scored["largest_family_fraction"]),
        "vocab_size": vocab_size,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", default="outputs/puma_reproduction/raw_results.json")
    parser.add_argument("--scores", default="scoring/scores_train.json")
    args = parser.parse_args()

    with resolve_workspace_path(args.raw).open() as handle:
        raw = json.load(handle)

    seed = int(raw.get("seed", 7))
    max_per_label = raw.get("max_per_label", 4000)
    max_dms_per_bin = raw.get("max_dms_per_bin", 0)
    clinical_path = resolve_workspace_path(raw.get("clinical_parquet", "data/downloads/proteingym_clinical_substitutions/train-00000-of-00001.parquet"))
    dms_path = resolve_workspace_path(raw.get("dms_path", "data/downloads/proteingym_dms_substitutions"))
    clinical_variants = load_clinical_variants(clinical_path, max_per_label, seed)
    dms_variants = load_dms_variants(dms_path, max_dms_per_bin or None, seed)

    scores = {
        "_metadata": {
            "slice": SLICE_NAME,
            "split": "deterministic_label_stratified_even_hash_ranks",
        },
        "experiments": {
            "clinical_sibling_association": {"results": {}},
            "dms_sibling_association": {"results": {}},
            "vocabulary_structure": {"results": {}},
        }
    }
    for name, result in sorted(raw["methods"].items()):
        clinical_scores = score_artifact(result, clinical_variants)
        dms_scores = score_artifact(result, dms_variants)
        scores["experiments"]["clinical_sibling_association"]["results"][name] = clinical_metric_block(clinical_scores)
        scores["experiments"]["dms_sibling_association"]["results"][name] = dms_metric_block(dms_scores)
        scores["experiments"]["vocabulary_structure"]["results"][name] = structure_metric_block(clinical_scores)

    scores_path = resolve_workspace_path(args.scores)
    scores_path.parent.mkdir(parents=True, exist_ok=True)
    with scores_path.open("w") as handle:
        json.dump(scores, handle, indent=2)
    print(f"Wrote {SLICE_NAME} scores to {scores_path}")


if __name__ == "__main__":
    main()
