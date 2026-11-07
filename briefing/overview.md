# Overview

- **Paper ID:** 2503.08838
- **Title:** PUMA: Discovery of Protein Units via Mutation-Aware Merging
- **Domain:** Computational Biology / Protein Sequence Tokenization
- **TL;DR:** PUMA extends BPE for proteins by adding substitution-matrix-guided mutational variants during merging, producing a vocabulary plus a biologically meaningful genealogy.

## Short Summary

The paper addresses how to discover contiguous protein sequence units that act like words in the language of life. PUMA keeps the frequency-based core of BPE but explicitly searches for plausible amino-acid substitution variants of each newly merged unit and records their genealogical relationships. The authors validate the resulting families using clinical variants, deep mutational scanning, ESM-2 masked-token preferences, and Gene Ontology topic modeling.

## Key Results

- On ProteinGym ClinVar substitutions, PUMA(BLOSUM62, 0.7, 0.05) at 6,400 tokens has a benign SAME sibling rate of 0.158 versus 0.074 for pathogenic variants.
- On human ProteinGym DMS substitutions, the same compact PUMA setting has a positive SAME sibling rate of 0.075 versus 0.047 for negative variants.
- The released 6,400-token PUMA vocabulary has 94.1% family coverage, while the frequency-only BPE baseline has no genealogy.
- The frequency-only BPE baseline has no genealogy and therefore zero SAME sibling rate under this metric.
- The gym reproduction trains PUMA(BLOSUM62, 0.7, 0.05) with the official code on the full human UniRef50 corpus at 6,400 units and submits exactly that trained vocabulary; it is scored on held-out ClinVar proteins, held-out DMS protein regions, and a segmentation-granularity constraint against the frequency-only BPE baseline.
