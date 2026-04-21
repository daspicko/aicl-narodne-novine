"""
normalize_data.py
-----------------
Normalizer for Croatian legal documents.

Input:   data/raw/<year>/<issue>/<doc>.json
Output:  data/normalized/<year>/<issue>/<doc>.json   (same tree, different root)

For each document that contains a 'doc' (raw HTML) field, this script:
  1. Strips HTML tags, removes \r/\n, and collapses whitespace  →  clean_text()
  2. Detects chapter (glava) headings using Roman numeral patterns (I., II., ...)
  3. Detects article (članak) boundaries using the "Član N." heading pattern
  4. Extracts the preamble (text before the first glava) into a top-level 'opis' field
  5. Groups paragraphs into stavci by the (1), (2), … prefix
  6. Within each stavak collects individual paragraphs as točke
  7. Writes the enriched document to the normalized output tree

Top-level properties added:
  "opis"          – plain text of the preamble before the first glava
  "doc_segmented" – list of chapters (see schema below)

Output shape of doc_segmented:
[
  {
    "glava": "I. OPĆE ODREDBE",
    "članci": [
      {
        "članak": "Član 1.",
        "stavci": [
          {
            "stavak": "(1)" | null,    # null = unnumbered block
            "točke": [
              "paragraph / sub-item text 1",
              "paragraph / sub-item text 2",
              ...
            ]
          },
          ...
        ]
      },
      ...
    ]
  },
  {
    "glava": "VI. KVALITETA ŠUMSKOG SJEMENA...",
    "članci": [...]
  },
  ...
]
"""

import json
import re
from pathlib import Path
from bs4 import BeautifulSoup, Tag

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# Script lives at:  data_processing/normalization/normalize_data.py
# Repo root is two levels up
_DATA_ROOT = Path(__file__).resolve().parents[2] / "data"

RAW_DIR = _DATA_ROOT / "raw"  # input:  data/raw/<year>/<issue>/<doc>.json
NORMALIZED_DIR = (
    _DATA_ROOT / "normalized"
)  # output: data/normalized/<year>/<issue>/<doc>.json

# ---------------------------------------------------------------------------
# Regex constants
# ---------------------------------------------------------------------------

# Chapter heading: "I. OPĆE ODREDBE", "VI. KVALITETA ŠUMSKOG SJEMENA...", "VII PROMET..."
_GLAVA_RE = re.compile(r"^[IVX]+\.?\s+.+", re.IGNORECASE)

# Article marker:  "Član 1."  "Član 12."  (with optional surrounding whitespace)
_CLANAK_RE = re.compile(r"^Član\s+\d+\.\s*$", re.IGNORECASE)

# Numbered stavak opening:  "(1)", "(2)", ...
_STAVAK_RE = re.compile(r"^\(\d+\)")

# Croatian legal abbreviations whose trailing period must NOT trigger a sentence split
_ABBREVS: frozenset[str] = frozenset(
    {
        "br",
        "st",
        "čl",
        "dr",
        "mr",
        "prof",
        "op",
        "sl",
        "tzv",
        "tj",
        "npr",
        "str",
        "god",
        "sv",
        "vs",
        "al",
        "ul",
        "bb",
        "no",
        "tar",
        "pos",
        "vel",
        "odg",
        "ref",
        "tel",
        "itd",
        "idr",
        "spec",
        "nar",
        "sr",
        "rh",
        "nn",
        "sfrj",
        "sfr",
    }
)


# ---------------------------------------------------------------------------
# Public cleanup function
# ---------------------------------------------------------------------------


def clean_text(html: str) -> str:
    """
    Remove HTML markup, strip \\r and \\n characters, and collapse whitespace.

    Args:
        html: Raw HTML string (value of the 'doc' field).

    Returns:
        Plain, single-line text with normalised whitespace.
    """
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(separator=" ")
    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _elem_text(element: Tag) -> str:
    """Return clean plain text for a BeautifulSoup element (no HTML, no newlines)."""
    raw = element.get_text(separator=" ")
    raw = raw.replace("\r", " ").replace("\n", " ")
    return re.sub(r"\s+", " ", raw).strip()


def _is_clanak(text: str) -> bool:
    """Return True if *text* matches an article (Član) header."""
    return bool(_CLANAK_RE.match(text))


def _is_glava(text: str) -> bool:
    """Return True if *text* matches a chapter (glava) heading."""
    return bool(_GLAVA_RE.match(text))


# ---------------------------------------------------------------------------
# Sentence splitter
# ---------------------------------------------------------------------------


def split_recenice(text: str) -> list[str]:
    """
    Split *text* into sentences using rules adapted for Croatian legal language.

    Strategy:
    - Split at [.!?] followed by whitespace and an uppercase letter.
    - Do NOT split:
        * after a digit  (ordinal numbers and article references like "stava 1.")
        * after a single character  (abbreviations like "v.", "r.")
        * after known Croatian legal abbreviations  (br., st., čl., Tar., …)

    Args:
        text: Plain text paragraph (already cleaned of HTML/newlines).

    Returns:
        List of sentence strings, each ending with its punctuation mark.
        Returns ``[text]`` when no split points are found.
    """
    if not text:
        return []

    _UC = "A-ZŠĐČĆŽ"

    sentences: list[str] = []
    start = 0

    for m in re.finditer(rf"[.!?]\s+(?=[{_UC}])", text):
        punct_pos = m.start()  # position of the punctuation character

        # Guard: digit immediately before the punctuation (e.g. "stava 1. U")
        if text[punct_pos - 1].isdigit():
            continue

        # Guard: look at the word immediately before the punctuation
        word_start = text.rfind(" ", 0, punct_pos) + 1
        word_before = text[word_start:punct_pos].lower().strip(".")

        # Single-character token  (e.g. "v", "r" from "v.r.")
        if len(word_before) <= 1:
            continue

        # Known Croatian abbreviation
        if word_before in _ABBREVS:
            continue

        # Commit sentence (include the punctuation character)
        sentence = text[start : punct_pos + 1].strip()
        if sentence:
            sentences.append(sentence)
        start = m.end()

    # Remaining text after last split (or the whole text if no splits found)
    tail = text[start:].strip()
    if tail:
        sentences.append(tail)

    return sentences if sentences else [text]


