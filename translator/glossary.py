"""Glossary loading, formatting, and post-processing utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

# Default glossary ships with the package
_DEFAULT_GLOSSARY_PATH = Path(__file__).resolve().parent.parent / "glossary.json"


def load_glossary(path: Optional[str] = None) -> Dict[str, Dict[str, str]]:
    """Load a glossary JSON file and return its contents.

    The JSON structure is:
        {
            "category_name": {
                "arabic_term": "english_equivalent",
                ...
            },
            ...
        }
    """
    glossary_path = Path(path) if path else _DEFAULT_GLOSSARY_PATH
    if not glossary_path.exists():
        return {}

    with open(glossary_path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def flatten_glossary(glossary: Dict[str, Dict[str, str]]) -> Dict[str, str]:
    """Flatten categorised glossary into a single {arabic: english} mapping."""
    flat: Dict[str, str] = {}
    for _category, terms in glossary.items():
        flat.update(terms)
    return flat


def format_glossary_for_prompt(glossary: Dict[str, Dict[str, str]]) -> str:
    """Format the glossary as a readable table to inject into the system prompt."""
    lines: list[str] = []
    for category, terms in glossary.items():
        # Human-friendly category header
        header = category.replace("_", " ").title()
        lines.append(f"\n### {header}")
        for arabic, english in terms.items():
            lines.append(f"- {arabic} → {english}")
    return "\n".join(lines)
