# Experiment Overview

## clinical_sibling_association

Tests whether a protein-unit vocabulary captures clinically meaningful mutation relationships. The experiment compares benign and pathogenic single amino-acid substitutions and measures whether the local unit before and after mutation remains in the same family when token boundaries are unchanged. It also reports whether the vocabulary provides broad family coverage at the fixed vocabulary scale.

## vocabulary_structure

Checks whether the produced unit vocabulary has a non-trivial family structure at the same vocabulary budget. This is a constraint-style experiment: future systems should not improve clinical association scores by abandoning the family coverage that makes the benchmark meaningful.
