# Overview

- **Paper ID:** 2503.08838
- **Title:** PUMA: Discovery of Protein Units via Mutation-Aware Merging
- **Domain:** Computational Biology / Protein Sequence Tokenization
- **TL;DR:** PUMA extends BPE for proteins by adding substitution-matrix-guided mutational variants during merging, producing a vocabulary plus a biologically meaningful genealogy.

## Short Summary

The paper addresses how to discover contiguous protein sequence units that act like words in the language of life. PUMA keeps the frequency-based core of BPE but explicitly searches for plausible amino-acid substitution variants of each newly merged unit and records their genealogical relationships. The authors validate the resulting families using clinical variants, deep mutational scanning, ESM-2 masked-token preferences, and Gene Ontology topic modeling.

## Key Results

- On ProteinGym ClinVar substitutions, PUMA(BLOSUM62, 0.7, 0.05) at 6,400 tokens has a benign SAME sibling rate of 0.158 versus 0.074 for pathogenic variants.
- On human ProteinGym DMS substitutions, the same compact PUMA setting has a positive SAME sibling rate of 0.075 versus 0.047 for negative variants.
- The released 6,400-token PUMA vocabulary has 94.1% family coverage, while the frequency-only BPE baseline has no genealogy.
- The frequency-only BPE baseline has no genealogy and therefore zero SAME sibling rate under this metric.
- The gym reproduction trains PUMA(BLOSUM62, 0.7, 0.05) with the official code on the full human UniRef50 corpus at 6,400 units and submits exactly that trained vocabulary; it is scored on held-out ClinVar proteins, held-out DMS protein regions, and a segmentation-granularity constraint against the frequency-only BPE baseline.

---

# Problem Definition

## Research Question

Can a protein sequence vocabulary segment complete amino-acid chains into reusable contiguous units while preserving biologically meaningful relationships between single-residue variants of those units?

## Why It Matters

Protein language models and downstream analyses usually operate at residue level or use frequency-only subwords. A useful intermediate vocabulary should expose larger interpretable units and should distinguish substitutions that preserve function from substitutions that are more disruptive.

## Success Criteria

A successful system should tokenize full protein sequences losslessly with a fixed budget of 6,400 units, group related unit variants into explicit families, and show — on proteins it has never seen labels for — that substitutions staying within a family are enriched among benign or high-fitness variants compared with pathogenic or low-fitness variants, without giving up segmentation granularity relative to a frequency-only vocabulary of the same size. Labels are never used to build the vocabulary.

---

# Paper's Method

## Key Contribution

PUMA discovers protein units with an iterative merge procedure that adds mutation-aware variants to a normal frequency-driven BPE merge vocabulary. Its output is both a vocabulary and a genealogy connecting parent units, child mutation units, and sibling variants.

## Approach

The vocabulary starts from amino-acid characters. At each iteration PUMA extracts the most frequent adjacent pair, merges it, and adds the merged string as a unit. For merged units within the configured length range, it enumerates candidate substitutions using non-negative entries in an amino-acid substitution matrix such as BLOSUM62. A candidate variant is accepted only if it meets the normalized alignment-score cutoff and if an adjacent pair currently exists in the corpus whose merge would form that candidate with sufficient frequency relative to the parent. Accepted variants are merged immediately and linked genealogically to the parent.

## Main Claims

The primary claim is that mutation-aware merging yields protein-unit families whose within-family substitutions are enriched for biologically favorable outcomes, such as benign ClinVar substitutions and high-fitness DMS substitutions. Secondary claims are that protein language models contextually prefer PUMA sibling substitutions over alternatives and that graph-aware topic models using the genealogy better align unit distributions with functional annotations.

## Reproduction in this gym

