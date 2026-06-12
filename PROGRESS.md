# Progress

## What Works

- Paper analysis and benchmark scaffolding are complete.
- Official PUMA code and released 6,400-token PUMA/BPE vocabularies are vendored under `method/PUMA_official/`.
- `scripts/download.sh` fetches the 9 MB ProteinGym clinical substitutions parquet from a verified Hugging Face URL.
- `method/run_puma.py` evaluates SAME sibling rates from method artifacts and optionally trains a small fresh PUMA vocabulary to exercise the actual mutation-aware merge algorithm.
- `eval/evaluate_puma.py` reads raw method artifacts and writes `scoring/scores.json` without importing from `method/`.
- The CPU container smoke job and expanded scoring rerun completed successfully; `python validate.py --compare` passes.
- Continuation audit confirmed the implementation uses the official PUMA mutation-aware merge code and released PUMA/BPE artifacts rather than a surrogate.
- `baseline/run_bpe.py` now writes a BPE-only raw artifact without delegating to the combined PUMA method runner.
- DMS sibling-association scoring has been added as an additional secondary validation target; the next CPU job computes reproduced DMS rates from downloaded ProteinGym DMS parquet shards.

## Results

Core claim reproduced on the compact 6,400-token clinical validation:
- PUMA benign SAME sibling rate: 0.1648 reproduced vs. 0.1579 paper.
- PUMA pathogenic SAME sibling rate: 0.0772 reproduced vs. 0.0744 paper.
- PUMA benign-pathogenic gap: 0.0876 reproduced vs. 0.0835 paper.
- BPE baseline SAME sibling rate: 0.0 reproduced for both labels, matching the paper's no-genealogy baseline.
- PUMA family coverage at 6,400 units: 0.94125 reproduced.

Secondary vocabulary-structure claim reproduced at the same 6,400-token budget:
- PUMA family coverage: 0.94125 reproduced vs. 0.94125 reference.
- PUMA mutated vocabulary fraction: 0.83719 reproduced vs. 0.83719 reference.
- PUMA parent vocabulary fraction: 0.10406 reproduced vs. 0.10406 reference.
- BPE family coverage and family fractions: 0.0 reproduced, as expected for a flat baseline vocabulary.

## Remaining

- Higher milestones would require adding more paper settings, such as DMS assays, ESM-2 preference scoring, GO topic analysis, or larger vocabulary sizes.
- Higher milestones would require adding heavier paper settings, such as ESM-2 preference scoring, GO topic analysis, more vocabulary sizes, or the full hyperparameter grid.

## Issues

- The paper's full 51,200-token grid and ESM-2/GO experiments are larger than the compact reproduction. Current results focus on clinical substitutions, DMS substitutions, vocabulary structure, and a small fresh PUMA training run.
- The official compact UniRef50-human FASTA and 6,400-token vocabularies are tracked under `method/PUMA_official/RSRC`; `scripts/download.sh` only fetches the external ProteinGym clinical parquet.

## Deviations from Paper

- The compact benchmark evaluates the released 6,400-token PUMA vocabulary rather than the paper's largest 51,200-token vocabulary. The official repository provides 6,400-token PUMA and BPE vocabularies directly, making this a faithful smaller-scale validation while preserving the paper's algorithm and evaluation metric.
- The submitted job trains a smaller fresh PUMA vocabulary only to verify the mutation-aware merge procedure runs end to end. The clinical reproduction scores are computed from the official 6,400-token PUMA/BPE vocabularies and the downloaded ProteinGym clinical substitutions.
