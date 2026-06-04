from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from collections import OrderedDict
from dotenv import load_dotenv
import json
import os
from typing import List

from src.llm.mq_iterclass import iter_items_from_files_with_helpers
from src.llm.mq_pipeline import (
    build_batch_apps,
    build_ocr_text,
    list_batch_dates,
    list_transcript_files,
)
from src.llm.mq_tag_summary import get_tag_summary
from template.template_20260525_2204 import (
    SCHEMA_EVIDENCE_EXTRACT as schema,
    SignalEvidence as template,
)
from tqdm import tqdm


load_dotenv()


TRANSCRIPT_GLOB = 'transcripts/clean/*'
OCR_JSON_FOLDER = 'ocr/json'
INSTRUMENT_OUTPUT_PREFIX = '2026_05_17_t1'
INSTRUMENT_MODEL = 'deepseek-v4-pro'
CLASSIFICATION_OUTPUT_PREFIX = 'class1_20260517'
CLASSIFICATION_MODEL = 'deepseek-v4-pro'
SIGNAL_MODEL = 'deepseek-v4-pro'
SIGNAL_OUTPUT_PREFIX = '2026_05_17_signal'
BATCHES = range(3)


def build_classification_map():
    return get_tag_summary(
        prefix=INSTRUMENT_OUTPUT_PREFIX,
        model=INSTRUMENT_MODEL,
        model_class=CLASSIFICATION_MODEL,
        classification_prefix=CLASSIFICATION_OUTPUT_PREFIX,
        batches=BATCHES,
    )['classification_map']


def load_instrument_rows(dt: str) -> List[dict]:
    rows = []
    for batch in BATCHES:
        instrument_path = os.path.join(
            'outputs',
            'model_output',
            f'{INSTRUMENT_OUTPUT_PREFIX}_{batch}_{INSTRUMENT_MODEL}',
            f'{dt}.json',
        )
        if not os.path.exists(instrument_path):
            continue

        try:
            with open(instrument_path, 'r', encoding='utf-8-sig') as ifile:
                payload = json.load(ifile)
        except Exception:
            continue

        rows.extend(payload.get('instruments', []))
    return rows


def build_instruments(dt: str, classification_map) -> List[dict]:
    helper_map = OrderedDict()

    for row in load_instrument_rows(dt):
        norm_inst = row['instrument_normalized']
        raw_inst = row['instrument']
        geography = row['geography']
        
        classified_rows = classification_map.get(norm_inst, [])
        for classified_row in classified_rows:
            instrument_normalized = classified_row['ua']
            ticker = classified_row.get('ticker')
            assert instrument_normalized, "missing instrument_normalized"
            if instrument_normalized in ['unclassified', 'unknown_stock']:
                continue
            if ticker:
                instrument_normalized = f'{instrument_normalized}_{ticker}'
            if geography.lower() in ['', 'unclear']:
                continue
            else:
                instrument_normalized = f'{instrument_normalized}_{geography}'

            if instrument_normalized not in helper_map:
                helper_map[instrument_normalized] = []
            if raw_inst not in helper_map[instrument_normalized]:
                helper_map[instrument_normalized].append(raw_inst)

    return [
        {
            'instrument': aliases,
            'instrument_normalized': instrument_normalized,
        }
        for instrument_normalized, aliases in helper_map.items()
        if aliases
    ]


def build_helper(dt: str, classification_map):
    helper = {
        'instruments': build_instruments(dt, classification_map),
    }
    ocr_text = build_ocr_text(dt, OCR_JSON_FOLDER)
    if ocr_text:
        helper['ocr_text'] = ocr_text
    return json.dumps(helper, ensure_ascii=False)


def run(batch_dates=None, debug=False):
    apps = build_batch_apps(
        template,
        schema,
        SIGNAL_MODEL,
        SIGNAL_OUTPUT_PREFIX,
        BATCHES,
        temperature=0,
    )
    classification_map = build_classification_map()
    errlist = []

    if batch_dates is None:
        batch_dates = list_batch_dates(TRANSCRIPT_GLOB)

    pbar = tqdm(batch_dates, desc='extract signal', unit='day')
    for dt in pbar:
        files = list_transcript_files(dt)
        if not files:
            continue
        helpers = []
        for transcript_file in files:
            dt2 = os.path.basename(transcript_file).split('.')[0]
            helpers.append(build_helper(dt2, classification_map))

        for batch, app in apps.items():
            try:
                pbar.set_postfix(dt=dt, batch=batch, files=len(files))
                app.run_batch_multiprocess(
                    iter_items_from_files_with_helpers(files, helpers=helpers),
                    show_progress=False,
                    force=debug,
                )
            except Exception as e:
                errlist.append((dt, batch, str(e)))

    return errlist


if __name__ == '__main__':
    # import datetime
    
    # batchlist = ["20211220","20211221","20211222","20211223","20211224","20211227","20211228","20211229","20251118","20260320","20260323","20260324","20260325","20260326","20260327","20260401","20260402"]
    # batchlist=  batchlist[:4]
    # # batchlist = ['20211223']
    # print(len(schema), datetime.datetime.now(), batchlist)
    # run(batchlist, debug=True)
    run()