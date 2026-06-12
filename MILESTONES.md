# Reproduction Milestones

**Current: core_claim_plus**

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

## Stop Justification
- Completed at milestone `core_claim_plus`.
