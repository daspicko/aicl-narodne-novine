"""
extract_data.py
------------------
Extraction process for Croatian legal documents.

Input:   data/summarized/<year>/<issue>/<doc>.json
Output:  data/extracted/<year>/<issue>/<doc>.json  (mirror tree, never mutates summarized)

For each document the following fields are added under "key_information":
{
  "key_information": {
    "responsible_bodies": [...],
    "obligations":        [...],
    "deadlines":          [...],
    "scope":              [...],
    "subjects":           [...],
    "sanctions":          [...]
  }
}

Run:
    python extract_data.py           # skip already-extracted files
    python extract-data.py --force   # re-extract everything
"""

import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_REPO_ROOT    = Path(__file__).resolve().parents[2]
SUMMARIZED_DIR = _REPO_ROOT / "data" / "summarized"
EXTRACTED_DIR  = _REPO_ROOT / "data" / "extracted"

# Make the extractor importable regardless of working directory
sys.path.insert(0, str(Path(__file__).resolve().parent))
from extractor import Extractor  # noqa: E402

# ---------------------------------------------------------------------------
# File-level processing
# ---------------------------------------------------------------------------


def process_file(path: Path, extractor: Extractor) -> None:
    """
    Load one summarized JSON, run extraction, write enriched copy to
    data/extracted/ mirroring the summarized tree.
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    # Skip documents without text (metadata-only entries)
    if not data.get("doc_cleaned", "").strip():
        print(f"  –  {path.name}: no doc_cleaned, skipping")
        return

    result = extractor.extract(data)
    data["key_information"] = result.to_dict()

    relative = path.relative_to(SUMMARIZED_DIR)
    out_path  = EXTRACTED_DIR / relative
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"  ✓  {relative}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(force: bool = False) -> None:
    if not SUMMARIZED_DIR.exists():
        print(f"ERROR: summarized data directory not found: {SUMMARIZED_DIR}")
        return

    print(f"Input:  {SUMMARIZED_DIR}")
    print(f"Output: {EXTRACTED_DIR}\n")

    extractor  = Extractor()
    json_files = sorted(SUMMARIZED_DIR.rglob("*.json"))
    print(f"Found {len(json_files)} JSON file(s)\n")

    errors:  list[tuple[Path, Exception]] = []
    skipped: int = 0

    for path in json_files:
        try:
            relative = path.relative_to(SUMMARIZED_DIR)
            out_path = EXTRACTED_DIR / relative

            if not force and out_path.exists():
                skipped += 1
                continue

            process_file(path, extractor)
        except Exception as exc:
            print(f"  ✗  {path}: {exc}")
            errors.append((path, exc))

    processed = len(json_files) - len(errors) - skipped
    print(
        f"\nDone. {processed} extracted, {skipped} skipped (already done), "
        f"{len(errors)} error(s)."
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract key information from summarized Croatian legal documents."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-extract files that already exist in data/extracted/.",
    )
    args = parser.parse_args()
    main(force=args.force)
