#!/usr/bin/env python3
"""Export the frequency-only BPE baseline in the gym submission format.

The evaluator already scores this baseline itself (as ``bpe_6400``, from its
own fixed copy), so a method cannot replace it. This script only writes the
same released 6,400-unit BPE vocabulary as ``tokenizer.json`` + a flat
``vocab.json`` (no genealogy) to show the submission format. By default it
writes outside ``outputs/`` so it is not scored twice.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASED = ROOT / "method" / "PUMA_official" / "RSRC" / "vocabs"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="tmp/bpe_baseline_submission")
    args = parser.parse_args()
    out = Path(args.output_dir)
    out = out if out.is_absolute() else ROOT / out
    out.mkdir(parents=True, exist_ok=True)
    tokenizer = json.loads((RELEASED / "hf_uniref50_bpe_6400.json").read_text())
    vocab = json.loads((RELEASED / "uniref50_bpe_6400.json").read_text())
    (out / "tokenizer.json").write_text(json.dumps(tokenizer))
    (out / "vocab.json").write_text(json.dumps(vocab))
    print(f"Wrote BPE baseline submission ({len(vocab)} units, no genealogy) to {out}")


if __name__ == "__main__":
    main()
