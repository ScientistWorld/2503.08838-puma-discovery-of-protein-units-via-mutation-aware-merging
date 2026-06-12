# Reproduction Milestones

**Current: secondary_claims**

## Progress Log

### [2026-06-12 00:00] - method_runs
- Vendored the official PUMA implementation and released UniRef50-human 6,400-token vocabularies.
- Confirmed the mutation-aware merge implementation can train a small fresh PUMA vocabulary end to end.

### [2026-06-12 00:00] - core_claim
- Reproduced the clinical SAME sibling association on ProteinGym ClinVar substitutions.
- PUMA shows a benign-pathogenic SAME sibling gap while frequency-only BPE has no sibling genealogy.

### [2026-06-12 00:00] - core_claim_plus
- Added the vocabulary-structure experiment to verify non-trivial mutation-linked family coverage at the same fixed vocabulary budget.
- `python validate.py --compare` passes with clean method/eval separation.

### [2026-06-12 13:47] - secondary_claims
- Audited method fidelity, evaluation independence, scripts, and documentation.
- Restored the `secondary_claims` milestone because the vocabulary-structure reproduction covers a secondary paper claim in addition to the core clinical association.
- Cleaned baseline and documentation inconsistencies found during the continuation audit.

### [2026-06-12 14:14] - secondary_claims
- CPU job `7d8d021d-1ba` completed successfully.
- Added and reproduced the human ProteinGym DMS SAME sibling association: PUMA positive-negative gap `0.02803`, matching the official 6,400-token reference.
- `python validate.py --compare` passed for clinical, DMS, and vocabulary-structure experiments.

## Stop Justification
- Completed at milestone `secondary_claims`.
