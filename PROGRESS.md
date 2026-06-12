# Progress

## What Works

- Paper analysis and benchmark scaffolding are complete.
- Official PUMA code and released 6,400-token PUMA/BPE vocabularies are vendored under `method/PUMA_official/`.
- `scripts/download.sh` fetches the 9 MB ProteinGym clinical substitutions parquet from a verified Hugging Face URL.
- `method/run_puma.py` evaluates SAME sibling rates from method artifacts and optionally trains a small fresh PUMA vocabulary to exercise the actual mutation-aware merge algorithm.
- `eval/evaluate_puma.py` reads raw method artifacts and writes `scoring/scores.json` without importing from `method/`.

## Results

No reproduced scores yet. A CPU job is being submitted to install dependencies, run compact PUMA training/evaluation, and write `scoring/scores.json`.

Paper/reference targets for the compact 6,400-token ClinVar validation:
- PUMA benign SAME sibling rate: 0.1579
- PUMA pathogenic SAME sibling rate: 0.0744
- BPE SAME sibling rate: 0.0 because BPE has no genealogy

## Remaining

- Run `scripts/method.sh` in the compute container.
- Inspect `scoring/scores.json` and compare with `scoring/reference.json`.
- If the reproduced clinical gap supports the paper's claim, advance to `core_claim`; otherwise diagnose counts, preprocessing, or tokenization mismatches and resubmit.

## Issues

- The paper's full 51,200-token grid and ESM-2/GO experiments are larger than the minimum core reproduction. This first job focuses on the clinical substitution validation and a small fresh PUMA training run.

## Deviations from Paper

- The compact benchmark evaluates the released 6,400-token PUMA vocabulary rather than the paper's largest 51,200-token vocabulary. The official repository provides 6,400-token PUMA and BPE vocabularies directly, making this a faithful smaller-scale validation while preserving the paper's algorithm and evaluation metric.
- The submitted job trains a smaller fresh PUMA vocabulary only to verify the mutation-aware merge procedure runs end to end. The clinical reproduction scores are computed from the official 6,400-token PUMA/BPE vocabularies and the downloaded ProteinGym clinical substitutions.
