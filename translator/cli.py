"""CLI entry point for the Arabic Book Translator."""

from __future__ import annotations

import argparse
import sys

from rich.console import Console
from rich.panel import Panel

from translator import __version__
from translator.config import ModelConfig
from translator.engine import translate
from translator.file_io import default_output_path, read_file, write_output


console = Console()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="arabic-translator",
        description=(
            "Translate Modern Standard Arabic books to English, "
            "optimised for formal Islamic scholarly works (Shia jurisprudence)."
        ),
    )
    parser.add_argument(
        "input",
        help="Path to the input file (.txt, .pdf, or .docx)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help=(
            "Path for the translated output file. "
            "Defaults to <input>_translated.md"
        ),
    )
    parser.add_argument(
        "--provider",
        choices=["gemini", "openai", "anthropic"],
        default="gemini",
        help="LLM provider to use (default: gemini)",
    )
    parser.add_argument(
        "--model",
        default="",
        help=(
            "Model name (default: gemini-1.5-pro for Gemini, "
            "gpt-4o for OpenAI, "
            "claude-sonnet-4-20250514 for Anthropic)"
        ),
    )
    parser.add_argument(
        "--glossary",
        default=None,
        help="Path to a custom glossary JSON file (default: built-in glossary)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1500,
        help="Target tokens per chunk (default: 1500)",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.3,
        help="LLM sampling temperature (default: 0.3)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip API calls; test chunking and file I/O only",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=4.0,
        help="Seconds to wait between API calls to avoid rate-limiting (default: 4.0, set to 0 to disable)",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    # --- Header ---
    console.print(
        Panel(
            "[bold]Arabic Book Translator[/bold]\n"
            "[dim]MSA → English · Islamic Scholarly Works[/dim]",
            border_style="bright_blue",
        )
    )



    # --- Read input ---
    console.print(f"[cyan]📂 Reading:[/cyan] {args.input}")
    try:
        source_text = read_file(args.input)
    except (ValueError, FileNotFoundError, ImportError) as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        sys.exit(1)

    char_count = len(source_text)
    console.print(f"[dim]   {char_count:,} characters loaded[/dim]")

    if not source_text.strip():
        console.print("[bold red]Error:[/bold red] Input file is empty.")
        sys.exit(1)

    # --- Configure model ---
    cfg = ModelConfig(
        provider=args.provider,
        model=args.model,
        temperature=args.temperature,
        chunk_size=args.chunk_size,
        chunk_delay=args.delay,
    )

    # --- Translate ---
    translated = translate(
        text=source_text,
        cfg=cfg,
        glossary_path=args.glossary,
        dry_run=args.dry_run,
    )

    # --- Write output ---
    output_path = args.output or default_output_path(args.input)
    write_output(translated, output_path)
    console.print(f"[bold green]📝 Output written to:[/bold green] {output_path}")


if __name__ == "__main__":
    main()
