# Verification Report

## Initial Assessment

The workspace already had a valid `secondary_claims` reproduction: clinical SAME sibling association, DMS sibling association, and vocabulary-structure scores were present and `python validate.py --compare` passed. The claimed milestone was justified by the reproduced gaps and constraints, but the gym needed a final separation audit.

## Issues Found

- Minor: `briefing/evaluation.md` leaked implementation details of the reproduced method in a method-agnostic file.
- Minor: `scoring/CONSTRAINTS.md` pointed future scientists to a benchmark FASTA under `method/`, which weakens from-scratch usability.
- Cosmetic: `scoring/DIRECTION.md` used more implementation-shaped wording than necessary for a high-level research direction.

## Fixes Applied

- Moved the benchmark FASTA reference to tracked problem data at `data/uniref50_human.fasta` and updated `method/run_puma.py`, `scripts/run.sh`, and `scripts/reproduce.sh` accordingly.
- Rewrote the method-agnostic evaluation briefing to describe metrics, artifacts, and protocol without naming the paper's algorithm or hyperparameters.
- Tightened `scoring/CONSTRAINTS.md` and `scoring/DIRECTION.md` so they guide future agents without exposing unnecessary implementation details.
- Verified all `scripts/download.sh` URLs resolve with HTTP 200, shell scripts pass `bash -n`, Python files compile, and `python validate.py --compare` passes.

## Final Judgment

The workspace is ready to serve as a research gym. Improve-mode agents can use the reproduced method and scores, while from-scratch agents can use the problem data and method-independent evaluator without importing from `method/`. The main limitation is that this is a compact 6,400-token reproduction rather than the full paper grid.

- Milestone: secondary_claims
- Ready for gym use: yes
- Confidence: high
- Key limitation: compact 6,400-token benchmark, not the full paper grid
