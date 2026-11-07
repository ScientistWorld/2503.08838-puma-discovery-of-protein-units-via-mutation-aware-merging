#!/usr/bin/env python3
"""Hidden test-slice evaluator for protein-unit vocabularies with a genealogy.

Run with no arguments (``bash scripts/evaluate_test.sh``). It scores

* every method on disk: each directory ``outputs/<method>/`` holding a
  ``tokenizer.json`` (HuggingFace tokenizers format) and a ``vocab.json``
  (one entry per vocabulary unit, optional ``"parent"`` links), and
* the fixed frequency-only BPE baseline owned by this directory.

Everything on the comparison side is fixed here: the variant populations and
labels (``downloads/split/``, built by ``prepare_split.py``), the baseline,
the 6,400-unit budget and every validity threshold. Nothing a method writes
besides its tokenizer and genealogy is read, and every number is recomputed
from those two artifacts. A submission that breaks a constraint is scored as
failed (worst value on every scored metric), never high.

Score tiers (with the weights in ``scoring/reference.json``):

* constraint violated (budget, lossless segmentation, genealogy, granularity,
  usage, boundary preservation): gaps -1, compression 0  -> rank score -0.9;
* valid, but a biological task is not solved (a sibling gap below its fixed
  minimum ``MIN_TASK_GAP``): no credit for either gap (each scored as
  ``min(measured, 0)``) -> rank score <= 0.1;
* valid and both tasks solved -> rank score >= 0.6*0.04 + 0.3*0.014 + 0.1*0.95
  = 0.123, so failing one task can never be bought back with the other.
"""

from __future__ import annotations

import argparse
import bisect
import json
import math
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SLICE = "test"
DATA_FILES = {
    "clinical": HERE / "downloads" / "split" / "clinical_test.parquet",
    "dms": HERE / "downloads" / "split" / "dms_test.parquet",
}
BASELINE_NAME = "bpe_6400"
BASELINE_TOKENIZER = HERE / "baseline_bpe_6400_tokenizer.json"
DEFAULT_SCORES = ROOT / "scoring" / "scores_test.json"

VOCAB_BUDGET = 6400
MIN_RESIDUES_PER_TOKEN = 2.0
MIN_OBSERVED_TOKENS = VOCAB_BUDGET // 2
MIN_SAME_IDX = 0.2
# Granularity tolerance: units on the scored proteins may be at most 5% shorter
# than those of the frequency-only baseline (the paper reports observed unit
# lengths nearly identical to BPE: 2.40 vs 2.46 residues at 6,400 units).
MIN_COMPRESSION_VS_BPE = 0.95
# Minimum within-family enrichment for a biological task to count as solved:
# about half of the published 6,400-unit effect (0.0835 clinical, 0.0280 DMS).
MIN_TASK_GAP = {"clinical": 0.04, "dms": 0.014}
ALLOWED_MODELS = ("BPE", "Unigram")
TOKEN_ALPHABET = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
LABELS = {"clinical": ("benign", "pathogenic"), "dms": ("positive", "negative")}
CHUNK = 1024


class InvalidSubmission(Exception):
    pass


# --------------------------------------------------------------------------
# Validation of the submitted artifacts (pure Python)
# --------------------------------------------------------------------------

def tokenizer_tokens(tok: object) -> list[str]:
    """Validate tokenizer.json and return its vocabulary (raises on violation)."""
    errors = []
    if not isinstance(tok, dict):
        raise InvalidSubmission("tokenizer.json must be a JSON object")
    for key in ("normalizer", "pre_tokenizer", "post_processor", "truncation", "padding"):
        if tok.get(key) is not None:
            errors.append(f"tokenizer.{key} must be null (raw residues are segmented as-is)")
    if tok.get("added_tokens"):
        errors.append("tokenizer.added_tokens must be empty")
    model = tok.get("model")
    if not isinstance(model, dict):
        raise InvalidSubmission("; ".join(errors + ["tokenizer.model is missing"]))
    mtype = model.get("type")
    tokens: list[str] = []
    if mtype not in ALLOWED_MODELS:
        errors.append(f"tokenizer.model.type must be one of {ALLOWED_MODELS}, got {mtype!r}")
    elif mtype == "BPE":
        if model.get("dropout") not in (None, 0, 0.0):
            errors.append("BPE dropout must be null (segmentation must be deterministic)")
        for key in ("continuing_subword_prefix", "end_of_word_suffix"):
            if model.get(key) not in (None, ""):
                errors.append(f"BPE {key} must be null")
        if model.get("byte_fallback"):
            errors.append("BPE byte_fallback must be false")
        vocab = model.get("vocab")
        if not isinstance(vocab, dict):
            errors.append("BPE vocab must be an object token -> id")
        else:
            ids = list(vocab.values())
            if not all(isinstance(i, int) and not isinstance(i, bool) for i in ids) or len(set(ids)) != len(ids):
                errors.append("BPE vocab ids must be distinct integers")
            tokens = list(vocab)
    else:  # Unigram
        if model.get("byte_fallback"):
            errors.append("Unigram byte_fallback must be false")
        vocab = model.get("vocab")
        if not isinstance(vocab, list) or not all(isinstance(e, list) and len(e) == 2 and isinstance(e[0], str) for e in vocab):
            errors.append("Unigram vocab must be a list of [token, score]")
        else:
            tokens = [e[0] for e in vocab]
            if len(set(tokens)) != len(tokens):
                errors.append("Unigram vocab contains duplicate tokens")
            if not all(isinstance(e[1], (int, float)) and not isinstance(e[1], bool) and math.isfinite(e[1]) for e in vocab):
                errors.append("Unigram scores must be finite numbers")
    if errors:
        raise InvalidSubmission("; ".join(errors))
    return tokens


