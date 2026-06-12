# Progress

## What Works

- Paper analysis and benchmark scaffolding are complete.
- Official PUMA code and released 6,400-token PUMA/BPE vocabularies are vendored under `method/PUMA_official/`.
- `scripts/download.sh` fetches the 9 MB ProteinGym clinical substitutions parquet from a verified Hugging Face URL.
- `method/run_puma.py` evaluates SAME sibling rates from method artifacts and optionally trains a small fresh PUMA vocabulary to exercise the actual mutation-aware merge algorithm.
- `eval/evaluate_puma.py` reads raw method artifacts and writes `scoring/scores.json` without importing from `method/`.
- The CPU container smoke job and expanded scoring rerun completed successfully; `python validate.py --compare` passes.

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
- A public ProteinGym DMS substitutions release exists, but the aggregate is multi-gigabyte scale; it was left out of this compact gym to keep the environment lightweight and reproducible.

## Issues

- The paper's full 51,200-token grid and ESM-2/GO experiments are larger than the compact core reproduction. Current results focus on the clinical substitution validation, vocabulary structure, and a small fresh PUMA training run.

## Deviations from Paper

- The compact benchmark evaluates the released 6,400-token PUMA vocabulary rather than the paper's largest 51,200-token vocabulary. The official repository provides 6,400-token PUMA and BPE vocabularies directly, making this a faithful smaller-scale validation while preserving the paper's algorithm and evaluation metric.
- The submitted job trains a smaller fresh PUMA vocabulary only to verify the mutation-aware merge procedure runs end to end. The clinical reproduction scores are computed from the official 6,400-token PUMA/BPE vocabularies and the downloaded ProteinGym clinical substitutions.
