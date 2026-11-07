# Hardening report

**Bottom line.** Before this round, the hidden test mostly rewarded structural counts. Now it ranks methods by the paper's biological quantity: how much more often benign (or high-fitness) substitutions stay inside a unit family than pathogenic (or low-fitness) ones. That is measured on held-out proteins, at the fixed 6,400-unit budget, without loss of segmentation granularity.

- Every major shortcut from `REDTEAM.md` now scores as a failed run or gains nothing.
- The method runner now trains the vocabulary it submits.
- Honest variants are ranked in the same order as their measured gaps.

All numbers below come from one CPU job (`d20a9bcd-202`, 63 min, exit 0). Evaluator source hashes were unchanged while the cases were scored, and `python validate.py --compare` passes. Raw evidence:

- `hardening/summary.json` and `hardening/summary.md`: every case, train and test;
- `hardening/scores_{train,test}_all.json`: the evaluator output with every case on disk;
- `hardening/legacy/scores/`: "before" scores from the frozen pre-hardening evaluator;
- `hardening/logs/`.

**Units.** "S" is Σ_experiment weight × Σ_metric coefficient × value, using the coefficients and weights in the relevant `reference.json`; Δ is S minus the reference's S.
- New scale: S ranges from −0.9 (failed run) to 1.0. A valid run is ≥ −0.82, because its compression ratio is ≥ 2.0 / 2.45.
- Old scale: S is in the hundreds, dominated by `0.06 × family_count`.

The two scales are not comparable with each other; compare rankings, not values.

## 1. Do better results now score higher?

Yes. Each row is the same submitted artifact scored by the old and the new hidden test.
- "Before" is the frozen old evaluator: seed-7 subsample of 2,000 per label, released-vocabulary reference S = 41.683.
- "After" is the new evaluator on held-out proteins; Δ is against the trained reference, S_test = 0.157388.

| Variant (honest, label-free) | Clinical gap (test) | DMS gap (test) | Before: Δ old S | After: Δ test | After: Δ train |
|---|---:|---:|---:|---:|---:|
| PUMA a = 0.6 (`var_a060`) | 0.0867 | **0.0334** | **−17.83** | **+0.00188** | +0.00269 |
| PUMA on 19,200 sequences (`var_n19200`) | 0.0871 | 0.0291 | −0.76 | +0.00140 | +0.00349 |
| PUMA f = 0.1 (`var_f010`) | 0.0851 | 0.0280 | +2.44 | +0.00048 | +0.00338 |
| PUMA on 4,800 sequences (`var_n4800`) | 0.0839 | 0.0323 | +0.36 | +0.00003 | −0.00313 |
| **Reference: PUMA(BLOSUM62, 0.7, 0.05), full corpus** | 0.0859 | 0.0269 | +0.05 | 0 | 0 |
| Released 6,400 vocabulary (no training) | 0.0855 | 0.0272 | 0 | −0.00010 | +0.00056 |
| PUMA on 1,200 sequences (`var_n1200`) | 0.0810 | 0.0319 | −0.50 | −0.00211 | −0.00218 |
| PUMA a = 0.65 (`var_a065`) | 0.0801 | 0.0279 | −9.90 | −0.00362 | −0.00216 |
| BPE + families added afterwards with PUMA's rule (`var_bpe_posthoc_families`) | 0.0683 | 0.0216 | **+32.40** | **−0.00989** | −0.00979 |
| Families kept only at similarity ≥ 0.9 (`var_links_sim090`) | 0.0092 | 0.0012 | −31.55 | −0.05374 | −0.04925 |
| No genealogy (`var_no_genealogy`) | 0 | 0 | −41.45 | −0.05962 | −0.05683 |
| BPE baseline (`bpe_6400`, owned by the evaluator) | 0 | 0 | — | −0.05739 | −0.05449 |

**Before.** The old rank was driven by unnormalized family counts.
- BPE with families added afterwards has clearly weaker gaps, but 1,211 families: it scored **+32.4** above the reference.
- `var_a060` has the best DMS gap, but only 366 families: it scored **−17.8**.

