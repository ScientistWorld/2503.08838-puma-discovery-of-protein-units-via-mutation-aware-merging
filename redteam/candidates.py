"""Audit candidates. Preparation uses only files exposed to a future agent.

No candidate imports test code, reads test scores, or changes an evaluator or
Python environment. All learned/generated candidate artifacts stay in redteam.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
VOCABS = ROOT / "method/PUMA_official/RSRC/vocabs"
PUMA = "puma_official_6400"
BPE = "bpe_official_6400"


def dump(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=2, allow_nan=True))
    return str(Path(path).relative_to(ROOT))


def released(name):
    stem = "uniref50_mutbpe_0.7_3_12_0.05_6400" if name == PUMA else "uniref50_bpe_6400"
    return {"tokenizer_path": str((VOCABS / f"hf_{stem}.json").relative_to(ROOT)),
            "vocab_path": str((VOCABS / f"{stem}.json").relative_to(ROOT))}


def base(seed=7, baseline=False):
    raw = {"seed": seed, "max_per_label": 4000, "max_dms_per_bin": 0,
           "clinical_parquet": "data/downloads/proteingym_clinical_substitutions/train-00000-of-00001.parquet",
           "dms_path": "data/downloads/proteingym_dms_substitutions",
           "training_summary": None, "methods": {PUMA: released(PUMA)}}
    if baseline:
        raw["methods"][BPE] = released(BPE)
    return raw


def puma_vocab():
    return json.loads((ROOT / released(PUMA)["vocab_path"]).read_text())


def artificial_pairs(tokens):
    """Shortcut: arbitrary pairs have no biological or learned relationships."""
    tokens = list(tokens)
    result = {}
    for i in range(0, len(tokens), 2):
        parent, child = tokens[i:i + 2]
        result[parent] = {"is_parent": True}
        result[child] = {"parent": parent}
    return result


def degenerate_tokenizer(out, empty=False):
    """Shortcut: erase a whole protein or replace it with one constant token."""
    from tokenizers import Tokenizer, Regex, models, normalizers
    tokenizer = Tokenizer(models.WordLevel({"A": 0}, unk_token="A"))
    tokenizer.normalizer = normalizers.Replace(Regex("(?s).+"), "" if empty else "A")
    path = out / "generated/tokenizer.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    tokenizer.save(str(path))
    return str(path.relative_to(ROOT))


def prepare(name, out, config):
    kind = config["kind"]
    raw = base(config.get("seed", 7), baseline=config.get("baseline", False))
    metadata = {"name": name, "kind": kind, "visible_inputs_only": True}

    if kind == "reference":
        # The submitted method's scored output is the released artifact pair.
        # Training its optional small vocabulary is not part of this prediction.
        pass
    elif kind == "more_training":
        # Run the actual optional training procedure, with twice as much data.
        # Preserve its advertised end-to-end pipeline, including its choice of
        # released artifacts for scoring; this tests the disconnected training.
        from method.run_puma import train_small_vocab
        n_sequences = config.get("n_sequences", 2400)
        raw["training_summary"] = train_small_vocab(out / "generated/training", n_sequences, 900)
        metadata["n_sequences"] = n_sequences
    elif kind == "weak_no_genealogy":
        vocab = puma_vocab()
        for entry in vocab.values():
            entry.pop("parent", None)
            entry.pop("is_parent", None)
        raw["methods"][PUMA]["vocab_path"] = dump(out / "generated/vocab.json", vocab)
    elif kind == "honest_stricter_links":
        # Unsupervised biological refinement: keep the released segmentation
        # but require a stronger normalized substitution score for a family link.
        # Never read clinical or DMS labels to choose this cutoff.
        vocab = puma_vocab()
        removed = 0
        for entry in vocab.values():
            if "parent" in entry and entry.get("similarity", 0) < config["cutoff"]:
                entry.pop("parent")
                removed += 1
        active_parents = {e["parent"] for e in vocab.values() if "parent" in e}
        for token, entry in vocab.items():
            if token not in active_parents:
                entry.pop("is_parent", None)
        raw["methods"][PUMA]["vocab_path"] = dump(out / "generated/vocab.json", vocab)
        metadata.update(cutoff=config["cutoff"], removed_links=removed)
    elif kind == "shortcut_skip_training":
        metadata["shortcut"] = "Skip all optional training; submit the same released outputs."
    elif kind == "shortcut_raw_fields":
        # Shortcut attempt: forged summaries, impossible values, nulls and flags.
        # Keep real tokenizer outputs, so rejection/overwrite can be distinguished
        # from a crash caused by an unrelated malformed tokenizer.
        for result in raw["methods"].values():
            result.update(vocab_size=6400, parent_count=6400, mutated_count=6400,
                          family_coverage=999999, usable_variant_count=None,
                          success=True, time_seconds=-1, labels={
                              "Benign": {"same_sibling_rate": 1e99, "same_idx": None},
                              "Pathogenic": {"same_sibling_rate": -1e99, "same_idx": None}},
                          dms={"positive_negative_gap": float("nan")})
        metadata["shortcut"] = "Write fake summary metrics and a pre-existing fake score file."
        forged = {"experiments": {e: {"results": {PUMA: {"family_coverage": 1e99}}}
                                    for e in ("clinical_sibling_association", "dms_sibling_association", "vocabulary_structure")}}
        dump(ROOT / "scoring/scores_test.json", forged)
        dump(out / "forged_scores_before_test.json", forged)
    elif kind in {"shortcut_family_padding", "shortcut_constant", "shortcut_empty"}:
        # Preserve the 6400-entry budget but fabricate 3200 arbitrary families.
        if kind == "shortcut_family_padding":
            tokens = sorted(puma_vocab())
        else:
            tokens = ["A"] + [f"shortcut_unused_{i:04d}" for i in range(6399)]
            raw["methods"][PUMA]["tokenizer_path"] = degenerate_tokenizer(out, kind.endswith("empty"))
        raw["methods"][PUMA]["vocab_path"] = dump(out / "generated/vocab.json", artificial_pairs(tokens))
        metadata["shortcut"] = "Artificial family count rewards; relationships are arbitrary."
    elif kind == "shortcut_impossible_flags":
        # Presence is counted as truth; parent strings need not exist. Each
        # entry counts twice toward coverage and creates an extra fake family.
        vocab = {t: {"is_parent": False, "parent": f"shortcut_missing_parent_{i}"}
                 for i, t in enumerate(puma_vocab())}
        raw["methods"][PUMA]["vocab_path"] = dump(out / "generated/vocab.json", vocab)
        metadata["shortcut"] = "False flags and dangling parent names produce 200% coverage."
    elif kind == "shortcut_label_lookup":
        # The full labeled evaluation pool is agent-visible. Memorize negative
        # full sequences. Unknown sequences, including nearly all originals and
        # favorable variants, return the constant token A, whose singleton family
        # is accepted by SAME. The actual tokenizer is not budget-constrained;
        # the evaluator checks only the separate genealogy JSON's length.
        from baseline.run_bpe import load_clinical_variants, load_dms_variants
        from tokenizers import Tokenizer, models
        clinical = load_clinical_variants(ROOT / raw["clinical_parquet"], 0, 7)
        dms = load_dms_variants(ROOT / raw["dms_path"], None, 7)
        negative = set(clinical.loc[clinical.annotation.str.lower() == "pathogenic", "mutated_sequence"])
        negative.update(dms.loc[dms.annotation == "Negative", "mutated_sequence"])
        negative.discard("A")
        words = {"A": 0}
        words.update({seq: i for i, seq in enumerate(sorted(negative), start=1)})
        tokenizer = Tokenizer(models.WordLevel(words, unk_token="A"))
        path = out / "generated/tokenizer.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        tokenizer.save(str(path))
        vocab = puma_vocab()
        vocab["A"]["is_parent"] = True
        raw["methods"][PUMA] = {"tokenizer_path": str(path.relative_to(ROOT)),
                                 "vocab_path": dump(out / "generated/vocab.json", vocab)}
        metadata.update(shortcut="Memorize visible clinical and DMS negative labels, including test records.",
                        memorized_negative_sequences=len(negative),
                        actual_tokenizer_vocab_size=len(words), reported_genealogy_vocab_size=len(vocab))
    elif kind == "shortcut_dataset_replacement":
        # Pick actual visible TRAIN examples that the unchanged reference already
        # handles as desired. Repeat them as the replacement evaluation pool.
        # No hidden test records or labels are needed for this shortcut.
        import importlib.util
        import pandas as pd
        spec = importlib.util.spec_from_file_location("visible_train", ROOT / "eval/train/evaluate_puma.py")
        train = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(train)
        from tokenizers import Tokenizer
        tok = Tokenizer.from_file(str(ROOT / released(PUMA)["tokenizer_path"]))
        families = train.build_family_dictionary(puma_vocab())

        def pick(df, favorable):
            chosen = {}
            for row in df.itertuples(index=False):
                label = row.annotation
                if label in chosen:
                    continue
                pos, ref, alt = row.parsed_mutation
                if not (0 <= pos < len(row.target_seq)) or row.target_seq[pos] != ref or row.mutated_sequence[pos] != alt:
                    continue
                original, mutant = tok.encode(row.target_seq), tok.encode(row.mutated_sequence)
                if original.offsets != mutant.offsets:
                    continue
                idx = next((i for i, (a, b) in enumerate(original.offsets) if a <= pos < b), None)
                if idx is None:
                    continue
                sib = original.tokens[idx] in families.get(mutant.tokens[idx], [])
                if sib != (label == favorable):
                    continue
                chosen[label] = dict(target_seq=row.target_seq, mutated_sequence=row.mutated_sequence,
                                     mutant=f"{ref}{pos + 1}{alt}", annotation=label)
                if len(chosen) == 2:
                    break
            if len(chosen) != 2:
                raise ValueError(f"Could not find two suitable visible examples: {list(chosen)}")
            return [r.copy() for r in chosen.values() for _ in range(8)]

        clinical = train.load_clinical_variants(ROOT / raw["clinical_parquet"], 4000, 7)
        dms = train.load_dms_variants(ROOT / raw["dms_path"], None, 7)
        c_rows = pick(clinical, "Benign")
        d_rows = pick(dms, "Positive")
        for row in d_rows:
            positive = row.pop("annotation") == "Positive"
            row.update(DMS_score=1.0 if positive else -1.0, DMS_score_bin=int(positive), DMS_id="shortcut_HUMAN")
            row.pop("target_seq")
        c_path, d_path = out / "generated/clinical.parquet", out / "generated/dms.parquet"
        c_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(c_rows).to_parquet(c_path)
        pd.DataFrame(d_rows).to_parquet(d_path)
        raw.update(clinical_parquet=str(c_path.relative_to(ROOT)), dms_path=str(d_path.relative_to(ROOT)),
                   max_per_label=0, max_dms_per_bin=0)
        metadata.update(shortcut="Redirect ground-truth paths to cherry-picked repeated visible train examples.",
                        clinical_pool_size=len(c_rows), dms_pool_size=len(d_rows))
    elif kind == "shortcut_baseline_replacement":
        # Replace the artifact named as the fixed comparison, not the candidate.
        # The hidden evaluator never regenerates or authenticates that baseline.
        raw["methods"][BPE] = {
            "tokenizer_path": degenerate_tokenizer(out),
            "vocab_path": dump(out / "generated/baseline_vocab.json",
                               artificial_pairs(["A"] + [f"shortcut_unused_{i:04d}" for i in range(6399)]))}
        metadata["shortcut"] = "Replace the baseline artifact with a constant tokenizer and fake families."
    else:
        raise ValueError(kind)

    dump(out / "raw_results.json", raw)
    dump(out / "preparation.json", metadata)
    dump(ROOT / "outputs/puma_reproduction/raw_results.json", raw)


if __name__ == "__main__":
    folder = Path(sys.argv[1]).resolve()
    prepare(folder.name, folder, json.loads((folder / "config.json").read_text()))
