#!/usr/bin/env python3
"""Generate raw artifacts for the released frequency-only BPE baseline."""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path

import pandas as pd
from tokenizers import Tokenizer

ROOT = Path(__file__).resolve().parents[1]


def parse_single_mutant(mutant: str) -> tuple[int, str, str] | None:
    if not isinstance(mutant, str) or ":" in mutant or len(mutant) < 3:
        return None
    try:
        return int(mutant[1:-1]) - 1, mutant[0], mutant[-1]
    except ValueError:
        return None


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
    return df.reset_index(drop=True)


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
    return df[["mutated_sequence", "target_seq", "parsed_mutation", "annotation"]].reset_index(drop=True)


def evaluate_bpe(tokenizer_path: Path, vocab_path: Path, variants: pd.DataFrame) -> dict[str, object]:
    tokenizer = Tokenizer.from_file(str(tokenizer_path))
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    with vocab_path.open() as handle:
        vocab = json.load(handle)

    label_counts: Counter[str] = Counter()
    same_counts: Counter[str] = Counter()
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
        if original.offsets == mutated.offsets:
            same_counts[label] += 1

    labels = {}
    for label, count in sorted(label_counts.items()):
        same = same_counts[label]
        labels[label] = {
            "variant_count": count,
            "same_count": same,
            "sibling_count": 0,
            "same_idx": same / count if count else 0.0,
            "same_sibling_rate": 0.0,
        }

    return {
        "name": "bpe_official_6400",
        "tokenizer_path": str(tokenizer_path),
        "vocab_path": str(vocab_path),
        "vocab_size": len(vocab),
        "parent_count": 0,
        "mutated_count": 0,
        "family_coverage": 0.0,
        "usable_variant_count": usable,
        "labels": labels,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="outputs/bpe_baseline/raw_results.json")
    parser.add_argument("--clinical-parquet", default="data/downloads/proteingym_clinical_substitutions/train-00000-of-00001.parquet")
    parser.add_argument("--dms-path", default="data/downloads/proteingym_dms_substitutions")
    parser.add_argument("--max-per-label", type=int, default=4000)
    parser.add_argument("--max-dms-per-bin", type=int, default=0)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    variants = load_clinical_variants(ROOT / args.clinical_parquet, args.max_per_label, args.seed)
    dms_variants = load_dms_variants(ROOT / args.dms_path, args.max_dms_per_bin or None, args.seed)
    vocab_dir = ROOT / "method" / "PUMA_official" / "RSRC" / "vocabs"
    result = evaluate_bpe(
        vocab_dir / "hf_uniref50_bpe_6400.json",
        vocab_dir / "uniref50_bpe_6400.json",
        variants,
    )
    result["dms"] = evaluate_bpe(
        vocab_dir / "hf_uniref50_bpe_6400.json",
        vocab_dir / "uniref50_bpe_6400.json",
        dms_variants,
    )

    output_path = ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "experiment": "clinical_sibling_association",
        "seed": args.seed,
        "max_per_label": args.max_per_label,
        "max_dms_per_bin": args.max_dms_per_bin,
        "clinical_parquet": args.clinical_parquet,
        "dms_path": args.dms_path,
        "training_summary": None,
        "methods": {"bpe_official_6400": result},
    }
    with output_path.open("w") as handle:
        json.dump(payload, handle, indent=2)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
