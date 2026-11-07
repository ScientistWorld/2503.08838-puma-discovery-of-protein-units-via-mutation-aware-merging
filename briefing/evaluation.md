# Evaluation

## What a method submits

A method writes one directory per system under `outputs/<method_name>/` with two files:

- `tokenizer.json` — a HuggingFace `tokenizers` file with a `BPE` or `Unigram` model, no normalizer, pre-tokenizer, post-processor, truncation, padding or added tokens, no BPE dropout. Raw protein sequences are segmented as-is.
- `vocab.json` — one entry per vocabulary unit (exactly the tokenizer's units). An entry may carry `"parent": "<unit>"` to place the unit in the family of another unit of the **same length** (a substitution variant); `"is_parent": true` may mark parents. Other fields are ignored. Families are the connected groups formed by parent links.

`bash scripts/evaluate_train.sh` (visible train slice) and `bash scripts/evaluate_test.sh` (hidden test) take no arguments and score **every** method directory on disk, plus a fixed frequency-only BPE baseline (`bpe_6400`) that the evaluator owns. Nothing else a method writes is read; every number is recomputed from the two files. `bash scripts/evaluate.sh` writes the train-slice scores to `scoring/scores.json`.

## Validity constraints (a violation scores the run as failed)

A submission is scored as failed — the worst value on every scored metric (`gap = -1`, `compression_vs_bpe = 0`) and `valid = 0` — if any of these fail:

- at most **6,400** vocabulary units; `vocab.json` units equal the tokenizer's units; units are uppercase residue strings; Unigram scores are finite;
- every parent link points to an existing unit of the same length;
- segmentation is **lossless**: on every scored wild-type and mutated sequence the units concatenate back to the sequence;
- the segmentation is a real unit vocabulary: at least **2.0 residues per unit** on average and at least **3,200 distinct units** used on the scored proteins;
- **granularity is not sacrificed**: residues per unit on the scored proteins are at least **0.95×** those of the frequency-only baseline (`compression_vs_bpe ≥ 0.95` before capping);
- for each label, at least **20%** of variants leave every unit boundary unchanged.

## Both biological tasks must be solved

A valid submission *solves* the two biological tasks when its benign−pathogenic gap is at least **0.04** and its positive−negative gap is at least **0.014** (about half of the published effect at this vocabulary size). If either gap is below its minimum, `task_solved = 0` and **neither** gap earns credit: each is scored as `min(measured gap, 0)`. With the weights below, a valid submission that solves both tasks always ranks above one that does not, and any valid submission ranks above a failed one:

| Outcome | Rank score S = 0.6·clinical gap + 0.3·DMS gap + 0.1·compression |
|---|---|
| constraint violated | −0.9 |
| valid, a task not solved | ≤ 0.1 |
| valid, both tasks solved | ≥ 0.6·0.04 + 0.3·0.014 + 0.1·0.95 ≈ 0.123 |

## Metrics

**SAME sibling rate.** For a single amino-acid substitution, the wild-type and mutated sequences are segmented. If every unit boundary is unchanged (a SAME case), the substitution is a *sibling* event when the wild-type unit and the mutated unit at the substituted position belong to the same family. The SAME sibling rate of a label is the fraction of its SAME cases that are sibling events; `*_same_idx` is the fraction of its variants that are SAME.

| Experiment | Weight | Scored metric (coefficient 1) | Meaning |
|---|---:|---|---|
| `clinical_sibling_association` | 0.6 | `benign_pathogenic_gap` | benign minus pathogenic SAME sibling rate on ClinVar variants of held-out proteins |
| `dms_sibling_association` | 0.3 | `positive_negative_gap` | positive (high-fitness) minus negative (low-fitness) SAME sibling rate on human DMS variants of held-out protein regions |
| `vocabulary_structure` | 0.1 | `compression_vs_bpe` | residues per unit on the scored proteins divided by the BPE baseline's, capped at 1 |

All other reported metrics (per-label rates, `*_same_idx`, family coverage and family-shape statistics, vocabulary size, residues per unit, distinct units used, `task_solved`, `valid`) have coefficient 0: they are for auditing. The rank of a method is the sum over experiments of weight × coefficient × (metric − reference metric).

## Data and splits

The populations are fixed by the evaluator. ProteinGym ClinVar single substitutions (benign / pathogenic) are split **by protein**; human ProteinGym DMS single substitutions (positive / negative fitness bin) are split by protein region (50-residue windows). Only substitutions in wild-type sequences of at most 3,000 standard residues are used. The train populations are visible in `data/downloads/proteingym_train/`; the hidden test populations are held out. All variants of each population are scored (no subsampling), so scores are deterministic.

The unlabeled training corpus is `data/uniref50_human.fasta` (human UniRef50 representatives). Labels must not be used to build a vocabulary or its families.

## Baselines and targets

`bpe_6400` is a frequency-only 6,400-unit vocabulary without families: its sibling gaps are 0, so it does not solve the biological tasks (`task_solved = 0`, S = 0.1 from its compression ratio of 1 by definition). `scoring/reference.json` lists the published numbers; `scoring/scores_train.json` and `scoring/scores_test.json` hold the reproduced reference.
