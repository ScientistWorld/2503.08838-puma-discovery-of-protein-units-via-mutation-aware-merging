# Scoring audit

This gym fails the audit. More training can leave its test score exactly unchanged, and methods that fail the task can outrank the reference by over 150 points. The weaker-method check passes. A genuinely better result above the reference was **not established**: the honest variants that change the scored model have mixed biological results, so they do not demonstrate positive quality monotonicity.

Here, **S** is the unnormalized weighted sum of metrics using every coefficient and experiment weight in `scoring/reference.json`. **Δ** subtracts the corresponding method's initial `scoring/scores_test.json` result. The reproduced PUMA reference has S = **41.683333**, Δ = **0**. These are rank units, not percentages. [Full arithmetic](redteam/summary.json) includes every metric contribution in each case's `rank.json`.

| Quality check (links run the variant) | S | Δ vs reference | Clinical gap | DMS gap |
|---|---:|---:|---:|---:|
| [Reference, seed 7](redteam/reference_seed7/run.sh) | 41.683333 | 0 | .101985 | .027749 |
| [Weaker: remove all genealogy](redteam/weak_no_genealogy/run.sh) | .235328 | −41.448005 | 0 | 0 |
| [Original optional training, 1,200 sequences](redteam/original_training/run.sh) | 41.683333 | 0 | .101985 | .027749 |
| [More optional training, 2,400 sequences](redteam/more_training/run.sh) | 41.683333 | 0 | .101985 | .027749 |
| [Actually score PUMA trained on 1,200 sequences](redteam/honest_trained_1200/run.sh) | 41.179839 | −.503493 | .084681 | .030613 |
| [Actually score PUMA trained on 2,400 sequences](redteam/honest_trained_2400/run.sh) | 39.895980 | −1.787353 | .087384 | .030211 |
| [Stricter unsupervised family links, cutoff .80](redteam/honest_stricter_links_080/run.sh) | 33.327370 | −8.355963 | .053394 | .010693 |
| [Stricter unsupervised family links, cutoff .90](redteam/honest_stricter_links_090/run.sh) | 9.970429 | −31.712903 | .010206 | .001734 |

The original runner trains an optional small vocabulary but submits the fixed released 6,400-token vocabulary for evaluation. Doubling that training data therefore does real additional work with **zero score movement**. The two optional-training runs are **honest alternatives the test cannot tell apart**. This is a disconnected training/output path, not evidence that the newly trained model improved. The weaker variant preserves segmentation and removes the method's central family relationships; its decline greatly exceeds seed variation.

To avoid relying only on that disconnected path, two additional variants train the actual official PUMA procedure at 6,400 entries and submit the learned artifacts. They use the same BLOSUM62/cutoff/frequency/length settings, no clinical or DMS labels, and the first 1,200 versus 2,400 unlabeled sequences. The official trainer can overshoot the vocabulary budget in its last batch; these variants retain the first 6,400 entries, dropping eight and one excess entries respectively. Doubling data improves the clinical gap by .002704 and its log ratio by .080555, slightly reduces the DMS gap by .000403, and increases family coverage. Nevertheless S falls **1.283860**, dominated by **1.32 lost points from having 22 fewer families**. The clinical gain is smaller than the reference clinical seed spread (.023123), so this is a mixed result, not a demonstrated scientific improvement wrongly ranked. The stricter-link variants improve clinical/DMS log enrichment but lose absolute gaps and coverage; they also are honest tradeoffs rather than proven better methods.

Three reference reruns give the following test variation:

| Seed | S | Δ vs seed 7 | Clinical gap | DMS gap |
|---|---:|---:|---:|---:|
| [7](redteam/reference_seed7/scores_test.json) | 41.683333 | 0 | .101985 | .027749 |
| [17](redteam/reference_seed17/scores_test.json) | 41.605713 | −.077619 | .078862 | .027749 |
| [29](redteam/reference_seed29/scores_test.json) | 41.628944 | −.054389 | .090628 | .027749 |

The **peak-to-peak test-score spread is .077619**, with sample standard deviation .039838 and mean 41.639330. A gain below .077619 is noise under this check. These are reruns of the provided reference: its seed changes the clinical subsample, while the released vocabulary and full DMS pool remain fixed. This does not estimate variance from retraining PUMA. Seed 7 reproduces the initial hidden score file exactly.

The compact reproduction **does beat its BPE baseline in the direction described in the agent-visible briefing**: clinical gap .101985 versus 0, DMS gap .027749 versus 0, and S 41.683333 versus **.239518**. This is a released-artifact reproduction check, not an independent reproduction of every paper result. BPE has no explicit families, making its sibling associations zero by construction; a mutation-aware competing baseline would be more informative. There is numerical room above the reference, as the runs below demonstrate, but its scale is dominated by structural counts rather than the biological task.

Every scored reference metric already at its individual optimum is listed here:

- `clinical_sibling_association.vocab_budget_error = 0`;
- `dms_sibling_association.vocab_budget_error = 0`;
- `vocabulary_structure.vocab_budget_error = 0`.

No other nonzero-coefficient metric is at its intended optimum. All three reported `vocab_size` values are the required 6,400, but those metrics have coefficient zero; budget error carries the constraint. Reference global family coverage is .94125, neither sibling gap is near its upper bound, and there are 666 families. Bounds themselves are not reliably enforced: malformed genealogy reaches coverage 2.0, and the actual tokenizer's vocabulary can exceed the nominal budget while its separate genealogy still reports 6,400 entries.

