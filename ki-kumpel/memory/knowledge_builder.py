"""Ableitung zeitloser Fakten aus gespeicherten Interaktionen."""
from __future__ import annotations

import re
from typing import List

from core.logger import get_logger

from .memory_db import Fact, Interaction, MemoryDB

_logger = get_logger(__name__)

_KEYWORD_HINTS = {
    "cad": "CAD-Fälle müssen vor 10 Uhr gemeldet werden.",
    "techniker": "Techniker-Mails an dk-tech.eu enthalten obligatorische Einsatzdetails.",
    "dispatch": "Dispatch-Kommunikation erfolgt präzise und mit klaren Deadlines.",
    "backup": "Regelmäßige Backups der Projektdaten sind Pflicht.",
}

_IMPORTANT_PHRASES = ("muss", "müssen", "soll", "sollen", "wichtig", "immer")

_SENTENCE_SPLIT = re.compile(r"[.!?]\s+")


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).lower()


def _extract_sentences(message: str) -> List[str]:
    message = message.strip()
    if not message:
        return []
    sentences = _SENTENCE_SPLIT.split(message)
    if len(sentences) == 1:
        return [message]
    return [sent.strip() for sent in sentences if sent.strip()]


class KnowledgeBuilder:
    def __init__(self, db: MemoryDB) -> None:
        self._db = db

    def refresh_facts(self) -> List[Fact]:
        seen_normalised = {_normalise(f.fact): f for f in self._db.get_facts()}
        new_facts: List[Fact] = []

        for interaction in self._db.iter_interactions():
            sentences = _extract_sentences(interaction.content)
            for sentence in sentences:
                lower = sentence.lower()
                if not any(phrase in lower for phrase in _IMPORTANT_PHRASES):
                    continue
                normalised = _normalise(sentence)
                if normalised in seen_normalised:
                    continue
                fact_text = sentence.strip()
                self._db.add_fact(
                    source=f"interaction:{interaction.timestamp}",
                    fact=fact_text,
                    importance=2,
                )
                stored = Fact(
                    timestamp="",  # wird aus DB nicht direkt zurückgegeben
                    source=f"interaction:{interaction.timestamp}",
                    fact=fact_text,
                    importance=2,
                )
                seen_normalised[normalised] = stored
                new_facts.append(stored)

        for keyword, template in _KEYWORD_HINTS.items():
            normalised_template = _normalise(template)
            if normalised_template not in seen_normalised:
                self._db.add_fact(source="heuristic", fact=template, importance=1)
                stored = Fact(timestamp="", source="heuristic", fact=template, importance=1)
                seen_normalised[normalised_template] = stored
                new_facts.append(stored)

        _logger.info("KnowledgeBuilder: %s neue Fakten", len(new_facts))
        return new_facts

    def get_relevant_facts(self, query: str, limit: int = 5) -> List[str]:
        query_lower = query.lower()
        scored: List[tuple[int, Fact]] = []
        for fact in self._db.get_facts():
            score = 0
            for token in re.findall(r"\w+", fact.fact.lower()):
                if token in query_lower:
                    score += 2
            if fact.source.startswith("interaction"):
                score += 1
            score += fact.importance
            if score:
                scored.append((score, fact))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [fact.fact for score, fact in scored[:limit]]


def get_relevant_facts(db: MemoryDB, query: str, limit: int = 5) -> List[str]:
    builder = KnowledgeBuilder(db)
    return builder.get_relevant_facts(query, limit=limit)
