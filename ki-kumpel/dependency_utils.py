"""Hilfsfunktionen für das Laden von Python-Abhängigkeiten."""

from __future__ import annotations

import importlib
import importlib.util
from types import ModuleType
from typing import Dict, Iterable, List, Optional, Tuple

DependencySpec = Tuple[str, str]


def _import_module(module_path: str) -> Optional[ModuleType]:
    """Lädt ein Modul dynamisch, wenn es vorhanden ist."""
    try:
        spec = importlib.util.find_spec(module_path)
    except ModuleNotFoundError:
        return None
    if spec is None:
        return None
    return importlib.import_module(module_path)


def resolve_dependencies(
    required: Iterable[DependencySpec],
    optional: Iterable[DependencySpec] | None = None,
) -> Tuple[Dict[str, ModuleType], List[DependencySpec], List[DependencySpec]]:
    """Prüft obligatorische und optionale Module und gibt sie gesammelt zurück."""

    modules: Dict[str, ModuleType] = {}
    missing_required: List[DependencySpec] = []
    missing_optional: List[DependencySpec] = []

    for module_path, pip_name in required:
        module = _import_module(module_path)
        if module is None:
            missing_required.append((module_path, pip_name))
        else:
            modules[module_path] = module

    if optional:
        for module_path, pip_name in optional:
            module = _import_module(module_path)
            if module is None:
                missing_optional.append((module_path, pip_name))
            else:
                modules[module_path] = module

    return modules, missing_required, missing_optional


def format_dependency_list(dependencies: Iterable[DependencySpec]) -> str:
    """Formatiert eine Liste von Abhängigkeiten für die Konsolenausgabe."""
    return ", ".join(f"{module} (pip install {pip})" for module, pip in dependencies)