The additive rank does **not** prevent a task-failing method from beating the reference. Each extra family contributes `.15 × .4 = .06` rank units, without normalization. Fabricating 3,200 families instead of 666 gives **+152.04** from this metric alone. In the empty-output shortcut, both biological gaps are zero and observed family coverage is zero, yet the structural experiment adds **151.675648**, outweighing clinical and DMS changes of **−.343137** and **−.025867**. The total gain is **151.306644**, about 1,949 times the seed spread. Structural constraints need validation and gating; their current additive rewards overwhelm failure on the task.

Every shortcut below has a runnable `run.sh`, submitted raw artifact, preparation record, train/test score files, and `rank.json` in its linked folder. **Ties are labeled shortcuts**, as requested. The reference for every proposed-method comparison is S = 41.683333.

| Shortcut | What it does | Test S | Δ vs reference | Works or fails |
|---|---|---:|---:|---|
| [shortcut_skip_training](redteam/shortcut_skip_training/run.sh) | Submits the released artifacts without optional training. | 41.683333 | 0 | **Works: tie shortcut.** Test cannot distinguish this from the original training pipeline. |
| [shortcut_raw_fields](redteam/shortcut_raw_fields/run.sh) | Writes fake scores, huge/negative rates, nulls, NaN, success and timing fields alongside the real artifact paths. | 41.683333 | 0 | **Tie shortcut; direct forgery fails.** Hidden evaluation overwrites the score file and ignores the forged summary fields. |
| [shortcut_family_padding](redteam/shortcut_family_padding/run.sh) | Keeps reference tokenization; replaces learned genealogy with 3,200 arbitrary pairs. | 192.686998 | +151.003665 | **Works.** Clinical gap becomes negative (−.000992), yet rank rises dramatically. |
| [shortcut_constant](redteam/shortcut_constant/run.sh) | Normalizes every protein to `A`; supplies 6,400 metadata entries in arbitrary pairs. | 193.477856 | +151.794523 | **Works.** One observed token and meaningless biology are rewarded; actual tokenizer has one vocabulary entry. |
| [shortcut_empty](redteam/shortcut_empty/run.sh) | Erases every sequence; supplies the same fabricated family metadata. | 192.989977 | +151.306644 | **Works.** Zero observed tokens, both sibling gaps zero, boundary-preservation rates one. |
| [shortcut_impossible_flags](redteam/shortcut_impossible_flags/run.sh) | Gives every entry `is_parent: false` and a distinct nonexistent parent name. | 385.455304 | +343.771972 | **Works.** Presence of the false flag counts as true; dangling parents produce 6,400 families and 200% coverage. |
| [shortcut_label_lookup](redteam/shortcut_label_lookup/run.sh) | Memorizes negative full sequences from the visible labeled pools; uses unknown token `A` for other sequences. | 53.762009 | +12.078676 | **Works.** Clinical/DMS gaps .996/.900748; 144,737 actual tokenizer entries evade the budget check against a separate 6,400-entry genealogy. |
| [shortcut_dataset_replacement](redteam/shortcut_dataset_replacement/run.sh) | Redirects raw ground-truth paths to repeated, cherry-picked visible train examples. | 53.944643 | +12.261310 | **Works.** Same reference model, both gaps one; test population shrinks to eight examples per task. |
| [shortcut_baseline_replacement](redteam/shortcut_baseline_replacement/run.sh) | Replaces the artifact called BPE with the constant-output shortcut while leaving PUMA unchanged. | 41.683333 | 0 | **Works as a tie shortcut for PUMA.** The nominal fixed baseline is also replaced successfully; its S becomes 193.477856 instead of .239518. |

For baseline replacement, the proposed method gains **zero**; if ranking also sums the baseline's metrics, the total gain is **193.238338**. That conditional gain is not presented as an improvement to PUMA. The other successful shortcuts require no favorable interpretation of whether baseline entries count.

The label-lookup shortcut needs no hidden answer reconstruction: the complete clinical and DMS labeled pools are already visible. The visible training split logic also exposes the complementary hash split, but this shortcut simply memorizes the whole pool. Dataset replacement needs only the visible train evaluator and real train examples; it submits two selected records per task repeated eight times each. No hidden test records are needed to construct it. The baseline probe replaces an artifact treated as a fixed comparison rather than retraining the candidate. The genealogy probes demonstrate that recomputing scores from submitted artifacts is insufficient when the artifacts themselves are unauthenticated and internally inconsistent.

The largest fixes for the next iteration are to normalize or gate structural metrics behind biological performance, pin scoring populations and fixed comparisons outside candidate-controlled raw options, validate family flags/references and tokenizer/genealogy consistency, require nonempty lossless tokenization of the protein, and keep held-out labels out of candidate-visible data. Connect the training runner to the artifacts actually scored. The direct-summary forgery probe already behaves correctly and should remain a recomputation check.

Execution evidence: **19 successful cases in two CPU jobs** (`3b500826-dbf`, `caada00b-f48`; [job receipts](redteam/job_receipts.json)). Three first-job probes failed during preparation because of an unsupported regex option; they were corrected and rerun successfully, with the original failures retained in `redteam/first_job_failures.json`. Each candidate is constructed using only agent-visible inputs, then the visible train entrypoint and the exact command `bash scripts/evaluate_test.sh` run in separate processes, with no arguments and no surviving candidate process. These file-only candidates make no evaluator-process or Python-environment changes. Evaluator source hashes match before/after every run. Original raw/scoring files are restored after each case, and the temporary job script is restored from git. The [evidence validator](redteam/validate_results.py) checks all 19 outcomes, finite scores, ranking arithmetic, the initial-reference match, and restoration of gym source; its [saved result](redteam/validation.json) records the checks. Generated artifacts are regenerated by each case's `run.sh`; small raw submissions and all scores remain in git. The paper was not used. Pre-existing root-file and trajectory differences were preserved; new tracked job-control records outside the audit were restored from the starting commit after retaining the receipts.
