import json
import shutil
from pathlib import Path
import datetime

import pandas as pd

base0 = Path("outputs/model_output/2026_06_04_signal_intent_0_deepseek-v4-pro")
base1 = Path("outputs/model_output/2026_06_04_signal_intent_1_deepseek-v4-pro")
base2 = Path("outputs/model_output/2026_06_04_signal_intent_2_deepseek-v4-pro")

non_list_group = ['instrument_normalized', 'instrument']

allrows = []
for f0 in base0.iterdir():

    f1 = base1 / f0.name
    f2 = base2 / f0.name
    rows_by_key = {}
    dt = f0.stem
    mtime = datetime.datetime.fromtimestamp(f0.stat().st_mtime)

    for batch, f in enumerate([f0, f1, f2]):
        if not f.exists():
            print("missing:", f)
            continue
        with open(f, "r") as fp:
            js = json.load(fp)
        
        
        for signal in js['signals']:
            try:
                instrument_normalized = signal['instrument_normalized']
                instrument = signal['instrument']
                intent = signal['intent']
            except:
                print("error:", f)
                # os.remove(f)
                break
            
            key = (instrument_normalized, tuple(instrument))
            if key not in rows_by_key:
                rows_by_key[key] = {
                    'instrument_normalized': instrument_normalized,
                    'instrument': instrument,
                    'mtime': mtime,
                    'dt': dt,
                    'intent0': '',
                    'intent1': '',
                    'intent2': '',
                }

            intent_col = f'intent{batch}'
            if rows_by_key[key][intent_col]:
                rows_by_key[key][intent_col] += f'|{intent}'
            else:
                rows_by_key[key][intent_col] = intent

            rows_by_key[key]['mtime'] = max(
                rows_by_key[key]['mtime'],
                datetime.datetime.fromtimestamp(f.stat().st_mtime),
            )

    allrows.extend(rows_by_key.values())


cols = non_list_group + ['mtime', 'dt', 'intent0', 'intent1', 'intent2']
pd.DataFrame(allrows, columns=cols).to_csv('review.csv', index=False)


dates = ["20211220", "20211221", "20211222", "20211223"]
# dates =  ["20211223"]
debug_dir = Path("debug")

if debug_dir.exists():
    shutil.rmtree(debug_dir)

debug_dir.mkdir(parents=True, exist_ok=True)

raw_dir = Path('transcripts/clean')
for batch in range(3):
    src_dir = Path(f"outputs/reasoning/debug_2026_06_04_signal_intent_{batch}_deepseek-v4-pro")

    for date in dates:
        src_file = src_dir / f"d{date}.txt"
        src_file2 = raw_dir / f"{date}.txt"
        if not src_file.exists():
            continue
        dst_file = debug_dir / f"batch{batch}_d{date}.txt"
        dst_file2 = debug_dir / f"transcript_{date}.txt"
        
        shutil.copy2(src_file, dst_file)
        shutil.copy2(src_file2, dst_file2)

shutil.copy2('review.csv', debug_dir/"review.csv")
print(f"Copied debug files to: {debug_dir}")