def genealogy_components(vocab: object, tokens: list[str]) -> dict[str, int]:
    """Validate vocab.json against the tokenizer; return token -> family id."""
    if not isinstance(vocab, dict) or not vocab:
        raise InvalidSubmission("vocab.json must be a non-empty JSON object")
    errors: list[str] = []
    if len(tokens) > VOCAB_BUDGET:
        errors.append(f"vocabulary has {len(tokens)} units, above the fixed budget of {VOCAB_BUDGET}")
    if set(vocab) != set(tokens):
        only_v = len(set(vocab) - set(tokens))
        only_t = len(set(tokens) - set(vocab))
        errors.append(f"vocab.json units differ from tokenizer vocabulary ({only_v} only in vocab.json, {only_t} only in tokenizer)")
    bad = [t for t in vocab if not isinstance(t, str) or not t or set(t) - TOKEN_ALPHABET]
    if bad:
        errors.append(f"{len(bad)} units are not non-empty uppercase residue strings, e.g. {bad[:3]!r}")
    parent_of: dict[str, str] = {}
    link_errors = []
    for token, entry in vocab.items():
        if not isinstance(entry, dict):
            link_errors.append(f"{token!r}: entry must be an object")
            continue
        if "is_parent" in entry and entry["is_parent"] is not True:
            link_errors.append(f"{token!r}: is_parent must be true when present")
        if "parent" in entry:
            parent = entry["parent"]
            if not isinstance(parent, str) or parent not in vocab:
                link_errors.append(f"{token!r}: parent {parent!r} is not a vocabulary unit")
            elif parent == token:
                link_errors.append(f"{token!r}: unit cannot be its own parent")
            elif len(parent) != len(token):
                link_errors.append(f"{token!r}: parent {parent!r} has a different length (families link substitution variants)")
            else:
                parent_of[token] = parent
    if link_errors:
        errors.append(f"{len(link_errors)} invalid genealogy entries, e.g. {link_errors[:3]}")
    if errors:
        raise InvalidSubmission("; ".join(errors))

    root = {t: t for t in vocab}

    def find(t: str) -> str:
        while root[t] != t:
            root[t] = root[root[t]]
            t = root[t]
        return t

    for child, parent in parent_of.items():
        a, b = find(child), find(parent)
        if a != b:
            root[a] = b
    ids: dict[str, int] = {}
    comp: dict[str, int] = {}
    for t in vocab:
        comp[t] = ids.setdefault(find(t), len(ids))
    return comp


def structure_stats(vocab: dict, comp: dict[str, int]) -> dict[str, float]:
    size = len(vocab)
    counts: dict[int, int] = {}
    for c in comp.values():
        counts[c] = counts.get(c, 0) + 1
    multi = [n for n in counts.values() if n > 1]
    children = [t for t, e in vocab.items() if "parent" in e]
    parents = {vocab[t]["parent"] for t in children}
    return {
        "vocab_size": float(size),
        "family_coverage": sum(multi) / size,
        "mutated_vocab_fraction": len(children) / size,
        "parent_vocab_fraction": len(parents) / size,
        "family_count": float(len(multi)),
        "mean_family_size": sum(multi) / len(multi) if multi else 0.0,
        "largest_family_fraction": max(multi) / size if multi else 0.0,
    }


# --------------------------------------------------------------------------
# Scoring
# --------------------------------------------------------------------------

