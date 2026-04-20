"""
extractor.py
------------
Hybrid information extractor for Croatian legal documents.

Extraction strategy:
  - deadlines          → regex patterns for Croatian temporal expressions
  - responsible_bodies → rule-based NER (capitalized institutional name patterns)
  - obligations        → obligation verb heuristics ("dužan je", "mora", "obvezna je" …)
  - scope              → scope-marker heuristics ("primjenjuje se na", "odnosi se na" …)
  - subjects           → noun phrase extraction from article headings + opis
  - sanctions          → penalty clause heuristics ("kaznit će se", "novčana kazna" …)

All extraction works on plain text (doc_cleaned) and/or doc_segmented paragraphs.
No external model or network access is required.
"""

import re
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class ExtractionResult:
    responsible_bodies: list[str] = field(default_factory=list)
    obligations: list[str] = field(default_factory=list)
    deadlines: list[str] = field(default_factory=list)
    scope: list[str] = field(default_factory=list)
    subjects: list[str] = field(default_factory=list)
    sanctions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "responsible_bodies": self.responsible_bodies,
            "obligations": self.obligations,
            "deadlines": self.deadlines,
            "scope": self.scope,
            "subjects": self.subjects,
            "sanctions": self.sanctions,
        }


# ---------------------------------------------------------------------------
# Regex constants
# ---------------------------------------------------------------------------

# Croatian ordinal / cardinal deadline patterns
_DEADLINE_PATTERNS: list[re.Pattern] = [
    # "u roku od 30 dana", "u roku od tri mjeseca"
    re.compile(
        r"u\s+roku\s+od\s+[\w\s]+?(?:dana|tjedna?|mjeseca?|godina?)",
        re.IGNORECASE,
    ),
    # "najkasnije u roku od …"
    re.compile(
        r"najkasnije\s+u\s+roku\s+od\s+[\w\s]+?(?:dana?|tjedna?|mjeseca?|godina?)",
        re.IGNORECASE,
    ),
    # "stupa na snagu osmoga dana", "stupa na snagu danom objave"
    re.compile(
        r"stupa\s+na\s+snagu\s+[\w\s,]+?(?:dana?|danom|objavom|objave|stupanja)",
        re.IGNORECASE,
    ),
    # "u roku 15 dana", "u roku od 8 dana"
    re.compile(
        r"u\s+roku\s+\d+\s+(?:dana?|tjedna?|mjeseca?|godina?)",
        re.IGNORECASE,
    ),
    # "do … godine" / "do kraja … godine"
    re.compile(
        r"do\s+\d{1,2}\.\s*\w+\s+\d{4}\.\s*godine",
        re.IGNORECASE,
    ),
    # "do 31. prosinca 1985. godine"
    re.compile(
        r"do\s+\d{1,2}\.\s+(?:siječnja|veljače|ožujka|travnja|svibnja|lipnja|"
        r"srpnja|kolovoza|rujna|listopada|studenog|prosinca)\s+\d{4}\.",
        re.IGNORECASE,
    ),
    # "idućeg dana", "u roku tri dana od dana"
    re.compile(
        r"(?:idućeg|narednog|sljedećeg)\s+dana\s+(?:nakon|od|po)\s+[\w\s]+",
        re.IGNORECASE,
    ),
    # "od dana stupanja na snagu"
    re.compile(
        r"od\s+dana\s+stupanja\s+na\s+snagu[\w\s,]*",
        re.IGNORECASE,
    ),
]

# Responsible body: sequences of ≥2 consecutive Title-Case or ALL-CAPS tokens,
# optionally followed by lowercase "za …" prepositional phrase.
_BODY_RE = re.compile(
    r"\b(?:[A-ZŠĐČĆŽ][a-zšđčćžA-ZŠĐČĆŽ]+(?:\s+[A-ZŠĐČĆŽ][a-zšđčćžA-ZŠĐČĆŽ]+)+)"
    r"(?:\s+(?:za|i|o|u)\s+[a-zšđčćžA-ZŠĐČĆŽ\s]+)?",
)

# Known institution keywords for boosting body detection
_INSTITUTION_KEYWORDS = re.compile(
    r"\b(?:ministarstvo|vlada|sabor|vijeće|odbor|komisija|ured|agencija|"
    r"zavod|fond|institut|sud|tužilaštvo|tužiteljstvo|inspektorat|"
    r"uprava|direkcija|tijelo|organ)\b",
    re.IGNORECASE,
)

# Obligation markers — Croatian verbs/phrases indicating a duty
_OBLIGATION_SENT_RE = re.compile(
    r"\b(?:dužan\s+je|dužna\s+je|dužni\s+su|obvezna?\s+je|obvezni\s+su|"
    r"mora(?:ju)?\s+(?:se\s+)?|mora\s+biti|obvezan\s+je|"
    r"podnijeti|dostaviti|prijaviti|obavijestiti|uskladiti|osigurati|"
    r"priložiti|čuvati|voditi|plaćati|platiti)\b",
    re.IGNORECASE,
)

