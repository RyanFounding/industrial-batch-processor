"""Streamlit front end for the datasheet batch processor."""

from __future__ import annotations

import os

import streamlit as st

from spec_extractor.extraction import GeminiSpecExtractor
from spec_extractor.pipeline import (
    DatasheetResult,
    comparison_frame,
    process_datasheets,
    to_csv_bytes,
)

st.set_page_config(page_title="Insan | Datasheet Batch", layout="wide")
st.title("Industrial Datasheet Batch Processor")
st.write(
    "Upload compressor datasheets as PDF to build one comparison table with "
    "standardized units. Missing values stay empty instead of being estimated."
)

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    st.error("GEMINI_API_KEY is not set. Add it to the environment or to Streamlit secrets.")
    st.stop()

model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
interval = float(os.environ.get("REQUEST_INTERVAL_SECONDS", "4"))


@st.cache_resource
def get_extractor(key: str, model_name: str) -> GeminiSpecExtractor:
    return GeminiSpecExtractor(api_key=key, model=model_name)


uploaded = st.file_uploader("Equipment datasheets (PDF)", type=["pdf"], accept_multiple_files=True)

if uploaded and st.button("Extract specifications", type="primary"):
    extractor = get_extractor(api_key, model)
    results: list[DatasheetResult] = []
    progress = st.progress(0.0, text="Starting...")

    files = ((f.name, f.getvalue()) for f in uploaded)
    for done, result in enumerate(process_datasheets(files, extractor, interval), start=1):
        results.append(result)
        if result.error:
            st.warning(f"{result.source_file}: extraction failed ({result.error})")
        progress.progress(done / len(uploaded), text=f"Processed {done} of {len(uploaded)}")
    progress.empty()

    table = comparison_frame(results)
    if table.empty:
        st.error("No datasheets were extracted successfully.")
        st.stop()

    st.subheader("Specification comparison")
    st.caption(
        "Completeness is the share of comparison fields the datasheet states. "
        "Warnings flag values that look implausible and should be checked against the PDF. "
        "The summary column is model-generated."
    )
    st.dataframe(
        table,
        hide_index=True,
        column_config={
            "completeness": st.column_config.ProgressColumn(
                "completeness", min_value=0.0, max_value=1.0, format="percent"
            )
        },
    )
    st.download_button(
        "Download comparison CSV",
        data=to_csv_bytes(table),
        file_name="datasheet_comparison.csv",
        mime="text/csv",
        type="primary",
    )
