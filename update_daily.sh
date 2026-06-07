cd /home/ytee/test/GuruArena

export CUDNN_PATH="/home/ytee/test/GuruArena/venv/lib/python3.12/site-packages/nvidia/cudnn/lib"
export LD_LIBRARY_PATH="/home/ytee/test/GuruArena/venv/lib/python3.12/site-packages/nvidia/cudnn/lib"

venv/bin/python pipelines/transcript/generate_transcript.py
venv/bin/python pipelines/ocr_text/generate_ocr.py

venv/bin/python pipelines/llm/extract_instrument.py
venv/bin/python pipelines/llm/extract_classification.py
venv/bin/python pipelines/llm/extract_signal_evidence.py
venv/bin/python pipelines/llm/extract_signal_intent.py
