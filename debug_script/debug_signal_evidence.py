import shutil
import pandas as pd
import json
from pathlib import Path
from collections import defaultdict
import datetime
from itertools import zip_longest
from copy import deepcopy
import os

dfsall = []
base0 = Path("outputs/model_output/2026_05_17_signal_0_deepseek-v4-pro")
base1 = Path("outputs/model_output/2026_05_17_signal_1_deepseek-v4-pro")
base2 = Path("outputs/model_output/2026_05_17_signal_2_deepseek-v4-pro")

non_list_group = ['instrument_normalized', 'instrument']

allrows = []
for f0 in base0.iterdir():

    f1 = base1 / f0.name
    f2 = base2 / f0.name
    dfs = []
    
    # allrows = defaultdict(list)

    for batch, f in enumerate([f0, f1, f2]):
        if not f.exists():
            print("missing:", f)
            continue
        with open(f, "r") as fp:
            js = json.load(fp)
        
        
        for signal in js['signals']:
            current_row = []
            try:
                for k1 in non_list_group:
                    k2 = signal.pop(k1)
                    current_row.append(k2)
                signal.pop('invalid')
                signal.pop('invalid_reason')
            except:
                print("error:", f)
                os.remove(f)
                break
            
            dt = datetime.datetime.fromtimestamp(f.stat().st_mtime)
            current_row.append(dt)
            current_row.append(f.name.replace('.json', ''))
            current_row.append(batch)

            for rows2 in zip_longest(*signal.values()):
                current_row2 = deepcopy(current_row)
                current_row2.extend(list(rows2))
                allrows.append(deepcopy(current_row2))

cols=  non_list_group + ['mtime', 'dt', 'batch']  + list(signal.keys())
pd.DataFrame(allrows, columns=cols).to_csv('review.csv', index=False)


dates = ["20211220", "20211221", "20211222", "20211223"]
# dates =  ["20211223"]
debug_dir = Path("debug")

if debug_dir.exists():
    shutil.rmtree(debug_dir)

debug_dir.mkdir(parents=True, exist_ok=True)

raw_dir = Path('transcripts/clean')
for batch in range(3):
    src_dir = Path(f"outputs/reasoning/debug_2026_05_17_signal_{batch}_deepseek-v4-pro")

    for date in dates:
        src_file = src_dir / f"d{date}.txt"
        src_file2 = raw_dir / f"{date}.txt"

        dst_file = debug_dir / f"batch{batch}_d{date}.txt"
        dst_file2 = debug_dir / f"transcript_{date}.txt"
        
        shutil.copy2(src_file, dst_file)
        shutil.copy2(src_file2, dst_file2)

shutil.copy2('review.csv', debug_dir/"review.csv")
print(f"Copied debug files to: {debug_dir}")