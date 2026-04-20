"""
services/importer.py
--------------------
Reads all JSON files from data/embedded/ and upserts every entity into
the PostgreSQL database.

Each JSON file maps to:
  documents                ← top-level scalar fields
  document_segments        ← doc_segmented[].stavci[].točke (joined per članak)
  document_summaries       ← summaries.{short,detailed,structured.*}
  document_key_information ← key_information.*
  document_embeddings      ← embeddings.{document,title,summary_*,segment_*}

The import is idempotent: existing records are updated in-place (matched by
ELI for documents, and by their unique constraints for sub-records).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from api.models.db import (
    Document,
    DocumentEmbedding,
    DocumentKeyInformation,
    DocumentSegment,
    DocumentSummary,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_REPO_ROOT   = Path(__file__).resolve().parents[2]
EMBEDDED_DIR = _REPO_ROOT / "data" / "embedded"

# ---------------------------------------------------------------------------
# Summary type key mapping  (JSON key → DB summary_type)
# ---------------------------------------------------------------------------

_SUMMARY_FLAT = {
    "short":    "short",
    "detailed": "detailed",
}

_SUMMARY_STRUCTURED_PREFIX = "structured_"

# Embedding type mapping  (summary_embeddings JSON key → DB embedding_type)
_EMBEDDING_TYPE_MAP: dict[str, str] = {
    "short":                              "summary_short",
    "detailed":                           "summary_detailed",
    "structured_što_zakon_uređuje":       "summary_structured_sto_zakon_ureduje",
    "structured_na_koga_se_odnosi":       "summary_structured_na_koga_se_odnosi",
    "structured_što_uvodi_ili_mijenja":   "summary_structured_sto_uvodi_ili_mijenja",
}

# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

@dataclass
class ImportResult:
    processed: int = 0
    skipped:   int = 0
    errors:    list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "processed": self.processed,
            "skipped":   self.skipped,
            "errors":    self.errors,
        }

# ---------------------------------------------------------------------------
# Date parser
# ---------------------------------------------------------------------------

_DATE_RE = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})")

def _parse_date(raw: str | None) -> datetime | None:
    if not raw:
        return None
    m = _DATE_RE.search(raw)
    if not m:
        return None
    try:
        return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None

# ---------------------------------------------------------------------------
# Upsert helpers
# ---------------------------------------------------------------------------

def _upsert_document(db: Session, data: dict) -> Document:
    eli = data["eli"]
    doc = db.query(Document).filter(Document.eli == eli).first()

    fields = {
        "eli":              eli,
        "eli_url":          data.get("eliUrl"),
        "broj_dokumenta":   data.get("brojDokumenta"),
        "dio":              data.get("dio"),
        "vrsta":            data.get("vrsta"),
        "izdanje":          data.get("izdanje"),
        "izdanje_url":      data.get("izdanjeUrl"),
        "donositelj":       data.get("donositelj"),
        "datum":            data.get("datum"),
        "publication_date": _parse_date(data.get("datum")),
        "naslov":           data.get("naslov", ""),
        "opis":             data.get("opis"),
        "doc_cleaned":      data.get("doc_cleaned"),
    }

    if doc:
        for k, v in fields.items():
            setattr(doc, k, v)
    else:
        doc = Document(**fields)
        db.add(doc)

    db.flush()
    return doc


def _upsert_segments(db: Session, doc: Document, doc_segmented: list) -> dict[str, int]:
    """Returns {clanak_label: segment_id} for embedding cross-reference."""
    label_to_id: dict[str, int] = {}

    for order, clanak in enumerate(doc_segmented):
        label    = clanak.get("članak", "")
        passages: list[str] = []
        for stavak in clanak.get("stavci", []):
            passages.extend(stavak.get("točke", []))
        text = " ".join(passages).strip()
        if not text:
            continue

        seg = (
            db.query(DocumentSegment)
            .filter(
                DocumentSegment.document_id   == doc.id,
                DocumentSegment.segment_order == order,
            )
            .first()
        )
        if seg:
            seg.clanak_label = label
            seg.text         = text
        else:
            seg = DocumentSegment(
                document_id   = doc.id,
                segment_order = order,
                clanak_label  = label,
                text          = text,
            )
            db.add(seg)

        db.flush()
        label_to_id[label] = seg.id

    return label_to_id


def _upsert_summaries(db: Session, doc: Document, summaries: dict, model_name: str) -> None:
    def _save(summary_type: str, text: str) -> None:
        if not text:
            return
        existing = (
            db.query(DocumentSummary)
            .filter(
                DocumentSummary.document_id  == doc.id,
                DocumentSummary.summary_type == summary_type,
            )
            .first()
        )
        if existing:
            existing.text       = text
            existing.model_name = model_name
        else:
            db.add(DocumentSummary(
                document_id  = doc.id,
                summary_type = summary_type,
                text         = text,
                model_name   = model_name,
            ))

    for key, db_type in _SUMMARY_FLAT.items():
        _save(db_type, summaries.get(key, ""))

    for key, text in summaries.get("structured", {}).items():
        _save(f"{_SUMMARY_STRUCTURED_PREFIX}{key}", text or "")


def _upsert_key_information(db: Session, doc: Document, ki: dict) -> None:
    existing = (
        db.query(DocumentKeyInformation)
        .filter(DocumentKeyInformation.document_id == doc.id)
        .first()
    )
    fields = {
        "responsible_bodies": ki.get("responsible_bodies", []),
        "obligations":        ki.get("obligations",        []),
        "deadlines":          ki.get("deadlines",          []),
        "scope":              ki.get("scope",              []),
        "subjects":           ki.get("subjects",           []),
        "sanctions":          ki.get("sanctions",          []),
    }
    if existing:
        for k, v in fields.items():
            setattr(existing, k, v)
    else:
        db.add(DocumentKeyInformation(document_id=doc.id, **fields))


def _upsert_embedding(
    db:             Session,
    doc:            Document,
    embedding_type: str,
    model_name:     str,
    embedding_dim:  int,
    vector:         list[float],
    segment_id:     int | None = None,
) -> None:
    existing = (
        db.query(DocumentEmbedding)
        .filter(
            DocumentEmbedding.document_id    == doc.id,
            DocumentEmbedding.embedding_type == embedding_type,
            DocumentEmbedding.model_name     == model_name,
            DocumentEmbedding.segment_id     == segment_id,
        )
        .first()
    )
    if existing:
        existing.embedding = vector
    else:
        db.add(DocumentEmbedding(
            document_id    = doc.id,
            segment_id     = segment_id,
            embedding_type = embedding_type,
            model_name     = model_name,
            embedding_dim  = embedding_dim,
            embedding      = vector,
        ))


def _upsert_embeddings(
    db:          Session,
    doc:         Document,
    emb_data:    dict,
    label_to_id: dict[str, int],
) -> None:
    model_name    = emb_data.get("model_name", "")
    embedding_dim = emb_data.get("embedding_dim", 384)

    if vec := emb_data.get("document_embedding"):
        _upsert_embedding(db, doc, "document", model_name, embedding_dim, vec)

    if vec := emb_data.get("title_embedding"):
        _upsert_embedding(db, doc, "title", model_name, embedding_dim, vec)

    for json_key, vec in emb_data.get("summary_embeddings", {}).items():
        db_type = _EMBEDDING_TYPE_MAP.get(json_key, f"summary_{json_key}")
        _upsert_embedding(db, doc, db_type, model_name, embedding_dim, vec)

    for seg_entry in emb_data.get("segment_embeddings", []):
        label  = seg_entry.get("članak", "")
        vec    = seg_entry.get("embedding")
        seg_id = label_to_id.get(label)
        if vec and seg_id:
            _upsert_embedding(db, doc, "segment", model_name, embedding_dim, vec, seg_id)

# ---------------------------------------------------------------------------
# Single-file import
# ---------------------------------------------------------------------------

def import_file(db: Session, path: Path) -> None:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    if not data.get("eli"):
        raise ValueError("Missing 'eli' field")

    doc         = _upsert_document(db, data)
    label_to_id = _upsert_segments(db, doc, data.get("doc_segmented", []))

    summaries = data.get("summaries", {})
    if summaries:
        _upsert_summaries(
            db, doc, summaries,
            model_name=data.get("embeddings", {}).get("model_name", ""),
        )

    ki = data.get("key_information")
    if ki:
        _upsert_key_information(db, doc, ki)

    emb_data = data.get("embeddings")
    if emb_data:
        _upsert_embeddings(db, doc, emb_data, label_to_id)

    db.commit()

# ---------------------------------------------------------------------------
# Batch import
# ---------------------------------------------------------------------------

def import_all(db: Session, embedded_dir: Path | None = None) -> ImportResult:
    """
    Recursively import all *.json files from *embedded_dir*.
    Returns an ImportResult with counts and any per-file error messages.
    """
    directory = embedded_dir or EMBEDDED_DIR
    result    = ImportResult()

    for path in sorted(directory.rglob("*.json")):
        try:
            import_file(db, path)
            result.processed += 1
            print(f"  ✓  {path.relative_to(directory)}")
        except Exception as exc:
            db.rollback()
            msg = f"{path.name}: {exc}"
            result.errors.append(msg)
            print(f"  ✗  {msg}")

    return result
