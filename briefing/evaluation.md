# Evaluation

## Metrics

The primary metric is `benign_pathogenic_gap`: the SAME sibling rate for benign clinical substitutions minus the SAME sibling rate for pathogenic substitutions. SAME sibling rate is computed only for point mutations where the original and mutated full sequence have identical token boundaries; among those SAME cases, it is the fraction where the original and mutated tokens at the mutation site belong to the same unit family.

The evaluation also reports the benign and pathogenic SAME sibling rates separately, SAME boundary rates (`benign_same_idx`, `pathogenic_same_idx`), vocabulary size, and family coverage. Family coverage is a constraint metric: a method should produce a meaningful genealogy rather than only a flat vocabulary.

A second biological validation uses human ProteinGym deep mutational scanning assays. It reports the SAME sibling-rate gap between positive/high-fitness and negative/low-fitness substitutions with the same unchanged-boundary filter.

A secondary vocabulary-structure experiment reports `family_coverage`, `mutated_vocab_fraction`, `parent_vocab_fraction`, and `vocab_size` at the same fixed vocabulary budget. This prevents future systems from improving the clinical metric by discarding the family structure that the task is meant to evaluate.

## Baselines and Targets

The baseline is frequency-only BPE at the same 6,400-token vocabulary size. The target is the paper's PUMA configuration trained on UniRef50-human with BLOSUM62, alignment cutoff 0.7, mutation length range 3-12, frequency cutoff 0.05, and vocabulary size 6,400.

## Evaluation Protocol

The compact reproduction uses ProteinGym clinical substitutions from ClinVar. The method writes raw tokenization and family-count artifacts to `outputs/puma_reproduction/raw_results.json`; `scripts/evaluate.sh` reads only that artifact and writes `scoring/scores.json`. The evaluator does not import from `method/`, so a future method can be scored by writing the same raw artifact schema.
