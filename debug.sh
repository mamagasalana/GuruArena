#!/usr/bin/env bash
set -euo pipefail

dates=(20211220 20211221 20211222 20211223)
out_dir="outputs/reasoning/debug_20211220_to_20211223_batches"
zip_path="outputs/reasoning/debug_20211220_to_20211223_batches.zip"

rm -rf "$out_dir"
mkdir -p "$out_dir"

for batch in 0 1 2; do
  src_dir="outputs/reasoning/debug_2026_05_17_signal_${batch}_deepseek-v4-pro"
  for date in "${dates[@]}"; do
    cp "$src_dir/d${date}.txt" "$out_dir/batch${batch}_d${date}.txt"
  done
done

rm -f "$zip_path"
zip -j "$zip_path" "$out_dir"/*.txt
echo "Saved zip to: $zip_path"
