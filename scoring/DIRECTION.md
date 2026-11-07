# Research Direction

## Research Problem

Protein sequence segmentation into contiguous, reusable units whose organization also reflects mutational relatedness: units that are variants of one another by plausible amino-acid substitutions should be grouped into families, and substitutions that stay within a family should be the less disruptive ones.

## Core Contribution Space

Unsupervised discovery of a fixed-size protein-unit vocabulary together with an explicit family structure. Improvements may change how units are proposed, scored and accepted, how variants are linked into families, which substitution model or evolutionary signal guides linking, or how the vocabulary budget is split between frequent units and their variants.

## What counts as progress

A larger benign-vs-pathogenic and high-vs-low-fitness difference in within-family substitution rates on held-out proteins, without giving up segmentation granularity relative to a frequency-only vocabulary of the same size.

## Out of Bounds

- Using clinical or DMS labels (including the visible train populations) to build or tune units or families, or reading the hidden test.
- Supervised variant-effect prediction or protein-language-model scoring that bypasses unit discovery.
- Exceeding the 6,400-unit budget, lossy or near-character-level segmentations, or editing the evaluator.
