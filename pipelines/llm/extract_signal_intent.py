from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from collections import OrderedDict
from dotenv import load_dotenv
import json
from typing import Iterable, List, Optional
import re

from src.llm.mq_iterclass import texts_to_items2

from src.llm.mq_pipeline import (
    build_batch_apps,
    list_batch_dates,
)
from template.template_20260525_2204 import (
    SCHEMA_SIGNAL_INTENT_EXTRACT as schema,
    TradingSignal as template,
)
from tqdm import tqdm


load_dotenv()

TRANSCRIPT_GLOB = 'transcripts/clean/*'
SIGNAL_EVIDENCE_OUTPUT_PREFIX = '2026_05_17_signal'
SIGNAL_EVIDENCE_MODEL = 'deepseek-v4-pro'
SIGNAL_INTENT_OUTPUT_PREFIX = '2026_06_04_signal_intent'
SIGNAL_INTENT_MODEL = 'deepseek-v4-pro'
BATCHES = range(3)
EVIDENCE_ROOT = Path('outputs') / 'model_output'

def load_evidence_rows(dt: str) -> List[dict]:
    rows = []
    for batch in BATCHES:
        path = EVIDENCE_ROOT / f'{SIGNAL_EVIDENCE_OUTPUT_PREFIX}_{batch}_{SIGNAL_EVIDENCE_MODEL}/{dt}.json'
        if not path.exists():
            continue
        with open(path, 'r', encoding='utf-8-sig') as ifile:
            payload = json.load(ifile)
        rows.extend(payload.get('signals', []))
    return rows

def merge_evidence_rows(rows: Iterable[dict]) -> dict:
    merged = OrderedDict()

    for row in rows:
        if row['invalid']:
            continue
        instrument = row['instrument']
        instrument_normalized = row['instrument_normalized']
        key = (instrument_normalized, tuple(instrument))

        if key not in merged:
            merged[key] = []

        for evidence_type, evidence in row.items():
            if not '_evidence' in evidence_type:
                continue

            evidence_type = evidence_type.removesuffix('_evidence')
            for ev in evidence:
                ev2 = {'type' : evidence_type}
                ev2.update(ev)
                merged[key].append(ev2)

    ret = []
    for (instrument_normalized, instrument), ev in merged.items():
        ev2 = {
            'instrument_normalized': instrument_normalized,
            'instrument' : list(instrument),
            'evidence': sorted(ev, key=lambda x: x['type'])
        }
        ret.append(ev2)
    return ret


def run(batch_dates=None, debug=False):
    apps = build_batch_apps(
        template,
        schema,
        SIGNAL_INTENT_MODEL,
        SIGNAL_INTENT_OUTPUT_PREFIX,
        BATCHES,
        default_block_label='Input',
        temperature=0,
    )
    errlist = []

    if batch_dates is None:
        batch_dates = list_batch_dates(TRANSCRIPT_GLOB, dt_size=8)
        batch_dates = [x[:8] for x in batch_dates]

    dates = []
    texts = []
    pbar = tqdm(batch_dates, desc='build signal intent input', unit='day')
    for dt in pbar:
        raw = load_evidence_rows(dt)
        if not raw:
            continue
        payload = merge_evidence_rows(raw)
        if payload is None:
            continue
        dates.append(dt)
        texts.append(json.dumps(payload, ensure_ascii=False))

    for batch, app in apps.items():
        try:
            pbar.set_postfix(dt=dt, batch=batch, files=len(dates))
            app.run_batch_multiprocess(
                texts_to_items2(texts, dates),
                show_progress=False,
                force=debug,
            )
        except Exception as e:
            errlist.append((dt, batch, str(e)))

    return errlist

if __name__ == '__main__':
    import datetime
    
    batchlist = ["20211220","20211221","20211222","20211223","20211224","20211227","20211228","20211229","20251118","20260320","20260323","20260324","20260325","20260326","20260327","20260401","20260402"]
    batchlist=  batchlist[:4]
    batchlist = ['20211220']
    print(len(schema), datetime.datetime.now(), batchlist)
    
    run(batchlist, debug=True)

