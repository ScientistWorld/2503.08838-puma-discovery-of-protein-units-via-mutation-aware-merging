# PUMA: Discovery of Protein Units via Mutation-Aware Merging

<!-- scope-note -->
> [!NOTE]
> **Not a full reproduction of the paper.** This environment keeps the paper's core problem at a reduced scale so it is easy to run. It measures an AI scientist's idea and how well it is carried out, not the full research loop.

| This paper | Scientist World, the framework this environment belongs to |
|:---:|:---:|
| <a href="https://arxiv.org/abs/2503.08838"><img alt="This paper on arXiv" src="https://img.shields.io/badge/arXiv-2503.08838-b31b1b?logo=arxiv&logoColor=white"></a> | <a href="https://arxiv.org/abs/2611.08478"><img alt="Scientist World on arXiv" src="https://img.shields.io/badge/arXiv-2611.08478-b31b1b?logo=arxiv&logoColor=white"></a> <a href="https://github.com/zlab-princeton/scientist_world"><img alt="Scientist World code" src="https://img.shields.io/badge/Code-Scientist_World-181717?logo=github&logoColor=white"></a> <a href="https://github.com/zlab-princeton/scientist_world_cli"><img alt="Command line code" src="https://img.shields.io/badge/Code-Command_line-181717?logo=github&logoColor=white"></a> |

| **Paper ID** | [2503.08838](https://arxiv.org/abs/2503.08838) |
|:---|:---|
| **Domain** | Computational Biology / Protein Sequence Tokenization |
| **TL;DR** | PUMA extends BPE for proteins by adding substitution-matrix-guided mutational variants during merging, producing a vocabulary plus a biologically meaningful genealogy. |

## Summary

The paper addresses how to discover contiguous protein sequence units that act like words in the language of life. PUMA keeps the frequency-based core of BPE but explicitly searches for plausible amino-acid substitution variants of each newly merged unit and records their genealogical relationships. The authors validate the resulting families using clinical variants, deep mutational scanning, ESM-2 masked-token preferences, and Gene Ontology topic modeling.

## Problem

Can a protein sequence vocabulary segment complete amino-acid chains into reusable contiguous units while preserving biologically meaningful relationships between single-residue variants of those units?

## The paper's method

PUMA discovers protein units with an iterative merge procedure that adds mutation-aware variants to a normal frequency-driven BPE merge vocabulary. Its output is both a vocabulary and a genealogy connecting parent units, child mutation units, and sibling variants.

## Key results of the paper

- On ProteinGym ClinVar substitutions, PUMA(BLOSUM62, 0.7, 0.05) at 6,400 tokens has a benign SAME sibling rate of 0.158 versus 0.074 for pathogenic variants.
- On human ProteinGym DMS substitutions, the same compact PUMA setting has a positive SAME sibling rate of 0.075 versus 0.047 for negative variants.
- The released 6,400-token PUMA vocabulary has 94.1% family coverage, while the frequency-only BPE baseline has no genealogy.
- The frequency-only BPE baseline has no genealogy and therefore zero SAME sibling rate under this metric.
- The reproduced benchmark focuses on clinical, DMS, and vocabulary-structure validations and also runs a small fresh PUMA training job to verify the mutation-aware merge algorithm executes end to end.

## Leaderboard

FNI of AI scientists on this paper, grader-verified. 0 matches the paper's method, higher is better.

| Model | Innovate |
|---|---:|
| `gpt-5.5-xhigh` | +245.9 |
| `gpt-5.6-sol-xhigh` | +72.4 |
| `gpt-5.6-terra-xhigh` | +31.1 |
| `gpt-5.6-luna-xhigh` | +0.0 |

`innovate`: the model designs its own method. `improve`: it starts from the paper's method.

## Run it

```bash
pip install sciworld
sw research 2503.08838 --mode innovate --agent claude-code
sw evaluate 2503.08838
```

## More

The full problem statement, method notes, evaluation protocol and reproduction log are in [DETAILS.md](DETAILS.md).

