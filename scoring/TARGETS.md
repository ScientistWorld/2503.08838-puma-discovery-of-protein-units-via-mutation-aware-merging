# Evaluation Targets

## Primary: clinical_sibling_association

Tests whether favorable clinical substitutions are more likely than pathogenic substitutions to preserve membership within the same discovered unit family.
- **Metric**: `benign_pathogenic_gap` (higher is better)
- **How to run**: `bash scripts/method.sh`, then `bash scripts/evaluate.sh outputs/puma_reproduction/raw_results.json`

## Constraint: vocabulary_genealogy

Checks that the submitted system preserves a genuine unit-family structure while using the fixed vocabulary scale.
- **Metrics**: `family_coverage` (higher is better), `vocab_size` (lower is better as a resource constraint at fixed target scale)
- **How to run**: same as `clinical_sibling_association`
