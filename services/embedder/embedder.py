"""
embedder.py
-----------
Multi-level embedding generator for Croatian legal documents.

Embedding levels produced per document:
  - document  : full doc_cleaned text (chunked + mean-pooled if too long)
  - title     : naslov field
  - summary   : short, detailed, and each structured summary field
  - segment   : each članak (article) text joined from its točke

Model: sentence-transformers/all-MiniLM-L6-v2
  - 384-dimensional dense embeddings
  - max 256 word-pieces per passage (longer texts are mean-pooled over chunks)
  - fully offline when HF_HUB_OFFLINE=1

No network access is made; the model must be cached locally.
"""
from dotenv import load_dotenv
load_dotenv()

import re
import torch
import torch.nn.functional as F
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from transformers import AutoTokenizer, AutoModel

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

_cfg = yaml.safe_load((Path(__file__).parent / "config.yaml").read_text())

MODEL_NAME    = _cfg["model_name"]
_MAX_TOKENS   = _cfg["max_tokens"]
_BATCH_SIZE   = _cfg["batch_size"]
_EMBEDDING_DIM = _cfg["embedding_dim"]

# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class EmbeddingResult:
    """
    Holds all embeddings for one document as plain Python lists (JSON-serialisable).

    Attributes:
        document_embedding  : single vector for the full document text
        title_embedding     : single vector for the document title
        summary_embeddings  : dict  { "short": [...], "detailed": [...],
                                      "što_zakon_uređuje": [...], ... }
        segment_embeddings  : list of { "članak": "Član N.", "embedding": [...] }
        model_name          : model identifier for provenance tracking
        embedding_dim       : dimensionality of all vectors
    """
    document_embedding:  list[float]              = field(default_factory=list)
    title_embedding:     list[float]              = field(default_factory=list)
    summary_embeddings:  dict[str, list[float]]   = field(default_factory=dict)
    segment_embeddings:  list[dict]               = field(default_factory=list)
    model_name:          str                      = MODEL_NAME
    embedding_dim:       int                      = _EMBEDDING_DIM

    def to_dict(self) -> dict:
        return {
            "model_name":         self.model_name,
            "embedding_dim":      self.embedding_dim,
            "document_embedding": self.document_embedding,
            "title_embedding":    self.title_embedding,
            "summary_embeddings": self.summary_embeddings,
            "segment_embeddings": self.segment_embeddings,
        }


# ---------------------------------------------------------------------------
# Embedder
# ---------------------------------------------------------------------------