# Scope markers
_SCOPE_SENT_RE = re.compile(
    r"\b(?:primjenjuje\s+se\s+na|odnosi\s+se\s+na|ovim\s+zakonom\s+(?:uređuje|određuje|propisuje|utvrđuje)|"
    r"zakon\s+se\s+primjenjuje|obvezuje\s+(?:sve\s+)?|"
    r"pravo\s+(?:imaju|na|na\s+to)|na\s+koje\s+se|na\s+koga\s+se)\b",
    re.IGNORECASE,
)

# Sanction / penalty markers
_SANCTION_SENT_RE = re.compile(
    r"\b(?:kaznit\s+(?:će\s+se|se)|novčana\s+kazna|kazna\s+zatvora|"
    r"novčanom\s+kaznom|kaznom\s+zatvora|kazneno\s+djelo|prekršaj|"
    r"oduzimanje|zabrana\s+djelovanja|raspuštanje|zabranit\s+(?:će\s+se|se))\b",
    re.IGNORECASE,
)

# Subjects: strip very short / stopword tokens from title words
_SUBJECT_STOPWORDS = frozenset(
    {
        "o",
        "u",
        "i",
        "a",
        "te",
        "za",
        "na",
        "od",
        "do",
        "po",
        "iz",
        "se",
        "je",
        "su",
        "će",
        "bi",
        "da",
        "li",
        "ali",
        "ili",
        "kao",
        "koji",
        "koja",
        "koje",
        "ovim",
        "ovoga",
        "toga",
        "tome",
        "ovome",
        "sve",
        "svi",
        "svim",
        "zakona",
        "zakon",
        "zakonom",
        "prečišćeni",
        "tekst",
        "izmjenama",
        "dopunama",
        "odredbama",
        "odredbe",
        "primjeni",
        "primjena",
        "br",
        "nn",
        "sl",
        "člana",
        "članak",
    }
)


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def _sentences_from_doc(data: dict) -> list[str]:
    """
    Collect all paragraph texts from doc_segmented + opis as a flat list.

    New structure: [{"glava": "...", "članci": [{"članak": "...", "stavci": [...]}]}]
    """
    sentences: list[str] = []
    opis = data.get("opis", "").strip()
    if opis:
        sentences.append(opis)
    for chapter in data.get("doc_segmented", []):
        for clanak in chapter.get("članci", []):
            for stavak in clanak.get("stavci", []):
                sentences.extend(stavak.get("točke", []))
    return sentences


def _dedupe_ordered(items: list[str], max_len: int = 120) -> list[str]:
    """Remove duplicates preserving order; truncate long items."""
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        item = item.strip()
        if not item:
            continue
        key = item.lower()[:60]
        if key not in seen:
            seen.add(key)
            result.append(item[:max_len] if len(item) > max_len else item)
    return result


# ---------------------------------------------------------------------------
# Extractor
# ---------------------------------------------------------------------------


