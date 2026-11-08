from __future__ import annotations

import pytest

from spec_extractor.extraction import GEMINI_API_VERSION, GeminiSpecExtractor


def test_client_pins_the_json_schema_capable_api_version(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_client(**kwargs: object) -> object:
        captured.update(kwargs)
        return object()

    monkeypatch.setattr("google.genai.Client", fake_client)

    GeminiSpecExtractor(api_key="test-key")

    assert GEMINI_API_VERSION == "v1beta"
    assert captured["http_options"].api_version == "v1beta"  # type: ignore[attr-defined]
