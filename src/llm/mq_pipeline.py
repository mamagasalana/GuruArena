import glob
import json
import os
from typing import Dict, Iterable, List

from pydantic import BaseModel

from src.llm.openai_api import OPENAI_API, get_app_cls
from src.transcript.normalize_transcript import NormFinder


nf = NormFinder('')


def build_batch_apps(
    pydantic_template: BaseModel,
    schema: str,
    model: str,
    output_prefix: str,
    batches: Iterable[int],
    *,
    temperature: float = 0,
    default_block_label: str = 'Transcript',
) -> Dict[int, OPENAI_API]:
    app_cls = get_app_cls(model)
    apps: Dict[int, OPENAI_API] = {}
    for batch in batches:
        apps[batch] = app_cls(
            pydantic_template,
            '%s_%s' % (output_prefix, batch),
            schema,
            model=model,
            temperature=temperature,
            default_block_label=default_block_label,
        )
    return apps


def build_app(
    pydantic_template: BaseModel,
    schema: str,
    model: str,
    output_folder: str,
    *,
    temperature: float = 0,
    default_block_label: str = 'Transcript',
) -> OPENAI_API:
    app_cls = get_app_cls(model)
    return app_cls(
        pydantic_template=pydantic_template,
        output_folder=output_folder,
        schema=schema,
        default_block_label=default_block_label,
        model=model,
        temperature=temperature,
    )


def list_batch_dates(transcript_glob: str) -> List[str]:
    batch_date = set()
    for transcript_file in glob.glob(transcript_glob):
        dt = os.path.basename(transcript_file)[:7] + '*'
        batch_date.add(dt)
    return sorted(batch_date)


def list_transcript_files(dt: str, transcript_folder: str = 'transcripts/clean') -> List[str]:
    return sorted(glob.glob(f'{transcript_folder}/{dt}.txt'))


def chunk_rows(rows: List[dict], chunk_size: int) -> List[List[dict]]:
    return [rows[i:i + chunk_size] for i in range(0, len(rows), chunk_size)]


def build_ocr_text(dt: str, ocr_json_folder: str = 'ocr/json') -> str:
    ocr_path = os.path.join(ocr_json_folder, f'【{dt}】.json')
    if not os.path.exists(ocr_path):
        return ''

    try:
        with open(ocr_path, 'r', encoding='utf-8') as ifile:
            payload = json.load(ifile)
    except Exception:
        return ''

    try:
        sorted_items = sorted(payload['data'].items(), key=lambda x: x[0])
    except Exception:
        return ''

    snippets = []
    for _, entry in sorted_items:
        text_raw = entry.get('text_zh', [])
        if text_raw:
            snippets.append(''.join(text_raw))

    return nf.normalize_zh_transcript('\n\n'.join(snippets).strip())
