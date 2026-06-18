# Design Notes

## Checks and changes

- Checked `scripts/evaluate_train.sh` and `scripts/evaluate_test.sh` side by side. The train script calls `eval/train/`, the test script calls `eval/test/`, and they write `scoring/scores_train.json` and `scoring/scores_test.json` respectively.
- Checked that both slice evaluators read tokenizer and vocabulary artifacts from the method output JSON instead of importing from `method/` or regenerating the method inline.
- Checked for train/test cross-imports; none were present.
- Added explicit `_metadata.slice` markers to train and test score outputs so generated artifacts are visibly slice-specific.
- Added log-ratio metrics for clinical and DMS label separation. These complement the raw gap metrics and make it harder to game the benchmark by uniformly inflating sibling rates across both favorable and unfavorable variants.
- Added `minimum_same_idx` to clinical and DMS metrics. This penalizes methods that make one class mostly unscorable by changing token boundaries.
- Added family-shape metrics to the vocabulary-structure experiment: `family_count`, `mean_family_size`, and `largest_family_fraction`. These make a collapsed genealogy with one or a few giant families less attractive.
- Updated `scoring/reference.json` so every active metric has `higher_is_better`, `coefficient`, and `description`.
- Confirmed `scoring/scores_train.json` and `scoring/scores_test.json` do not exist.
- Ran static-only checks: `python -m json.tool scoring/reference.json`, `bash -n scripts/evaluate_train.sh`, and `bash -n scripts/evaluate_test.sh`.

## Runtime concerns for the next iteration

- I did not run either evaluator, per the source-edit-only instruction. The next runner should confirm the added metrics appear in both generated score files.
- The log-ratio metrics use a small epsilon for zero denominators. If a future method produces exact zero rates for one label and nonzero for the other, the metric can become large; this is intentional for enrichment, but the runner should watch for coefficient scale dominating the raw gap.
- The family-shape metrics assume PUMA-style vocabulary metadata with `is_parent` and `parent` fields. Methods without explicit genealogy will score zero for family structure, which matches the current benchmark constraint.
