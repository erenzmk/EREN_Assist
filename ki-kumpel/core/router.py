"""Zentrale Orchestrierung zwischen UI, Speicher und LLM."""
from __future__ import annotations

from typing import List

from PIL import Image

from core.logger import get_logger, log_line
from core.llm_client import LLMClient
from core.tts import speak
from memory.knowledge_builder import KnowledgeBuilder
from memory.memory_db import MemoryDB
from memory.style_profile import apply_style, build_style_profile

_logger = get_logger(__name__)


class AssistantRouter:
    def __init__(self) -> None:
        self.memory = MemoryDB()
        self.knowledge = KnowledgeBuilder(self.memory)
        self.style_profile = build_style_profile()
        self.llm = LLMClient()
        self._context_cache = self._load_context()
        self.knowledge.refresh_facts()

    def _load_context(self) -> List[str]:
        recent = self.memory.get_recent_interactions(limit=30)
        context = [
            f"{interaction.role.upper()} ({interaction.timestamp}): {interaction.content}" for interaction in reversed(recent)
        ]
        _logger.info("Kontext geladen (%d Einträge)", len(context))
        return context

    def _update_context(self) -> None:
        self._context_cache = self._load_context()

    def _record_interaction(self, role: str, content: str, meta: str | None = None) -> None:
        self.memory.add_interaction(role, content, meta)
        self._update_context()

    def _gather_facts(self, query: str) -> List[str]:
        self.knowledge.refresh_facts()
        return self.knowledge.get_relevant_facts(query)

    def handle_text(self, question: str) -> str:
        log_line(f"USER Frage (Text): {question}")
        self._record_interaction("user", question)
        facts = self._gather_facts(question)
        answer = self.llm.ask_text(
            question,
            context_messages=self._context_cache,
            facts=facts,
        )
        styled = apply_style(answer, self.style_profile)
        self._record_interaction("assistant", styled)
        log_line(f"ASSISTANT Antwort: {styled}")
        speak(styled)
        return styled

    def handle_vision(self, question: str, image: Image.Image) -> str:
        log_line(f"USER Frage (Vision): {question}")
        self._record_interaction("user", question, meta="vision")
        facts = self._gather_facts(question)
        answer = self.llm.ask_vision(
            question,
            image,
            context_messages=self._context_cache,
            facts=facts,
        )
        styled = apply_style(answer, self.style_profile)
        self._record_interaction("assistant", styled, meta="vision")
        log_line(f"ASSISTANT Antwort: {styled}")
        speak(styled)
        return styled

    def cleanup(self) -> None:
        self.memory.close()
