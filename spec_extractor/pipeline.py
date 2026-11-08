"""Batch processing and the comparison table, independent of the UI."""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass

import pandas as pd

from spec_extractor.extraction import ExtractionError, SpecExtractor
from spec_extractor.quality import SpecWarning, completeness, plausibility_warnings
from spec_extractor.schemas import SPEC_FIELDS, CompressorSpecs

COMPARISON_COLUMNS = [
    "source_file",
    "model_name",
    *SPEC_FIELDS,
    "completeness",
    "warnings",
    "summary",
]


@dataclass(frozen=True)
class DatasheetResult:
    source_file: str
    specs: CompressorSpecs | None = None
    warnings: tuple[SpecWarning, ...] = ()
    error: str | None = None


def process_datasheets(
    files: Iterable[tuple[str, bytes]],
    extractor: SpecExtractor,
    interval_seconds: float = 0.0,
    sleep: Callable[[float], None] = time.sleep,
) -> Iterator[DatasheetResult]:
    """Extract each datasheet, yielding results as they complete.

    A failed file is recorded and skipped so the rest of the batch continues.
    ``interval_seconds`` spaces out requests to stay within API rate limits.
    """
    for index, (name, pdf_bytes) in enumerate(files):
        if index and interval_seconds > 0:
            sleep(interval_seconds)
        try:
            specs = extractor.extract(pdf_bytes)
        except ExtractionError as exc:
            yield DatasheetResult(source_file=name, error=str(exc))
            continue
        yield DatasheetResult(
            source_file=name, specs=specs, warnings=tuple(plausibility_warnings(specs))
        )


def comparison_frame(results: Iterable[DatasheetResult]) -> pd.DataFrame:
    """One row per datasheet with standardized units, for side-by-side comparison."""
    rows: list[dict[str, object]] = []
    for result in results:
        if result.specs is None:
            continue
        rows.append(
            {
                "source_file": result.source_file,
                **result.specs.model_dump(),
                "completeness": completeness(result.specs),
                "warnings": "; ".join(f"{w.field}: {w.message}" for w in result.warnings),
            }
        )
    return pd.DataFrame(rows, columns=COMPARISON_COLUMNS)


def to_csv_bytes(frame: pd.DataFrame) -> bytes:
    # utf-8-sig adds a BOM so Excel opens the file with the right encoding
    return frame.to_csv(index=False).encode("utf-8-sig")
