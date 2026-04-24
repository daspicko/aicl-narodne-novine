"""
embed_data.py
-----------------
Embedding process for Croatian legal documents.

Input:   data/extracted/<year>/<issue>/<doc>.json
Output:  data/embedded/<year>/<issue>/<doc>.json  (mirror tree, never mutates extracted)

For each document the following field is added:

{
  "embeddings": {
    "model_name":         "sentence-transformers/all-MiniLM-L6-v2",
    "embedding_dim":      384,
    "document_embedding": [ 0.021, ... ],          // 384 floats
    "title_embedding":    [ 0.013, ... ],          // 384 floats
    "summary_embeddings": {
      "short":                        [ ... ],
      "detailed":                     [ ... ],
      "structured_što_zakon_uređuje": [ ... ],
      "structured_na_koga_se_odnosi": [ ... ],
      "structured_što_uvodi_ili_mijenja": [ ... ]
    },
    "segment_embeddings": [
      { "glava": "I. OPĆE ODREDBE", "članak": "Član 1.", "embedding": [ ... ] },
      ...
    ]
  }
}

Run:
    python embed_data.py           # skip already-embedded files
    python embed_data.py --force   # re-embed everything
"""

from dotenv import load_dotenv

load_dotenv()

import json
import sys
from pathlib import Path

import torch  # noqa: E402 – must come after env vars

import yaml
from dotenv import load_dotenv

# ==================== Load configurations ====================
MODULE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(MODULE_DIR / ".env")
with open(MODULE_DIR / "config.yaml") as f:
    _cfg = yaml.safe_load(f)

# ==================== Configure ====================
DATA_ROOT_DIR = REPO_ROOT / "data"
DATA_EXTRACTED_DIR = DATA_ROOT_DIR / "extracted"  # output: data/extracted/<year>/<issue>/<doc>.json
DATA_EMBEDDED_DIR = DATA_ROOT_DIR / "embedded"  # output: data/embedded/<year>/<issue>/<doc>.json

sys.path.insert(0, str(MODULE_DIR))
from embedder import Embedder  # noqa: E402

def process_file(path: Path, embedder: Embedder) -> None:
    """
    Load one extracted JSON, generate all embeddings, write enriched copy to
    data/embedded/ mirroring the extracted tree.
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    if not data.get("doc_cleaned", "").strip():
        print(f"  –  {path.name}: no doc_cleaned, skipping")
        return

    result = embedder.embed(data)
    data["embeddings"] = result.to_dict()

    relative = path.relative_to(DATA_EXTRACTED_DIR)
    out_path = DATA_EMBEDDED_DIR / relative
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    n_segments = len(result.segment_embeddings)
    n_summaries = len(result.summary_embeddings)
    print(f"  ✓  {relative}  (doc+title+{n_summaries} summaries+{n_segments} segments)")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(force: bool = False) -> None:
    if not DATA_EXTRACTED_DIR.exists():
        print(f"ERROR: extracted data directory not found: {DATA_EXTRACTED_DIR}")
        return

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    print(f"Input:  {DATA_EXTRACTED_DIR}")
    print(f"Output: {DATA_EMBEDDED_DIR}\n")

    print("Loading embedding model …")
    embedder = Embedder(device=device)
    print(f"Model loaded: {embedder.model_name}  (dim={embedder.embedding_dim})\n")

    json_files = sorted(DATA_EXTRACTED_DIR.rglob("*.json"))
    print(f"Found {len(json_files)} JSON file(s)\n")

    errors: list[tuple[Path, Exception]] = []
    skipped: int = 0

    for path in json_files:
        try:
            relative = path.relative_to(DATA_EXTRACTED_DIR)
            out_path = DATA_EMBEDDED_DIR / relative

            if not force and out_path.exists():
                skipped += 1
                continue

            process_file(path, embedder)

            if device == "cuda":
                torch.cuda.empty_cache()

        except Exception as exc:
            print(f"  ✗  {path.name}: {exc}")
            errors.append((path, exc))

    processed = len(json_files) - len(errors) - skipped
    print(
        f"\nDone. {processed} embedded, {skipped} skipped (already done), "
        f"{len(errors)} error(s)."
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate multi-level embeddings for extracted Croatian legal documents."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-embed files that already exist in data/embedded/.",
    )
    args = parser.parse_args()
    main(force=args.force)
