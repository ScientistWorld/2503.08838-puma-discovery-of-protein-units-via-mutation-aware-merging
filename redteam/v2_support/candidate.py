"""Prepare real submissions using scientist-visible sources only.

This module never reads eval/, scoring/, hardening/, the paper, old audit
results, or test splits. Public-answer shortcuts download their OWN copies
of files from URLs in scripts/download.sh. Forbidden label use is explicit.
"""
from __future__ import annotations

import bisect
import copy
import heapq
import json
import os
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
R = ROOT / "redteam"
CACHE = R / "cache"
STANDARD = "ACDEFGHIKLMNPQRSTVWY"
CLASSES = ["ILVM", "FYW", "KRH", "DE", "NQ", "STAG", "C", "P"]


def load(path):
    return json.loads(Path(path).read_text())


def dump(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=2))


def trained(seed=7, cutoff=0.7):
    path = CACHE / f"seed{seed}_cutoff{cutoff}"
    if not (path / "training_summary.json").exists():
        path.mkdir(parents=True, exist_ok=True)
        env = dict(os.environ, PYTHONHASHSEED=str(seed))
        with (path / "training.log").open("w") as log:
            subprocess.run([sys.executable, "redteam/v2_support/train_seed.py", "--seed", str(seed),
                            "--cutoff", str(cutoff), "--output-dir", str(path)],
                           cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
                           check=True, timeout=3600)
    return path


def clean_flags(vocab):
    parents = {v["parent"] for v in vocab.values() if "parent" in v}
    for token, entry in vocab.items():
        entry.pop("is_parent", None)
        if token in parents:
            entry["is_parent"] = True
    return vocab


def flat(vocab):
    return {t: {} for t in vocab}


def chemical_families(vocab):
    cls = {a: i for i, group in enumerate(CLASSES) for a in group}
    parents = {}
    result = {}
    for token in vocab:
        key = tuple(cls.get(a, 100 + ord(a)) for a in token)
        if key in parents:
            result[token] = {"parent": parents[key]}
        else:
            parents[key] = token
            result[token] = {}
    return clean_flags(result)


def normalized_public_frames():
    """Rebuild all public eligible labels WITHOUT knowing the test split rule."""
    import pandas as pd

    out = CACHE / "public_normalized"
    if all((out / (n + ".parquet")).exists() for n in ("clinical", "dms")):
        return {n: pd.read_parquet(out / (n + ".parquet")) for n in ("clinical", "dms")}
    out.mkdir(parents=True, exist_ok=True)
    clinical = pd.read_parquet(R / "downloads/clinical.parquet")
    clinical_records = zip(clinical.target_seq, clinical.mutated_sequence, clinical.mutant,
                           clinical.annotation, ["clinvar"] * len(clinical))
    raw_dms = pd.concat([pd.read_parquet(p) for p in sorted((R / "downloads/dms").glob("*.parquet"))], ignore_index=True)
    mask = pd.Series(False, index=raw_dms.index)
    for c in ("DMS_id", "assay_name", "target_name"):
        if c in raw_dms:
            mask |= raw_dms[c].astype(str).str.contains("HUMAN", case=False, na=False)
    raw_dms = raw_dms[mask & raw_dms.DMS_score.between(-5, 5)]
    dms_records = []
    for m, mu, b, src in zip(raw_dms.mutated_sequence, raw_dms.mutant, raw_dms.DMS_score_bin, raw_dms.DMS_id):
        if not isinstance(mu, str) or ":" in mu:
            continue
        try:
            pos = int(mu[1:-1]) - 1
            if not isinstance(m, str) or not 0 <= pos < len(m):
                continue
            wt = m[:pos] + mu[0] + m[pos + 1:]
        except (ValueError, IndexError):
            continue
        dms_records.append((wt, m, mu, "positive" if int(b) == 1 else "negative", str(src)))

    frames = {}
    for name, records in (("clinical", clinical_records), ("dms", dms_records)):
        seen = {}
        for target, mutated, mutant, label, source in records:
            label = str(label).strip().lower()
            if name == "clinical" and label not in ("benign", "pathogenic"):
                continue
            if not isinstance(mutant, str) or ":" in mutant or len(mutant) < 3:
                continue
            try:
                pos = int(mutant[1:-1]) - 1
            except ValueError:
                continue
            if not isinstance(target, str) or not isinstance(mutated, str):
                continue
            if len(target) > 3000 or len(target) != len(mutated) or not 0 <= pos < len(target):
                continue
            ref, alt = mutant[0], mutant[-1]
            if ref == alt or target[pos] != ref or mutated != target[:pos] + alt + target[pos + 1:]:
                continue
            if set(target) - set(STANDARD) or alt not in STANDARD:
                continue
            key = (target, pos, alt, source) if name == "dms" else (target, pos, alt)
            row = (target, mutated, pos, ref, alt, label, source)
            if key not in seen:
                seen[key] = row
            elif seen[key] is not None and seen[key][5] != label:
                seen[key] = None
        frame = pd.DataFrame([r for r in seen.values() if r is not None],
                             columns=["target_seq", "mutated_sequence", "pos", "ref", "alt", "label", "source"])
        frame.to_parquet(out / f"{name}.parquet", index=False)
        frames[name] = frame
    return frames


