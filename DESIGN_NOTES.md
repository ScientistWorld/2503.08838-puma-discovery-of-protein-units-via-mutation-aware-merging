# Design Notes (current, after hardening)

- **Interface.** A method writes `outputs/<name>/tokenizer.json` (HF tokenizers, BPE or Unigram, raw segmentation) and `outputs/<name>/vocab.json` (units + same-length `parent` links). `scripts/evaluate_{train,test}.sh` take no arguments and score every such directory plus the evaluator-owned `bpe_6400` baseline.
- **Comparison side fixed in `eval/`.** Populations and labels (built by `eval/test/prepare_split.py`; test under `eval/test/downloads/split/`, train under `data/downloads/proteingym_train/`), baseline copy, 6,400 budget and thresholds. No seeds, paths or sizes are read from method outputs.
- **Validity gates → failed run.** ≤ 6,400 units; tokenizer units = `vocab.json` units; uppercase residue units; no normalizer/pre-tokenizer/post-processor/padding/truncation/added tokens/dropout; valid same-length parent links; lossless segmentation of every scored sequence; ≥ 2.0 residues per unit; ≥ 3,200 distinct units used; ≥ 20% SAME cases per label. Failure → gaps −1, compression 0, `valid` 0.
- **Scored metrics (bounded).** `benign_pathogenic_gap` (0.6), `positive_negative_gap` (0.3), `compression_vs_bpe` capped at 1 (0.1). Everything else coefficient 0 (reported).
- **Families** are connected groups of parent links (union-find); a sibling event requires the wild-type and mutated units at the site to be in the same group.
- **Train/test independence.** The two evaluators are independent copies; `eval/` never imports `method/`.
- **Diagnostics** per method in `_validation` (errors, per-label counts, analytic gap standard errors).
