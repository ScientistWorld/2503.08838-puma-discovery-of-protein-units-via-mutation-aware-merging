# Problem Definition

## Research Question

Can a protein sequence vocabulary segment complete amino-acid chains into reusable contiguous units while preserving biologically meaningful relationships between single-residue variants of those units?

## Why It Matters

Protein language models and downstream analyses usually operate at residue level or use frequency-only subwords. A useful intermediate vocabulary should expose larger interpretable units and should distinguish substitutions that preserve function from substitutions that are more disruptive.

## Success Criteria

A successful system should tokenize full protein sequences without gaps, group related unit variants into reusable families, and show that mutations staying within those families are enriched among favorable or benign variants compared with unfavorable or pathogenic variants.