def edge_statistics(tok, source):
    """Sufficient statistics for a forbidden supervised family-fitting shortcut."""
    import pandas as pd
    from tokenizers import Tokenizer

    cache = CACHE / f"shortcut_label_edges_{source}.json"
    if cache.exists():
        return load(cache)
    tokenizer = Tokenizer.from_str(json.dumps(tok))
    if source == "visible_train":
        frames = {n: pd.read_parquet(ROOT / f"data/downloads/proteingym_train/{n}_train.parquet") for n in ("clinical", "dms")}
    else:
        frames = normalized_public_frames()
    result = {}
    for name, frame in frames.items():
        targets = sorted(set(frame.target_seq))
        originals = {}
        for start in range(0, len(targets), 512):
            seqs = targets[start:start + 512]
            for seq, enc in zip(seqs, tokenizer.encode_batch(seqs)):
                originals[seq] = (enc.tokens, enc.offsets, [p[0] for p in enc.offsets])
        total, same = Counter(), Counter()
        pairs = defaultdict(Counter)
        records = list(zip(frame.target_seq, frame.mutated_sequence, frame.pos, frame.label))
        for start in range(0, len(records), 512):
            rows = records[start:start + 512]
            for row, enc in zip(rows, tokenizer.encode_batch([r[1] for r in rows])):
                target, _m, pos, label = row
                total[label] += 1
                tokens, offsets, starts = originals[target]
                if enc.offsets != offsets:
                    continue
                same[label] += 1
                idx = bisect.bisect_right(starts, pos) - 1
                a, b = tokens[idx], enc.tokens[idx]
                if a != b:
                    pairs[tuple(sorted((a, b)))][label] += 1
        result[name] = {"total": dict(total), "same": dict(same),
                        "pairs": [[a, b, dict(c)] for (a, b), c in sorted(pairs.items())]}
    dump(cache, result)
    return result


def shortcut_fit_families(tok, vocab, source, clinical_only=False, abandon_dms=False):
    """Greedily maximize the LABELLED objective on a fixed, unchanged tokenizer.

    Each edge weight is the weighted good-minus-bad SAME frequency. Joining
    two components is allowed only if the total weight between them is positive.
    No vocabulary discovery, tokenization change or scientific improvement.
    """
    stats = edge_statistics(tok, source)
    tokens = list(vocab)
    index = {t: i for i, t in enumerate(tokens)}
    weights = Counter()
    for pop, good, bad, coefficient in (("clinical", "benign", "pathogenic", 0.6),
                                        ("dms", "positive", "negative", 0.0 if clinical_only else 0.3)):
        for a, b, counts in stats[pop]["pairs"]:
            weights[index[a], index[b]] += coefficient * (counts.get(good, 0) / stats[pop]["same"][good]
                                                         - counts.get(bad, 0) / stats[pop]["same"][bad])
    if abandon_dms:
        # Shortcut: forbid every DMS SAME pair from ever sharing a family.
        # A penalty of 2 exceeds the sum of all positive clinical weights
        # (at most .6), so even indirect joins cannot defeat this constraint.
        for a, b, _counts in stats["dms"]["pairs"]:
            weights[index[a], index[b]] -= 2.0
    adjacency = {i: {} for i in range(len(tokens))}
    parent = list(range(len(tokens)))
    heap = []
    for (a, b), w in weights.items():
        if not w:
            continue
        adjacency[a][b] = w
        adjacency[b][a] = w
        if w > 0:
            heapq.heappush(heap, (-w, a, b))
    gain = 0.0
    merges = 0
    while heap:
        negative_w, a, b = heapq.heappop(heap)
        w = -negative_w
        if a not in adjacency or b not in adjacency or abs(adjacency[a].get(b, 0) - w) > 1e-14:
            continue
        if w <= 1e-14:
            continue
        if len(adjacency[a]) < len(adjacency[b]):
            a, b = b, a
        parent[b] = a
        gain += w
        merges += 1
        adjacency[a].pop(b, None)
        for neighbor, wb in list(adjacency[b].items()):
            if neighbor == a:
                continue
            adjacency[neighbor].pop(b, None)
            new_w = adjacency[a].get(neighbor, 0.0) + wb
            adjacency[a][neighbor] = new_w
            adjacency[neighbor][a] = new_w
            if new_w > 1e-14:
                x, y = sorted((a, neighbor))
                heapq.heappush(heap, (-new_w, x, y))
        del adjacency[b]

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    if abandon_dms:
        assert all(root(index[a]) != root(index[b]) for a, b, _ in stats["dms"]["pairs"])
    result = {}
    for i, token in enumerate(tokens):
        r = root(i)
        result[token] = {"parent": tokens[r]} if r != i else {}
    return clean_flags(result), {"shortcut": True, "forbidden_labels": source,
        "objective_gain_on_source": gain, "merges": merges,
        "source_counts": {k: {"total": v["total"], "same": v["same"]} for k, v in stats.items()},
        "tokenizer_unchanged": True, "uses_test_split_rule": False,
        "shortcut_abandons_dms": abandon_dms}


