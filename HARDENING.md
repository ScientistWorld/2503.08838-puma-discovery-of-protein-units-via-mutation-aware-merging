# Hardening report (round 3, final)

**Bottom line.**
- Better results now score higher, worse ones lower, and failing a task can no longer be bought back.
- The two shortcuts the evaluator can close are closed:
  - **abandon-DMS** (fail the DMS task, win on the clinical one);
  - **compression tradeoff** (shorter units than the written constraint allows).
- Two label-fitting shortcuts are left to the compliance grader, because the submitted artifacts cannot reveal label use (§3).
- The reference scores exactly what it did before (test S = 0.157388).
- A genuinely better label-free variant beats it by +0.095, with paired z = 19.

All "after" numbers come from one CPU job (`a711a2ea-5cc`, 33 min, exit 0). It ran on the final code:
1. retrained the reference with `scripts/method.sh`. The result is content-identical to the previous training and to the red team's seed-7/17/29 runs, so seed spread is 0.
2. installed 28 saved artifacts in `outputs/`.
3. ran the unmodified, argument-free `bash scripts/evaluate_train.sh` and `bash scripts/evaluate_test.sh`. Evaluator hashes were unchanged during scoring.
4. ran a paired bootstrap.
5. removed the cases, regenerated the reference-only score files and passed `python validate.py --compare`.

Raw evidence:
- `hardening/v3/summary.md` / `summary.json` (every case, before/after, train/test);
- `hardening/v3/scores_{train,test}_all.json` (evaluator output with all cases on disk);
- `hardening/v3/paired_noise_{train,test}.json`;
- `hardening/v3/state.json` and `hardening/v3/logs/`.

Driver: `python hardening/v3/run_v3.py`. The previous round's report is in `hardening/HARDENING_round2.md`.

**Units.** `S = 0.6·C + 0.3·D + 0.1·R`, with:
- C = clinical benign−pathogenic SAME sibling gap;
- D = DMS positive−negative gap;
- R = `compression_vs_bpe`;
- weights and coefficients from `scoring/reference.json`, unchanged.

ΔS = S − S(reference) on the same slice and evaluator.

"Before" is the previous evaluator: the red-team runs in `redteam/<case>/scores_*.json` and the round-2 variants in `hardening/scores_*_all.json`.

## What changed in the evaluator (`eval/train/evaluate.py`, `eval/test/evaluate.py`, independent copies)

1. **Non-compensatory task gate.** A run *solves* the biological tasks only if C ≥ 0.04 **and** D ≥ 0.014, about half the published 6,400-unit effects (0.0835 / 0.0280). Otherwise:
   - `task_solved = 0`;
   - neither gap earns credit: each is scored as min(measured, 0).

   Score tiers:

   | Outcome | S |
   |---|---|
   | constraint violated | −0.9 |
   | valid, a task not solved | ≤ 0.1 |
   | valid, both tasks solved | ≥ 0.6·0.04 + 0.3·0.014 + 0.1·0.95 = 0.123 |

   A method that fails a task can therefore never outrank one that solves both, whatever its other metrics. The BPE baseline (gaps 0) keeps its paper-consistent values (C = D = 0, R = 1, S = 0.1); it is reported with `task_solved = 0`.
