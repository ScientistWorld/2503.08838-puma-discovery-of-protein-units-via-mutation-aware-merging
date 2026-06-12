# Reproduction Milestones

**Current: core_claim**

## Progress Log

### [2026-06-12 13:55] - none
- Read the paper and identified PUMA as a mutation-aware BPE algorithm for protein-unit discovery.
- Cloned the official PUMA repository and inspected the released training, vocabulary, and validation code.
- Downloaded the public ProteinGym clinical substitutions split used for the paper's ClinVar-style validation.
- Implemented method and evaluation wrappers; the compute job will test whether the method executes end to end.

### [2026-06-12 13:56] - core_claim
- CPU smoke job completed successfully in the container.
- The actual PUMA mutation-aware merge code ran end to end on a compact training subset and wrote a fresh small vocabulary checkpoint.
- The released 6,400-token PUMA vocabulary reproduced the paper's clinical sibling-association claim on 4,000 benign and 4,000 pathogenic ProteinGym variants.
- PUMA reproduced a benign-pathogenic SAME sibling gap of 0.0876 versus the paper's 0.0835; the BPE baseline remained at 0.0 because it has no mutation genealogy.
- Expanded scoring now also records vocabulary-family structure at the fixed 6,400-unit budget.

## Stop Justification
- Not stopped. A CPU job is being submitted to rerun the expanded scoring suite in the container.
