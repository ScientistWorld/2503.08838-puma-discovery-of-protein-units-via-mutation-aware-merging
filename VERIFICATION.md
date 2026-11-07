> **Superseded in part (2026-11-07):** the evaluation interface and scoring described below were replaced during hardening (trained reference submission, fixed protein-level split, evaluator-owned baseline, validity gates, bounded metrics). Round 3 then added a non-compensatory task gate and a granularity tolerance. See `HARDENING.md` for the current design and verification, and `hardening/HARDENING_round2.md` for round 2.

# Verification Report

## Initial Assessment

The workspace already had a plausible `secondary_claims` reproduction: clinical SAME sibling association, DMS sibling association, and vocabulary-structure scores were present and `python validate.py --compare` passed. The claimed milestone was justified by the reproduced gaps and constraints, but the gym needed a final separation and scoring-schema audit.

## Issues Found

- Minor: `briefing/evaluation.md` leaked implementation details of the reproduced method in a method-agnostic file.
- Minor: `scoring/CONSTRAINTS.md` pointed future scientists to a benchmark FASTA under `method/`, which weakens from-scratch usability.
- Minor: after the evaluator was expanded with additional constraint metrics, the visible `scoring/scores.json` needed regeneration inside the packaged environment so every nonzero-coefficient metric in `reference.json` had a reproduced value.
- Cosmetic: `scoring/DIRECTION.md` used more implementation-shaped wording than necessary for a high-level research direction.

## Fixes Applied

- Moved the benchmark FASTA reference to tracked problem data at `data/uniref50_human.fasta` and updated `method/run_puma.py`, `scripts/run.sh`, and `scripts/reproduce.sh` accordingly.
- Rewrote the method-agnostic evaluation briefing to describe metrics, artifacts, and protocol without naming the paper's algorithm or hyperparameters.
- Tightened `scoring/CONSTRAINTS.md` and `scoring/DIRECTION.md` so they guide future agents without exposing unnecessary implementation details.
- Verified the ProteinGym URLs in `scripts/download.sh` resolve through Hugging Face, and confirmed there are no committed `shared/` references in `method/`, `eval/`, `baseline/`, `scripts/`, `data/`, `environment/`, `scoring/`, or `briefing/`.
- Submitted CPU verification job `adc14804-28b`, which regenerated `outputs/puma_reproduction/raw_results.json`, `scoring/scores.json`, `scoring/scores_train.json`, and `scoring/scores_test.json` inside the container. The job completed with exit code 0 and `python validate.py --compare` passed.

## Final Judgment

The workspace is ready to serve as a research gym. Improve-mode agents can use the reproduced method and scores, while from-scratch agents can use the problem data and method-independent evaluator without importing from `method/`. Scoring includes benefit metrics and constraint metrics for the reproduced experiments, with the primary clinical target receiving the largest weight. The main limitation is that this is a compact 6,400-token reproduction rather than the full paper grid.

- Milestone: secondary_claims
- Ready for gym use: yes
- Confidence: high
- Key limitation: compact 6,400-token benchmark, not the full paper grid
