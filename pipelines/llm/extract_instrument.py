from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
import json
import os

from src.llm.mq_iterclass import iter_items_from_files_with_helpers
from src.llm.mq_pipeline import (
    build_batch_apps,
    build_ocr_text,
    list_batch_dates,
    list_transcript_files,
)
from template.template_20260525_2204 import (
    SCHEMA_INSTRUMENT_RULES_EXTRACT2 as schema,
    TradingInstrument as ts,
)
from tqdm import tqdm


load_dotenv()


TRANSCRIPT_GLOB = 'transcripts/clean/*'
OCR_JSON_FOLDER = 'ocr/json'
# MODEL = 'deepseek-v4-flash'
MODEL = 'mimo-v2.5-pro'
OUTPUT_PREFIX = '2026_05_17_t1'
BATCHES = range(3)


def build_helper(dt: str):
    helper = {}
    ocr_text = build_ocr_text(dt, OCR_JSON_FOLDER)
    if ocr_text:
        helper['ocr_text'] = ocr_text
    return json.dumps(helper, ensure_ascii=False)


def run(batch_dates=None, debug=False):
    apps = build_batch_apps(
        ts,
        schema,
        MODEL,
        OUTPUT_PREFIX,
        BATCHES,
        temperature=0,
    )
    errlist = []

    if batch_dates is None:
        batch_dates = list_batch_dates(TRANSCRIPT_GLOB)

    pbar = tqdm(batch_dates, desc='extract instrument', unit='day')
    for dt in pbar:
        files = list_transcript_files(dt)
        if not files:
            continue
        helpers = []
        for transcript_file in files:
            dt2 = os.path.basename(transcript_file).split('.')[0]
            helpers.append(build_helper(dt2))

        for batch, app in apps.items():
            try:
                pbar.set_postfix(dt=dt, batch=batch, files=len(files))
                app.run_batch_multiprocess(
                    iter_items_from_files_with_helpers(files, helpers=helpers),
                    show_progress=False,
                    force=debug,
                )
            except Exception as e:
                # pbar.write('error %s %s %s' % (dt, batch, e))
                errlist.append((dt, batch, str(e)))

    return errlist


if __name__ == '__main__':
    import datetime
    print(len(schema), datetime.datetime.now())
    MODEL = 'mimo-v2.5-pro'
    OUTPUT_PREFIX = '2026_05_17_t1'
    run()
    MODEL = 'deepseek-v4-pro'
    OUTPUT_PREFIX = '2026_05_17_t1'
    run()
