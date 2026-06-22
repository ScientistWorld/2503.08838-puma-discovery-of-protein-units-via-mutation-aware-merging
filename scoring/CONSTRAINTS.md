# Scientist Constraints

## Data

Use the provided ProteinGym clinical substitutions parquet at `data/downloads/proteingym_clinical_substitutions/train-00000-of-00001.parquet`, the ProteinGym DMS parquet shards in `data/downloads/proteingym_dms_substitutions/`, and the released UniRef50-human FASTA at `data/uniref50_human.fasta`. Do not add external clinical-variant datasets for scoring this benchmark; doing so changes the evaluation population rather than improving the method.

## Vocabulary Scale

Report scores at the 6,400-token scale used by this compact benchmark. Larger vocabularies may improve rates by increasing coverage, but that is resource scaling rather than a methodological improvement under this gym.

## Evaluation Protocol

Keep the SAME sibling definition fixed: evaluate only single substitutions whose original and mutated sequence token offsets are identical, then count whether the original and mutated tokens at the mutation site are in the same family. Do not train on labels from the ProteinGym clinical substitutions file.

## Compliance Checklist

- [ ] Uses the provided ProteinGym clinical substitutions file for scoring
- [ ] Reports the benchmark at 6,400 vocabulary entries
- [ ] Does not use clinical labels during vocabulary construction
- [ ] Computes SAME sibling rates with unchanged token-boundary filtering
- [ ] Writes raw artifacts for `scripts/evaluate.sh` rather than modifying evaluator internals