`scripts/method.sh` runs `method/run_puma.py`, which trains PUMA(BLOSUM62, a=0.7, f=0.05, mutation lengths 3-12) with the official implementation (`method/PUMA_official/Prog/bpe_functions.py`) on all sequences of `data/uniref50_human.fasta`, keeps the first 6,400 entries in merge order (the authors' downsampling rule for the released vocabularies), and writes `outputs/puma_6400/{tokenizer,vocab}.json`. The trained vocabulary is the scored artifact.

---

# Evaluation

## What a method submits

A method writes one directory per system under `outputs/<method_name>/` with two files:

- `tokenizer.json` — a HuggingFace `tokenizers` file with a `BPE` or `Unigram` model, no normalizer, pre-tokenizer, post-processor, truncation, padding or added tokens, no BPE dropout. Raw protein sequences are segmented as-is.
- `vocab.json` — one entry per vocabulary unit (exactly the tokenizer's units). An entry may carry `"parent": "<unit>"` to place the unit in the family of another unit of the **same length** (a substitution variant); `"is_parent": true` may mark parents. Other fields are ignored. Families are the connected groups formed by parent links.

`bash scripts/evaluate_train.sh` (visible train slice) and `bash scripts/evaluate_test.sh` (hidden test) take no arguments and score **every** method directory on disk, plus a fixed frequency-only BPE baseline (`bpe_6400`) that the evaluator owns. Nothing else a method writes is read; every number is recomputed from the two files. `bash scripts/evaluate.sh` writes the train-slice scores to `scoring/scores.json`.

## Validity constraints (a violation scores the run as failed)

A submission is scored as failed — the worst value on every scored metric (`gap = -1`, `compression_vs_bpe = 0`) and `valid = 0` — if any of these fail:

- at most **6,400** vocabulary units; `vocab.json` units equal the tokenizer's units; units are uppercase residue strings;
- every parent link points to an existing unit of the same length;
- segmentation is **lossless**: on every scored wild-type and mutated sequence the units concatenate back to the sequence;
- the segmentation is a real unit vocabulary: at least **2.0 residues per unit** on average and at least **3,200 distinct units** used on the scored proteins;
- for each label, at least **20%** of variants leave every unit boundary unchanged.

## Metrics

**SAME sibling rate.** For a single amino-acid substitution, the wild-type and mutated sequences are segmented. If every unit boundary is unchanged (a SAME case), the substitution is a *sibling* event when the wild-type unit and the mutated unit at the substituted position belong to the same family. The SAME sibling rate of a label is the fraction of its SAME cases that are sibling events; `*_same_idx` is the fraction of its variants that are SAME.

| Experiment | Weight | Scored metric (coefficient 1) | Meaning |
|---|---:|---|---|
| `clinical_sibling_association` | 0.6 | `benign_pathogenic_gap` | benign minus pathogenic SAME sibling rate on ClinVar variants of held-out proteins |
| `dms_sibling_association` | 0.3 | `positive_negative_gap` | positive (high-fitness) minus negative (low-fitness) SAME sibling rate on human DMS variants of held-out protein regions |
| `vocabulary_structure` | 0.1 | `compression_vs_bpe` | residues per unit on the scored proteins divided by the BPE baseline's, capped at 1 |

All other reported metrics (per-label rates, `*_same_idx`, family coverage and family-shape statistics, vocabulary size, residues per unit, distinct units used, `valid`) have coefficient 0: they are for auditing. The rank of a method is the sum over experiments of weight × coefficient × (metric − reference metric).

## Data and splits

The populations are fixed by the evaluator. ProteinGym ClinVar single substitutions (benign / pathogenic) are split **by protein**; human ProteinGym DMS single substitutions (positive / negative fitness bin) are split by protein region (50-residue windows). Only substitutions in wild-type sequences of at most 3,000 standard residues are used. The train populations are visible in `data/downloads/proteingym_train/`; the hidden test populations are held out. All variants of each population are scored (no subsampling), so scores are deterministic.

The unlabeled training corpus is `data/uniref50_human.fasta` (human UniRef50 representatives). Labels must not be used to build a vocabulary or its families.

## Baselines and targets

`bpe_6400` is a frequency-only 6,400-unit vocabulary without families (sibling gaps 0, compression ratio 1 by definition). `scoring/reference.json` lists the published numbers; `scoring/scores_train.json` and `scoring/scores_test.json` hold the reproduced reference.

---

# Reproduction Log

### Iteration 1: gpt-5.5
- **Milestone**: `secondary_claims` | **Status**: done
- **Working time**: 14m | **GPU**: 0.0h
- **Jobs**: 2 total (2 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-12 13:55] - none
- Read the paper and identified PUMA as a mutation-aware BPE algorithm for protein-unit discovery.
- Cloned the official PUMA repository and inspected the released training, vocabulary, and validation code.
- Downloaded the public ProteinGym clinical substitutions split used for the paper's ClinVar-style validation.
- Implemented method and evaluation wrappers; the compute job will test whether the method executes end to end.

### [2026-06-12 13:56] - core_claim
- CPU smoke job completed successfully in the container.
- The actual PUMA mutation-aware merge code ran end to end on a compact training subset and wrote a fresh small vocabulary checkpoint.
- The released 6,400-token PUMA vocabulary reproduced the paper's clinical sibling-association claim on 4,000 benign and 4,000 pathogenic ProteinGym variants.
- PUMA reproduced a benign-pathogenic SAME sibling gap of 0.0876 versus the paper's 0.0835; the BPE baseline remained at 0.0 because it has no mutation genealogy.
- Expanded scoring now also records vocabulary-family structure at the fixed 6,400-unit budget.

### [2026-06-12 14:00] - secondary_claims
- Expanded scoring suite reran successfully inside the compute container.
- The vocabulary-structure experiment reproduced the released 6,400-token PUMA family coverage of 0.94125, mutated vocabulary fraction of 0.83719, and parent vocabulary fraction of 0.10406.
- `python validate.py --compare` passed with clinical and vocabulary-structure experiments, import separation, artifact-based evaluation, and shared-path checks.

</details>

### Iteration 2: gpt-5.5
- **Milestone**: `secondary_claims` | **Status**: done
- **Working time**: 10m | **GPU**: 0.0h
- **Jobs**: 3 total (3 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-12 00:00] - method_runs
- Vendored the official PUMA implementation and released UniRef50-human 6,400-token vocabularies.
- Confirmed the mutation-aware merge implementation can train a small fresh PUMA vocabulary end to end.

### [2026-06-12 00:00] - core_claim
- Reproduced the clinical SAME sibling association on ProteinGym ClinVar substitutions.
- PUMA shows a benign-pathogenic SAME sibling gap while frequency-only BPE has no sibling genealogy.

### [2026-06-12 00:00] - core_claim_plus
- Added the vocabulary-structure experiment to verify non-trivial mutation-linked family coverage at the same fixed vocabulary budget.
- `python validate.py --compare` passes with clean method/eval separation.

### [2026-06-12 13:47] - secondary_claims
- Audited method fidelity, evaluation independence, scripts, and documentation.
- Restored the `secondary_claims` milestone because the vocabulary-structure reproduction covers a secondary paper claim in addition to the core clinical association.
- Cleaned baseline and documentation inconsistencies found during the continuation audit.

### [2026-06-12 14:14] - secondary_claims
- CPU job `7d8d021d-1ba` completed successfully.
- Added and reproduced the human ProteinGym DMS SAME sibling association: PUMA positive-negative gap `0.02803`, matching the official 6,400-token reference.
- `python validate.py --compare` passed for clinical, DMS, and vocabulary-structure experiments.

</details>

### Iteration 3: gpt-5.5
- **Milestone**: `secondary_claims` | **Status**: done
- **Working time**: 8m | **GPU**: 0.0h
- **Jobs**: 4 total (4 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-12 14:21] - secondary_claims
- Reproduced the core clinical SAME sibling-rate association for PUMA versus BPE on ProteinGym ClinVar substitutions.
- Reproduced secondary DMS sibling-association and vocabulary-structure targets at the compact 6,400-token setting.
- Verified the implementation runs the official mutation-aware PUMA merge code for a small fresh vocabulary and scores released PUMA/BPE vocabularies through a method-independent evaluator.

### [2026-06-12 14:25] - core_claim_plus
- Continuation reset starts this audit one level below the previous `secondary_claims` claim.
- The method implementation remains a real PUMA reproduction using the official mutation-aware merge code and released PUMA/BPE vocabulary artifacts.
- The evaluator has been made independent of method-side counters; a CPU test job is queued to verify the regenerated clinical, DMS, and vocabulary-structure scores before restoring `secondary_claims`.

### [2026-06-12 14:34] - secondary_claims
- CPU verification job `083b2b54-456` completed successfully with exit code 0.
- `scripts/reproduce.sh` regenerated raw method artifacts and `scoring/scores.json` through the independent evaluator.
- `python validate.py --compare` passed, confirming reproduced clinical, DMS, and vocabulary-structure metrics plus method/eval separation checks.

</details>

### Iteration 4: gpt-5.5 (designer_stage_1)
- **Milestone**: `secondary_claims` | **Status**: done
- **Working time**: 5m | **GPU**: 0.0h
- **Jobs**: 4 total (4 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-12 14:21] - secondary_claims
- Reproduced the core clinical SAME sibling-rate association for PUMA versus BPE on ProteinGym ClinVar substitutions.
- Reproduced secondary DMS sibling-association and vocabulary-structure targets at the compact 6,400-token setting.
- Verified the implementation runs the official mutation-aware PUMA merge code for a small fresh vocabulary and scores released PUMA/BPE vocabularies through a method-independent evaluator.

### [2026-06-12 14:25] - core_claim_plus
- Continuation reset starts this audit one level below the previous `secondary_claims` claim.
- The method implementation remains a real PUMA reproduction using the official mutation-aware merge code and released PUMA/BPE vocabulary artifacts.
- The evaluator has been made independent of method-side counters; a CPU test job is queued to verify the regenerated clinical, DMS, and vocabulary-structure scores before restoring `secondary_claims`.

### [2026-06-12 14:34] - secondary_claims
- CPU verification job `083b2b54-456` completed successfully with exit code 0.
- `scripts/reproduce.sh` regenerated raw method artifacts and `scoring/scores.json` through the independent evaluator.
- `python validate.py --compare` passed, confirming reproduced clinical, DMS, and vocabulary-structure metrics plus method/eval separation checks.

</details>

### Iteration 5: gpt-5.5 (designer_stage_2)
- **Milestone**: `secondary_claims` | **Status**: error
- **Working time**: 15m | **GPU**: 0.0h
- **Jobs**: 4 total (4 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-12 14:21] - secondary_claims
- Reproduced the core clinical SAME sibling-rate association for PUMA versus BPE on ProteinGym ClinVar substitutions.
- Reproduced secondary DMS sibling-association and vocabulary-structure targets at the compact 6,400-token setting.
- Verified the implementation runs the official mutation-aware PUMA merge code for a small fresh vocabulary and scores released PUMA/BPE vocabularies through a method-independent evaluator.

### [2026-06-12 14:25] - core_claim_plus
- Continuation reset starts this audit one level below the previous `secondary_claims` claim.
- The method implementation remains a real PUMA reproduction using the official mutation-aware merge code and released PUMA/BPE vocabulary artifacts.
- The evaluator has been made independent of method-side counters; a CPU test job is queued to verify the regenerated clinical, DMS, and vocabulary-structure scores before restoring `secondary_claims`.

### [2026-06-12 14:34] - secondary_claims
- CPU verification job `083b2b54-456` completed successfully with exit code 0.
- `scripts/reproduce.sh` regenerated raw method artifacts and `scoring/scores.json` through the independent evaluator.
- `python validate.py --compare` passed, confirming reproduced clinical, DMS, and vocabulary-structure metrics plus method/eval separation checks.

</details>

### Iteration 5: gpt-5.5 (designer_stage_2)
- **Milestone**: `secondary_claims` | **Status**: error
- **Working time**: 15m | **GPU**: 0.0h
- **Jobs**: 4 total (4 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-12 14:21] - secondary_claims
- Reproduced the core clinical SAME sibling-rate association for PUMA versus BPE on ProteinGym ClinVar substitutions.
- Reproduced secondary DMS sibling-association and vocabulary-structure targets at the compact 6,400-token setting.
- Verified the implementation runs the official mutation-aware PUMA merge code for a small fresh vocabulary and scores released PUMA/BPE vocabularies through a method-independent evaluator.

### [2026-06-12 14:25] - core_claim_plus
- Continuation reset starts this audit one level below the previous `secondary_claims` claim.
- The method implementation remains a real PUMA reproduction using the official mutation-aware merge code and released PUMA/BPE vocabulary artifacts.
- The evaluator has been made independent of method-side counters; a CPU test job is queued to verify the regenerated clinical, DMS, and vocabulary-structure scores before restoring `secondary_claims`.

### [2026-06-12 14:34] - secondary_claims
- CPU verification job `083b2b54-456` completed successfully with exit code 0.
- `scripts/reproduce.sh` regenerated raw method artifacts and `scoring/scores.json` through the independent evaluator.
- `python validate.py --compare` passed, confirming reproduced clinical, DMS, and vocabulary-structure metrics plus method/eval separation checks.

</details>

### Iteration 5: gpt-5.5 (designer_stage_2)
- **Milestone**: `secondary_claims` | **Status**: error
- **Working time**: 15m | **GPU**: 0.0h
- **Jobs**: 4 total (4 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-12 14:21] - secondary_claims
- Reproduced the core clinical SAME sibling-rate association for PUMA versus BPE on ProteinGym ClinVar substitutions.
- Reproduced secondary DMS sibling-association and vocabulary-structure targets at the compact 6,400-token setting.
- Verified the implementation runs the official mutation-aware PUMA merge code for a small fresh vocabulary and scores released PUMA/BPE vocabularies through a method-independent evaluator.

### [2026-06-12 14:25] - core_claim_plus
- Continuation reset starts this audit one level below the previous `secondary_claims` claim.
- The method implementation remains a real PUMA reproduction using the official mutation-aware merge code and released PUMA/BPE vocabulary artifacts.
- The evaluator has been made independent of method-side counters; a CPU test job is queued to verify the regenerated clinical, DMS, and vocabulary-structure scores before restoring `secondary_claims`.

### [2026-06-12 14:34] - secondary_claims
- CPU verification job `083b2b54-456` completed successfully with exit code 0.
- `scripts/reproduce.sh` regenerated raw method artifacts and `scoring/scores.json` through the independent evaluator.
- `python validate.py --compare` passed, confirming reproduced clinical, DMS, and vocabulary-structure metrics plus method/eval separation checks.

</details>

### Iteration 5: gpt-5.5 (designer_stage_2)
- **Milestone**: `secondary_claims` | **Status**: done
- **Working time**: 3m | **GPU**: 0.0h
- **Jobs**: 4 total (4 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-12 14:21] - secondary_claims
- Reproduced the core clinical SAME sibling-rate association for PUMA versus BPE on ProteinGym ClinVar substitutions.
- Reproduced secondary DMS sibling-association and vocabulary-structure targets at the compact 6,400-token setting.
- Verified the implementation runs the official mutation-aware PUMA merge code for a small fresh vocabulary and scores released PUMA/BPE vocabularies through a method-independent evaluator.

### [2026-06-12 14:25] - core_claim_plus
- Continuation reset starts this audit one level below the previous `secondary_claims` claim.
- The method implementation remains a real PUMA reproduction using the official mutation-aware merge code and released PUMA/BPE vocabulary artifacts.
- The evaluator has been made independent of method-side counters; a CPU test job is queued to verify the regenerated clinical, DMS, and vocabulary-structure scores before restoring `secondary_claims`.

### [2026-06-12 14:34] - secondary_claims
- CPU verification job `083b2b54-456` completed successfully with exit code 0.
- `scripts/reproduce.sh` regenerated raw method artifacts and `scoring/scores.json` through the independent evaluator.
- `python validate.py --compare` passed, confirming reproduced clinical, DMS, and vocabulary-structure metrics plus method/eval separation checks.

</details>

### Iteration 6: gpt-5.5 (designer_stage_3)
- **Milestone**: `secondary_claims` | **Status**: error
- **Working time**: 23m | **GPU**: 0.0h
- **Jobs**: 7 total (7 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-12 14:21] - secondary_claims
- Reproduced the core clinical SAME sibling-rate association for PUMA versus BPE on ProteinGym ClinVar substitutions.
- Reproduced secondary DMS sibling-association and vocabulary-structure targets at the compact 6,400-token setting.
- Verified the implementation runs the official mutation-aware PUMA merge code for a small fresh vocabulary and scores released PUMA/BPE vocabularies through a method-independent evaluator.

### [2026-06-12 14:25] - core_claim_plus
- Continuation reset starts this audit one level below the previous `secondary_claims` claim.
- The method implementation remains a real PUMA reproduction using the official mutation-aware merge code and released PUMA/BPE vocabulary artifacts.
- The evaluator has been made independent of method-side counters; a CPU test job is queued to verify the regenerated clinical, DMS, and vocabulary-structure scores before restoring `secondary_claims`.

### [2026-06-12 14:34] - secondary_claims
- CPU verification job `083b2b54-456` completed successfully with exit code 0.
- `scripts/reproduce.sh` regenerated raw method artifacts and `scoring/scores.json` through the independent evaluator.
- `python validate.py --compare` passed, confirming reproduced clinical, DMS, and vocabulary-structure metrics plus method/eval separation checks.

</details>

### Iteration 6: gpt-5.5 (designer_stage_3)
- **Milestone**: `secondary_claims` | **Status**: done
- **Working time**: 2m | **GPU**: 0.0h
- **Jobs**: 7 total (7 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-12 14:21] - secondary_claims
- Reproduced the core clinical SAME sibling-rate association for PUMA versus BPE on ProteinGym ClinVar substitutions.
- Reproduced secondary DMS sibling-association and vocabulary-structure targets at the compact 6,400-token setting.
- Verified the implementation runs the official mutation-aware PUMA merge code for a small fresh vocabulary and scores released PUMA/BPE vocabularies through a method-independent evaluator.

### [2026-06-12 14:25] - core_claim_plus
- Continuation reset starts this audit one level below the previous `secondary_claims` claim.
- The method implementation remains a real PUMA reproduction using the official mutation-aware merge code and released PUMA/BPE vocabulary artifacts.
- The evaluator has been made independent of method-side counters; a CPU test job is queued to verify the regenerated clinical, DMS, and vocabulary-structure scores before restoring `secondary_claims`.

### [2026-06-12 14:34] - secondary_claims
- CPU verification job `083b2b54-456` completed successfully with exit code 0.
- `scripts/reproduce.sh` regenerated raw method artifacts and `scoring/scores.json` through the independent evaluator.
- `python validate.py --compare` passed, confirming reproduced clinical, DMS, and vocabulary-structure metrics plus method/eval separation checks.

</details>

### Iteration 7: gpt-5.5 (packager)
- **Milestone**: `secondary_claims` | **Status**: done
- **Working time**: 3m | **GPU**: 0.0h
- **Jobs**: 7 total (7 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-12 14:21] - secondary_claims
- Reproduced the core clinical SAME sibling-rate association for PUMA versus BPE on ProteinGym ClinVar substitutions.
- Reproduced secondary DMS sibling-association and vocabulary-structure targets at the compact 6,400-token setting.
- Verified the implementation runs the official mutation-aware PUMA merge code for a small fresh vocabulary and scores released PUMA/BPE vocabularies through a method-independent evaluator.

### [2026-06-12 14:25] - core_claim_plus
- Continuation reset starts this audit one level below the previous `secondary_claims` claim.
- The method implementation remains a real PUMA reproduction using the official mutation-aware merge code and released PUMA/BPE vocabulary artifacts.
- The evaluator has been made independent of method-side counters; a CPU test job is queued to verify the regenerated clinical, DMS, and vocabulary-structure scores before restoring `secondary_claims`.

### [2026-06-12 14:34] - secondary_claims
- CPU verification job `083b2b54-456` completed successfully with exit code 0.
- `scripts/reproduce.sh` regenerated raw method artifacts and `scoring/scores.json` through the independent evaluator.
- `python validate.py --compare` passed, confirming reproduced clinical, DMS, and vocabulary-structure metrics plus method/eval separation checks.

</details>

### Iteration 8: gpt-5.5 (verifier)
- **Milestone**: `secondary_claims` | **Status**: done
- **Working time**: 8m | **GPU**: 0.0h
- **Jobs**: 7 total (7 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-12 14:21] - secondary_claims
- Reproduced the core clinical SAME sibling-rate association for PUMA versus BPE on ProteinGym ClinVar substitutions.
- Reproduced secondary DMS sibling-association and vocabulary-structure targets at the compact 6,400-token setting.
- Verified the implementation runs the official mutation-aware PUMA merge code for a small fresh vocabulary and scores released PUMA/BPE vocabularies through a method-independent evaluator.

### [2026-06-12 14:25] - core_claim_plus
- Continuation reset starts this audit one level below the previous `secondary_claims` claim.
- The method implementation remains a real PUMA reproduction using the official mutation-aware merge code and released PUMA/BPE vocabulary artifacts.
- The evaluator has been made independent of method-side counters; a CPU test job is queued to verify the regenerated clinical, DMS, and vocabulary-structure scores before restoring `secondary_claims`.

### [2026-06-12 14:34] - secondary_claims
- CPU verification job `083b2b54-456` completed successfully with exit code 0.
- `scripts/reproduce.sh` regenerated raw method artifacts and `scoring/scores.json` through the independent evaluator.
- `python validate.py --compare` passed, confirming reproduced clinical, DMS, and vocabulary-structure metrics plus method/eval separation checks.

### [2026-06-22 22:24] - secondary_claims
- Audited the resumed workspace and confirmed `python validate.py --compare` still passes.
- Updated `scripts/run.sh` to regenerate raw PUMA artifacts before scoring train/test slices, removing dependence on ignored `outputs/` state.
- Submitting a CPU test verification job for the refreshed end-to-end job wrapper.

### [2026-06-22 22:28] - secondary_claims
- Final verification confirmed the reproduced clinical, DMS, and vocabulary-structure scores are plausible and pass `python validate.py --compare`.
- Removed method-specific details from the method-agnostic evaluation briefing and moved the benchmark FASTA reference to tracked `data/uniref50_human.fasta`.
- Verified download URLs, shell scripts, Python syntax, method/eval separation, and train/test score wiring.

</details>

### Iteration 9: gpt-5.5 (verifier)
- **Milestone**: `secondary_claims` | **Status**: done
- **Working time**: 9m | **GPU**: 0.0h
- **Jobs**: 8 total (8 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-12 14:21] - secondary_claims
- Reproduced the core clinical SAME sibling-rate association for PUMA versus BPE on ProteinGym ClinVar substitutions.
- Reproduced secondary DMS sibling-association and vocabulary-structure targets at the compact 6,400-token setting.
- Verified the implementation runs the official mutation-aware PUMA merge code for a small fresh vocabulary and scores released PUMA/BPE vocabularies through a method-independent evaluator.

### [2026-06-12 14:25] - core_claim_plus
- Continuation reset starts this audit one level below the previous `secondary_claims` claim.
- The method implementation remains a real PUMA reproduction using the official mutation-aware merge code and released PUMA/BPE vocabulary artifacts.
- The evaluator has been made independent of method-side counters; a CPU test job is queued to verify the regenerated clinical, DMS, and vocabulary-structure scores before restoring `secondary_claims`.

### [2026-06-12 14:34] - secondary_claims
- CPU verification job `083b2b54-456` completed successfully with exit code 0.
- `scripts/reproduce.sh` regenerated raw method artifacts and `scoring/scores.json` through the independent evaluator.
- `python validate.py --compare` passed, confirming reproduced clinical, DMS, and vocabulary-structure metrics plus method/eval separation checks.

### [2026-06-22 22:24] - secondary_claims
- Audited the resumed workspace and confirmed `python validate.py --compare` still passes.
- Updated `scripts/run.sh` to regenerate raw PUMA artifacts before scoring train/test slices, removing dependence on ignored `outputs/` state.
- Submitting a CPU test verification job for the refreshed end-to-end job wrapper.

### [2026-06-22 22:28] - secondary_claims
- Final verification confirmed the reproduced clinical, DMS, and vocabulary-structure scores are plausible and pass `python validate.py --compare`.
- Removed method-specific details from the method-agnostic evaluation briefing and moved the benchmark FASTA reference to tracked `data/uniref50_human.fasta`.
- Verified download URLs, shell scripts, Python syntax, method/eval separation, and train/test score wiring.

### [2026-06-22 22:32] - secondary_claims
- Tightened the default method-independent evaluator so `scripts/evaluate.sh` emits all benefit and constraint metrics declared in `scoring/reference.json`, matching the richer train/test evaluators.
- Local `python -m py_compile ...` and `python validate.py --compare` passed; direct local evaluator execution is deferred to the packaged CPU test job because the login-node Python environment lacks declared container dependencies.
- Added explicit DMS shard preflight checks to `scripts/run.sh` after background audit found that partial downloads would otherwise fail later inside Python.
- Submitting a CPU test job to regenerate method artifacts, default/train/test scores, and validation output inside the reproducible container.

### [2026-06-22 22:48] - secondary_claims
- CPU verification job `adc14804-28b` completed successfully with exit code 0.
- The job regenerated raw method artifacts plus `scoring/scores.json`, `scoring/scores_train.json`, and `scoring/scores_test.json` inside the packaged container.
- `python validate.py --compare` passed after regeneration, including method/eval separation, shared-path portability, train/test independence, and method-key consistency checks.

</details>

### Iteration 10: gpt-6.1-sol (redteam)
- **Milestone**: `secondary_claims` | **Status**: done
- **Working time**: 8m | **GPU**: 0.0h
- **Jobs**: 8 total (8 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-12 14:21] - secondary_claims
- Reproduced the core clinical SAME sibling-rate association for PUMA versus BPE on ProteinGym ClinVar substitutions.
- Reproduced secondary DMS sibling-association and vocabulary-structure targets at the compact 6,400-token setting.
- Verified the implementation runs the official mutation-aware PUMA merge code for a small fresh vocabulary and scores released PUMA/BPE vocabularies through a method-independent evaluator.

### [2026-06-12 14:25] - core_claim_plus
- Continuation reset starts this audit one level below the previous `secondary_claims` claim.
- The method implementation remains a real PUMA reproduction using the official mutation-aware merge code and released PUMA/BPE vocabulary artifacts.
- The evaluator has been made independent of method-side counters; a CPU test job is queued to verify the regenerated clinical, DMS, and vocabulary-structure scores before restoring `secondary_claims`.

### [2026-06-12 14:34] - secondary_claims
- CPU verification job `083b2b54-456` completed successfully with exit code 0.
- `scripts/reproduce.sh` regenerated raw method artifacts and `scoring/scores.json` through the independent evaluator.
- `python validate.py --compare` passed, confirming reproduced clinical, DMS, and vocabulary-structure metrics plus method/eval separation checks.

### [2026-06-22 22:24] - secondary_claims
- Audited the resumed workspace and confirmed `python validate.py --compare` still passes.
- Updated `scripts/run.sh` to regenerate raw PUMA artifacts before scoring train/test slices, removing dependence on ignored `outputs/` state.
- Submitting a CPU test verification job for the refreshed end-to-end job wrapper.

### [2026-06-22 22:28] - secondary_claims
- Final verification confirmed the reproduced clinical, DMS, and vocabulary-structure scores are plausible and pass `python validate.py --compare`.
- Removed method-specific details from the method-agnostic evaluation briefing and moved the benchmark FASTA reference to tracked `data/uniref50_human.fasta`.
- Verified download URLs, shell scripts, Python syntax, method/eval separation, and train/test score wiring.

### [2026-06-22 22:32] - secondary_claims
- Tightened the default method-independent evaluator so `scripts/evaluate.sh` emits all benefit and constraint metrics declared in `scoring/reference.json`, matching the richer train/test evaluators.
- Local `python -m py_compile ...` and `python validate.py --compare` passed; direct local evaluator execution is deferred to the packaged CPU test job because the login-node Python environment lacks declared container dependencies.
- Added explicit DMS shard preflight checks to `scripts/run.sh` after background audit found that partial downloads would otherwise fail later inside Python.
- Submitting a CPU test job to regenerate method artifacts, default/train/test scores, and validation output inside the reproducible container.

### [2026-06-22 22:48] - secondary_claims
- CPU verification job `adc14804-28b` completed successfully with exit code 0.
- The job regenerated raw method artifacts plus `scoring/scores.json`, `scoring/scores_train.json`, and `scoring/scores_test.json` inside the packaged container.
- `python validate.py --compare` passed after regeneration, including method/eval separation, shared-path portability, train/test independence, and method-key consistency checks.

</details>


---

# Reproduction Milestones

**Current: secondary_claims**

## Stop Justification
- Completed at milestone `secondary_claims`.