class Extractor:
    """
    Hybrid extractor for Croatian legal documents.

    Usage::

        extractor = Extractor()
        result = extractor.extract(data)   # data = one normalized/summarized JSON dict
        print(result.to_dict())
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract(self, data: dict) -> ExtractionResult:
        """
        Run all extractors against *data* and return an ExtractionResult.

        Args:
            data: A normalized / summarized document dict with at least
                  'doc_cleaned', 'doc_segmented', 'opis', and 'naslov' keys.
        """
        text = data.get("doc_cleaned", "")
        sentences = _sentences_from_doc(data)
        title = data.get("naslov", "")
        doc_segmented = data.get("doc_segmented")

        return ExtractionResult(
            responsible_bodies=self.extract_responsible_bodies(text, sentences),
            obligations=self.extract_obligations(sentences),
            deadlines=self.extract_deadlines(text),
            scope=self.extract_scope(sentences),
            subjects=self.extract_subjects(title, sentences, doc_segmented),
            sanctions=self.extract_sanctions(sentences),
        )

    # ------------------------------------------------------------------
    # Deadlines  – regex-based
    # ------------------------------------------------------------------

    def extract_deadlines(self, text: str) -> list[str]:
        """
        Extract temporal / deadline expressions using regex patterns.
        Returns a deduplicated list of matched strings.
        """
        matches: list[str] = []
        for pattern in _DEADLINE_PATTERNS:
            for m in pattern.finditer(text):
                matches.append(m.group().strip())
        return _dedupe_ordered(matches, max_len=200)

    # ------------------------------------------------------------------
    # Responsible bodies  – rule-based NER
    # ------------------------------------------------------------------

    def extract_responsible_bodies(self, text: str, sentences: list[str]) -> list[str]:
        """
        Extract institutional / government body names using:
        1. Sentences that contain an institution keyword (ministry, court, …).
        2. Title-Case multi-word sequences extracted from those sentences.
        """
        bodies: list[str] = []

        # Find sentences containing institution keywords
        candidate_sentences = [s for s in sentences if _INSTITUTION_KEYWORDS.search(s)]

        for sent in candidate_sentences:
            for m in _BODY_RE.finditer(sent):
                candidate = m.group().strip()
                # Must contain at least one institution keyword OR ≥3 title-case tokens
                tokens = candidate.split()
                if len(tokens) >= 2 and (
                    _INSTITUTION_KEYWORDS.search(candidate)
                    or all(t[0].isupper() for t in tokens if len(t) > 2)
                ):
                    bodies.append(candidate)

        # Also scan the full text for ALL-CAPS institution names (header-style)
        for m in re.finditer(r"\b([A-ZŠĐČĆŽ][A-ZŠĐČĆŽА-ЯЁ\s]{10,60})\b", text):
            candidate = m.group().strip()
            if _INSTITUTION_KEYWORDS.search(candidate):
                bodies.append(candidate.title())

        return _dedupe_ordered(bodies, max_len=150)

    # ------------------------------------------------------------------
    # Obligations  – heuristic sentence filter
    # ------------------------------------------------------------------

    def extract_obligations(self, sentences: list[str]) -> list[str]:
        """
        Return sentences that contain obligation-marking verbs/phrases.
        Each returned string is one obligation statement (≤ 250 chars).
        """
        obligations: list[str] = []
        for sent in sentences:
            if _OBLIGATION_SENT_RE.search(sent):
                obligations.append(sent.strip())
        return _dedupe_ordered(obligations, max_len=250)

    # ------------------------------------------------------------------
    # Scope  – heuristic sentence filter
    # ------------------------------------------------------------------

    def extract_scope(self, sentences: list[str]) -> list[str]:
        """
        Return sentences that explicitly define the law's scope / applicability.
        """
        scope: list[str] = []
        for sent in sentences:
            if _SCOPE_SENT_RE.search(sent):
                scope.append(sent.strip())
        return _dedupe_ordered(scope, max_len=250)

    # ------------------------------------------------------------------
    # Subjects  – title + heading noun extraction
    # ------------------------------------------------------------------

    def extract_subjects(
        self, title: str, sentences: list[str], doc_segmented: list | None = None
    ) -> list[str]:
        """
        Extract thematic subjects from:
        1. The document title (split on known delimiters).
        2. Chapter (glava) headings from doc_segmented.
        3. ALL-CAPS section headings inside the text.
        """
        subjects: list[str] = []

        # From title: split on " i ", comma, "o ", parenthesis
        if title:
            # Remove parenthetical notes like "(prečišćeni tekst)"
            clean_title = re.sub(r"\(.*?\)", "", title).strip()
            # Split "Zakon o X i Y" → ["X", "Y"]
            for part in re.split(
                r"\s+i\s+|\s*,\s*|\s+te\s+", clean_title, flags=re.IGNORECASE
            ):
                part = part.strip()
                # Strip leading "Zakon o", "Pravilnik o" etc.
                part = re.sub(
                    r"^(?:zakon|pravilnik|uredba|odluka|naredba|"
                    r"rješenje|naputak|uputa)\s+o\s+",
                    "",
                    part,
                    flags=re.IGNORECASE,
                ).strip()
                tokens = [
                    t
                    for t in part.split()
                    if t.lower() not in _SUBJECT_STOPWORDS and len(t) > 2
                ]
                if tokens:
                    subjects.append(" ".join(tokens))

        # Chapter (glava) headings from doc_segmented
        if doc_segmented:
            for chapter in doc_segmented:
                glava = chapter.get("glava", "")
                if glava:
                    # Strip leading Roman numeral and period
                    cleaned = re.sub(r"^[IVX]+\.?\s+", "", glava).strip()
                    if cleaned:
                        subjects.append(cleaned)

        # ALL-CAPS section headings inside doc (e.g. "I. ZAJEDNIČKE ODREDBE")
        for sent in sentences:
            if re.match(r"^[IVXLC]+\.\s+[A-ZŠĐČĆŽ\s]{5,}", sent):
                heading = re.sub(r"^[IVXLC]+\.\s+", "", sent).strip().title()
                if heading:
                    subjects.append(heading)

        return _dedupe_ordered(subjects, max_len=120)

    # ------------------------------------------------------------------
    # Sanctions  – heuristic sentence filter
    # ------------------------------------------------------------------

    def extract_sanctions(self, sentences: list[str]) -> list[str]:
        """
        Return sentences that describe penalties, fines, or prohibitions.
        """
        sanctions: list[str] = []
        for sent in sentences:
            if _SANCTION_SENT_RE.search(sent):
                sanctions.append(sent.strip())
        return _dedupe_ordered(sanctions, max_len=250)
