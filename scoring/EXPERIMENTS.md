# Experiment Overview

## clinical_sibling_association (weight 0.6)

Asks whether the families of a protein-unit vocabulary carry clinical meaning. When a single amino-acid substitution keeps the local unit inside the same family, is that variant more often benign than pathogenic? It is scored on ClinVar variants of proteins whose labels are held out. The scored quantity is the benign-minus-pathogenic difference in the within-family rate, so inflating family membership uniformly does not help.

## dms_sibling_association (weight 0.3)

Asks the same question with experimental fitness instead of clinical annotation. Are within-family substitutions enriched among high-fitness variants of human deep mutational scanning assays, compared with low-fitness variants? It is scored on held-out regions of the assayed proteins.

The two biological experiments are a joint requirement. A vocabulary must show at least a minimum enrichment on **both**: a gap of at least 0.04 clinically and 0.014 on DMS, about half the published effect at this scale. If it falls short on either one, neither experiment earns credit. A family structure that only works for one kind of evidence therefore cannot outrank one that works for both.

## vocabulary_structure (weight 0.1)

This is the constraint side. The vocabulary must remain a genuine segmentation at the fixed 6,400-unit budget:
- complete and lossless;
- explicit, consistent families;
- units essentially as long as those of a frequency-only vocabulary of the same size.

The scored quantity is unit length relative to the frequency-only baseline, capped at 1. Each of the following is a validity gate, and violating any one fails the run:
- the budget;
- losslessness;
- family consistency;
- minimum unit length;
- units no more than 5% shorter than the baseline's;
- minimum vocabulary use;
- minimum boundary preservation.
