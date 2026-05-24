from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
import json

from src.llm.mq_iterclass import texts_to_items
from src.llm.mq_tag_summary import get_tag_summary
from src.llm.openai_api import get_app_cls
from template.template_20260424_2026 import (
    InstrumentTag as template,
    SCHEMA_INSTRUMENT_TAG_CLASSIFICATION2 as schema,
)


load_dotenv()


MODEL = 'deepseek-v4-flash' # model from instrument extraction
MODEL_CLASS = 'deepseek-v4-pro' # model for tag summary
INSTRUMENT_OUTPUT_PREFIX = '2026_04_24_t0'
CLASSIFICATION_OUTPUT_PREFIX = 'class4'
CHUNK_SIZE = 20


def pending_classification_inputs(prefix, model, model_class, classification_prefix):
    ret = get_tag_summary(
        prefix=prefix,
        model=model,
        model_class=model_class,
        classification_prefix=classification_prefix,
    )

    return [
        {
            'instrument_normalized': k,
            'aliases': sorted(v),
        }
        for k, v in sorted(ret['norm2raw'].items())
        if k not in ret['classification_map']
    ]


def chunk_inputs(rows, chunk_size=30):
    return [rows[i:i + chunk_size] for i in range(0, len(rows), chunk_size)]


def run():
    rows = pending_classification_inputs(
        prefix=INSTRUMENT_OUTPUT_PREFIX,
        model=MODEL,
        model_class=MODEL_CLASS,
        classification_prefix=CLASSIFICATION_OUTPUT_PREFIX,
        )
    chunks = chunk_inputs(rows, CHUNK_SIZE)
    texts = [json.dumps(chunk, ensure_ascii=False) for chunk in chunks]

    app_cls = get_app_cls(MODEL_CLASS)
    app = app_cls(
        pydantic_template=template,
        output_folder=CLASSIFICATION_OUTPUT_PREFIX,
        schema=schema,
        default_block_label='Input',
        model=MODEL_CLASS,
        temperature=0,
    )
    return app.run_batch_multiprocess(texts_to_items(texts))


if __name__ == '__main__':

    MODEL = 'mimo-v2.5-pro' # model from instrument extraction
    MODEL_CLASS = 'mimo-v2.5-pro' # model for tag summary
    INSTRUMENT_OUTPUT_PREFIX = '2026_05_17_t1'
    CLASSIFICATION_OUTPUT_PREFIX = 'class1_20260517'
    CHUNK_SIZE = 30
    run()

    MODEL = 'deepseek-v4-pro' # model from instrument extraction
    MODEL_CLASS = 'deepseek-v4-pro' # model for tag summary
    INSTRUMENT_OUTPUT_PREFIX = '2026_05_17_t1'
    CLASSIFICATION_OUTPUT_PREFIX = 'class1_20260517'
    CHUNK_SIZE = 30
    run()
