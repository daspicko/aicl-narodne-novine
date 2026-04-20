"""
summarize_data.py
-----------------
Summarization pipeline for Croatian legal documents.

Input:   data/normalized/<year>/<issue>/<doc>.json
Output:  data/summarized/<year>/<issue>/<doc>.json  (mirror tree, never mutates normalized)

For each document that contains a 'doc_cleaned' field, this script generates:
  1. short_summary     – 3 extractive sentences (2–4 range)
  2. detailed_summary  – 8 extractive sentences (6–10 range)
  3. structured_summary:
       - što_zakon_uređuje  – 2 sentences focused on scope/purpose (opis + first Član)
       - na_koga_se_odnosi  – 2 sentences focused on subjects (diverse selection)
       - što_uvodi_ili_mijenja – 2 sentences focused on changes (full text)

Output shape added to each document:
{
  "summaries": {
    "short": "...",
    "detailed": "...",
    "structured": {
      "sto_zakon_ureduje": "...",
      "na_koga_se_odnosi": "...",
      "sto_uvodi_ili_mijenja": "..."
    }
  }
}

The Summarizer uses extractive MMR-based summarization (classla/bcms-bertic).
The model is loaded once per run and shared across all document calls.

Note: The doc_segmented structure has changed from:
  [{"članak": "...", "stavci": [...]}]
To:
  [{"glava": "...", "članci": [{"članak": "...", "stavci": [...]}]}]
"""

from dotenv import load_dotenv

load_dotenv()

import json
import sys
from pathlib import Path
import torch
from transformers import AutoTokenizer, AutoModel

# Maximum number of sentences embedded in a single forward pass.
# Lower this if you still hit OOM on your GPU.
_EMBED_BATCH_SIZE = 16

# Documents with more sentences than this threshold are split into chunks
# and summarized via map-reduce before a final synthesis pass.
_CHUNK_SENTENCE_LIMIT = 80

# ---------------------------------------------------------------------------
# Resolve paths
# ---------------------------------------------------------------------------

# Script lives at:  services/summarizer/summarize_data.py
# Repo root is two levels up
_REPO_ROOT = Path(__file__).resolve().parents[2]
NORMALIZED_DIR = _REPO_ROOT / "data" / "normalized"
SUMMARIZED_DIR = _REPO_ROOT / "data" / "summarized"

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
        first_chapter = segments[0]
        first_clanak = first_chapter.get("članci", [])[0]
        for stavak in first_clanak.get("stavci", []):
            parts.extend(stavak.get("točke", []))

    if parts:
        return " ".join(parts)

    return data.get("doc_cleaned", "")


def _make_summarizer_with_shared_model(tokenizer, model, device: str) -> Summarizer:
    """
    Return a Summarizer that reuses a single pre-loaded tokenizer + model for
    every call, avoiding repeated HuggingFace API hits and model reloads.

    Two methods are patched on the instance:
      - embed_texts      – batched embedding to avoid CUDA OOM
      - extractive_summary – bypasses the internal from_pretrained calls
    """
    summarizer = Summarizer()
    _orig_embed = summarizer.embed_texts

    # ------------------------------------------------------------------
    # Batched embed_texts – avoids OOM on large sentence sets
    # ------------------------------------------------------------------
    def _embed_batched(texts: list[str], _tok, _mdl, device=device) -> torch.Tensor:
        all_embeddings: list[torch.Tensor] = []
        for start in range(0, len(texts), _EMBED_BATCH_SIZE):
            batch = texts[start : start + _EMBED_BATCH_SIZE]
            emb = _orig_embed(batch, tokenizer, model, device=device)
            all_embeddings.append(emb.cpu())
            if device == "cuda":
                torch.cuda.empty_cache()
        combined = torch.cat(all_embeddings, dim=0)
        return combined.to(device)

    summarizer.embed_texts = _embed_batched

    # ------------------------------------------------------------------
    # extractive_summary – skip internal from_pretrained, use shared model
    # ------------------------------------------------------------------
    def _extractive_summary_no_reload(
        text: str,
        num_sentences: int = 3,
        lambda_param: float = 0.7,
        device: str = device,
    ) -> str:
        sentences = summarizer.split_sentences(text)
        if len(sentences) <= num_sentences:
            return text

        sentence_embeddings = _embed_batched(sentences, None, None, device=device)
        doc_embedding = _embed_batched([text], None, None, device=device)

        selected_indices = summarizer.mmr_select(
            sentence_embeddings,
            doc_embedding,
            num_sentences=num_sentences,
            lambda_param=lambda_param,
        )
        return " ".join(sentences[i] for i in selected_indices)

    summarizer.extractive_summary = _extractive_summary_no_reload
    return summarizer


# ---------------------------------------------------------------------------
# Map-reduce summarization for long documents
# ---------------------------------------------------------------------------


def _chunk_sentences(sentences: list[str], chunk_size: int) -> list[list[str]]:
    """Split a flat sentence list into overlapping chunks of *chunk_size*."""
    chunks: list[list[str]] = []
    step = max(1, chunk_size - 5)  # 5-sentence overlap between chunks
    for start in range(0, len(sentences), step):
        chunk = sentences[start : start + chunk_size]
        if chunk:
            chunks.append(chunk)
    return chunks


