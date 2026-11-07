#!/usr/bin/env python3
"""Train PUMA with the official implementation and write a gym submission.

The scored artifact is exactly what this script trains: it runs the official
mutation-aware merge procedure (``method/PUMA_official/Prog/bpe_functions.py``)
on the UniRef50-human corpus, keeps the first ``--vocab-size`` vocabulary
entries in merge order (the official ``vocab_downsampler`` rule used for the
released vocabularies), and writes

    <output-dir>/vocab.json      PUMA vocabulary with genealogy links
    <output-dir>/tokenizer.json  HuggingFace BPE tokenizer built from it
    <output-dir>/training_summary.json

Default configuration is the paper's PUMA(BLOSUM62, a=0.7, f=0.05) with
mutation lengths 3-12 at the gym's 6,400-unit budget, trained on all
sequences of ``data/uniref50_human.fasta`` (the paper's training corpus).
No clinical or DMS labels are used.
"""

from __future__ import annotations

import argparse
import gc
import json
import resource
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_PROG = ROOT / "method" / "PUMA_official" / "Prog"
sys.path.insert(0, str(OFFICIAL_PROG))

import helper_classes  # noqa: E402


class _SlottedSym:
    """Memory-lean drop-in for ``helper_classes.Sym`` (identical behaviour).

    The official linked-list node keeps a per-instance ``__dict__``; training
    on the full 22M-residue corpus creates tens of millions of nodes, so the
    node gets ``__slots__``. Attributes and methods are unchanged.
    """

    __slots__ = ("literal", "prev", "next")

    def __init__(self, symbol_str: str):
        self.literal = symbol_str
        self.prev = None
        self.next = None

    def __len__(self):
        return len(self.literal)

    def __str__(self):
        return self.literal

    def __repr__(self):
        return self.literal


helper_classes.Sym = _SlottedSym

import bpe_functions  # noqa: E402  (binds the slotted Sym)
import vocabulary_functions  # noqa: E402
from Bio.Align import substitution_matrices  # noqa: E402

# Alphabet used by the official training script (multiprocess_training.py).
OFFICIAL_ALPHABET = ["A", "R", "N", "D", "C", "E", "Q", "G", "H", "I", "L", "K", "M",
                     "F", "P", "S", "T", "W", "Y", "V", "U", "O", "X", "B", "Z", "J"]


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


def train_vocab(sequences: list[str], args: argparse.Namespace) -> dict:
    kwargs = dict(
        corpus=sequences,
        alphabet=list(OFFICIAL_ALPHABET),
        tokenizer_type=args.tokenizer_type,
        stop_type="vocab_size",
        stop_parameter=args.vocab_size,
    )
    if args.tokenizer_type == "mutated":
        kwargs.update(
            subs_matrix=substitution_matrices.load(args.matrix),
            mutation_cutoff=args.cutoff,
            min_mutation_freq=args.min_freq,
            min_mutation_len=args.min_len,
            max_mutation_len=args.max_len,
        )
    # The official trainer builds a huge cyclic linked structure; cyclic GC
    # passes over it only cost time (memory is released at process exit).
    gc.disable()
    return bpe_functions.train_bpe(**kwargs)


def trim_vocab(vocab: dict, size: int) -> tuple[dict, int]:
    """First ``size`` entries in merge order (official vocab_downsampler rule)."""
    trimmed = dict(list(vocab.items())[:size])
    dropped = 0
    for entry in trimmed.values():
        # A parent always precedes its children in merge order, so this only
        # triggers if a duplicate token was re-labelled by the official code.
        if "parent" in entry and entry["parent"] not in trimmed:
            entry.pop("parent")
            entry.pop("similarity", None)
            dropped += 1
    return trimmed, dropped


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output-dir", default="outputs/puma_6400")
    parser.add_argument("--fasta", default="data/uniref50_human.fasta")
    parser.add_argument("--n-sequences", type=int, default=0, help="0 = all sequences in the corpus")
    parser.add_argument("--vocab-size", type=int, default=6400)
    parser.add_argument("--tokenizer-type", choices=("mutated", "default"), default="mutated")
    parser.add_argument("--matrix", default="BLOSUM62")
    parser.add_argument("--cutoff", type=float, default=0.7, help="alignment score cut-off a")
    parser.add_argument("--min-freq", type=float, default=0.05, help="frequency cut-off f")
    parser.add_argument("--min-len", type=int, default=3)
    parser.add_argument("--max-len", type=int, default=12)
    args = parser.parse_args()

    out = Path(args.output_dir)
    out = out if out.is_absolute() else ROOT / out
    fasta = Path(args.fasta)
    fasta = fasta if fasta.is_absolute() else ROOT / fasta

    start = time.time()
    sequences = read_fasta_sequences(fasta, args.n_sequences or None)
    print(f"Training {args.tokenizer_type} vocabulary on {len(sequences)} sequences "
          f"({sum(map(len, sequences))} residues)", flush=True)
    vocab = train_vocab(sequences, args)
    untrimmed = len(vocab)
    vocab, dropped = trim_vocab(vocab, args.vocab_size)

    out.mkdir(parents=True, exist_ok=True)
    (out / "vocab.json").write_text(json.dumps(vocab))
    (out / "tokenizer.json").write_text(json.dumps(vocabulary_functions.vocab_dict_to_HF_dict(vocab)))
    summary = {
        "config": vars(args),
        "n_sequences": len(sequences),
        "untrimmed_vocab_size": untrimmed,
        "vocab_size": len(vocab),
        "parent_links_dropped_by_trim": dropped,
        "parent_count": len({e["parent"] for e in vocab.values() if "parent" in e}),
        "mutated_count": sum("parent" in e for e in vocab.values()),
        "seconds": time.time() - start,
        "max_rss_mb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
        "labels_used": False,
    }
    (out / "training_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