2. **Granularity tolerance.** `compression_vs_bpe` < 0.95 (units more than 5% shorter than the frequency-only baseline's) fails the run.
   - The paper reports observed unit lengths "nearly identical" to BPE: 2.40 vs 2.46 residues, ratio 0.976.
   - Every honest PUMA variant tried sits at 0.971–0.984.
3. **Small fix.** Unigram scores must be finite numbers (non-finite scores fail the run).
4. `task_solved` is reported (coefficient 0). The thresholds are written into `_metadata.thresholds`. Diagnostics include the measured gaps and why a task is unsolved.

Everything else is unchanged:
- the populations and protein-level split;
- the evaluator-owned baseline;
- the other gates;
- the weights;
- the paper numbers in `reference.json`.

## 1. Do better results score higher? (test; train in the last column)

| Variant (honest, label-free) | C | D | R | Before ΔS | After ΔS | Paired SD | z | After ΔS train |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Reference units, families = same-length units with identical residue-class pattern (`v2_better_chemical_families`) | 0.2215 | 0.0720 | 0.978 | +0.0949 | **+0.0949** | 0.0049 | **+19.4** | +0.0990 |
| PUMA retrained, a = 0.60 (`v2_better_cutoff060`) | 0.0867 | 0.0334 | 0.972 | +0.0019 | +0.0019 | 0.0033 | +0.6 | +0.0027 |
| PUMA on 19,200 sequences | 0.0871 | 0.0291 | 0.978 | +0.0014 | +0.0014 | 0.0019 | +0.7 | +0.0035 |
| PUMA f = 0.1 | 0.0851 | 0.0280 | 0.984 | +0.0005 | +0.0005 | 0.0014 | +0.3 | +0.0034 |
| PUMA on 4,800 sequences | 0.0839 | 0.0323 | 0.974 | +0.0000 | +0.0000 | 0.0025 | +0.0 | −0.0031 |
| **Reference: PUMA(BLOSUM62, 0.7, 0.05), full corpus** | 0.0859 | 0.0269 | 0.978 | 0 | 0 | — | — | 0 |
| Released 6,400 vocabulary (no training) | 0.0855 | 0.0272 | 0.978 | −0.0001 | −0.0001 | 0.0005 | −0.2 | +0.0006 |
| PUMA on 1,200 sequences | 0.0810 | 0.0319 | 0.971 | −0.0021 | −0.0021 | 0.0026 | −0.8 | −0.0022 |
| PUMA a = 0.65 | 0.0801 | 0.0279 | 0.974 | −0.0036 | −0.0036 | 0.0027 | −1.3 | −0.0022 |
| BPE + families added afterwards with PUMA's rule | 0.0683 | 0.0216 | 1.000 | −0.0099 | −0.0099 | 0.0028 | **−3.5** | −0.0098 |
| Links of similarity ≥ 0.9 only (task not solved) | 0.0092* | 0.0012* | 0.978 | −0.0537 | **−0.0596** | 0.0030 | −17.9 | −0.0568 |
| No genealogy (task not solved) | 0* | 0* | 0.978 | −0.0596 | −0.0596 | 0.0031 | −19.3 | −0.0568 |
| Frequency-only BPE as a method (task not solved) | 0* | 0* | 1.000 | −0.0574 | −0.0574 | 0.0031 | −18.6 | −0.0545 |

\* measured gap; the scored gap for a task-unsolved run is min(measured, 0) = 0.

**Paired noise.** "Paired SD" is the bootstrap SD of ΔS, 2,000 replicates. Each replicate resamples the split's own units with replacement: 1,272 ClinVar proteins and 205 DMS protein × 50-residue windows on test. The same weights apply to every method, so all methods see the same resampled variants. Compression is held at its full-population value. On train, the SDs are within about 20% of these (0.0006–0.0051).

**Ordering.**
- The genuinely better variant beats the reference by **19 paired SDs**: 95% CI [+0.085, +0.104], positive in 100% of replicates. Train agrees: +0.099, z = 19.4.
- The weaker mutation-aware baseline (BPE + post-hoc families) is below by 3.5 SDs. Train agrees: −0.0098, z = −3.0.
- Everything without real family signal is ≈ 19 SDs below.
- Before vs after, the honest ordering is unchanged; it was already right.
- What changed is the weak tail. Families kept only at similarity ≥ 0.9 have a tiny gap, so they no longer solve the task. They are now tied with no-genealogy at 0.0978 instead of sitting slightly above it.

**Not resolved.** Differences among PUMA hyperparameter settings (|ΔS| ≤ 0.004) are below 2 paired SDs, i.e. within test noise. These are honest alternatives the test cannot tell apart. The test already scores every eligible ProteinGym ClinVar and human DMS single substitution of the held-out proteins; no larger public labelled pool exists for this metric. This is a resolution limit, not a loophole: headroom above the reference is real (+0.095 above).

## 2. Major shortcuts: fix, before, after

| Shortcut (`REDTEAM.md`) | Fix | Before S / ΔS | After S / ΔS |
|---|---|---:|---:|
| **Abandon-DMS**: public-label clinical fitting with every DMS sibling event removed (C 0.1118, D 0) | Task gate: D < 0.014 → no credit for either gap | 0.1648 / **+0.0074** | 0.0978 / **−0.0596** |
| **Compression tradeoff**: 3,600 units, units 7.4% shorter than BPE (R 0.926) + class families | Granularity tolerance R ≥ 0.95 → failed run | 0.2484 / **+0.0910** | −0.9 / **−1.0574** (failed) |
| Forged fields (no families + forged scores/flags, pre-written `scores_test.json`) | Already ignored/overwritten; now also task-unsolved | 0.0978 / −0.0596 | 0.0978 / −0.0596 |
| Move baseline (no families, submitted as `bpe_6400`) | Renamed `submitted_bpe_6400`; evaluator's baseline unchanged | 0.0978 / −0.0596 | 0.0978 / −0.0596 |
| Move data / settings (no families + redirect config) | Ignored; task-unsolved | 0.0978 / −0.0596 | 0.0978 / −0.0596 |
| Replace released artifacts (no families) | Evaluator-owned copy | 0.0978 / −0.0596 | 0.0978 / −0.0596 |
| Constant / empty / copied residues / impossible values | Structural gates (copied residues now also fails the granularity tolerance) | −0.9 / −1.0574 | −0.9 / −1.0574 |
| Character / dipeptide units + class families (round-2 probes) | Structural gates | −0.9 | −0.9 |
| Identical artifact | Tie: an identical honest method, not forgery | 0.1574 / 0 | 0.1574 / 0 |

The abandon-DMS fix does not depend on provenance. Any family structure, label-free or not, that delivers no DMS effect now scores ≤ 0.1, below every run that solves both tasks. The compression-tradeoff fix enforces the written "without sacrificing granularity" condition: REDTEAM noted that even the reference was only scored, not gated, on it.

## 3. Shortcuts left open, and why

| Shortcut | Test S / ΔS (after) | Why it is left |
|---|---:|---|
| **Public-answer fitting**: download the public ProteinGym files, reconstruct labels, fit families to them | 0.4100 / **+0.2526** | The hidden test scores public variants (ClinVar and ProteinGym DMS are public by nature). Fitted families are ordinary same-length parent links: the artifacts cannot reveal that labels chose them, and no evaluator-side rule can separate "links chosen by labels" from "links chosen by a substitution prior" without dictating the method. No unpublished labelled pool exists to replace them. |
| **Visible-label fitting**: fit families to labelled SAME pairs of the visible train split | 0.2294 / **+0.0720** (train +0.3046) | Same reason. It does show the expected train/test generalization gap (+0.30 on train vs +0.07 on test). |
| Train-label pruning (round 2) | 0.1575 / +0.0001 | Same reason; pays nothing (z 0.7). |

Mitigations in place:
- Label use, including downloading or reading ProteinGym, ClinVar or DMS labels in method code, is explicitly forbidden in `scoring/CONSTRAINTS.md`, `scoring/DIRECTION.md` and the briefing. This is for the separate compliance grader, which checks method code and logs.
- The hidden labels live only under `eval/test/`.
- The task gate also means a label-fitting method must deliver both effects.

These two are the only major shortcuts that still pay.

## 4. Reference before and after

| | Before | After |
|---|---:|---:|
| Test S (C / D / R) | 0.157388 (0.08594 / 0.02686 / 0.97766) | **0.157388** (identical) |
| Train S (C / D / R) | 0.154487 (0.08088 / 0.02768 / 0.97657) | **0.154487** (identical) |
| `task_solved` | — | 1 (test and train) |
| BPE baseline test S | 0.100 | 0.100 (`task_solved` = 0) |
| Paper (6,400 units) | C 0.0835, D 0.0280, R 0.976 | unchanged in `reference.json` |

The reference passes every new gate with margin:
- C 0.086 vs ≥ 0.04;
- D 0.027 vs ≥ 0.014;
- R 0.978 vs ≥ 0.95.

The paper's effect is far above noise:
- the reference's clinical gap is 17.2 cluster-bootstrap SDs, its DMS gap 9.9 SDs;
- reference vs BPE is 18.6 paired SDs;
- seed spread is 0, because training is deterministic and was verified content-identical across three seeds and this rerun.

## 5. Headroom check

| Scored metric | Bound | Reference | At bound? |
|---|---:|---:|---|
| `benign_pathogenic_gap` | 1 | 0.086 | no |
| `positive_negative_gap` | 1 | 0.027 | no |
| `compression_vs_bpe` | 1 (cap) | 0.978 | no |

The reference is at the bound of **no** scored metric. A label-free variant scores +0.095 above it (z = 19), at the same granularity, without reaching any bound (S 0.252 of 1.0). No experiment needed to be added.

The simple baselines sit clearly below on a scale with room above:

| Baseline | Test S | ΔS | Paired z |
|---|---:|---:|---:|
| BPE | 0.100 | −0.057 | −18.6 |
| BPE + post-hoc families | 0.1475 | −0.0099 | −3.5 |

No metric is saturated or constant across methods, and none depends on wall-clock time.

## 6. Weights

Unchanged: clinical 0.6, DMS 0.3, structure 0.1.
- The clinical association is the paper's primary validation.
- DMS is its second biological validation.
- Granularity is the constraint side, now also a hard tolerance.

The new task gate makes the two biological weights non-compensatory below the minimums; above them they trade off as before.

## 7. What could not be fixed

- **Label provenance** (§3): the public-answer and visible-label fitting shortcuts still pay (+0.25 / +0.07). They are left to the compliance grader.
- **Test resolution**: about 0.003 in S (one paired SD). Differences among PUMA hyperparameter settings are within it. The test already uses every eligible public labelled variant of the held-out proteins.
- **The thresholds are judgment calls** fixed in `eval/`: 0.04 / 0.014 is half the paper's effect, and 0.95 is a 5% granularity tolerance. They are set well below the reference and every honest PUMA variant, and well above runs with no real family signal.
- **Scope is unchanged**: the paper's ESM-2 preference and GO topic-model experiments are not in the gym (milestone `secondary_claims`).
