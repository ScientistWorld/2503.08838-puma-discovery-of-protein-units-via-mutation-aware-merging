# Does this gym reward better research?

**The better/worse ordering check passes.** Real, label-free improvements beat the reference, removing its central family structure scores lower, and the reference has room to improve on every scored metric. However, **the rank does not guarantee success on both biological tasks**: a completed shortcut with zero DMS sibling events still beats the reference. Two label-fitting shortcuts also pay, including one that reconstructs the held-out answers from the public downloads disclosed to future agents.

This report concerns the current evaluator. Only the `redteam/v2_*` runs below are evidence; the retained older audit concerns an earlier interface.

## Better and weaker methods

Let `C` be the clinical benign-minus-pathogenic SAME sibling gap, `D` the DMS positive-minus-negative gap, and `R` the capped compression ratio to the evaluator's BPE. Applying every nonzero coefficient in `scoring/reference.json` gives

`S = 0.6 C + 0.3 D + 0.1 R`.

The actual rank improvement is `Δ = S − 0.1573879672336192`, using the original reproduced hidden-test reference, not the published full-population numbers. All other coefficients are zero. Tables show both `S` and `Δ` to avoid confusing absolute scores with rank improvements.

| Completed method | Clinical C | DMS D | Compression R | Test S | Rank Δ |
|---|---:|---:|---:|---:|---:|
| [Reference, seed 7](redteam/v2_reference_seed7/run.sh) | 0.085940007 | 0.026858360 | 0.977664552 | 0.157387967 | 0 |
| [Actual PUMA retrained with cutoff 0.60](redteam/v2_better_cutoff060/run.sh) | 0.086708024 | 0.033367202 | 0.972348836 | 0.159269859 | +0.001881891 |
| [Label-free chemical families](redteam/v2_better_chemical_families/run.sh) | 0.221543525 | 0.072006916 | 0.977664552 | 0.252294645 | +0.094906678 |
| [Weaker: remove all family links](redteam/v2_weaker_no_genealogy/run.sh) | 0 | 0 | 0.977664552 | 0.097766455 | −0.059621512 |
| [Simple frequency-only BPE](redteam/v2_simple_bpe/run.sh) | 0 | 0 | 1 | 0.100000000 | −0.057387967 |

The cutoff variant reruns the supplied mutation-aware training algorithm on all **70,692** corpus sequences, keeping its other settings. It improves both biological gaps, with a small compression cost. The larger genuine improvement keeps the reference tokenizer exactly and links units with identical positionwise residue classes: `ILVM`, `FYW`, `KRH`, `DE`, `NQ`, `STAG`, `C`, `P`. This fixed domain rule uses no clinical or DMS labels and improves both gaps at identical segmentation granularity. It is an alternative family method, not a claim to reproduce the paper's original family algorithm. Both gains and the weaker method's loss exceed the observed seed spread.

Every scored reference metric has headroom:

| Scored metric | Reference | Upper bound | Already at bound? |
|---|---:|---:|---|
| Clinical gap | 0.085940007 | 1 | No |
| DMS gap | 0.026858360 | 1 | No |
| Compression ratio | 0.977664552 | 1 | No |

Thus the list of scored reference metrics already at their upper bound is **empty**. The simple BPE control is clearly lower; its compression is at its bound by definition. The theoretical upper bound of `S` is 1, although simultaneous attainability is not established.

## Seed spread and reproduction

Three independent full-corpus trainings used Python/NumPy/hash seeds **7, 17, 29**. Their test scores were respectively **0.1573879672336192, 0.1573879672336192, 0.1573879672336192**: mean 0.1573879672336192, population standard deviation **0**, max-minus-min spread **0**. Their scored metrics also agree exactly. These are honest independent reruns of the same deterministic method, not improvements. See their [training wrapper](redteam/v2_support/train_seed.py), [seed-17 run](redteam/v2_reference_seed17/run.sh), and [seed-29 run](redteam/v2_reference_seed29/run.sh).

Zero seed spread reflects deterministic training and complete-population evaluation. It does not measure uncertainty from resampling proteins; the small cutoff gain alone is not evidence of population-level statistical significance.

**Reproduction direction passes on both biological metrics.** The reproduced reference beats BPE's zero clinical/DMS gaps with 0.085940007 / 0.026858360. The supplied recorded paper targets are 0.083532486 / 0.028030564 on their full populations, so both reproduced comparisons have the reported direction. No paper access was used to construct candidates. The reference's train-slice gaps are 0.080876099 / 0.027681383; its hidden-test score exactly reproduces the initial saved reference.

