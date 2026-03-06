"""Configuration: prompt templates, model defaults, and settings."""

from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------------------
# System prompt — the core scholarly translation instruction
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are an expert translator specializing in Modern Standard Arabic (MSA) to English translation \
of formal Islamic scholarly texts, with deep expertise in Shia jurisprudence (fiqh Jaʿfari).

Your task is to translate the provided Arabic text into clear, accurate, and fluent English while \
adhering to the following guidelines:

1. **Tone & Register**: Maintain the respectful, academic tone of the original. The output should \
read as a polished English-language scholarly work — not a casual paraphrase.

2. **Religious Honorifics**: Render Arabic honorifics using their conventional English equivalents \
in parentheses after the name. For example:
   - صلى الله عليه وآله وسلم → (peace be upon him and his family)
   - عليه السلام → (peace be upon him)
   - قدس سره → (may his soul be sanctified)

3. **Technical Terminology**: Use the established English transliteration followed by a brief \
gloss on first occurrence. For example:
   - الاجتهاد → ijtihad (independent juridical reasoning)
   After the first occurrence, use the transliterated term alone.

4. **Quranic Verses & Hadith**: When the source quotes the Quran, provide an accurate English \
rendering of the meaning (not a literal word-for-word translation) and note the surah and ayah \
number. For hadith, preserve the chain of narration (sanad) references faithfully.

5. **Structure & Formatting**: Preserve the structural hierarchy of the original text — chapter \
headings, section breaks, numbered points, and footnotes.

6. **Accuracy over Elegance**: When there is tension between a more elegant phrasing and a more \
accurate one, prioritize accuracy. Do not omit or summarize any part of the source text.

7. **Translator's Notes**: If a passage is ambiguous or requires cultural context for an English \
reader, add a brief translator's note in square brackets, e.g., [Translator's note: ...].
"""

# ---------------------------------------------------------------------------
# Glossary injection addendum (appended when a glossary is loaded)
# ---------------------------------------------------------------------------

GLOSSARY_ADDENDUM_TEMPLATE = """\

The following glossary of preferred English equivalents MUST be used consistently throughout \
the translation. Use these exact renderings whenever the corresponding Arabic term appears:

{glossary_text}
"""

# ---------------------------------------------------------------------------
# User-message wrapper
# ---------------------------------------------------------------------------

USER_PROMPT_TEMPLATE = """\
Translate the following Arabic text to English. Output ONLY the English translation, preserving \
all paragraph breaks and structural formatting. Do not include the original Arabic.

---

{chunk}
"""

# ---------------------------------------------------------------------------
# Model configuration
# ---------------------------------------------------------------------------

@dataclass
class ModelConfig:
    """Configuration for the LLM provider and model."""

    provider: str = "gemini"          # "gemini", "openai", or "anthropic"
    model: str = ""                   # resolved at runtime if empty
    temperature: float = 0.3          # low temperature for faithful translation
    max_output_tokens: int = 4096
    chunk_size: int = 1500            # target tokens per chunk
    chunk_delay: float = 4.0          # seconds between API calls (rate-limit guard)

    # provider-specific defaults
    GEMINI_DEFAULT_MODEL: str = field(default="gemini-3.1-flash-lite-preview", repr=False)
    OPENAI_DEFAULT_MODEL: str = field(default="gpt-4o", repr=False)
    ANTHROPIC_DEFAULT_MODEL: str = field(default="claude-sonnet-4-20250514", repr=False)

    def resolved_model(self) -> str:
        """Return the model name, falling back to the provider default."""
        if self.model:
            return self.model
        if self.provider == "anthropic":
            return self.ANTHROPIC_DEFAULT_MODEL
        if self.provider == "openai":
            return self.OPENAI_DEFAULT_MODEL
        return self.GEMINI_DEFAULT_MODEL
