"""Analyse und Anwendung des Eren-Schreibstils."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from core.config import STYLE_SAMPLE_DIR
from core.logger import get_logger

_logger = get_logger(__name__)


@dataclass
class StyleProfile:
    rules: Dict[str, str] = field(default_factory=dict)
    examples: List[str] = field(default_factory=list)
    greeting: str = "Hallo zusammen"
    closing: str = "Viele Grüße\nEren"


def _load_samples() -> List[str]:
    samples: List[str] = []
    for sample_file in sorted(STYLE_SAMPLE_DIR.glob("*.txt")):
        try:
            samples.append(sample_file.read_text(encoding="utf-8"))
        except OSError as exc:
            _logger.error("Konnte Style-Sample nicht lesen: %s", exc)
    return samples


def _extract_greeting(samples: List[str]) -> str:
    for sample in samples:
        lines = [line.strip() for line in sample.strip().splitlines() if line.strip()]
        if not lines:
            continue
        first_line = lines[0]
        if first_line.lower().startswith(("hallo", "hi", "guten", "liebe")):
            return first_line.strip()
    return "Hallo zusammen"


def _extract_closing(samples: List[str]) -> str:
    for sample in samples:
        lines = [line.strip() for line in sample.strip().splitlines() if line.strip()]
        if len(lines) >= 2:
            closing = "\n".join(lines[-2:])
            if "grüße" in closing.lower() or "thanks" in closing.lower():
                return closing
    return "Viele Grüße\nEren"


def build_style_profile() -> StyleProfile:
    samples = _load_samples()
    rules = {
        "ton": "Direkt, lösungsorientiert, höflich und mit klaren Aufgaben.",
        "struktur": "Kurze Einleitung, Problem benennen, klare nächsten Schritte, Bitte um Rückmeldung.",
        "abschluss": "Immer mit freundlicher Grußformel und Namen enden.",
    }
    examples = [sample.strip() for sample in samples if sample.strip()]
    if not examples:
        examples.append(
            "Hallo zusammen,\n\nkurzes Update: Bitte prüft die CAD-Cases bis 10 Uhr und gebt mir eine Rückmeldung.\n\nViele Grüße\nEren"
        )

    greeting = _extract_greeting(samples)
    closing = _extract_closing(samples)

    profile = StyleProfile(rules=rules, examples=examples, greeting=greeting, closing=closing)
    _logger.info("StyleProfile geladen (%d Beispiele)", len(examples))
    return profile


def apply_style(raw_text: str, profile: StyleProfile | None = None) -> str:
    profile = profile or build_style_profile()

    body = raw_text.strip()
    if not body:
        return profile.greeting + "\n\n" + profile.closing

    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [body.replace("\n", " ")]

    adjusted: List[str] = []
    for para in paragraphs:
        para = para.replace("ich denke", "ich empfehle").replace("vielleicht", "bitte")
        if not para.endswith((".", "!", "?")):
            para += "."
        adjusted.append(para)

    result = [profile.greeting, "", *adjusted, "", profile.closing]
    return "\n".join(result)
