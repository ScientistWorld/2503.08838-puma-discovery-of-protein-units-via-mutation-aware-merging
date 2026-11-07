# Scientist Constraints

## Data

- Build vocabularies and families from unlabeled protein sequences only (the provided `data/uniref50_human.fasta`, or other unlabeled sequence data). **Never use ClinVar or DMS labels** — neither the visible train populations in `data/downloads/proteingym_train/` nor anything else — to choose units, families, links or hyperparameters. The train populations exist to measure progress, not to fit on.
- This includes public copies: do not download or read ProteinGym, ClinVar, MaveDB or any other variant-effect labels (clinical significance, DMS scores or bins) in method code. The hidden test scores public variants, so fitting families to public labels would score the answers rather than the method. Label use cannot be detected from the submitted artifacts; the separate compliance grader checks method code and logs for it.
- Never read `eval/test/` (hidden populations, labels and their raw sources) or modify `eval/` or `scripts/evaluate_*.sh`.

## Vocabulary scale

- At most 6,400 units (enforced). Larger vocabularies raise the scores through resource scaling, not method.
- Units must be uppercase residue strings; the tokenizer must segment raw sequences losslessly (no normalizer, pre-tokenizer, post-processor, added tokens or dropout; model type `BPE` or `Unigram`).
- The segmentation must stay a real unit vocabulary: ≥ 2.0 residues per unit and ≥ 3,200 distinct units used on the scored proteins.
- No loss of granularity: residues per unit on the scored proteins must be at least 0.95× those of the frequency-only 6,400-unit baseline (`compression_vs_bpe` ≥ 0.95), otherwise the run fails.

## Families

- Families are given by `"parent"` links in `vocab.json` between units of the same length (substitution variants). Links must point to existing units.
- The SAME sibling definition is fixed: only substitutions that leave every unit boundary unchanged are counted; at least 20% of each label's variants must be SAME.
- Both biological tasks must be solved: clinical gap ≥ 0.04 and DMS gap ≥ 0.014. Below either minimum, neither gap earns credit.

## Submission

- Write `outputs/<method_name>/tokenizer.json` and `outputs/<method_name>/vocab.json`. The evaluators score every such directory; do not name a method `bpe_6400` (reserved for the fixed baseline).

## Compliance checklist

- [ ] No clinical or DMS labels (visible train split or public downloads) used anywhere in vocabulary or family construction
- [ ] ≤ 6,400 units, lossless deterministic segmentation, valid same-length parent links, `compression_vs_bpe` ≥ 0.95
- [ ] Artifacts written to `outputs/<method_name>/`; evaluator and data splits untouched
