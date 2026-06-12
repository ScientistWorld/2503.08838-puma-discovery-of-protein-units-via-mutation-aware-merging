# Paper's Method

## Key Contribution

PUMA discovers protein units with an iterative merge procedure that adds mutation-aware variants to a normal frequency-driven BPE merge vocabulary. Its output is both a vocabulary and a genealogy connecting parent units, child mutation units, and sibling variants.

## Approach

The vocabulary starts from amino-acid characters. At each iteration PUMA extracts the most frequent adjacent pair, merges it, and adds the merged string as a unit. For merged units within the configured length range, it enumerates candidate substitutions using non-negative entries in an amino-acid substitution matrix such as BLOSUM62. A candidate variant is accepted only if it meets the normalized alignment-score cutoff and if an adjacent pair currently exists in the corpus whose merge would form that candidate with sufficient frequency relative to the parent. Accepted variants are merged immediately and linked genealogically to the parent.

## Main Claims

The primary claim is that mutation-aware merging yields protein-unit families whose within-family substitutions are enriched for biologically favorable outcomes, such as benign ClinVar substitutions and high-fitness DMS substitutions. Secondary claims are that protein language models contextually prefer PUMA sibling substitutions over alternatives and that graph-aware topic models using the genealogy better align unit distributions with functional annotations.
