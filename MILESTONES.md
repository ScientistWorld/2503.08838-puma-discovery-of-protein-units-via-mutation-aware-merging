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

## Stop Justification
- Completed at milestone `secondary_claims`.
