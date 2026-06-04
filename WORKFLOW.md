# Workflow

This project currently works in 4 main steps:

1. Step 1: extract instrument
2. Step 2: classify instrument
3. Step 3: extract signal evidence
4. Step 4: extract signal intent

The key idea is:

- Step 1 answers: "what is the speaker talking about?"
- Step 2 answers: "how should we tag it in our taxonomy?"
- Step 3 answers: "which same-date transcript sentences can support a signal?"
- Step 4 answers: "what is the host's final trading intent from those hints?"

All 4 jobs should stay separate.

## Step 1

Entry:

- [pipelines/llm/extract_instrument.py](/home/ytee/test/GuruArena/pipelines/llm/extract_instrument.py)

Purpose:

- read transcript files
- extract financial instruments mentioned in the transcript
- normalize noisy mentions into a stable `instrument_normalized`

What Step 1 should do:

- identify the instrument from full transcript context
- normalize obvious ASR noise when confidence is high
- keep the normalized result close to what the speaker actually meant
- preserve a useful alias cluster from transcript raw values

What Step 1 should not do:

- should not over-resolve a generic concept into a very specific branded index
- should not invent a country, benchmark, or product wrapper unless transcript context really supports it
- should not turn a broad factor / sector / theme into a specific index just because such an index exists

Common failure mode in Step 1:

- over-normalization

Examples:

- `周期因子` should usually stay `周期因子`, not jump to `MSCI World Cyclical Sectors Index`
- `市值因子` should stay a generic factor concept, not a branded benchmark
- `四值因子` is likely ASR noise and should be corrected to `市值因子` if confidence is high
- `两年期的国债期货` should only become a US-specific treasury product if transcript context clearly supports that

## Step 2

Entry:

- [pipelines/llm/extract_classification.py](/home/ytee/test/GuruArena/pipelines/llm/extract_classification.py)
- schema lives in [template/template_20260525_2204.py](/home/ytee/test/GuruArena/template/template_20260525_2204.py)

Purpose:

- take `instrument_normalized`
- use aliases as supporting evidence
- map the instrument into the internal tag taxonomy

Current input shape:

```json
{
  "instrument_normalized": "...",
  "aliases": ["...", "..."]
}
```

What Step 2 should do:

- trust `instrument_normalized` first
- use aliases only as support, disambiguation, or ASR sanity check
- map the input into stable internal tags like:
  - `equity_benchmark`
  - `equity_sector11Financials`
  - `equity_sector25Banks`
  - `equity_factorSize`
  - `gov_2Y`
  - `cmd_soybean`
  - `fx_basket`

What Step 2 should not do:

- should not re-extract the transcript
- should not casually override a good normalized instrument
- should not invent a more specific entity than the normalized input supports

## Step 3

Entry:

- [pipelines/llm/extract_signal_evidence.py](/home/ytee/test/GuruArena/pipelines/llm/extract_signal_evidence.py)
- schema lives in [template/template_20260525_2204.py](/home/ytee/test/GuruArena/template/template_20260525_2204.py)

Purpose:

- read the full transcript for one date at a time
- take the helper generated after Step 1 and Step 2
- extract only the sentences that may contribute to final signal judgment
- keep evidence categorized so the final intent decision is auditable

Current helper shape:

```json
{
  "instruments": [
    {
      "instrument": ["美国股市", "标普500", "道琼指数"],
      "instrument_normalized": "equity_benchmark_USA"
    }
  ],
  "ocr_text": "..."
}
```

Step 3 output shape:

```json
{
  "signals": [
    {
      "instrument": ["美国股市", "标普500", "道琼指数"],
      "instrument_normalized": "equity_benchmark_USA",
      "direction_evidence": [],
      "action_evidence": [],
      "price_level_evidence": [],
      "technical_evidence": [],
      "conditional_evidence": [],
      "rhetoric_evidence": [],
      "negation_uncertainty_evidence": [],
      "other_evidence": [],
      "invalid": false,
      "invalid_reason": null
    }
  ]
}
```

What Step 3 should do:

