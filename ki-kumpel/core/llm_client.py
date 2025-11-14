"""Kapselung aller LLM-Aufrufe."""
from __future__ import annotations

import base64
import io
import os
from typing import Iterable, List, Optional

from PIL import Image
from openai import OpenAI

from core.config import (
    DEFAULT_SYSTEM_PROMPT_TEXT,
    DEFAULT_SYSTEM_PROMPT_VISION,
    MODEL_TEXT,
    MODEL_VISION,
)
from core.logger import get_logger

_logger = get_logger(__name__)


class LLMClient:
    """Wrapper für das OpenAI SDK."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY ist nicht gesetzt")
        self._client = OpenAI(api_key=key)

    @staticmethod
    def _encode_image(image: Image.Image) -> str:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("ascii")

    def ask_text(
        self,
        question: str,
        *,
        context_messages: Iterable[str] | None = None,
        facts: Iterable[str] | None = None,
        temperature: float = 0.3,
    ) -> str:
        messages: List[dict] = [
            {"role": "system", "content": DEFAULT_SYSTEM_PROMPT_TEXT},
        ]

        if facts:
            fact_block = "\n".join(f"- {fact}" for fact in facts)
            messages.append(
                {
                    "role": "system",
                    "content": "Relevantes Hintergrundwissen:\n" + fact_block,
                }
            )

        if context_messages:
            for entry in context_messages:
                messages.append({"role": "system", "content": entry})

        messages.append({"role": "user", "content": question})

        _logger.info("Text-Anfrage an Modell %s", MODEL_TEXT)
        response = self._client.chat.completions.create(
            model=MODEL_TEXT,
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""

    def ask_vision(
        self,
        question: str,
        image: Image.Image,
        *,
        context_messages: Iterable[str] | None = None,
        facts: Iterable[str] | None = None,
        temperature: float = 0.3,
    ) -> str:
        encoded = self._encode_image(image)

        messages: List[dict] = [
            {"role": "system", "content": DEFAULT_SYSTEM_PROMPT_VISION},
        ]

        if facts:
            fact_block = "\n".join(f"- {fact}" for fact in facts)
            messages.append(
                {
                    "role": "system",
                    "content": "Relevantes Hintergrundwissen:\n" + fact_block,
                }
            )

        if context_messages:
            for entry in context_messages:
                messages.append({"role": "system", "content": entry})

        messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Hier ist ein Screenshot meines Bildschirms. "
                            "Nutze ihn zur Beantwortung der Frage. Frage: " + question
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": "data:image/png;base64," + encoded},
                    },
                ],
            }
        )

        _logger.info("Vision-Anfrage an Modell %s", MODEL_VISION)
        response = self._client.chat.completions.create(
            model=MODEL_VISION,
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""
