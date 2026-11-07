# Reproduction Milestones

**Current: secondary_claims**

## Progress Log

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

### [2026-06-22 22:24] - secondary_claims
- Audited the resumed workspace and confirmed `python validate.py --compare` still passes.
- Updated `scripts/run.sh` to regenerate raw PUMA artifacts before scoring train/test slices, removing dependence on ignored `outputs/` state.
- Submitting a CPU test verification job for the refreshed end-to-end job wrapper.

### [2026-06-22 22:28] - secondary_claims
- Final verification confirmed the reproduced clinical, DMS, and vocabulary-structure scores are plausible and pass `python validate.py --compare`.
- Removed method-specific details from the method-agnostic evaluation briefing and moved the benchmark FASTA reference to tracked `data/uniref50_human.fasta`.
- Verified download URLs, shell scripts, Python syntax, method/eval separation, and train/test score wiring.

### [2026-06-22 22:32] - secondary_claims
- Tightened the default method-independent evaluator so `scripts/evaluate.sh` emits all benefit and constraint metrics declared in `scoring/reference.json`, matching the richer train/test evaluators.
- Local `python -m py_compile ...` and `python validate.py --compare` passed; direct local evaluator execution is deferred to the packaged CPU test job because the login-node Python environment lacks declared container dependencies.
- Added explicit DMS shard preflight checks to `scripts/run.sh` after background audit found that partial downloads would otherwise fail later inside Python.
- Submitting a CPU test job to regenerate method artifacts, default/train/test scores, and validation output inside the reproducible container.

### [2026-06-22 22:48] - secondary_claims
- CPU verification job `adc14804-28b` completed successfully with exit code 0.
- The job regenerated raw method artifacts plus `scoring/scores.json`, `scoring/scores_train.json`, and `scoring/scores_test.json` inside the packaged container.
- `python validate.py --compare` passed after regeneration, including method/eval separation, shared-path portability, train/test independence, and method-key consistency checks.

### [2026-11-07 12:15] - secondary_claims
- Hardening: reference now trains PUMA on the full corpus and submits the trained vocabulary; evaluators rewritten with a fixed protein-level split, evaluator-owned baseline, validity gates and bounded scored metrics.
- CPU job `d20a9bcd-202` (exit 0): reference test gaps 0.0859 clinical / 0.0269 DMS vs paper 0.0835 / 0.0280; all REDTEAM shortcuts now fail or tie; honest variants rank by their gaps. Details in `HARDENING.md`.

### [2026-11-07 21:40] - secondary_claims
- Hardening round 3 added a task gate: both biological gaps must clear half the published effect or neither earns credit. Units more than 5% shorter than BPE's now fail the run.
- CPU job `a711a2ea-5cc` (exit 0):
  - the reference is unchanged (test S 0.157388);
  - the abandon-DMS and compression-tradeoff shortcuts no longer pay;
  - a genuinely better label-free variant beats the reference by 19 paired SDs;
  - label-fitting shortcuts are documented and left to the grader.

## Stop Justification
- Completed at milestone `secondary_claims`.