**After.** The order follows the measured gaps.
- The four variants above the reference all improve the clinical gap, the DMS gap, or both.
- `var_a060`, `var_n19200` and `var_f010` are above the reference on **both** train and test.
- Everything weaker is below on both splits.
- The redteam's own disconnected-training case cannot recur: the method now submits what it trains (§2, item 1).

**Not monotone in data size.** 1,200 < 4,800 ≈ full corpus < 19,200 sequences. Differences among PUMA variants (≤ 0.004 in S) are of the order of the sampling uncertainty (§6).

## 2. Major shortcuts: fix, before, after

| Shortcut (`REDTEAM.md`) | Fix | Before Δ (old S) | After |
|---|---|---:|---|
| Disconnected training: the runner trains a toy vocabulary but submits the released one; more training doesn't move the score | `method/run_puma.py` now trains PUMA on the full corpus with the official code. It keeps the first 6,400 merges (the authors' downsampling rule) and **submits that output**. | 0 (tie) | Training changes are scored. Submitting the released vocabulary without training: **−0.00010**. |
| Family padding: 3,200 arbitrary pairs | Family count no longer scored. Parent links must point to an existing unit **of the same length**, otherwise the run fails. | +151.00 | **failed**: S = −0.9, Δ −1.057 |
| Constant tokenizer: normalizer maps everything to `A` | `tokenizer.json` must have no normalizer, pre-tokenizer, post-processor, padding, truncation or added tokens, and model type BPE or Unigram. Every scored sequence must be reproduced exactly by its units (lossless). | +151.79 | **failed** |
| Empty tokenizer: normalizer erases the sequence | Same | +151.31 | **failed** |
| Impossible flags: `is_parent: false`, dangling parents, coverage 200% | `is_parent` must be `true` if present; dangling parent links fail the run. Coverage is computed from validated family groups, so it stays in [0, 1]. | +343.77 | **failed** |
| Label lookup: WordLevel tokenizer memorizing 144k negative sequences; tokenizer and genealogy disagree | Tokenizer units must equal `vocab.json` units, with ≤ 6,400 units, model type BPE/Unigram, and lossless output. Hidden labels moved to `eval/test/`. | +12.08 | **failed** |
| Dataset replacement: raw JSON redirects the ground-truth paths | The evaluator reads only `tokenizer.json` and `vocab.json`; populations, labels and test size are fixed in `eval/`. The probe's redirect files are ignored. | +12.26 | **tie, Δ 0**: same artifacts as the reference, no gain |
| Baseline replacement: the "BPE" artifact is replaced | The baseline is the evaluator's own fixed copy, `eval/*/baseline_bpe_6400_tokenizer.json`. A method directory named `bpe_6400` is renamed `submitted_bpe_6400` and scored as a method. | 0 for PUMA; baseline S became 193.48 | Baseline stays at S = 0.100; the submission is **failed** |
| Raw-field forgery: fake scores, NaN, success flags; pre-written score file | Nothing a method writes besides its two artifacts is read; every number is recomputed; the score file is overwritten. | 0 (tie) | **tie, Δ 0**: forged files ignored, forged `scores_test.json` overwritten |
| Additive structure rewards outweighing task failure | Rank uses only bounded metrics: gaps in [−1, 1] and compression ratio in [0, 1]. Any failed constraint gives the worst value on every scored metric, so a failed run (−0.9) is always below any valid one (≥ −0.82; BPE alone is 0.1). | +151.3 for the empty run | not possible |
| Seed-dependent test population (peak-to-peak 0.078 old S) | No sampling: all eligible variants of the held-out proteins are scored (32,609 ClinVar, 160,498 DMS). Seed and population size can no longer be set from the method's output. | — | identical scores on every rerun; the 3 identical-artifact cases score identically |

New probes beyond REDTEAM, all built from agent-visible inputs only:

