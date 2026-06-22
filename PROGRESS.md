# Progress

## What Works

- Paper analysis and benchmark scaffolding are complete.
- Official PUMA code and released 6,400-token PUMA/BPE vocabularies are vendored under `method/PUMA_official/`.
- `scripts/download.sh` fetches the ProteinGym clinical substitutions parquet and five DMS substitution parquet shards from verified Hugging Face URLs.
- `method/run_puma.py` writes method artifacts and optionally trains a small fresh PUMA vocabulary to exercise the actual mutation-aware merge algorithm.
- `eval/evaluate_puma.py` independently recomputes clinical, DMS, and vocabulary-structure scores from raw artifacts and writes `scoring/scores.json` without importing from `method/`.
- CPU verification job `083b2b54-456` completed successfully after the independent evaluator refactor; `python validate.py --compare` passes.
- Continuation audit confirmed the implementation uses the official PUMA mutation-aware merge code and released PUMA/BPE artifacts rather than a surrogate.
- `baseline/run_bpe.py` now writes a BPE-only raw artifact without delegating to the combined PUMA method runner.
- DMS sibling-association scoring has been added as an additional secondary validation target and was reproduced in CPU job `7d8d021d-1ba`.
- `scripts/run.sh` now regenerates method artifacts before scoring, so submitted verification jobs do not depend on ignored `outputs/` files.
- Final verification copied the UniRef50-human FASTA into tracked `data/uniref50_human.fasta`, so from-scratch agents can access benchmark data without depending on `method/`.
- 2026-06-22 audit tightened the default evaluator so `scripts/evaluate.sh` reports the same log-ratio, minimum SAME-index, vocabulary-budget, observed-token, and family-size constraint metrics declared in `scoring/reference.json`.

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

Secondary DMS sibling-association claim reproduced on human ProteinGym DMS substitutions:
- PUMA positive SAME sibling rate: 0.07539 reproduced vs. 0.07539 reference.
- PUMA negative SAME sibling rate: 0.04736 reproduced vs. 0.04736 reference.
- PUMA positive-negative gap: 0.02803 reproduced vs. 0.02803 reference.
- BPE baseline SAME sibling rate: 0.0 for both bins because it has no genealogy.

## Remaining

- Higher milestones would require adding heavier paper settings, such as ESM-2 preference scoring, GO topic analysis, more vocabulary sizes, or the full hyperparameter grid.

## Issues

- The paper's full 51,200-token grid and ESM-2/GO experiments are larger than the compact reproduction. Current results focus on clinical substitutions, DMS substitutions, vocabulary structure, and a small fresh PUMA training run.
- The official released 6,400-token vocabularies and released result CSVs remain under `method/PUMA_official/RSRC` and `method/PUMA_official/Prog/result_files`; the compact UniRef50-human FASTA used as benchmark data is also tracked at `data/uniref50_human.fasta`. `scripts/download.sh` fetches external ProteinGym clinical and DMS parquets.
- A 2026-06-22 audit found that the previous `scripts/run.sh` assumed `outputs/puma_reproduction/raw_results.json` already existed even though `outputs/` is gitignored. This was fixed by making `scripts/run.sh` call `scripts/method.sh` before evaluation.
- A final 2026-06-22 verification found method details in `briefing/evaluation.md` and a problem-data path pointing into `method/`; both were corrected.
- The login-node Python environment does not have the packaged dependencies such as `pandas`, so local evaluator execution is intentionally skipped; the CPU test job validates inside the declared container environment.

## Deviations from Paper

- The compact benchmark evaluates the released 6,400-token PUMA vocabulary rather than the paper's largest 51,200-token vocabulary. The official repository provides 6,400-token PUMA and BPE vocabularies and matching result CSVs directly, making this a faithful smaller-scale validation while preserving the paper's algorithm and evaluation metric.
- The submitted job trains a smaller fresh PUMA vocabulary only to verify the mutation-aware merge procedure runs end to end. The clinical reproduction scores are computed from the official 6,400-token PUMA/BPE vocabularies and the downloaded ProteinGym clinical substitutions.
