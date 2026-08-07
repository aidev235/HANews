from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol

from hanews.config import ModelConfig


@dataclass(frozen=True)
class LLMResponse:
    data: dict[str, Any]
    requested_model: str
    actual_model: str
    provider: str
    response_id: str | None = None

    def model_log(self, task: str, configuration: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "task": task,
            "provider": self.provider,
            "requested_model": self.requested_model,
            "actual_model": self.actual_model,
            "configuration": configuration or {},
        }


class LLMClient(Protocol):
    def generate_json(
        self,
        *,
        task: str,
        model: ModelConfig,
        instructions: str,
        payload: dict[str, Any],
        schema: dict[str, Any],
    ) -> LLMResponse: ...


class OpenAIResponsesClient:
    """OpenAI Responses API adapter; imported lazily so deterministic tests need no SDK."""

    def __init__(self) -> None:
        self._client: Any | None = None

    def generate_json(
        self,
        *,
        task: str,
        model: ModelConfig,
        instructions: str,
        payload: dict[str, Any],
        schema: dict[str, Any],
    ) -> LLMResponse:
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError as exc:  # pragma: no cover - environment-specific
                raise RuntimeError(
                    "Install the 'openai' project dependency before generation"
                ) from exc
            self._client = OpenAI()
        response = self._client.responses.create(
            model=model.model,
            input=[
                {"role": "system", "content": instructions},
                {
                    "role": "user",
                    "content": json.dumps(payload, ensure_ascii=False, sort_keys=True),
                },
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": task.replace("-", "_")[:64],
                    "schema": schema,
                    "strict": True,
                }
            },
            temperature=model.temperature,
            store=False,
        )
        status = getattr(response, "status", None)
        if status and status != "completed":
            details = getattr(response, "incomplete_details", None)
            raise RuntimeError(f"Model response status was {status}: {details}")
        output_text = getattr(response, "output_text", "")
        if not output_text:
            raise RuntimeError("Model response contained no output_text")
        try:
            parsed = json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Model returned invalid JSON despite structured output") from exc
        if not isinstance(parsed, dict):
            raise RuntimeError("Model JSON output must be an object")
        return LLMResponse(
            data=parsed,
            requested_model=model.model,
            actual_model=str(getattr(response, "model", model.model)),
            provider=model.provider,
            response_id=str(getattr(response, "id", "")) or None,
        )
