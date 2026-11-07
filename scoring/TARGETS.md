# Evaluation Targets

Every target below is an experiment in `scoring/reference.json` and is reported in `scoring/scores_train.json` / `scoring/scores_test.json` for every method on disk and for the evaluator's BPE baseline.

Rank score: S = 0.6 · `benign_pathogenic_gap` + 0.3 · `positive_negative_gap` + 0.1 · `compression_vs_bpe`. A method's rank is S minus the reference's S.

## Primary: clinical_sibling_association (weight 0.6)

Benign variants should keep the mutated unit inside the same family more often than pathogenic variants.
- **Metric**: `benign_pathogenic_gap` (higher is better, coefficient 1)
- **Paper (6,400 units, full ClinVar pool)**: PUMA 0.0835 (benign 0.158 vs pathogenic 0.074); BPE 0
- **Reproduced (trained reference `puma_6400`)**: hidden test 0.0859 (benign 0.156 vs pathogenic 0.070, ±0.0046), train 0.0809; BPE 0
- **Task minimum**: gap ≥ 0.04 (see below)
- **Reported only**: per-label SAME sibling rates and SAME rates, family coverage, vocabulary size, `task_solved`, validity

## Secondary: dms_sibling_association (weight 0.3)

High-fitness DMS variants should keep the mutated unit inside the same family more often than low-fitness variants.
- **Metric**: `positive_negative_gap` (higher is better, coefficient 1)
- **Paper (6,400 units)**: PUMA 0.0280 (positive 0.075 vs negative 0.047); BPE 0
- **Reproduced**: hidden test 0.0269 (positive 0.075 vs negative 0.048, ±0.0016), train 0.0277; BPE 0
- **Task minimum**: gap ≥ 0.014 (see below)

## Both tasks must be solved

A valid run *solves* the biological tasks when the clinical gap is ≥ 0.04 **and** the DMS gap is ≥ 0.014 (about half the published 6,400-unit effects). Otherwise `task_solved = 0` and neither gap earns credit (each is scored as `min(measured, 0)`), so S ≤ 0.1. Any run that solves both tasks has S ≥ 0.123. Failing one task therefore cannot be bought back with the other. The BPE baseline (no families, gaps 0) does not solve the tasks: S = 0.1. The reference solves both: S = 0.157 (test).

## Constraint: vocabulary_structure (weight 0.1)

The vocabulary remains a genuine 6,400-unit segmentation with explicit families and no loss of granularity.
- **Metric**: `compression_vs_bpe` (higher is better, capped at 1, coefficient 1). Paper (released statistics): PUMA 0.976, BPE 1. Reproduced: 0.978 test / 0.977 train
- **Validity gates (failure scores the run as failed, S = −0.9)**: ≤ 6,400 units; lossless segmentation; consistent same-length parent links; ≥ 2.0 residues per unit; **`compression_vs_bpe` ≥ 0.95** (units at most 5% shorter than BPE's); ≥ 3,200 distinct units used; ≥ 20% SAME cases per label
- **Reported only**: family coverage (paper 0.941), mutated / parent fractions (paper 0.837 / 0.104), family count and shape, residues per unit, distinct units used

## How to run

```
bash scripts/method.sh          # trains the reference into outputs/puma_6400/
bash scripts/evaluate_train.sh  # visible train slice -> scoring/scores_train.json
bash scripts/evaluate_test.sh   # hidden test         -> scoring/scores_test.json
```
