#!/bin/bash
set -euo pipefail
cd /home/user
cases=(reference_seed7 reference_seed17 reference_seed29 weak_no_genealogy honest_stricter_links_080 honest_stricter_links_090 shortcut_skip_training shortcut_raw_fields shortcut_family_padding shortcut_constant shortcut_empty shortcut_impossible_flags shortcut_label_lookup shortcut_dataset_replacement shortcut_baseline_replacement original_training more_training)
for name in "${cases[@]}"; do
  if [ -f "redteam/$name/scores_test.json" ]; then
    echo "Already completed $name"
    continue
  fi
  echo "Running $name"
  if bash "redteam/$name/run.sh"; then
    echo "Completed $name"
  else
    echo "FAILED $name; continuing to retain other independent audit evidence"
  fi
done
python redteam/summarize.py
