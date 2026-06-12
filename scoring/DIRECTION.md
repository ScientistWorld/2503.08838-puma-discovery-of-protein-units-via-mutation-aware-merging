# Research Direction

## Research Problem

This benchmark studies protein sequence tokenization where units should be contiguous, reusable, and informative about the effects of amino-acid substitutions. The scientific question is whether sequence units can represent mutational relatedness, not just frequent substrings.

## Core Contribution

The contribution space is mutation-aware protein-unit discovery with an explicit genealogy between related units. Improvements should change how unit families are discovered, filtered, weighted, or used while preserving the goal of a sequence-derived vocabulary with family relationships.

## Approach Scope

In-bounds work may modify substitution scoring, candidate search, merge ordering, frequency thresholds, genealogy construction, or family post-processing. It may also introduce additional biologically motivated constraints if they operate within the same protein-unit discovery problem.

## Out of Bounds

Replacing the task with a supervised pathogenicity predictor is out of bounds. Using a protein language model to directly classify variants is also out of bounds because it bypasses the paper's unit-discovery claim. Scaling the vocabulary far beyond the benchmark size or adding external labeled clinical data for scoring is not a valid improvement under this gym.