- cover every helper item
- copy `instrument` and `instrument_normalized`
- extract continuous transcript substrings exactly into `text`
- summarize why each evidence item matters
- mark invalid when the helper item is merely mentioned, used as historical example, used as information source, or clearly mismatched

What Step 3 should not do:

- should not conclude the final intent
- should not merge views across dates
- should not re-classify or rewrite helper targets
- should not invent evidence not present in the transcript

## Step 4

Entry:

- [pipelines/llm/extract_signal_intent.py](/home/ytee/test/GuruArena/pipelines/llm/extract_signal_intent.py)
- schema lives in [template/template_20260525_2204.py](/home/ytee/test/GuruArena/template/template_20260525_2204.py)

Purpose:

- consume Step 3 signal evidence, grouped by date
- merge evidence batches `0-2` for the same date
- flatten `direction_evidence`, `action_evidence`, `price_level_evidence`, and other evidence buckets into one `evidence` list with a `type` field
- skip Step 3 rows marked `invalid`
- deduplicate repeated evidence hints by `type` and exact text
- conclude the final host intent for each helper item

Step 4 input shape:

```json
{
  "dt": "20230525",
  "signal_evidence": [
    {
      "instrument": ["美国股市", "标普500", "道琼指数"],
      "instrument_normalized": "equity_benchmark_USA",
      "evidence": [
        {
          "type": "direction",
          "text": "...",
          "summary": "..."
        }
      ]
    }
  ]
}
```

Step 4 output shape:

```json
{
  "signals": [
    {
      "instrument": ["美国股市", "标普500", "道琼指数"],
      "instrument_normalized": "equity_benchmark_USA",
      "intent": "open_sell",
      "evidence": ["..."],
      "summary": ["..."]
    }
  ]
}
```

What Step 4 should do:

- use only Step 3 evidence from the same date
- copy helper fields exactly
- output one or more final signals per helper item
- read evidence from `evidence[*].text`, using `evidence[*].type` as the evidence category
- merge repeated evidence supporting the same intent
- allow multiple intents only when the same helper item has genuinely different views
- use `invalid`, `unclear`, and `duplicate` as exclusive fallback labels

What Step 4 should not do:

- should not read transcript files directly
- should not use evidence from other dates
- should not add instruments outside the Step 3 evidence input
- should not rewrite `instrument` or `instrument_normalized`

Intent labels:

- `open_buy`: bullish exposure, buy, add, layout, or clear upside thesis
- `open_sell`: bearish exposure, sell, short, avoid due to downside thesis
- `close_buy`: reduce/avoid current long exposure, do not chase, wait, hold cash
- `close_sell`: reduce/avoid current short exposure, cover, do not keep shorting
- `unclear`: valid discussion but insufficient final trading intent
- `invalid`: not a usable trading discussion for this helper item
- `duplicate`: another helper item better represents the same discussion target

## Duplicate Handling

`duplicate` only applies across different helper items.

Typical cases:

- overlapping raw `instrument` wording
- local stock vs ADR for the same company
- a broad taxonomy target and a more specific country/tag target for the same discussion

Default preference:

- keep the local/origin-market stock over ADR unless the transcript clearly points to the ADR or US-listed line
- keep the more context-specific taxonomy target when the transcript makes geography or market scope clear

## Trust Hierarchy

The intended trust order through the pipeline is:

1. Transcript evidence
2. Step 1 normalized target
3. Step 2 taxonomy tag
4. Step 3 evidence summaries
5. conservative financial common knowledge only where the schema explicitly allows it

For Step 4 specifically, trust only current-date Step 3 evidence. This is the guardrail that prevents one date's intent from contaminating another date.

## Running

```bash
python pipelines/llm/extract_instrument.py
python pipelines/llm/extract_classification.py
python pipelines/llm/extract_signal_evidence.py
python pipelines/llm/extract_signal_intent.py
python pipelines/llm/visualize.py
```

## Summary

Short version:

- Step 1 is semantic extraction and normalization
- Step 2 is taxonomy tagging
- Step 3 is transcript-grounded evidence extraction
- Step 4 is same-date intent conclusion from evidence

If Step 3 stays evidence-only, Step 4 becomes easier to audit. If Step 4 only sees one date at a time, host intent does not leak across episodes.
