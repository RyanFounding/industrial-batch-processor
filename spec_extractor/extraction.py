"""Model-backed datasheet extraction."""

from __future__ import annotations

from typing import Protocol

from pydantic import ValidationError

from spec_extractor.schemas import CompressorSpecs

EXTRACTION_PROMPT = (
    "Extract the technical specifications from this equipment datasheet. "
    "If the datasheet covers a range of models, use the highest rated values. "
    "Leave any specification that is not stated as null; do not estimate."
)

MAX_PDF_BYTES = 20 * 1024 * 1024  # Gemini's limit for inline request data


# JSON-schema responses (response_mime_type + response_schema) are only available on the
# v1beta endpoint. Set it explicitly so a change in the SDK's default cannot break extraction.
GEMINI_API_VERSION = "v1beta"


class ExtractionError(RuntimeError):
    pass


class SpecExtractor(Protocol):
    def extract(self, pdf_bytes: bytes) -> CompressorSpecs: ...


class GeminiSpecExtractor:
    """Sends the PDF inline, so no copy is stored in Gemini's file service."""

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash") -> None:
        from google import genai
        from google.genai import types

        self._client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(api_version=GEMINI_API_VERSION),
        )
        self._model = model

    def extract(self, pdf_bytes: bytes) -> CompressorSpecs:
        from google.genai import types

        if len(pdf_bytes) > MAX_PDF_BYTES:
            raise ExtractionError("PDF is larger than the 20 MB request limit.")
        contents: list[types.PartUnionDict] = [
            types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
            types.Part.from_text(text=EXTRACTION_PROMPT),
        ]
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=CompressorSpecs,
                    temperature=0.0,
                ),
            )
        except Exception as exc:
            raise ExtractionError(f"Model request failed: {exc}") from exc

        if not response.text:
            raise ExtractionError("Model returned an empty response.")
        try:
            return CompressorSpecs.model_validate_json(response.text)
        except ValidationError as exc:
            raise ExtractionError("Model output did not match the specification schema.") from exc
