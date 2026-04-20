"""
summarize_data.py
-----------------
Summarization pipeline for Croatian legal documents.

Input:   data/normalized/<year>/<issue>/<doc>.json
Output:  same files, enriched with a "summaries" field (in-place update)

For each document that contains a 'doc_cleaned' field, this script generates:
  1. short_summary     – 3 extractive sentences (2–4 range)
  2. detailed_summary  – 8 extractive sentences (6–10 range)
  3. structured_summary:
       - što_zakon_uređuje  – 2 sentences focused on scope/purpose (opis + Član 1)
       - na_koga_se_odnosi  – 2 sentences focused on subjects (diverse selection)
       - što_uvodi_ili_mijenja – 2 sentences focused on changes (full text)

Output shape added to each document:
{
  "summaries": {
    "short": "...",
    "detailed": "...",
    "structured": {
      "što_zakon_uređuje": "...",
      "na_koga_se_odnosi": "...",
      "što_uvodi_ili_mijenja": "..."
    }
  }
}

The Summarizer uses extractive MMR-based summarization (classla/bcms-bertic).
The model is loaded once per run and shared across all document calls.
"""

import json
import sys
from pathlib import Path

import torch
from transformers import AutoTokenizer, AutoModel

# ---------------------------------------------------------------------------
# Resolve paths
# ---------------------------------------------------------------------------

# Script lives at:  services/summarizer/summarize_data.py
# Repo root is two levels up
_REPO_ROOT = Path(__file__).resolve().parents[2]
NORMALIZED_DIR = _REPO_ROOT / "data" / "normalized"

# Add services/summarizer to sys.path so we can import Summarizer
sys.path.insert(0, str(Path(__file__).resolve().parent))
from summarizer import Summarizer  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_scope_text(data: dict) -> str:
    """
    Build a focused text for 'što zakon uređuje' from:
      - opis (preamble)
      - text of the first article (Član 1.) if available
    Falls back to the full doc_cleaned if neither is available.
    """
    parts: list[str] = []

    opis = data.get("opis", "").strip()
    if opis:
        parts.append(opis)

    segments = data.get("doc_segmented", [])
    if segments:
        first = segments[0]
        for stavak in first.get("stavci", []):
            parts.extend(stavak.get("točke", []))

    if parts:
        return " ".join(parts)

    return data.get("doc_cleaned", "")


def _make_summarizer_with_shared_model(
    tokenizer, model, device: str
) -> Summarizer:
    """
    Return a Summarizer whose embed_texts reuses the already-loaded
    tokenizer and model instead of loading them fresh on every call.
    """
    summarizer = Summarizer()
    _orig_embed = summarizer.embed_texts

    def _embed_reuse(texts, _tok, _mdl, device=device):
        return _orig_embed(texts, tokenizer, model, device=device)

    summarizer.embed_texts = _embed_reuse
    return summarizer


# ---------------------------------------------------------------------------
# File-level processing
# ---------------------------------------------------------------------------


def process_file(path: Path, summarizer: Summarizer, device: str) -> None:
    """
    Load a normalized JSON, generate three summary types, and write back
    in-place with the new "summaries" key added.

    Skips files that have no 'doc_cleaned' field.
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    doc_cleaned = data.get("doc_cleaned", "").strip()
    if not doc_cleaned:
        print(f"  –  {path.name}: no doc_cleaned, skipping")
        return

    # ------------------------------------------------------------------
    # Short summary  (3 sentences → covers the 2–4 range)
    # ------------------------------------------------------------------
    short = summarizer.extractive_summary(
        doc_cleaned,
        num_sentences=3,
        lambda_param=0.75,   # balanced relevance / diversity
        device=device,
    )

    # ------------------------------------------------------------------
    # Detailed summary  (8 sentences → covers the 6–10 range)
    # ------------------------------------------------------------------
    detailed = summarizer.extractive_summary(
        doc_cleaned,
        num_sentences=8,
        lambda_param=0.65,   # slightly more diverse to cover more ground
        device=device,
    )

    # ------------------------------------------------------------------
    # Structured summary
    # ------------------------------------------------------------------

    # što zakon uređuje – preamble + Član 1 (purpose / scope)
    scope_text = _build_scope_text(data)
    što_uređuje = summarizer.extractive_summary(
        scope_text,
        num_sentences=2,
        lambda_param=0.80,   # prefer the most relevant sentences
        device=device,
    )

    # na koga se odnosi – high diversity to surface different subject mentions
    na_koga = summarizer.extractive_summary(
        doc_cleaned,
        num_sentences=2,
        lambda_param=0.45,   # lean toward diversity → surfaces different subjects
        device=device,
    )

    # što uvodi ili mijenja – balanced, full document
    što_uvodi = summarizer.extractive_summary(
        doc_cleaned,
        num_sentences=2,
        lambda_param=0.60,
        device=device,
    )

    # ------------------------------------------------------------------
    # Write back
    # ------------------------------------------------------------------
    data["summaries"] = {
        "short": short,
        "detailed": detailed,
        "structured": {
            "što_zakon_uređuje": što_uređuje,
            "na_koga_se_odnosi": na_koga,
            "što_uvodi_ili_mijenja": što_uvodi,
        },
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"  ✓  {path.relative_to(NORMALIZED_DIR)}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(force: bool = False) -> None:
    """
    Recursively process every .json file under NORMALIZED_DIR.

    Args:
        force: When True, re-summarize files that already have a 'summaries'
               field. When False (default), those files are skipped.
    """
    if not NORMALIZED_DIR.exists():
        print(f"ERROR: normalized data directory not found: {NORMALIZED_DIR}")
        return

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}\n")

    # Load model once and share across all file calls
    print(f"Loading model '{Summarizer.MODEL_NAME}' …")
    tokenizer = AutoTokenizer.from_pretrained(Summarizer.MODEL_NAME)
    model = AutoModel.from_pretrained(Summarizer.MODEL_NAME).to(device)
    model.eval()
    print("Model loaded.\n")

    summarizer = _make_summarizer_with_shared_model(tokenizer, model, device)

    json_files = sorted(NORMALIZED_DIR.rglob("*.json"))
    print(f"Found {len(json_files)} JSON file(s) in {NORMALIZED_DIR}\n")

    errors: list[tuple[Path, Exception]] = []
    skipped = 0

    for path in json_files:
        try:
            # Quick peek to check for existing summaries without full processing
            with open(path, encoding="utf-8") as f:
                peek = json.load(f)

            if not force and "summaries" in peek:
                skipped += 1
                continue

            process_file(path, summarizer, device)
        except Exception as exc:
            print(f"  ✗  {path}: {exc}")
            errors.append((path, exc))

    processed = len(json_files) - len(errors) - skipped
    print(
        f"\nDone. {processed} summarized, {skipped} skipped (already done), "
        f"{len(errors)} error(s)."
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate extractive summaries for normalized Croatian legal documents."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-summarize files that already have a 'summaries' field.",
    )
    args = parser.parse_args()
    main(force=args.force)
