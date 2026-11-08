# Industrial Datasheet Batch Processor

Extracts technical specifications from a batch of vendor equipment datasheets (PDF) into one comparison table with standardized units.

Live demo: [insan-datasheet-batch.streamlit.app](https://insan-datasheet-batch.streamlit.app)

## Problem

Choosing equipment means comparing specifications across vendors, and every vendor publishes them differently. Power is listed in kW or hp, weight in kg or lb, efficiency as a percentage or a ratio, and the key figures can sit anywhere from page 1 to page 12. Engineers and procurement teams copy these values into a spreadsheet by hand, which is slow, error-prone, and makes it hard to tell a missing value from an overlooked one.

## Solution

Upload a set of datasheets. For each one, Gemini extracts a fixed set of compressor specifications, converts them to standard units, and leaves anything not stated in the datasheet empty instead of estimating it. The results are combined into one table, and each row gets two quality signals:

- **Completeness:** the share of comparison fields the datasheet actually states.
- **Plausibility warnings:** values that are physically impossible or likely in the wrong unit. A common case is efficiency extracted as 0.78 instead of 78%.

The table exports to CSV for Excel or further analysis.

## Architecture

```
PDF uploads
    |
    v
extraction.py   PDF sent inline to Gemini with a response schema -> CompressorSpecs (validated)
    |
    v
quality.py      completeness score, plausibility warnings
    |
    v
pipeline.py     batch loop with per-file error isolation and rate limiting -> comparison table -> CSV
    |
    v
industrial_app.py   Streamlit UI
```

| Module | Responsibility |
|---|---|
| `schemas.py` | The specification schema. Field descriptions include the unit conversions the model must apply. |
| `extraction.py` | The model call, behind a `SpecExtractor` protocol so it can be replaced in tests or swapped for another provider. |
| `quality.py` | Completeness and plausibility checks. Pure functions, no I/O. |
| `pipeline.py` | Batch processing and table building. Doesn't depend on Streamlit. |
| `industrial_app.py` | UI only. |

## Tech stack

| Choice | Why |
|---|---|
| Gemini 2.5 Flash | Reads long, multi-column PDFs with tables, and supports a JSON response schema. Temperature 0 for repeatable output. |
| Pydantic v2 | Optional typed fields keep "not stated" (null) separate from zero. The same model is the response schema and the validator. |
| pandas | Builds the comparison table and the CSV export. |
| Streamlit | Batch upload, progress feedback and download, hosted for free on Community Cloud. |
| pytest, ruff, mypy (strict) | CI runs lint, type checks and tests on every push. |

## Key technical decisions

- **Null over guessing.** Every numeric field is optional, and the model is told not to estimate. In an engineering comparison, an empty cell is safer than a plausible-looking invented number.
- **Units fixed in the schema.** Conversions such as hp to kW and lb to kg are part of the field descriptions, so every row in the table uses the same units.
- **Check what the model returns.** Completeness and plausibility are calculated in Python after extraction, so reviewers can see which values need checking against the source PDF.
- **Send PDFs inline.** An earlier version uploaded each PDF to Gemini's file storage and then deleted it. Sending the bytes with the request means no stored copy and no cleanup step.
- **Isolate errors per file.** One unreadable datasheet is reported and skipped; the rest of the batch still completes.

## Running locally

Requires Python 3.11 or newer.

```bash
git clone https://github.com/insan-sll/industrial-batch-processor.git
cd industrial-batch-processor
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env               # set GEMINI_API_KEY
export $(grep -v '^#' .env | xargs)
streamlit run industrial_app.py
```

Upload the PDFs in `samples/` to try it: a Rotrex fuel-cell compressor, an Atlas Copco GA rotary screw series and an ELGi reciprocating range. They cover very different machines, which shows how completeness varies between datasheets. A dev container is included for GitHub Codespaces.

### Configuration

| Variable | Default | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | none | Required. On Streamlit Cloud, set it in the app's secrets. |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Model used for extraction. |
| `REQUEST_INTERVAL_SECONDS` | `4` | Pause between requests, which keeps the free tier under 15 requests per minute. |

## Testing

```bash
pytest           # quality checks, batch pipeline and UI smoke tests; no API key needed
ruff check .
mypy
```

## Limitations

- The schema is built for compressors. Other equipment types need their own schema, though the pipeline and quality modules are generic.
- For datasheets that cover a model range, the highest rated values are extracted rather than one row per model.
- Plausibility checks catch impossible values and unit slips, not values that are plausible but wrong.
- The summary column is generated by the model and is not checked.