# ---------------------------------------------------------------------------
# Stavak builder  –  each paragraph becomes one točka
# ---------------------------------------------------------------------------


def _build_stavci(paragraphs: list[str]) -> list[dict]:
    """
    Group a flat list of paragraph texts into stavci.

    A new stavak starts when a paragraph begins with the "(N)" prefix.
    Every paragraph within a stavak (including the opening "(N) …" line
    and any subsequent sub-items) is stored verbatim as one **točka**.

    Returns:
        List of dicts:  {"stavak": "(N)" | null, "točke": [...]}
    """
    stavci: list[dict] = []
    current_label: str | None = None
    current_tocke: list[str] = []

    def _commit() -> None:
        if current_tocke:
            stavci.append(
                {
                    "stavak": current_label,
                    "točke": list(current_tocke),
                }
            )

    for para in paragraphs:
        m = _STAVAK_RE.match(para)
        if m:
            _commit()
            current_label = m.group()
            current_tocke = [para]
        else:
            current_tocke.append(para)

    _commit()
    return stavci


# ---------------------------------------------------------------------------
# Main segmentation function
# ---------------------------------------------------------------------------


def segment_doc(html: str) -> tuple[list[dict], str]:
    """
    Parse *html* and segment it into glava → članci → stavci → točke.

    The preamble (everything before the first glava) is **not** included in the
    returned segment list; instead its text is returned as a plain string so
    the caller can store it in the top-level ``"opis"`` field.

    Args:
        html: Raw HTML string from the 'doc' field.

    Returns:
        ``(segments, opis)`` where *segments* is the list of glava dicts
        and *opis* is the cleaned preamble text.
    """
    soup = BeautifulSoup(html, "lxml")
    container = soup.find("div") or soup.find("body") or soup

    chapters: list[dict] = []
    current_glava: str | None = None
    current_clanak: str | None = None
    current_paragraphs: list[str] = []
    current_clanci: list[dict] = []

    def _flush_clanak() -> None:
        nonlocal current_clanak, current_paragraphs
        if not current_paragraphs:
            return
        stavci = _build_stavci(current_paragraphs)
        if stavci:
            current_clanci.append(
                {
                    "članak": current_clanak,
                    "stavci": stavci,
                }
            )
        current_paragraphs = []

    for child in container.children:
        if not isinstance(child, Tag):
            continue
        text = _elem_text(child)
        if not text:
            continue
        if _is_glava(text):
            _flush_clanak()
            if current_clanci:
                chapters.append({"glava": current_glava, "članci": current_clanci})
            current_glava = text
            current_clanci = []
        elif _is_clanak(text):
            _flush_clanak()
            current_clanak = text
        else:
            current_paragraphs.append(text)

    _flush_clanak()
    if current_clanci:
        chapters.append({"glava": current_glava, "članci": current_clanci})

    # Separate preamble (text before first article) from chapters
    opis_parts: list[str] = []
    segments: list[dict] = []

    for ch in chapters:
        filtered_clanci: list[dict] = []

        for cl in ch["članci"]:
            if cl["članak"] is None:
                # Preamble text - goes to opis
                for st in cl["stavci"]:
                    opis_parts.extend(st["točke"])
            else:
                # Actual article
                filtered_clanci.append(cl)

        if filtered_clanci:
            segments.append({"glava": ch["glava"], "članci": filtered_clanci})

    opis = " ".join(opis_parts)
    return segments, opis


# ---------------------------------------------------------------------------
# File-level processing
# ---------------------------------------------------------------------------


def process_file(raw_path: Path) -> None:
    """
    Read *raw_path* from ``data/raw/``, enrich it, and write to ``data/normalized/``.

    The output directory tree mirrors the input tree.
    Files without a non-empty 'doc' field are copied as-is.
    Running the script again overwrites previous normalized output (idempotent).
    """
    relative = raw_path.relative_to(RAW_DIR)
    out_path = NORMALIZED_DIR / relative
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(raw_path, encoding="utf-8") as f:
        data = json.load(f)

    doc_html = data.get("doc")
    if not doc_html:
        # No HTML content – copy metadata fields unchanged
        out_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return

    segments, opis = segment_doc(doc_html)
    data["opis"] = opis
    data["doc_cleaned"] = clean_text(doc_html)
    data["doc_segmented"] = segments
    del data["doc"]

    # Remove stale doc_segmented that may have been written to the raw file earlier
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"  ✓  {relative}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Recursively process every .json file under RAW_DIR → NORMALIZED_DIR."""
    if not RAW_DIR.exists():
        print(f"ERROR: raw data directory not found: {RAW_DIR}")
        return

    json_files = sorted(RAW_DIR.rglob("*.json"))
    print(f"Found {len(json_files)} JSON file(s) in {RAW_DIR}\n")

    errors: list[tuple[Path, Exception]] = []

    for path in json_files:
        try:
            process_file(path)
        except Exception as exc:
            print(f"  ✗  {path}: {exc}")
            errors.append((path, exc))

    print(f"\nDone. {len(json_files) - len(errors)} processed, {len(errors)} error(s).")


if __name__ == "__main__":
    main()