| Probe | What it exploits | Before | After |
|---|---|---|---|
| `sc_char_level_classes` | Single-residue vocabulary + amino-acid-class families | Gaps **0.186 / 0.070**, about 2× PUMA on both biological metrics (old S low only because of family count) | **failed**: 1.0 residues/unit < 2.0; 20 units used < 3,200 |
| `sc_dipeptide_classes` | 400 dipeptides + class families | Gaps 0.152 / 0.064 | **failed**: 1.76 residues/unit; 417 units used |
| `sc_oversize_vocab` | Reference + 6,400 never-used units | −0.70 (only a budget penalty) | **failed**: 12,800 > 6,400 |
| `sc_bpe_dropout` | Stochastic segmentation | −0.22 | **failed** |
| `sc_train_label_pruning` | Drops reference links whose substitution type is pathogenic-enriched in the **visible train** labels (87 links) | −0.20 | **valid, Δ +0.00015 test / +0.00020 train** (see §3) |

The character-level and dipeptide probes are the biggest real loophole that remained in the biological metrics themselves. Substitution-class families on a near-character vocabulary beat the paper's method by 2× without discovering any units. The granularity and usage gates close them. Thresholds are fixed in `eval/`, with large margins for real vocabularies:

| Vocabulary | Residues per unit | Distinct units used |
|---|---:|---:|
| PUMA (reference) | 2.40 | 6,251 |
| BPE | 2.45 | 6,373 |
| weakest variant | 2.38 | — |

## 3. Shortcuts left open

- **Using labels from the visible train split** to build or prune families (`sc_train_label_pruning`).
  - The artifacts cannot reveal how they were built, so the evaluator cannot detect this.
  - The protein-level split limits transfer. The substitution-type pruning probe gained **+0.00015** on test, about 0.05 of one unpaired S standard error, i.e. nothing.
  - More aggressive per-token label fitting was not tested; the held-out-protein split is the mitigation.
  - Label use is forbidden in `scoring/CONSTRAINTS.md` and `scoring/DIRECTION.md`; the grader must check method code for it.
- **Fetching ProteinGym from the internet or reading `eval/test/`.** The hidden labels are public data. The evaluator cannot prevent this (left to the grader); the files live only under `eval/test/` in this workspace.
- **Submitting the released PUMA vocabulary instead of training.** −0.00010, does not pay.
- **Accepted genealogy oddities:**
  - parent-link cycles;
  - same-length links between units that differ at several positions.

  Only units differing by exactly one residue can create a sibling event, and family-shape statistics are unscored, so these cannot raise S.
- **Vocabularies just above the gates** (≥ 2.0 residues/unit, ≥ 3,200 units used, ≥ 20% boundary-preserving variants per label) are accepted. Such a vocabulary is a genuine segmentation, so its gaps are honest results.

## 4. Reference score before and after