def _summarize_long(
    text: str,
    summarizer: Summarizer,
    num_sentences: int,
    lambda_param: float,
    device: str,
) -> str:
    """
    Map-reduce extractive summary for texts that exceed _CHUNK_SENTENCE_LIMIT.

    1. Split the document into overlapping sentence chunks.
    2. Extract a mini-summary (3 sentences) from each chunk  → map step.
    3. Concatenate mini-summaries into an intermediate text.
    4. Extract the final *num_sentences* from the intermediate text → reduce step.
    """
    sentences = summarizer.split_sentences(text)

    if len(sentences) <= _CHUNK_SENTENCE_LIMIT:
        return summarizer.extractive_summary(
            text, num_sentences=num_sentences, lambda_param=lambda_param, device=device
        )

    chunks = _chunk_sentences(sentences, _CHUNK_SENTENCE_LIMIT)
    chunk_summaries: list[str] = []
    for chunk_sents in chunks:
        chunk_text = " ".join(chunk_sents)
        mini = summarizer.extractive_summary(
            chunk_text,
            num_sentences=3,
            lambda_param=lambda_param,
            device=device,
        )
        chunk_summaries.append(mini)
        if device == "cuda":
            torch.cuda.empty_cache()

    intermediate = " ".join(chunk_summaries)
    result = summarizer.extractive_summary(
        intermediate,
        num_sentences=num_sentences,
        lambda_param=lambda_param,
        device=device,
    )
    if device == "cuda":
        torch.cuda.empty_cache()
    return result


# ---------------------------------------------------------------------------
# File-level processing
# ---------------------------------------------------------------------------


def process_file(path: Path, summarizer: Summarizer, device: str) -> None:
    """
    Load a normalized JSON, generate three summary types, and write the
    enriched document to data/summarized/ (mirroring the normalized tree).

    The source file under data/normalized/ is never modified.
    Skips files that have no 'doc_cleaned' field.
    Long documents are handled via map-reduce chunking to avoid CUDA OOM.
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    doc_cleaned = data.get("doc_cleaned", "").strip()
    if not doc_cleaned:
        print(f"  –  {path.name}: no doc_cleaned, skipping")
        return

    def _summarize(text: str, num_sentences: int, lambda_param: float) -> str:
        return _summarize_long(text, summarizer, num_sentences, lambda_param, device)

    # ------------------------------------------------------------------
    # Short summary  (3 sentences → covers the 2–4 range)
    # ------------------------------------------------------------------
    short = _summarize(doc_cleaned, num_sentences=3, lambda_param=0.75)

    # ------------------------------------------------------------------
    # Detailed summary  (8 sentences → covers the 6–10 range)
    # ------------------------------------------------------------------
    detailed = _summarize(doc_cleaned, num_sentences=8, lambda_param=0.65)

    # ------------------------------------------------------------------
    # Structured summary
    # ------------------------------------------------------------------

    # što zakon uređuje – preamble + Član 1 (purpose / scope)
    scope_text = _build_scope_text(data)
    sto_ureduje = _summarize(scope_text, num_sentences=2, lambda_param=0.80)

    # na koga se odnosi – high diversity to surface different subject mentions
    na_koga = _summarize(doc_cleaned, num_sentences=2, lambda_param=0.45)

    # što uvodi ili mijenja – balanced, full document
    sto_uvodi = _summarize(doc_cleaned, num_sentences=2, lambda_param=0.60)

    # ------------------------------------------------------------------
    # Write to data/summarized/ (mirrors the normalized tree)
    # ------------------------------------------------------------------
    data["summaries"] = {
        "short": short,
        "detailed": detailed,
        "structured": {
            "sto_zakon_ureduje": sto_ureduje,
            "na_koga_se_odnosi": na_koga,
            "sto_uvodi_ili_mijenja": sto_uvodi,
        },
    }

    relative = path.relative_to(NORMALIZED_DIR)
    out_path = SUMMARIZED_DIR / relative
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    if device == "cuda":
        torch.cuda.empty_cache()

    print(f"  ✓  {relative}")


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
    print(f"Input:  {NORMALIZED_DIR}")
    print(f"Output: {SUMMARIZED_DIR}\n")

    # Load model once and share across all file calls.
    # local_files_only=True prevents HuggingFace API calls on every invocation
    # once the model is cached locally.
    print(f"Loading model '{Summarizer.MODEL_NAME}' …")
    tokenizer = AutoTokenizer.from_pretrained(
        Summarizer.MODEL_NAME, local_files_only=True
    )
    model = AutoModel.from_pretrained(Summarizer.MODEL_NAME, local_files_only=True).to(
        device
    )
    model.eval()
    print("Model loaded.\n")

    summarizer = _make_summarizer_with_shared_model(tokenizer, model, device)

    json_files = sorted(NORMALIZED_DIR.rglob("*.json"))
    print(f"Found {len(json_files)} JSON file(s) in {NORMALIZED_DIR}\n")

    errors: list[tuple[Path, Exception]] = []
    skipped = 0

    for path in json_files:
        try:
            # Skip if output already exists in data/summarized/ (idempotent)
            relative = path.relative_to(NORMALIZED_DIR)
            out_path = SUMMARIZED_DIR / relative

            if not force and out_path.exists():
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
