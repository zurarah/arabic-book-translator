"""Translation engine: chunked LLM-powered Arabic → English translation."""

from __future__ import annotations

import os
import random
import time
from typing import List, Optional

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
)

from translator.config import (
    GLOSSARY_ADDENDUM_TEMPLATE,
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
    ModelConfig,
)
from translator.file_io import chunk_text
from translator.glossary import format_glossary_for_prompt, load_glossary

console = Console()

# ---------------------------------------------------------------------------
# Retry helper
# ---------------------------------------------------------------------------

MAX_RETRIES = 10
INITIAL_BACKOFF = 4  # seconds


def _retry_with_backoff(fn, retries: int = MAX_RETRIES):
    """Call *fn* with exponential back-off + jitter on transient errors."""
    for attempt in range(retries):
        try:
            return fn()
        except Exception as exc:
            # Catch rate-limit / transient server errors
            err_str = str(exc).lower()
            if any(
                kw in err_str
                for kw in ("rate", "limit", "429", "500", "502", "503", "overloaded")
            ):
                wait = INITIAL_BACKOFF * (2 ** attempt) + random.uniform(0, 2)
                console.print(
                    f"  [yellow]⏳ Rate-limited (attempt {attempt + 1}/{retries}), "
                    f"retrying in {wait:.1f}s…[/yellow]"
                )
                time.sleep(wait)
            else:
                raise
    raise RuntimeError(f"Failed after {retries} retries.")


# ---------------------------------------------------------------------------
# Provider-specific translation calls
# ---------------------------------------------------------------------------

def _translate_chunk_gemini(
    chunk: str,
    system_prompt: str,
    cfg: ModelConfig,
) -> str:
    """Translate a single chunk using the Google Gemini API."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
    user_msg = USER_PROMPT_TEMPLATE.format(chunk=chunk)

    def _call():
        resp = client.models.generate_content(
            model=cfg.resolved_model(),
            contents=user_msg,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=cfg.temperature,
                max_output_tokens=cfg.max_output_tokens,
            ),
        )
        return resp.text.strip()

    return _retry_with_backoff(_call)


def _translate_chunk_openai(
    chunk: str,
    system_prompt: str,
    cfg: ModelConfig,
) -> str:
    """Translate a single chunk using the OpenAI API."""
    from openai import OpenAI

    client = OpenAI()  # uses OPENAI_API_KEY env var
    user_msg = USER_PROMPT_TEMPLATE.format(chunk=chunk)

    def _call():
        resp = client.chat.completions.create(
            model=cfg.resolved_model(),
            temperature=cfg.temperature,
            max_tokens=cfg.max_output_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
        )
        return resp.choices[0].message.content.strip()

    return _retry_with_backoff(_call)


def _translate_chunk_anthropic(
    chunk: str,
    system_prompt: str,
    cfg: ModelConfig,
) -> str:
    """Translate a single chunk using the Anthropic API."""
    from anthropic import Anthropic

    client = Anthropic()  # uses ANTHROPIC_API_KEY env var
    user_msg = USER_PROMPT_TEMPLATE.format(chunk=chunk)

    def _call():
        resp = client.messages.create(
            model=cfg.resolved_model(),
            max_tokens=cfg.max_output_tokens,
            temperature=cfg.temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_msg}],
        )
        return resp.content[0].text.strip()

    return _retry_with_backoff(_call)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def translate(
    text: str,
    cfg: ModelConfig,
    glossary_path: Optional[str] = None,
    dry_run: bool = False,
) -> str:
    """Translate a full Arabic text to English.

    Parameters
    ----------
    text:
        The complete Arabic source text.
    cfg:
        Model / provider configuration.
    glossary_path:
        Path to a custom glossary JSON. ``None`` uses the built-in glossary.
    dry_run:
        If ``True``, skip API calls and return placeholder text (for testing).

    Returns
    -------
    str
        The complete English translation, chunks joined by double newlines.
    """
    # 1. Build system prompt (with glossary if available)
    glossary = load_glossary(glossary_path)
    system_prompt = SYSTEM_PROMPT
    if glossary:
        glossary_text = format_glossary_for_prompt(glossary)
        system_prompt += GLOSSARY_ADDENDUM_TEMPLATE.format(glossary_text=glossary_text)

    # 2. Chunk the source text
    chunks = chunk_text(text, max_tokens=cfg.chunk_size)
    total = len(chunks)

    console.print(
        f"\n[bold green]📖 Source text split into {total} chunk(s) "
        f"(~{cfg.chunk_size} tokens each)[/bold green]"
    )
    console.print(
        f"[dim]   Provider: {cfg.provider} | Model: {cfg.resolved_model()}[/dim]\n"
    )

    if dry_run:
        console.print("[yellow]🔸 Dry-run mode — skipping API calls[/yellow]\n")
        translated_chunks = [
            f"[DRY RUN] Translated chunk {i + 1}/{total}\n\n"
            f"(Original {len(c)} chars)"
            for i, c in enumerate(chunks)
        ]
        return "\n\n".join(translated_chunks)

    # 3. Pick the provider function
    if cfg.provider == "anthropic":
        translate_fn = _translate_chunk_anthropic
    elif cfg.provider == "openai":
        translate_fn = _translate_chunk_openai
    else:
        translate_fn = _translate_chunk_gemini

    # 4. Translate each chunk with a progress bar
    translated_chunks: List[str] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Translating…", total=total)
        for i, chunk in enumerate(chunks):
            progress.update(task, description=f"Chunk {i + 1}/{total}")
            translated = translate_fn(chunk, system_prompt, cfg)
            translated_chunks.append(translated)
            progress.advance(task)
            # Proactive delay between chunks to avoid rate-limiting
            if i < total - 1 and cfg.chunk_delay > 0:
                time.sleep(cfg.chunk_delay)

    console.print("\n[bold green]✅ Translation complete![/bold green]\n")
    return "\n\n".join(translated_chunks)