def prepare(name):
    cfg = load(R / name / "config.json")
    kind = cfg["kind"]
    out = R / name / "artifact"
    out.mkdir(parents=True, exist_ok=True)
    reference = trained(cfg.get("seed", 7), cfg.get("cutoff", 0.7))
    tok = load(reference / "tokenizer.json")
    vocab = load(reference / "vocab.json")
    details = {"kind": kind, "inputs": ["method/", "data/uniref50_human.fasta"],
               "seed": cfg.get("seed", 7), "cutoff": cfg.get("cutoff", 0.7)}
    if kind in ("reference", "better_cutoff"):
        shutil.copyfile(reference / "training_summary.json", R / name / "training_summary.json")
    elif kind in ("weaker_no_genealogy", "shortcut_forged_fields", "shortcut_move_baseline", "shortcut_move_data", "shortcut_replace_released"):
        vocab = flat(vocab)
    elif kind == "better_chemical_families":
        vocab = chemical_families(vocab)
        details["class_rule"] = CLASSES
        details["labels_used"] = False
    elif kind == "simple_bpe":
        src = ROOT / "method/PUMA_official/RSRC/vocabs"
        tok = load(src / "hf_uniref50_bpe_6400.json")
        vocab = flat(load(src / "uniref50_bpe_6400.json"))
    elif kind in ("shortcut_visible_label_fitting", "shortcut_public_answer_fitting"):
        source = "visible_train" if kind == "shortcut_visible_label_fitting" else "public_download"
        vocab, fit = shortcut_fit_families(tok, vocab, source)
        details.update(fit)
    elif kind == "shortcut_abandon_dms":
        vocab, fit = shortcut_fit_families(tok, vocab, "public_download", clinical_only=True, abandon_dms=True)
        details.update(fit)
    elif kind == "shortcut_compression_tradeoff":
        # Spend only 3,600 units and abandon the no-granularity-sacrifice claim.
        # Chemical-class labels require no variant labels.
        keep = set(list(vocab)[:3600])
        tok["model"]["vocab"] = {t: i for i, t in enumerate(t for t in vocab if t in keep)}
        tok["model"]["merges"] = [m for m in tok["model"]["merges"]
                                  if "".join(m.split(" ") if isinstance(m, str) else m) in keep]
        vocab = chemical_families({t: v for t, v in vocab.items() if t in keep})
        details.update({"shortcut": True, "labels_used": False, "units": 3600, "class_rule": CLASSES})
    elif kind == "shortcut_constant":
        tok = {"version": "1.0", "normalizer": {"type": "Replace", "pattern": {"Regex": ".+"}, "content": "A"},
               "model": {"type": "WordLevel", "vocab": {"A": 0}, "unk_token": "A"}}
        vocab = {"A": {}}
    elif kind == "shortcut_empty":
        tok["model"]["vocab"] = {}
        tok["model"]["merges"] = []
        vocab = {}
    elif kind == "shortcut_copied_residues":
        tok["model"]["vocab"] = {t: i for i, t in enumerate(STANDARD)}
        tok["model"]["merges"] = []
        vocab = chemical_families(dict.fromkeys(STANDARD))
    elif kind == "shortcut_impossible_values":
        vocab = {t: {"is_parent": False, "parent": "SHORTCUTMISSING", "success": True,
                     "time_seconds": -1, "valid": 1, "score": float("inf")} for t in vocab}
    elif kind == "shortcut_identical_artifact":
        # Explicit tie control: reusing a trained reference is scientifically
        # indistinguishable, not evidence of a score-forgery vulnerability.
        details["shortcut"] = True
        details["tie_control"] = True
    else:
        raise ValueError(kind)
    dump(out / "tokenizer.json", tok)
    dump(out / "vocab.json", vocab)
    dump(R / name / "preparation.json", details)
    if cfg.get("seed", 7) == 7 and cfg.get("cutoff", 0.7) == 0.7:
        dump(R / name / "reference_artifact_hashes.json", __import__("hashlib").sha256((reference / "tokenizer.json").read_bytes()).hexdigest())
    print(f"Prepared {name}: {len(vocab)} units", flush=True)


if __name__ == "__main__":
    prepare(sys.argv[1])