def encode_checked(tokenizer, sequences: list[str]):
    """Encode and enforce lossless, complete segmentation."""
    out = []
    for start in range(0, len(sequences), CHUNK):
        chunk = sequences[start:start + CHUNK]
        for seq, enc in zip(chunk, tokenizer.encode_batch(chunk)):
            tokens = enc.tokens
            offsets = enc.offsets
            if not tokens or "".join(tokens) != seq or offsets[-1][1] != len(seq) or offsets[0][0] != 0:
                raise InvalidSubmission("segmentation is not lossless: tokens do not reproduce the protein sequence")
            out.append((tokens, offsets))
    return out


def score_population(tokenizer, comp: dict[str, int], data: dict, labels: tuple[str, str]) -> dict:
    """SAME sibling counts for one labelled population."""
    targets = sorted(set(data["target_seq"]))
    original = {}
    for seq, (tokens, offsets) in zip(targets, encode_checked(tokenizer, targets)):
        original[seq] = (tokens, offsets, [s for s, _ in offsets])
    counts = {label: [0, 0, 0] for label in labels}  # variants, SAME, SAME & sibling
    rows = list(zip(data["target_seq"], data["mutated_sequence"], data["pos"], data["label"]))
    for start in range(0, len(rows), CHUNK):
        chunk = rows[start:start + CHUNK]
        encoded = encode_checked(tokenizer, [r[1] for r in chunk])
        for (target, _mutated, pos, label), (tokens, offsets) in zip(chunk, encoded):
            c = counts[label]
            c[0] += 1
            o_tokens, o_offsets, o_starts = original[target]
            if offsets != o_offsets:
                continue
            c[1] += 1
            j = bisect.bisect_right(o_starts, pos) - 1
            a, b = o_tokens[j], tokens[j]
            if a != b and comp.get(a) is not None and comp.get(a) == comp.get(b):
                c[2] += 1
    result = {}
    for label, (n, same, sib) in counts.items():
        if n == 0:
            raise RuntimeError(f"evaluation population has no {label} variants")
        result[label] = {
            "variants": n,
            "same": same,
            "sibling": sib,
            "same_idx": same / n,
            "same_sibling_rate": sib / same if same else 0.0,
        }
    return {"labels": result, "original": original}


def protein_stats(originals: list[dict]) -> dict[str, float]:
    residues = tokens = 0
    seen = set()
    used: set[str] = set()
    for original in originals:
        for seq, (toks, _offsets, _starts) in original.items():
            if seq in seen:
                continue
            seen.add(seq)
            residues += len(seq)
            tokens += len(toks)
            used.update(toks)
    return {"residues_per_token": residues / tokens if tokens else 0.0, "observed_token_count": float(len(used))}


def measured_gap(counts: dict, labels: tuple[str, str]) -> float:
    good, bad = labels
    return counts[good]["same_sibling_rate"] - counts[bad]["same_sibling_rate"]


def gap_block(prefix: tuple[str, str], counts: dict, struct: dict, task_solved: bool) -> dict[str, float]:
    """Metric block of one biological experiment.

    The scored gap is the measured gap when both biological tasks are solved;
    otherwise the run earns no credit for it (``min(measured, 0)``).
    """
    good, bad = prefix
    g, b = counts[good], counts[bad]
    gap = measured_gap(counts, prefix)
    return {
        f"{good}_same_sibling_rate": g["same_sibling_rate"],
        f"{bad}_same_sibling_rate": b["same_sibling_rate"],
        f"{good}_{bad}_gap": gap if task_solved else min(gap, 0.0),
        f"{good}_same_idx": g["same_idx"],
        f"{bad}_same_idx": b["same_idx"],
        "family_coverage": struct["family_coverage"],
        "vocab_size": struct["vocab_size"],
        "task_solved": 1.0 if task_solved else 0.0,
        "valid": 1.0,
    }


def gap_standard_error(counts: dict, labels: tuple[str, str]) -> float:
    total = 0.0
    for label in labels:
        p, n = counts[label]["same_sibling_rate"], counts[label]["same"]
        total += p * (1 - p) / n if n else 0.0
    return math.sqrt(total)


