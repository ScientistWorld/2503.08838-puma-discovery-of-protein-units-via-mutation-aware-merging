#!/usr/bin/env python3
"""Build the fixed train / hidden-test variant populations from raw ProteinGym.

This file is owned by the hidden test. It reads the raw ProteinGym parquet
files that ``scripts/download.sh`` stores under ``eval/test/downloads/raw/``
and writes

* the agent-visible TRAIN populations to ``data/downloads/proteingym_train/``
* the hidden TEST populations to ``eval/test/downloads/split/``

The split is fixed here, never by a submitted method:

* ClinVar (clinical) variants are split by protein: every variant of a given
  wild-type sequence lands on the same side, so the hidden test scores
  proteins whose labels were never visible.
* DMS variants are split by protein region (wild-type sequence x 50-residue
  window), so every assay contributes to both sides while no residue window
  is shared between them.

Filtering mirrors the paper's single-substitution analyses: one amino-acid
substitution, wild-type length <= 3000, and only the 20 standard residues so
that every scored sequence can be segmented by any vocabulary over them.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RAW_DIR = HERE / "downloads" / "raw"
RAW_CLINICAL = RAW_DIR / "clinical_substitutions" / "train-00000-of-00001.parquet"
RAW_DMS_DIR = RAW_DIR / "DMS_substitutions"
TEST_DIR = HERE / "downloads" / "split"
TRAIN_DIR = ROOT / "data" / "downloads" / "proteingym_train"
OUTPUTS = {
    "clinical_test": TEST_DIR / "clinical_test.parquet",
    "dms_test": TEST_DIR / "dms_test.parquet",
    "clinical_train": TRAIN_DIR / "clinical_train.parquet",
    "dms_train": TRAIN_DIR / "dms_train.parquet",
}
STANDARD = frozenset("ACDEFGHIKLMNPQRSTVWY")
MAX_LENGTH = 3000
DMS_WINDOW = 50
COLUMNS = ["protein_id", "target_seq", "mutated_sequence", "pos", "ref", "alt", "label", "source"]


def parse_single_mutant(mutant: object) -> tuple[int, str, str] | None:
    if not isinstance(mutant, str) or ":" in mutant or len(mutant) < 3:
        return None
    try:
        pos = int(mutant[1:-1]) - 1
    except ValueError:
        return None
    return pos, mutant[0], mutant[-1]


def is_test_key(key: str) -> bool:
    return int(hashlib.sha256(key.encode("utf-8")).hexdigest(), 16) % 2 == 1


def protein_id(seq: str) -> str:
    return hashlib.sha1(seq.encode("utf-8")).hexdigest()[:16]


def clean_rows(records, label_of, per_source: bool):
    """Return validated single-substitution rows as dicts.

    Duplicate listings of one variant are kept once (per assay when
    ``per_source``); a variant listed with conflicting labels is dropped.
    """
    seen = {}
    for target, mutated, mutant, raw_label, source in records:
        label = label_of(raw_label)
        if label is None:
            continue
        parsed = parse_single_mutant(mutant)
        if parsed is None:
            continue
        pos, ref, alt = parsed
        if not isinstance(target, str) or not isinstance(mutated, str):
            continue
        if ref == alt or len(target) != len(mutated) or len(target) > MAX_LENGTH:
            continue
        if not (0 <= pos < len(target)) or target[pos] != ref or mutated[pos] != alt:
            continue
        if mutated != target[:pos] + alt + target[pos + 1:]:
            continue
        if set(target) - STANDARD or alt not in STANDARD:
            continue
        key = (target, pos, alt, str(source)) if per_source else (target, pos, alt)
        if key in seen:
            # Same variant listed twice: keep it once; drop it if labels conflict.
            if seen[key] is not None and seen[key]["label"] != label:
                seen[key] = None
            continue
        seen[key] = {
            "protein_id": protein_id(target),
            "target_seq": target,
            "mutated_sequence": mutated,
            "pos": int(pos),
            "ref": ref,
            "alt": alt,
            "label": label,
            "source": str(source),
        }
    return [row for row in seen.values() if row is not None]


def clinical_label(value: object) -> str | None:
    text = str(value).strip().lower()
    return text if text in {"benign", "pathogenic"} else None


def build(force: bool = False) -> dict:
    import pandas as pd

    if not force and all(path.exists() for path in OUTPUTS.values()):
        print("Split already present; use --force to rebuild.")
        return json.loads((TEST_DIR / "manifest.json").read_text()) if (TEST_DIR / "manifest.json").exists() else {}

    dms_files = sorted(RAW_DMS_DIR.glob("*.parquet"))
    if not RAW_CLINICAL.exists() or len(dms_files) != 5:
        raise FileNotFoundError(
            "Raw ProteinGym files are missing under eval/test/downloads/raw/. "
            "Run `bash scripts/download.sh` on an internet-enabled node first."
        )

    clinical = pd.read_parquet(RAW_CLINICAL, columns=["target_seq", "mutated_sequence", "mutant", "annotation"])
    clinical_rows = clean_rows(
        zip(clinical["target_seq"], clinical["mutated_sequence"], clinical["mutant"], clinical["annotation"],
            ["clinvar"] * len(clinical)),
        clinical_label,
        per_source=False,
    )

    frames = []
    for file in dms_files:
        frame = pd.read_parquet(file)
        keep = [c for c in ("DMS_id", "assay_name", "target_name", "mutated_sequence", "mutant", "DMS_score", "DMS_score_bin") if c in frame.columns]
        frames.append(frame[keep])
    dms = pd.concat(frames, ignore_index=True)
    human_columns = [c for c in ("DMS_id", "assay_name", "target_name") if c in dms.columns]
    mask = pd.Series(False, index=dms.index)
    for column in human_columns:
        mask = mask | dms[column].astype(str).str.contains("HUMAN", case=False, na=False)
    dms = dms[mask]
    dms = dms[(dms["DMS_score"] >= -5) & (dms["DMS_score"] <= 5)]
    dms = dms[~dms["mutant"].astype(str).str.contains(":", na=False)]

    def wild_type(mutated: object, mutant: object) -> str | None:
        parsed = parse_single_mutant(mutant)
        if parsed is None or not isinstance(mutated, str):
            return None
        pos, ref, _alt = parsed
        if not (0 <= pos < len(mutated)):
            return None
        return mutated[:pos] + ref + mutated[pos + 1:]

    dms_targets = [wild_type(m, mu) for m, mu in zip(dms["mutated_sequence"], dms["mutant"])]
    dms_labels = ["positive" if int(b) == 1 else "negative" for b in dms["DMS_score_bin"]]
    dms_source = dms["DMS_id"].astype(str).tolist() if "DMS_id" in dms.columns else ["dms"] * len(dms)
    dms_rows = clean_rows(
        zip(dms_targets, dms["mutated_sequence"], dms["mutant"], dms_labels, dms_source),
        lambda value: value,
        per_source=True,
    )

    split = {"clinical_train": [], "clinical_test": [], "dms_train": [], "dms_test": []}
    for row in clinical_rows:
        side = "test" if is_test_key("clinical:" + row["target_seq"]) else "train"
        split[f"clinical_{side}"].append(row)
    for row in dms_rows:
        side = "test" if is_test_key(f"dms:{row['target_seq']}:{row['pos'] // DMS_WINDOW}") else "train"
        split[f"dms_{side}"].append(row)

    TEST_DIR.mkdir(parents=True, exist_ok=True)
    TRAIN_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {"split_rule": {
        "clinical": "sha256('clinical:' + wild-type sequence) odd -> test",
        "dms": f"sha256('dms:' + wild-type sequence + ':' + (pos // {DMS_WINDOW})) odd -> test",
    }}
    for name, rows in split.items():
        frame = pd.DataFrame(rows, columns=COLUMNS)
        frame = frame.sort_values(["protein_id", "pos", "alt", "source"]).reset_index(drop=True)
        frame.to_parquet(OUTPUTS[name], index=False)
        manifest[name] = {
            "variants": int(len(frame)),
            "proteins": int(frame["protein_id"].nunique()),
            "labels": {str(k): int(v) for k, v in frame["label"].value_counts().sort_index().items()},
        }
    train_manifest = {k: v for k, v in manifest.items() if not k.endswith("_test")}
    (TEST_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))
    (TRAIN_DIR / "manifest.json").write_text(json.dumps(train_manifest, indent=2))
    print(json.dumps(manifest, indent=2))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="rebuild even if split files exist")
    args = parser.parse_args()
    try:
        build(force=args.force)
    except ImportError as error:
        print(f"Cannot build the split here ({error}); run inside the gym container.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