class Embedder:
    """
    Multi-level embedder for Croatian legal documents.

    The model is loaded once on construction and reused for all calls.

    Usage::

        embedder = Embedder()                        # loads model
        result   = embedder.embed(data)              # data = extracted JSON dict
        print(result.embedding_dim)                  # 384
        print(len(result.document_embedding))        # 384
        print(len(result.segment_embeddings))        # one per article
    """

    def __init__(self, device: str | None = None) -> None:
        self.device        = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model_name    = MODEL_NAME
        self.embedding_dim = _EMBEDDING_DIM
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, local_files_only=True)
        self.model     = AutoModel.from_pretrained(MODEL_NAME, local_files_only=True)
        self.model     = self.model.to(self.device)
        self.model.eval()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def embed(self, data: dict) -> EmbeddingResult:
        """
        Generate all embedding levels for *data*.

        Args:
            data: A single extracted document dict containing at minimum
                  'doc_cleaned', 'naslov', 'summaries', 'doc_segmented'.

        Returns:
            EmbeddingResult with all levels populated.
        """
        result = EmbeddingResult(model_name=MODEL_NAME, embedding_dim=_EMBEDDING_DIM)

        # 1. Document-level
        doc_text = data.get("doc_cleaned", "").strip()
        if doc_text:
            result.document_embedding = self._embed_long_text(doc_text)

        # 2. Title-level
        title = data.get("naslov", "").strip()
        if title:
            result.title_embedding = self._embed_single(title)

        # 3. Summary-level
        summaries = data.get("summaries", {})
        summary_embeddings: dict[str, list[float]] = {}

        for key in ("short", "detailed"):
            text = summaries.get(key, "").strip()
            if text:
                summary_embeddings[key] = self._embed_single(text)

        structured = summaries.get("structured", {})
        for key, text in structured.items():
            text = (text or "").strip()
            if text:
                summary_embeddings[f"structured_{key}"] = self._embed_single(text)

        result.summary_embeddings = summary_embeddings

        # 4. Segment-level (one per članak)
        segment_embeddings: list[dict] = []
        for clanak in data.get("doc_segmented", []):
            label    = clanak.get("članak", "")
            passages = []
            for stavak in clanak.get("stavci", []):
                passages.extend(stavak.get("točke", []))
            segment_text = " ".join(passages).strip()
            if segment_text:
                emb = self._embed_long_text(segment_text)
                segment_embeddings.append({
                    "članak":    label,
                    "embedding": emb,
                })

        result.segment_embeddings = segment_embeddings
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _mean_pool(
        self,
        last_hidden: torch.Tensor,
        attention_mask: torch.Tensor,
    ) -> torch.Tensor:
        mask    = attention_mask.unsqueeze(-1).expand(last_hidden.size()).float()
        summed  = (last_hidden * mask).sum(dim=1)
        counts  = mask.sum(dim=1).clamp(min=1e-9)
        pooled  = summed / counts
        return F.normalize(pooled, p=2, dim=1)

    def _encode_batch(self, texts: list[str]) -> torch.Tensor:
        """Tokenize and embed a batch of short texts. Returns (N, 384) tensor."""
        encoded = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=_MAX_TOKENS,
            return_tensors="pt",
        )
        encoded = {k: v.to(self.device) for k, v in encoded.items()}
        with torch.no_grad():
            outputs = self.model(**encoded)
        return self._mean_pool(outputs.last_hidden_state, encoded["attention_mask"])

    def _embed_single(self, text: str) -> list[float]:
        """Embed a single short text → list[float]."""
        return self._encode_batch([text])[0].cpu().tolist()

    def _embed_long_text(self, text: str) -> list[float]:
        """
        Embed a potentially long text by:
        1. Splitting into sentences.
        2. Grouping sentences into token-safe chunks.
        3. Embedding each chunk in batches.
        4. Mean-pooling chunk embeddings → single document vector.
        """
        sentences = self._split_sentences(text)
        chunks    = self._pack_chunks(sentences)

        if not chunks:
            return self._embed_single(text)

        all_embs: list[torch.Tensor] = []
        for i in range(0, len(chunks), _BATCH_SIZE):
            batch = chunks[i: i + _BATCH_SIZE]
            embs  = self._encode_batch(batch)        # (B, 384)
            all_embs.append(embs.cpu())
            if self.device == "cuda":
                torch.cuda.empty_cache()

        stacked = torch.cat(all_embs, dim=0)         # (N_chunks, 384)
        pooled  = stacked.mean(dim=0)                # (384,)
        pooled  = F.normalize(pooled.unsqueeze(0), p=2, dim=1).squeeze(0)
        return pooled.tolist()

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        """Simple sentence splitter."""
        parts = re.split(r'(?<=[.!?])\s+', text.strip())
        return [s.strip() for s in parts if s.strip()]

    def _pack_chunks(self, sentences: list[str]) -> list[str]:
        """
        Greedily pack consecutive sentences into chunks that fit within
        _MAX_TOKENS. Returns a list of chunk strings.
        """
        chunks:   list[str] = []
        current:  list[str] = []
        cur_len:  int       = 0

        for sent in sentences:
            token_len = len(self.tokenizer.tokenize(sent))
            if cur_len + token_len > _MAX_TOKENS and current:
                chunks.append(" ".join(current))
                current  = []
                cur_len  = 0
            current.append(sent)
            cur_len += token_len

        if current:
            chunks.append(" ".join(current))

        return chunks
