# Current audit (after hardening)

Only `v2_*` cases and this support directory describe the current evaluator.
Other files in `redteam/` are the retained historical audit of the old interface;
their scores are not evidence about the present gym.

Submit `python redteam/v2_support/run_all.py` as a CPU job in the gym container.
There are 20 completed cases. Every case also has a standalone `run.sh`. It trains/reuses full-corpus PUMA
artifacts from allowed inputs, installs one candidate under `outputs/`, invokes
the visible train script and then exactly `bash scripts/evaluate_test.sh` with
no arguments, saves both score files, and restores every external file.

The test evaluator, its baseline and its data are never changed. The candidate
process ends before evaluation starts; no environment or process manipulation
is involved. Candidate construction uses no hidden files. Audit-only ranking
uses copies of the initial reference and coefficients. Downloads for the public
answer shortcut are independent copies obtained from the URLs exposed by
`scripts/download.sh`, using `download_public.sh` on the internet-enabled node.
No candidate depends on old audit or hardening artifacts.

Generated artifacts, downloads, caches and logs are ignored by `redteam/.gitignore`.
Small configs, scores, training summaries, rank calculations and run receipts
are committed. `summary.json` lists only actual completed runs.

The final report is `../../REDTEAM.md`. The follow-up case
`v2_shortcut_abandon_dms` demonstrates an aggregate-score win with exactly
zero DMS sibling events. Public-download cases require running
`bash redteam/v2_support/download_public.sh` before submitting the offline job.
They intentionally violate the documented label-use constraint.
