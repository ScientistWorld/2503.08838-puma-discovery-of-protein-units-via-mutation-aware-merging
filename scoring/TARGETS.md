# Evaluation Targets

## Primary: clinical_sibling_association

Tests whether favorable clinical substitutions are more likely than pathogenic substitutions to preserve membership within the same discovered unit family.
- **Metric**: `benign_pathogenic_gap` (higher is better)
- **How to run**: `bash scripts/method.sh`, then `bash scripts/evaluate.sh outputs/puma_reproduction/raw_results.json`

## Secondary: vocabulary_structure

Checks that the submitted system preserves a genuine unit-family structure while using the fixed vocabulary scale.
- **Metric**: `family_coverage` (higher is better)
- **Constraint metrics**: `mutated_vocab_fraction`, `parent_vocab_fraction`, and `vocab_size`
- **How to run**: same as `clinical_sibling_association`

## Secondary: dms_sibling_association

Tests whether experimentally positive or high-fitness DMS substitutions are more likely than negative or low-fitness substitutions to preserve membership within the same discovered unit family.
- **Metric**: `positive_negative_gap` (higher is better)
- **How to run**: `bash scripts/method.sh`, then `bash scripts/evaluate.sh outputs/puma_reproduction/raw_results.json`
