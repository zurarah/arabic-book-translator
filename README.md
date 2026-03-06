# 📖 Arabic Book Translator

Translate Arabic (MSA) books to English — purpose-built for formal Islamic scholarly works, particularly Shia jurisprudence.

Uses an LLM with a carefully crafted scholarly prompt and a built-in Islamic terminology glossary to produce consistent, accurate translations.

---

## ✨ Features

- **PDF / DOCX / TXT** — reads Arabic text from any of these formats via PyMuPDF and python-docx
- **Multi-provider** — supports **Gemini**, **OpenAI**, and **Anthropic** out of the box
- **Scholarly prompt** — maintains respectful academic tone, handles honorifics, Quranic verses, and hadith references
- **70+ term glossary** — built-in Islamic terminology glossary (honorifics, technical terms, Shia-specific vocabulary)
- **Smart chunking** — splits text at paragraph/sentence boundaries to stay within token limits
- **Rate-limit resilience** — automatic exponential back-off with jitter on transient API errors

---

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set your API key
export GOOGLE_API_KEY="your-key-here"

# Translate a book
python3 -m translator book.pdf -o translated.md
```

---

## 📋 Usage

```
python3 -m translator <input> [options]
```

| Option | Description | Default |
|---|---|---|
| `input` | Input file (`.txt`, `.pdf`, `.docx`) | *required* |
| `-o, --output` | Output file path | `<input>_translated.md` |
| `--provider` | `gemini`, `openai`, or `anthropic` | `gemini` |
| `--model` | Override the default model name | provider default |
| `--glossary` | Path to a custom glossary JSON | built-in |
| `--chunk-size` | Target tokens per chunk | `1500` |
| `--temperature` | Sampling temperature | `0.3` |
| `--delay` | Seconds between API calls | `4.0` |
| `--dry-run` | Test chunking without making API calls | — |

### Examples

```bash
# Translate a PDF with Gemini (default)
python3 -m translator kitab.pdf

# Use OpenAI instead
python3 -m translator risala.txt --provider openai --model gpt-4o

# Use Anthropic
python3 -m translator book.docx --provider anthropic

# Custom glossary + smaller chunks
python3 -m translator book.pdf --glossary my_terms.json --chunk-size 1000

# Dry run (test without API calls)
python3 -m translator book.pdf --dry-run
```

---

## 🔄 How It Works

```
┌─────────┐     ┌─────────┐     ┌───────────┐     ┌──────────┐
│  Read   │ ──▶ │  Chunk  │ ──▶ │ Translate │ ──▶ │  Write   │
│ PDF/TXT │     │  Text   │     │ via LLM   │     │ Markdown │
└─────────┘     └─────────┘     └───────────┘     └──────────┘
```

1. **Read** — extracts text from PDF (PyMuPDF), DOCX (python-docx), or plain .txt files
2. **Chunk** — splits into ~1500-token chunks at paragraph and sentence boundaries
3. **Translate** — sends each chunk to the LLM with the scholarly system prompt + glossary
4. **Write** — joins translated chunks and writes the output Markdown file

---

## 📚 Glossary

The built-in `glossary.json` provides 70+ preferred English renderings across three categories:

| Category | Examples |
|---|---|
| **Honorifics** | صلى الله عليه وآله → *(peace be upon him and his family)* |
| **Technical Terms** | الاجتهاد → *ijtihad (independent juridical reasoning)* |
| **Shia-specific** | أهل البيت → *Ahl al-Bayt (the Household of the Prophet)* |

Override or extend with `--glossary path/to/custom.json`:

```json
{
  "category_name": {
    "arabic_term": "english_equivalent"
  }
}
```

