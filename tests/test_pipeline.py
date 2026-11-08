from __future__ import annotations

from spec_extractor.extraction import ExtractionError
from spec_extractor.pipeline import COMPARISON_COLUMNS, comparison_frame, process_datasheets
from spec_extractor.schemas import CompressorSpecs

ATLAS = CompressorSpecs(
    model_name="GA 15-30",
    max_supported_power_kw=30.0,
    cooling_medium="air",
    summary="Integrated dryer; oil-injected design needs oil maintenance.",
)
ROTREX = CompressorSpecs(
    model_name="EK40C",
    max_supported_power_kw=60.0,
    aerodynamic_efficiency_percent=0.78,
    summary="High power density for heavy-duty fuel cells.",
)


class FakeExtractor:
    def __init__(self, results: dict[bytes, CompressorSpecs | ExtractionError]) -> None:
        self.results = results

    def extract(self, pdf_bytes: bytes) -> CompressorSpecs:
        result = self.results[pdf_bytes]
        if isinstance(result, ExtractionError):
            raise result
        return result


def test_batch_isolates_failures_and_paces_requests() -> None:
    extractor = FakeExtractor({b"a": ATLAS, b"x": ExtractionError("timeout"), b"r": ROTREX})
    sleeps: list[float] = []

    results = list(
        process_datasheets(
            [("atlas.pdf", b"a"), ("broken.pdf", b"x"), ("rotrex.pdf", b"r")],
            extractor,
            interval_seconds=4,
            sleep=sleeps.append,
        )
    )

    assert [r.error for r in results] == [None, "timeout", None]
    assert sleeps == [4, 4]


def test_comparison_frame_has_one_row_per_datasheet() -> None:
    extractor = FakeExtractor({b"a": ATLAS, b"r": ROTREX})

    frame = comparison_frame(
        process_datasheets([("atlas.pdf", b"a"), ("rotrex.pdf", b"r")], extractor)
    )

    assert list(frame.columns) == COMPARISON_COLUMNS
    assert frame["model_name"].tolist() == ["GA 15-30", "EK40C"]
    assert frame.loc[0, "completeness"] == 0.33
    assert frame.loc[0, "warnings"] == ""
    assert "fraction" in str(frame.loc[1, "warnings"])


def test_empty_batch_keeps_columns() -> None:
    frame = comparison_frame([])

    assert frame.empty
    assert list(frame.columns) == COMPARISON_COLUMNS