| | Before (old test) | After |
|---|---|---|
| Scored reference artifact | released vocabulary (S = **41.683**); trained full-corpus vocabulary under the old test: 41.735 | trained full-corpus vocabulary: **S_test = 0.157388**, S_train = 0.154487 |
| Clinical gap | 0.1020 (subsample) | **0.0859** test / 0.0809 train (paper 0.0835) |
| DMS gap | 0.0277 | **0.0269** test / 0.0277 train (paper 0.0280) |
| Compression vs BPE | — | 0.978 test / 0.977 train (paper's released stats 0.976) |
| BPE baseline | S 0.240 | S 0.100 (gaps 0, compression 1) |

The trained reference shares 6,219 of 6,400 units with the released vocabulary. The first divergence is at merge 155, presumably from corpus order or tie-breaking in the heap: the authors trained from their own database export. Scores agree within 0.0001 S, and family stats are 667 vs 666 families with 0.940 vs 0.941 coverage.

Full-corpus training takes 112 s and 5.5 GB on one CPU. The hidden test takes about 90 s for the reference plus baseline and never retrains.

Train and hidden test measure the same thing at comparable difficulty:
- reference gaps 0.0809 / 0.0859 (clinical) and 0.0277 / 0.0269 (DMS);
- variant Δs keep their sign across the two splits for all but `var_n4800`, whose Δ is within noise.

## 5. Headroom check

The reference sits at the bound of **no** scored metric:

| Scored metric | Bound | Reference |
|---|---:|---:|
| clinical gap | 1 | 0.086 |
| DMS gap | 1 | 0.027 |
| compression vs BPE | 1 | 0.978 |

Only the BPE baseline sits at the compression cap, by construction. Three honest label-free variants already score above the reference on both splits, and the character-level probe shows that substitution information can push the gaps far higher (0.19 / 0.07). So no extra experiment was needed. None was added.

The simple baselines sit clearly below the reference on a scale with room above:
- BPE: 0.100 vs 0.157.
- The mutation-aware but naive "BPE + families added afterwards": −0.0099, below the reference on both splits.

## 6. Noise

- **Repeat-run variation is zero.** Training has no random component, and scoring uses the full fixed populations. The reference was scored twice (all-cases pass and final pass), and two other cases with identical artifacts all gave identical numbers. Training was not separately rerun.
- **Sampling uncertainty** of the held-out measurement, analytic standard errors from the evaluator:
  - clinical gap ±0.0046;
  - DMS gap ±0.0016;
  - together ≈ ±0.003 in S, unpaired.
- **The paper's effect is ≈ 20× that.** PUMA vs BPE is 0.0574 S on test.
- **Differences between PUMA variants are ≈ 1 standard error.** Because every method is scored on the same variants (paired), the noise in a difference is smaller than this, but I did not quantify it.

## 7. Weights and coefficients

| Item | Before | After | Why |
|---|---|---|---|
| Clinical weight | 0.6 | 0.6 (unchanged) | Primary claim |
| DMS weight | 0.25 | 0.3 | It is the paper's second biological validation, and its gap is ~3× smaller in absolute terms; at 0.25 the 0.15 structure weight could outweigh it |
| Structure weight | 0.15 | 0.1 | It is now the constraint side. The paper's family statistics are descriptive (">94% coverage"), not "more is better" |
| Gaps | — | coefficient 1 | The scored quantities |
| `compression_vs_bpe` | — | coefficient 1, new | Scored constraint: the paper reports observed unit lengths nearly identical to BPE (Fig. S2b) |
| Per-label rates, boundary-preservation rates, family coverage/count/shape, vocabulary size | various | coefficient 0 | Reported only. They were the redteam's levers (unbounded counts) or reward uniform inflation |
| Log-ratio metrics | scored | removed | Unbounded with ε = 1e-9: a tiny genealogy with zero pathogenic siblings would earn ≈ 18 nats |
| Budget error | scored | validity gate | — |

The paper's reported numbers in `scoring/reference.json` are unchanged:
- result keys were renamed `puma_official_6400` → `puma_6400` and `bpe_official_6400` → `bpe_6400`;
- compression values from the authors' released `general_stats.csv` were added, with notes.

## 8. What could not be fixed / limitations

- **Statistical resolution between close variants is limited.** The test already uses every eligible ClinVar variant of the held-out proteins and every human DMS single substitution in the held-out windows; no larger public labelled pool exists for this metric.
- **More data is not monotonically better at 6,400 units.** 19,200 sequences scored slightly above the full corpus. This is reported, not tuned away.
- **Scope is unchanged:** the paper's ESM-2 preference and GO topic-model experiments are not in the gym (milestone `secondary_claims`).
- **`redteam/` is the audit record of the old interface.** Its scripts write `outputs/puma_reproduction/raw_results.json`, which the new evaluator ignores. Its label-derived generated artifacts were deleted from disk. Re-auditing should use `hardening/build_cases.py` as the template.

## Layout after hardening

- `eval/test/prepare_split.py` builds the populations from raw ProteinGym:
  - raw files: `eval/test/downloads/raw/`, fetched by `scripts/download.sh`;
  - hidden test: `eval/test/downloads/split/`;
  - visible train: `data/downloads/proteingym_train/`.
- `eval/test/evaluate.py` and `eval/train/evaluate.py` are independent copies with no shared code.
- `scripts/run.sh` and `scripts/reproduce.sh` reproduce the reference end to end. `python hardening/run_hardening.py` reproduces this report.
