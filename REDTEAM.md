# Scoring audit of the hardened gym

The first bundled job completed all 19 cases successfully. Genuine improvements score higher: the reference is **0.157387967**, a label-free chemical family rule is **0.252294645**, and removing genealogy falls to **0.097766455**. Three independent full-corpus reference retrainings produce identical scores (seed spread **0**).

Two label-fitting shortcuts pay: fitting the visible training labels scores **0.229352382**, and rebuilding labels from the public download URLs scores **0.409993813**. Tokenization stays identical to the reference. Forged fields, moved baseline/data settings, replaced released artifacts, and the tested degenerate submissions do not pay.

A final CPU run tests the remaining additive-score concern: clinical-answer fitting with every DMS SAME pair forbidden from sharing a family. The final report will replace this interim summary after that run.

All current results are in [redteam/v2_support/summary.json](redteam/v2_support/summary.json). Each current case has `redteam/v2_*/run.sh`, original train/test scores, its rank calculation and an evaluator-integrity receipt. Older unprefixed cases predate the current evaluator and are not evidence about it.
