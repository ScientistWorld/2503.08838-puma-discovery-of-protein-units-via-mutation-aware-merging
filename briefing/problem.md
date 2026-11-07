# Problem Definition

## Research Question

Can a protein sequence vocabulary segment complete amino-acid chains into reusable contiguous units while preserving biologically meaningful relationships between single-residue variants of those units?

## Why It Matters

Protein language models and downstream analyses usually operate at residue level or use frequency-only subwords. A useful intermediate vocabulary should expose larger interpretable units and should distinguish substitutions that preserve function from substitutions that are more disruptive.

## Success Criteria

A successful system should tokenize full protein sequences losslessly with a fixed budget of 6,400 units, group related unit variants into explicit families, and show — on proteins it has never seen labels for — that substitutions staying within a family are enriched among benign or high-fitness variants compared with pathogenic or low-fitness variants, without giving up segmentation granularity relative to a frequency-only vocabulary of the same size. Labels are never used to build the vocabulary.