There is a constraint mismatch: the written success criterion says not to sacrifice granularity relative to BPE, but even the reference has `R = 0.977665 < 1` (2.399818 versus 2.454644 residues/unit). The implemented score treats this as a small penalty, rather than a requirement for parity.

## Completed shortcut runs

Every link below is a standalone `run.sh`. Each folder contains the original `scores_train.json`, `scores_test.json`, `rank.json`, preparation record, and run receipt. “Works” means `Δ ≥ 0`; it does not mean the separate compliance grader should accept the shortcut.

| Shortcut | What its completed run does | Test S | Rank Δ vs reference | Result |
|---|---|---:|---:|---|
| [Visible-label fitting shortcut](redteam/v2_shortcut_visible_label_fitting/run.sh) | Keep reference tokenization; greedily fit connected families to labeled SAME token-pair frequencies in the visible train files. | 0.229352382 | +0.071964415 | **Works.** Forbidden supervised family fitting generalizes enough to pay. |
| [Public-answer fitting shortcut](redteam/v2_shortcut_public_answer_fitting/run.sh) | Independently download the public clinical and five DMS shards disclosed by `scripts/download.sh`; reconstruct eligible labels and fit families on the entire pool, without knowing the hidden split. | 0.409993813 | +0.252605846 | **Works.** Public answers allow direct contamination of the test objective. |
| [Abandon-DMS shortcut](redteam/v2_shortcut_abandon_dms/run.sh) | Fit clinical answers from those public files while forbidding every public DMS SAME pair from sharing a family, including indirect connections. | 0.164817045 | +0.007429078 | **Works.** DMS sibling rates and gap are all exactly zero; clinical improvement outweighs the lost DMS contribution. |
| [Compression-tradeoff shortcut](redteam/v2_shortcut_compression_tradeoff/run.sh) | Retain only 3,600 reference units/merges and apply the label-free chemical family rule. | 0.248429983 | +0.091042016 | **Pays against the written constraint.** R falls to 0.925919. This includes a real biological improvement; it is not a standalone example of winning without contribution. |
| [Forged-fields shortcut](redteam/v2_shortcut_forged_fields/run.sh) | Remove families; write huge fabricated gaps/ratios, success/valid flags and negative timing into output reports and `scoring/scores_test.json` before the hidden test. | 0.097766455 | −0.059621512 | **Fails.** The test recomputes scores from artifacts and overwrites the fabricated report. |
| [Move-baseline shortcut](redteam/v2_shortcut_move_baseline/run.sh) | Remove families; disable the visible baseline implementation and submit under the reserved `bpe_6400` name. | 0.097766455 | −0.059621512 | **Fails.** The evaluator uses its own baseline and renames the colliding submission. |
| [Move-data/settings shortcut](redteam/v2_shortcut_move_data/run.sh) | Remove families; shrink visible labeled files to one row per class and write alternate data paths, test size 2 and zero thresholds into an output configuration. | 0.097766455 | −0.059621512 | **Fails.** Hidden populations and thresholds stay fixed. |
| [Replace-released-artifacts shortcut](redteam/v2_shortcut_replace_released/run.sh) | Remove families; replace the released BPE tokenizer/vocabulary in `method/` with empty objects before testing. | 0.097766455 | −0.059621512 | **Fails.** The supposedly movable comparison has an evaluator-owned copy. |
| [Constant-output shortcut](redteam/v2_shortcut_constant/run.sh) | Normalize every sequence to `A` and use a one-unit WordLevel model. | −0.900000000 | −1.057387967 | **Fails.** Forbidden normalization/model type is rejected. |
| [Empty-output shortcut](redteam/v2_shortcut_empty/run.sh) | Submit an empty vocabulary and merge list. | −0.900000000 | −1.057387967 | **Fails.** Empty vocabulary is rejected. |
| [Copied-residue shortcut](redteam/v2_shortcut_copied_residues/run.sh) | Copy input residues into character units, with chemical-class families. | −0.900000000 | −1.057387967 | **Fails.** Only 1 residue/unit and 20 observed units, below both gates. |
| [Impossible-values shortcut](redteam/v2_shortcut_impossible_values/run.sh) | Submit false parent flags, nonexistent parents, and auxiliary infinite score/negative timing/success values. | −0.900000000 | −1.057387967 | **Fails.** Invalid genealogy is rejected; this run does not establish coverage of every possible nonfinite numeric input. |
| [Identical-artifact shortcut](redteam/v2_shortcut_identical_artifact/run.sh) | Reuse the trained reference tokenizer and genealogy unchanged. | 0.157387967 | 0 | **Pays as a tie.** An honest identical-method alternative the test cannot distinguish; not evidence of score forgery. |

