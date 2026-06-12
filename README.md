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
- The reproduced benchmark focuses on clinical, DMS, and vocabulary-structure validations and also runs a small fresh PUMA training job to verify the mutation-aware merge algorithm executes end to end.

---

# Problem Definition

## Research Question

Can a protein sequence vocabulary segment complete amino-acid chains into reusable contiguous units while preserving biologically meaningful relationships between single-residue variants of those units?

## Why It Matters

Protein language models and downstream analyses usually operate at residue level or use frequency-only subwords. A useful intermediate vocabulary should expose larger interpretable units and should distinguish substitutions that preserve function from substitutions that are more disruptive.

## Success Criteria

A successful system should tokenize full protein sequences without gaps, group related unit variants into reusable families, and show that mutations staying within those families are enriched among favorable or benign variants compared with unfavorable or pathogenic variants.

---

# Paper's Method

## Key Contribution

PUMA discovers protein units with an iterative merge procedure that adds mutation-aware variants to a normal frequency-driven BPE merge vocabulary. Its output is both a vocabulary and a genealogy connecting parent units, child mutation units, and sibling variants.

## Approach

The vocabulary starts from amino-acid characters. At each iteration PUMA extracts the most frequent adjacent pair, merges it, and adds the merged string as a unit. For merged units within the configured length range, it enumerates candidate substitutions using non-negative entries in an amino-acid substitution matrix such as BLOSUM62. A candidate variant is accepted only if it meets the normalized alignment-score cutoff and if an adjacent pair currently exists in the corpus whose merge would form that candidate with sufficient frequency relative to the parent. Accepted variants are merged immediately and linked genealogically to the parent.

## Main Claims

The primary claim is that mutation-aware merging yields protein-unit families whose within-family substitutions are enriched for biologically favorable outcomes, such as benign ClinVar substitutions and high-fitness DMS substitutions. Secondary claims are that protein language models contextually prefer PUMA sibling substitutions over alternatives and that graph-aware topic models using the genealogy better align unit distributions with functional annotations.

---

# Evaluation

## Metrics

The primary metric is `benign_pathogenic_gap`: the SAME sibling rate for benign clinical substitutions minus the SAME sibling rate for pathogenic substitutions. SAME sibling rate is computed only for point mutations where the original and mutated full sequence have identical token boundaries; among those SAME cases, it is the fraction where the original and mutated tokens at the mutation site belong to the same unit family.

The evaluation also reports the benign and pathogenic SAME sibling rates separately, SAME boundary rates (`benign_same_idx`, `pathogenic_same_idx`), vocabulary size, and family coverage. Family coverage is a constraint metric: a method should produce a meaningful genealogy rather than only a flat vocabulary.

A second biological validation uses human ProteinGym deep mutational scanning assays. It reports the SAME sibling-rate gap between positive/high-fitness and negative/low-fitness substitutions with the same unchanged-boundary filter.

A secondary vocabulary-structure experiment reports `family_coverage`, `mutated_vocab_fraction`, `parent_vocab_fraction`, and `vocab_size` at the same fixed vocabulary budget. This prevents future systems from improving the clinical metric by discarding the family structure that the task is meant to evaluate.

## Baselines and Targets

The baseline is frequency-only BPE at the same 6,400-token vocabulary size. The target is the paper's PUMA configuration trained on UniRef50-human with BLOSUM62, alignment cutoff 0.7, mutation length range 3-12, frequency cutoff 0.05, and vocabulary size 6,400.

## Evaluation Protocol

The compact reproduction uses ProteinGym clinical substitutions from ClinVar. The method writes raw tokenization and family-count artifacts to `outputs/puma_reproduction/raw_results.json`; `scripts/evaluate.sh` reads only that artifact and writes `scoring/scores.json`. The evaluator does not import from `method/`, so a future method can be scored by writing the same raw artifact schema.

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


---

# Reproduction Milestones

**Current: secondary_claims**

## Stop Justification
- Completed at milestone `secondary_claims`.
