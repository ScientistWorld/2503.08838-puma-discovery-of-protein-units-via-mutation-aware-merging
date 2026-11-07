# Experiment Overview

## clinical_sibling_association (weight 0.6)

Establishes whether the families of a protein-unit vocabulary carry clinical meaning: when a single amino-acid substitution keeps the local unit inside the same family, is that variant more often benign than pathogenic? Scored on ClinVar variants of proteins whose labels are held out. The scored quantity is the benign-minus-pathogenic difference of the within-family rate, so inflating family membership uniformly does not help.

## dms_sibling_association (weight 0.3)

Asks the same question with experimental fitness instead of clinical annotation: are within-family substitutions enriched among high-fitness variants of human deep mutational scanning assays, compared with low-fitness variants? Scored on held-out regions of the assayed proteins.

## vocabulary_structure (weight 0.1)

The constraint side. The vocabulary must remain a genuine segmentation at the fixed 6,400-unit budget: complete and lossless, with explicit and consistent families, and with units as long as those of a frequency-only vocabulary of the same size. The scored quantity is the unit length relative to the frequency-only baseline (capped at 1); budget, losslessness, family consistency, minimum unit length, minimum vocabulary use and minimum boundary preservation are validity gates whose violation fails the run.