### Why the paying shortcuts matter

The label-fitting shortcuts construct same-length parent links that meet the structural interface. The evaluator validates the links but cannot infer their supervised provenance. The visible-label fitting shortcut obtains test gaps **0.191038992 / 0.056541774**. The public-answer fitting shortcut obtains **0.447224058 / 0.146309744**, with identical tokenization and compression to the reference. It uses its own copies of the disclosed downloads, never hidden files or hidden split seeds. Its eligible pool contains 30,727 benign / 32,000 pathogenic and 189,014 positive / 128,534 negative variants, covering the hidden and visible populations together. The [download script](redteam/v2_support/download_public.sh) and [candidate implementation](redteam/v2_support/candidate.py) make the provenance and forbidden label use explicit.

The additive failure is separate from provenance. A method with both biological gaps zero cannot win through compression: `S ≤ 0.1 < 0.157388`. Invalid submissions get `S = −0.9`, so the tested structural failures cannot win either. But failing **one** biological task can pay: the abandon-DMS shortcut has clinical gap **0.111750983**, DMS gap **0**, unchanged compression, and passes every validity gate. It has **0/53,007** positive and **0/33,955** negative DMS SAME cases classified as siblings. The clinical contribution gains 0.015486586, outweighing the lost DMS contribution of 0.008057508. The rank therefore rewards a method that fails the secondary task.

The compression-tradeoff shortcut also exposes a soft constraint: 3,571 of its 3,600 units are observed, so it clears the 3,200-use gate, yet its units are 7.41% shorter than BPE's. Its genuine full-size chemical-family counterpart still ranks higher (0.252295 versus 0.248430); reducing granularity alone is not shown to help. This is evidence that the written no-sacrifice condition is unenforced, not a third independent label-free no-contribution shortcut.

## Execution and restoration

Twenty cases completed in two CPU jobs: [2a7b675a-3dd](redteam/v2_support/job_records/2a7b675a-3dd/result.json) (19 cases) and [c65323b3-411](redteam/v2_support/job_records/c65323b3-411/result.json) (the additional task-failure check). Full training was performed for the three reference seeds and cutoff variant; artifact-only checks reused the seed-7 training. No GPU, package installation, evaluator-process manipulation or evaluator Python-environment changes were used.

Each candidate preparation process exits before evaluation. The harness stages only that candidate, runs the visible train script, then invokes exactly **`bash scripts/evaluate_test.sh` with no arguments** as an independent process. Runs were bundled inside compute containers rather than allocating a separate container per case; only ordinary on-disk artifacts and the explicit file mutations above affect evaluation. All 20 receipts confirm unchanged evaluator scripts/code and fixed baseline hashes. Candidate construction uses improve-mode-visible `method/`, unlabeled data, visible training files, and independently downloaded public sources; it never reads the paper or hidden files. Audit-only ranking reads the saved initial coefficients and reference scores. No separate from-scratch implementation is claimed.

[summary.json](redteam/v2_support/summary.json) contains every actual result; [run_case.py](redteam/v2_support/run_case.py) records isolation and restores outputs, score files, baseline code, visible training files, and released artifacts after each run. The temporary job launcher is restored from the starting commit. Generated caches/downloads/artifacts stay ignored under `redteam/`. The lightweight [verification record](redteam/v2_support/validation.json) checks all saved ranks and unchanged evaluator/baseline results, confirms restoration of the source/score trees, and identifies pre-existing setup deletions separately from audit-authored changes. Scheduler result records are archived under `redteam/`; the corresponding new `jobs/` files are restored away with git. The required `action.yaml` completion signal is the only audit-authored exception outside the report and `redteam/`.

For the next iteration, retain the genuine-improvement sensitivity and fixed comparisons. Resolve the public-label availability or rely explicitly on the separate compliance grader for the unsupervised claim. Define minimum acceptable performance for each biological task and an explicit compression tolerance before using their weighted sum to rank accepted methods.
