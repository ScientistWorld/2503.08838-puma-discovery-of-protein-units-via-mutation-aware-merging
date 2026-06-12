#!/usr/bin/env python3
"""Run a compact PUMA reproduction.

This script uses the official PUMA implementation and released 6,400-token
vocabularies, evaluates SAME sibling rates on ProteinGym clinical
substitutions, and optionally trains a small PUMA vocabulary from the released
UniRef50-human FASTA to verify the paper's mutation-aware merging algorithm
executes end-to-end.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
from Bio.Align import substitution_matrices
from tokenizers import Tokenizer

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_PROG = ROOT / "method" / "PUMA_official" / "Prog"
sys.path.insert(0, str(OFFICIAL_PROG))

import bpe_functions  # noqa: E402
import vocabulary_functions  # noqa: E402


def read_fasta_sequences(path: Path, limit: int | None = None) -> list[str]:
    sequences: list[str] = []
    current: list[str] = []
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            if line.startswith(">"):
                if current:
                    sequences.append("".join(current))
                    current = []
                    if limit is not None and len(sequences) >= limit:
                        break
            else:
                current.append(line)
        if current and (limit is None or len(sequences) < limit):
            sequences.append("".join(current))
    return sequences


def train_small_vocab(output_dir: Path, n_sequences: int, vocab_size: int) -> dict[str, object]:
    fasta_path = ROOT / "method" / "PUMA_official" / "RSRC" / "dataset" / "uniref_50.fasta"
    sequences = read_fasta_sequences(fasta_path, limit=n_sequences)
    matrix = substitution_matrices.load("BLOSUM62")
    output_dir.mkdir(parents=True, exist_ok=True)

    puma_vocab = bpe_functions.train_bpe(
        corpus=sequences,
        tokenizer_type="mutated",
        subs_matrix=matrix,
        mutation_cutoff=0.7,
        min_mutation_freq=0.05,
        min_mutation_len=3,
        max_mutation_len=12,
        stop_type="vocab_size",
        stop_parameter=vocab_size,
    )
    puma_vocab_path = output_dir / "small_puma_vocab.json"
    puma_hf_path = output_dir / "small_puma_hf.json"
    with puma_vocab_path.open("w") as handle:
        json.dump(puma_vocab, handle)
    with puma_hf_path.open("w") as handle:
        json.dump(vocabulary_functions.vocab_dict_to_HF_dict(puma_vocab), handle)

    bpe_vocab = bpe_functions.train_bpe(
        corpus=sequences,
        tokenizer_type="default",
        stop_type="vocab_size",
        stop_parameter=vocab_size,
    )
    bpe_vocab_path = output_dir / "small_bpe_vocab.json"
    bpe_hf_path = output_dir / "small_bpe_hf.json"
    with bpe_vocab_path.open("w") as handle:
        json.dump(bpe_vocab, handle)
    with bpe_hf_path.open("w") as handle:
        json.dump(vocabulary_functions.vocab_dict_to_HF_dict(bpe_vocab), handle)

    return {
        "n_sequences": len(sequences),
        "target_vocab_size": vocab_size,
        "puma_vocab_size": len(puma_vocab),
        "puma_parent_count": sum("is_parent" in v for v in puma_vocab.values()),
        "puma_mutated_count": sum("parent" in v for v in puma_vocab.values()),
        "bpe_vocab_size": len(bpe_vocab),
        "puma_vocab_path": str(puma_vocab_path),
        "puma_tokenizer_path": str(puma_hf_path),
        "bpe_vocab_path": str(bpe_vocab_path),
        "bpe_tokenizer_path": str(bpe_hf_path),
    }


def parse_single_mutant(mutant: str) -> tuple[int, str, str] | None:
    if not isinstance(mutant, str) or ":" in mutant or len(mutant) < 3:
        return None
    ref = mutant[0]
    alt = mutant[-1]
    try:
        pos = int(mutant[1:-1]) - 1
    except ValueError:
        return None
    return pos, ref, alt


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


def evaluate_tokenizer(
    name: str,
    tokenizer_path: Path,
    vocab_path: Path,
    variants: pd.DataFrame,
    has_genealogy: bool,
) -> dict[str, object]:
    tokenizer = Tokenizer.from_file(str(tokenizer_path))
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    with vocab_path.open() as handle:
        vocab = json.load(handle)
    families = vocabulary_functions.get_family_dictionary(vocab) if has_genealogy else defaultdict(list)

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
        if has_genealogy and original_token in families.get(mutated_token, []):
            sibling_counts[label] += 1

    per_label = {}
    for label, count in sorted(label_counts.items()):
        same = same_counts[label]
        sibling = sibling_counts[label]
        per_label[label] = {
            "variant_count": count,
            "same_count": same,
            "sibling_count": sibling,
            "same_idx": same / count if count else 0.0,
            "same_sibling_rate": sibling / same if same else 0.0,
        }

    return {
        "name": name,
        "tokenizer_path": str(tokenizer_path),
        "vocab_path": str(vocab_path),
        "vocab_size": len(vocab),
        "parent_count": sum("is_parent" in v for v in vocab.values()),
        "mutated_count": sum("parent" in v for v in vocab.values()),
        "family_coverage": sum(("is_parent" in v) or ("parent" in v) for v in vocab.values()) / len(vocab),
        "usable_variant_count": usable,
        "labels": per_label,
    }


def evaluate_dms_tokenizer(
    name: str,
    tokenizer_path: Path,
    vocab_path: Path,
    variants: pd.DataFrame,
    has_genealogy: bool,
) -> dict[str, object]:
    return evaluate_tokenizer(name, tokenizer_path, vocab_path, variants, has_genealogy)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="outputs/puma_reproduction/raw_results.json")
    parser.add_argument("--clinical-parquet", default="data/downloads/proteingym_clinical_substitutions/train-00000-of-00001.parquet")
    parser.add_argument("--max-per-label", type=int, default=4000)
    parser.add_argument("--dms-path", default="data/downloads/proteingym_dms_substitutions")
    parser.add_argument("--max-dms-per-bin", type=int, default=0)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--train-small", action="store_true")
    parser.add_argument("--train-sequences", type=int, default=1200)
    parser.add_argument("--train-vocab-size", type=int, default=900)
    args = parser.parse_args()

    random.seed(args.seed)
    output_path = ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    training_summary = None
    if args.train_small:
        training_summary = train_small_vocab(
            ROOT / "checkpoints" / "puma_small",
            n_sequences=args.train_sequences,
            vocab_size=args.train_vocab_size,
        )

    variants = load_clinical_variants(ROOT / args.clinical_parquet, args.max_per_label, args.seed)
    vocab_dir = ROOT / "method" / "PUMA_official" / "RSRC" / "vocabs"
    methods = [
        (
            "puma_official_6400",
            vocab_dir / "hf_uniref50_mutbpe_0.7_3_12_0.05_6400.json",
            vocab_dir / "uniref50_mutbpe_0.7_3_12_0.05_6400.json",
            True,
        ),
        (
            "bpe_official_6400",
            vocab_dir / "hf_uniref50_bpe_6400.json",
            vocab_dir / "uniref50_bpe_6400.json",
            False,
        ),
    ]

    method_results = {}
    dms_variants = load_dms_variants(ROOT / args.dms_path, args.max_dms_per_bin or None, args.seed)
    for name, tokenizer_path, vocab_path, has_genealogy in methods:
        method_results[name] = evaluate_tokenizer(name, tokenizer_path, vocab_path, variants, has_genealogy)
        method_results[name]["dms"] = evaluate_dms_tokenizer(name, tokenizer_path, vocab_path, dms_variants, has_genealogy)

    payload = {
        "experiment": "clinical_sibling_association",
        "seed": args.seed,
        "max_per_label": args.max_per_label,
        "max_dms_per_bin": args.max_dms_per_bin,
        "clinical_parquet": args.clinical_parquet,
        "dms_path": args.dms_path,
        "training_summary": training_summary,
        "methods": method_results,
    }
    with output_path.open("w") as handle:
        json.dump(payload, handle, indent=2)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