def failed_blocks(vocab_size: float) -> dict[str, dict[str, float]]:
    blocks = {}
    for exp, (good, bad) in (("clinical_sibling_association", LABELS["clinical"]), ("dms_sibling_association", LABELS["dms"])):
        blocks[exp] = {
            f"{good}_same_sibling_rate": 0.0,
            f"{bad}_same_sibling_rate": 0.0,
            f"{good}_{bad}_gap": -1.0,
            f"{good}_same_idx": 0.0,
            f"{bad}_same_idx": 0.0,
            "family_coverage": 0.0,
            "vocab_size": vocab_size,
            "task_solved": 0.0,
            "valid": 0.0,
        }
    blocks["vocabulary_structure"] = {
        "compression_vs_bpe": 0.0,
        "residues_per_token": 0.0,
        "observed_token_count": 0.0,
        "family_coverage": 0.0,
        "mutated_vocab_fraction": 0.0,
        "parent_vocab_fraction": 0.0,
        "family_count": 0.0,
        "mean_family_size": 0.0,
        "largest_family_fraction": 0.0,
        "vocab_size": vocab_size,
        "valid": 0.0,
    }
    return blocks


def load_tokenizer_from_json(tok: dict):
    from tokenizers import Tokenizer

    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    try:
        return Tokenizer.from_str(json.dumps(tok))
    except Exception as error:  # noqa: BLE001 - any load failure invalidates the submission
        raise InvalidSubmission(f"tokenizer.json cannot be loaded: {error}") from error


def score_submission(tok: object, vocab: object, populations: dict, bpe_residues_per_token: float | None):
    """Return (metric blocks per experiment, diagnostics)."""
    tokens = tokenizer_tokens(tok)
    comp = genealogy_components(vocab, tokens)
    struct = structure_stats(vocab, comp)
    tokenizer = load_tokenizer_from_json(tok)
    scored = {name: score_population(tokenizer, comp, data, LABELS[name]) for name, data in populations.items()}
    prot = protein_stats([s["original"] for s in scored.values()])
    problems = []
    if prot["residues_per_token"] < MIN_RESIDUES_PER_TOKEN:
        problems.append(f"segmentation averages {prot['residues_per_token']:.3f} residues per unit, below the minimum {MIN_RESIDUES_PER_TOKEN}")
    if prot["observed_token_count"] < MIN_OBSERVED_TOKENS:
        problems.append(f"only {int(prot['observed_token_count'])} distinct units are used on the scored proteins, below the minimum {MIN_OBSERVED_TOKENS}")
    for name, s in scored.items():
        for label, c in s["labels"].items():
            if c["same_idx"] < MIN_SAME_IDX:
                problems.append(f"{name}/{label}: only {c['same_idx']:.3f} of variants keep unit boundaries, below the minimum {MIN_SAME_IDX}")
    reference_rpt = bpe_residues_per_token if bpe_residues_per_token else prot["residues_per_token"]
    compression = prot["residues_per_token"] / reference_rpt
    if compression < MIN_COMPRESSION_VS_BPE:
        problems.append(f"units are {100 * (1 - compression):.1f}% shorter than the frequency-only baseline's "
                        f"(compression {compression:.4f} < {MIN_COMPRESSION_VS_BPE}): segmentation granularity sacrificed")
    if problems:
        raise InvalidSubmission("; ".join(problems))
    gaps = {name: measured_gap(s["labels"], LABELS[name]) for name, s in scored.items()}
    unsolved = sorted(name for name, gap in gaps.items() if not gap >= MIN_TASK_GAP[name])
    task_solved = not unsolved
    blocks = {
        "clinical_sibling_association": gap_block(LABELS["clinical"], scored["clinical"]["labels"], struct, task_solved),
        "dms_sibling_association": gap_block(LABELS["dms"], scored["dms"]["labels"], struct, task_solved),
        "vocabulary_structure": {
            "compression_vs_bpe": min(1.0, compression),
            "residues_per_token": prot["residues_per_token"],
            "observed_token_count": prot["observed_token_count"],
            "family_coverage": struct["family_coverage"],
            "mutated_vocab_fraction": struct["mutated_vocab_fraction"],
            "parent_vocab_fraction": struct["parent_vocab_fraction"],
            "family_count": struct["family_count"],
            "mean_family_size": struct["mean_family_size"],
            "largest_family_fraction": struct["largest_family_fraction"],
            "vocab_size": struct["vocab_size"],
            "valid": 1.0,
        },
    }
    diagnostics = {
        "valid": True,
        "task_solved": task_solved,
        "measured_gap": gaps,
        "unsolved_tasks": [f"{name}: gap {gaps[name]:.4f} < minimum {MIN_TASK_GAP[name]} (no credit for either gap)" for name in unsolved],
        "counts": {name: s["labels"] for name, s in scored.items()},
        "gap_standard_error": {name: gap_standard_error(s["labels"], LABELS[name]) for name, s in scored.items()},
        "residues_per_token": prot["residues_per_token"],
        "compression_vs_bpe_uncapped": compression,
    }
    return blocks, diagnostics


# --------------------------------------------------------------------------
# Data, discovery, main
# --------------------------------------------------------------------------

def ensure_split() -> None:
    if all(path.exists() for path in DATA_FILES.values()):
        return
    subprocess.run([sys.executable, str(HERE / "prepare_split.py")], check=True)


def load_populations() -> dict:
    import pandas as pd

    populations = {}
    for name, path in DATA_FILES.items():
        frame = pd.read_parquet(path, columns=["target_seq", "mutated_sequence", "pos", "label"])
        populations[name] = {
            "target_seq": frame["target_seq"].tolist(),
            "mutated_sequence": frame["mutated_sequence"].tolist(),
            "pos": [int(p) for p in frame["pos"].tolist()],
            "label": [str(x) for x in frame["label"].tolist()],
        }
    return populations


def discover_methods(outputs_dir: Path) -> dict[str, Path]:
    methods: dict[str, Path] = {}
    if not outputs_dir.is_dir():
        return methods
    for directory in sorted(p for p in outputs_dir.iterdir() if p.is_dir()):
        if not ((directory / "tokenizer.json").exists() or (directory / "vocab.json").exists()):
            continue
        name = directory.name
        if name == BASELINE_NAME or name.startswith("_"):
            name = "submitted_" + name.lstrip("_")
        methods[name] = directory
    return methods


def read_json(path: Path):
    try:
        return json.loads(path.read_text())
    except FileNotFoundError as error:
        raise InvalidSubmission(f"missing {path.name}") from error
    except (OSError, ValueError) as error:
        raise InvalidSubmission(f"{path.name} is not valid JSON: {error}") from error


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--outputs-dir", default=str(ROOT / "outputs"), help="directory holding one sub-directory per method")
    parser.add_argument("--scores", default=str(DEFAULT_SCORES))
    args = parser.parse_args()

    ensure_split()
    populations = load_populations()
    experiments = {e: {"results": {}} for e in ("clinical_sibling_association", "dms_sibling_association", "vocabulary_structure")}
    validation = {}

    baseline_tok = json.loads(BASELINE_TOKENIZER.read_text())
    baseline_vocab = {t: {} for t in tokenizer_tokens(baseline_tok)}
    blocks, diag = score_submission(baseline_tok, baseline_vocab, populations, None)
    bpe_rpt = diag["residues_per_token"]
    for exp, block in blocks.items():
        experiments[exp]["results"][BASELINE_NAME] = block
    validation[BASELINE_NAME] = {**diag, "source": "fixed baseline owned by the evaluator"}

    methods = discover_methods(Path(args.outputs_dir))
    if not methods:
        print(f"No method directories with tokenizer.json/vocab.json under {args.outputs_dir}; scoring the baseline only.")
    for name, directory in methods.items():
        vocab_size = 0.0
        try:
            tok = read_json(directory / "tokenizer.json")
            vocab = read_json(directory / "vocab.json")
            vocab_size = float(len(vocab)) if isinstance(vocab, dict) else 0.0
            blocks, diag = score_submission(tok, vocab, populations, bpe_rpt)
        except Exception as error:  # noqa: BLE001 - a broken submission fails, it never crashes scoring
            blocks = failed_blocks(vocab_size)
            kind = "constraint check" if isinstance(error, InvalidSubmission) else f"evaluation ({type(error).__name__})"
            diag = {"valid": False, "errors": f"{kind}: {error}"}
            print(f"[{name}] FAILED {kind}: {error}")
        for exp, block in blocks.items():
            experiments[exp]["results"][name] = block
        validation[name] = {**diag, "directory": str(directory)}
        status = "failed" if not diag["valid"] else ("valid" if diag["task_solved"] else "valid, task not solved: " + "; ".join(diag["unsolved_tasks"]))
        print(f"[{name}] scored ({status})")

    scores = {
        "_metadata": {
            "slice": SLICE,
            "populations": {name: {lab: sum(1 for x in data["label"] if x == lab) for lab in LABELS[name]} for name, data in populations.items()},
            "thresholds": {
                "vocab_budget": VOCAB_BUDGET,
                "min_residues_per_token": MIN_RESIDUES_PER_TOKEN,
                "min_observed_tokens": MIN_OBSERVED_TOKENS,
                "min_same_idx": MIN_SAME_IDX,
                "min_compression_vs_bpe": MIN_COMPRESSION_VS_BPE,
                "min_task_gap": MIN_TASK_GAP,
            },
            "baseline": BASELINE_NAME,
        },
        "experiments": experiments,
        "_validation": validation,
    }
    path = Path(args.scores)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(scores, indent=2))
    print(f"Wrote {SLICE} scores for {len(methods)} method(s) + baseline to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
