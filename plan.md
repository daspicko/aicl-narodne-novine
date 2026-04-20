# Plan projekta

## Radni naslov teme
**NLP sustav za sažimanje, izdvajanje ključnih informacija i semantičko pretraživanje državnih zakona**

Alternativna formalnija verzija:
**Primjena NLP metoda za sažimanje, izdvajanje ključnih informacija i semantičko pretraživanje korpusa državnih zakona**

---

## Konačna ideja projekta
Projekt nije scraping aplikacija sa “sažetkom kao featureom”, nego **pipeline za obogaćivanje korpusa zakona NLP slojem** i web aplikacija koja taj sloj koristi za inteligentno pretraživanje i pregled.

### Što već postoji
- scraper za dohvat zakona iz službenog izvora
- spremanje u JSON
- scraper izdvaja:
  - vrstu dokumenta
  - datum
  - ELI
  - naslov
  - puni tekst

### Što sustav treba raditi
- offline generirati sažetak zakona
- offline izdvajati ključne informacije
- offline generirati embeddinge
- spremati rezultate u JSON / PostgreSQL / vector store
- u NextJS aplikaciji omogućiti semantičko pretraživanje i pregled zakona

---

## Kako projekt gledati iz AI/NLP kuta
Scraping je samo **data ingestion layer**.

Pravi AI dio je:
1. **sažimanje** dugih pravnih tekstova
2. **izdvajanje ključnih informacija** iz nestrukturiranog teksta
3. **semantička reprezentacija** zakona pomoću embeddinga
4. **semantička pretraga** po značenju, a ne samo po ključnim riječima

### Važna razlika
- obična search/filter aplikacija: sprema tekst i traži po riječima
- AI/NLP sustav: nad tekstom gradi sažetak, strukturu i semantički indeks

Dobra formulacija:
> Scraping koristim samo za izgradnju korpusa zakona. Središnji dio rada je NLP obrada tog korpusa: automatsko generiranje sažetaka, izdvajanje ključnih informacija i stvaranje embeddinga za semantičko pretraživanje.

---

## Problem koji projekt rješava
Državni zakoni su:
- dugi
- formalni
- teško pregledni
- često se pretražuju samo po ključnim riječima
- korisniku nije lako brzo razumjeti sadržaj niti pronaći relevantan zakon ako ne zna točan termin

### Rješenje
Korpus zakona obogaćuje se NLP slojem koji omogućuje:
- kratki sažetak
- strukturirani pregled ključnih informacija
- semantičku pretragu po značenju

---

## Konačni cilj projekta
Izgraditi **NLP pipeline** koji nad korpusom državnih zakona automatski generira:
- sažetke
- ključne informacije
- vektorske reprezentacije dokumenata

i zatim ih koristi u **NextJS aplikaciji** za:
- inteligentno pretraživanje
- pregled zakona
- prikaz sažetaka i ključnih informacija

---

## Arhitektura sustava
Sustav se dijeli na 6 glavnih modula:

1. **Ingestion module**
2. **Normalization and document modeling module**
3. **NLP enrichment module**
4. **Storage and indexing module**
5. **Search/API module**
6. **NextJS frontend module**

---

## 1. Ingestion module
### Odgovornosti
- dohvat svih zakona iz službenog izvora
- parsiranje HTML/PDF izvora
- ekstrakcija:
  - ELI
  - title
  - date
  - document type
  - full text
  - source URL
  - broj NN ako postoji
- spremanje raw JSON-a

### Output primjer
```json
{
  "eli": "eli/...",
  "title": "Naziv zakona",
  "document_type": "zakon",
  "publication_date": "2024-01-01",
  "source_url": "https://...",
  "nn_number": "NN 123/2024",
  "raw_html": "...",
  "full_text": "...",
  "scraped_at": "2026-04-06T12:00:00Z"
}
```

### Napomene
- deduplikacija po ELI
- idempotentno pokretanje
- logiranje grešaka
- raw storage odvojiti od finalnih tablica

---

## 2. Normalization and document modeling
### Odgovornosti
- validacija raw podataka
- čišćenje teksta
- standardizacija polja
- segmentacija dokumenta
- izrada canonical document modela

### Canonical model dokumenta
- id
- eli
- title
- slug
- document_type
- publication_date
- source_url
- nn_number
- full_text
- clean_text
- language
- status
- version_hash

### Segmentacija
Treba imati i segmente:
- članci
- odlomci
- rečenice

Segmenti su važni za:
- extraction
- passage retrieval
- fine-grained embeddings
- prikaz relevantnih dijelova u UI-u

---

## 3. NLP enrichment module
Ovo je jezgra projekta.

Dijeli se na 4 podmodula:
1. summarization
2. information extraction
3. embeddings
4. enrichment orchestration

### 3.1 Summarization
Generirati više vrsta sažetka:
- **short summary**: 2–4 rečenice
- **detailed summary**: 6–10 rečenica
- **structured summary**:
  - što zakon uređuje
  - na koga se odnosi
  - što uvodi ili mijenja

Za duge zakone koristiti:
- chunking
- map-reduce summarization
- final synthesis

### 3.2 Information extraction
Izdvajati:
- responsible bodies
- obligations
- deadlines
- scope
- subjects
- opcionalno sanctions / consequences

Primjeri:
- **responsible bodies**: Ministarstvo financija, Vlada RH
- **obligations**: tko što mora učiniti
- **deadlines**: “u roku od 30 dana”, “stupa na snagu osmoga dana”
- **scope**: na koga se zakon odnosi
- **subjects**: teme zakona

Preporučeni pristup je **hibridan**:
- regex i pravila za rokove
- NER / entity extraction za tijela
- LLM / structured extraction za scope i obligations
- heuristike za validaciju

### 3.3 Embeddings
Generirati embeddinge na više razina:
- **document embedding**
- **summary embedding**
- **segment embedding**

To omogućuje:
- retrieval relevantnog zakona
- retrieval relevantnog dijela zakona
- bolju semantičku pretragu

### 3.4 Enrichment orchestration
Pipeline po dokumentu:
1. normalize document
2. generate segments
3. generate summaries
4. extract key information
5. generate embeddings
6. persist outputs
7. mark document as indexed

Statusi obrade:
- raw
- normalized
- summarized
- extracted
- embedded
- published
- failed

---

## 4. Storage and indexing
### Preporučeni stack
- **PostgreSQL + pgvector**

To je preporučeno umjesto odvojene vector baze jer je jednostavnije za deployment, a dovoljno jako za projekt.

### Vrste pohrane
- **JSON**: eksport, debug, batch obrada, reproducibilnost
- **PostgreSQL**: metapodaci, tekst, summary, key info
- **pgvector**: embeddingi i semantic similarity search

---

## 5. Search / API module
### Preporučena tehnologija
- **FastAPI** backend

### Zašto odvojeni backend
NLP i search orchestration je čišće držati odvojeno od NextJS-a.

### API endpointi
#### Documents
- `GET /api/documents`
- `GET /api/documents/{id}`
- `GET /api/documents/{eli}`
- `GET /api/documents/{slug}`

#### Search
- `POST /api/search`
- `GET /api/search/suggest?q=...`

#### Admin
- `POST /api/admin/documents/{id}/reindex`
- `POST /api/admin/documents/{id}/summarize`
- `POST /api/admin/documents/{id}/extract`
- `POST /api/admin/documents/{id}/embed`
- `GET /api/admin/jobs`

### Search strategija
Koristiti **hybrid search**:
1. lexical search
2. semantic search
3. reranking

#### Query flow
1. korisnik upiše upit
2. query se normalizira
3. generira se query embedding
4. lexical retrieval vraća kandidate
5. semantic retrieval vraća kandidate
6. kandidati se spajaju
7. radi se reranking
8. vraćaju se top rezultati s:
   - title
   - short summary
   - highlights
   - key info preview

---

## 6. NextJS frontend module
### Tehnologije
- NextJS
- TypeScript
- Tailwind

### Glavne stranice
- `/` home
- `/search?q=...`
- `/documents/[slug]`
- `/admin` opcionalno

### Home
- search bar
- opis sustava
- primjeri upita
- zadnji dodani / popularni zakoni

### Search results
- lista rezultata
- sažetak
- highlights
- key info preview
- filter sidebar

### Document page
Prikazati:
- title
- ELI
- datum
- vrstu dokumenta
- short summary
- detailed summary
- key information
- relevant segments
- puni tekst
- link na izvor

### Bitno za UX
Na result card prikazivati:
- naslov
- datum
- kratki sažetak
- 1–2 ključne informacije
- jedan relevantni segment

Na detail page:
- summary gore
- structured info odmah ispod
- full text niže

---

## End-to-end tok sustava
### Offline tok
1. scraper dohvaća zakon
2. raw JSON se sprema
3. normalization pipeline čisti dokument
4. segmentation pipeline dijeli ga na članke/paragrafe
5. summarizer generira summaryje
6. extractor generira key info
7. embedding generator stvara vektore
8. sve se sprema u PostgreSQL/pgvector
9. dokument dobiva status `published`

### Online tok
1. korisnik otvara NextJS aplikaciju
2. upisuje upit
3. frontend šalje upit backendu
4. backend radi hybrid retrieval
5. dohvaća top dokumente i segmente
6. vraća strukturirani rezultat
7. frontend prikazuje rezultate
8. klik na dokument otvara detaljni prikaz

---

## Preporučeni model podataka
Glavne tablice:
- `documents`
- `document_segments`
- `document_summaries`
- `document_key_information`
- `document_embeddings`
- `processing_jobs`
- opcionalno `document_versions`

### documents
Drži canonical zapis zakona.
Polja:
- id
- eli
- title
- slug
- document_type
- publication_date
- nn_number
- source_url
- language_code
- status
- full_text
- clean_text
- text_hash
- raw_payload
- created_at
- updated_at

### document_segments
Drži članke, odlomke i druge segmente.
Polja:
- id
- document_id
- segment_type
- segment_order
- article_label
- heading
- text
- text_hash
- metadata

### document_summaries
Drži više summary varijanti.
Polja:
- id
- document_id
- summary_type (`short`, `detailed`, `structured`)
- model_name
- model_version
- summary_text
- summary_json
- quality_score

### document_key_information
Drži strukturirano izdvojene informacije.
Polja:
- id
- document_id
- responsible_bodies
- obligations
- deadlines
- scope
- subjects
- sanctions
- extraction_model_name
- extraction_model_version
- confidence_score

### document_embeddings
Drži embeddinge.
Polja:
- id
- document_id
- segment_id nullable
- embedding_type (`document`, `summary`, `segment`, `title`)
- model_name
- model_version
- text_snapshot
- embedding

### processing_jobs
Praćenje statusa obrade.
Polja:
- id
- document_id
- job_type
- status
- attempt_count
- payload
- result
- error_message
- started_at
- finished_at
- created_at

---

## Ključni response shapeovi API-ja
### Document detail response
Treba sadržavati:
- osnovne metapodatke
- summaries:
  - short
  - detailed
  - structured
- keyInformation:
  - responsibleBodies
  - obligations
  - deadlines
  - scope
  - subjects
- relevantSegments
- fullText

### Search response
Treba sadržavati:
- query
- pagination
- results[]

Svaki rezultat:
- documentId
- slug
- eli
- title
- documentType
- publicationDate
- nnNumber
- shortSummary
- matchScore
- matchType
- highlights
- keyInfoPreview

---

## Tehnička organizacija repozitorija
Predloženi monorepo:

```text
project-root/
├── apps/
│   ├── web/                  # NextJS
│   └── api/                  # FastAPI
├── services/
│   ├── scraper/
│   ├── normalizer/
│   ├── summarizer/
│   ├── extractor/
│   ├── embedder/
│   └── indexer/
├── packages/
│   ├── shared-types/
│   └── shared-config/
├── infra/
│   ├── docker/
│   ├── migrations/
│   └── scripts/
├── data/
│   ├── raw/
│   ├── normalized/
│   └── exports/
├── notebooks/
├── docs/
└── docker-compose.yml
```

---

## Točan plan implementacije po fazama
### Faza 1 — Core ingestion and storage
- stabilizirati scraper
- definirati canonical document schema
- napraviti PostgreSQL schema
- import raw JSON -> DB
- generirati slugove
- napraviti document detail API

### Faza 2 — Summarization pipeline
- chunking za duge zakone
- short summary
- detailed summary
- structured summary
- spremanje summaryja u bazu

### Faza 3 — Extraction pipeline
- deadlines extraction
- responsible bodies extraction
- obligations extraction
- scope extraction
- validacija i spremanje

### Faza 4 — Embeddings and search
- document embeddings
- segment embeddings
- query embeddings
- hybrid search
- reranking

### Faza 5 — NextJS app
- homepage
- search page
- document page
- filters
- result ranking UI

### Faza 6 — Ops and quality
- processing job queue
- retry/failure handling
- logging
- benchmarking
- evaluacija

---

## Evaluacija projekta
Pošto je cilj puna aplikacija, evaluirati treba i NLP i search.

### NLP evaluacija
- kvaliteta sažetka
- kvaliteta extractiona
- ručna evaluacija korisnosti

### Search evaluacija
Na skupu queryja mjeriti:
- Precision@k
- Recall@k
- MRR
- opcionalno nDCG

### Performance evaluacija
- vrijeme odgovora searcha
- veličina embedding indeksa
- RAM usage
- ponašanje na malom VPS-u

---

## Skalabilnost na malom VPS-u
Rješenje je da gotovo sve radi **offline**:
- summary generation offline
- info extraction offline
- embeddings offline
- indexing offline

Online ostaje:
- query embedding
- vector similarity search
- DB read
- render

Ako treba:
- frontend hostati odvojeno
- batch enrichment raditi lokalno ili na jačem stroju
- deployati samo gotov indeks i bazu

---

## Konačna formulacija teme
**NLP sustav za sažimanje, izdvajanje ključnih informacija i semantičko pretraživanje državnih zakona**

### Kratki opis teme
Projekt obuhvaća izgradnju korpusa državnih zakona iz službenog izvora, njihovu normalizaciju i obogaćivanje NLP metodama. Nad zakonima se offline generiraju sažeci, izdvajaju ključne informacije poput nadležnih tijela, obveza, rokova i područja primjene te stvaraju vektorske reprezentacije za semantičko pretraživanje. Obogaćeni korpus koristi se u NextJS web aplikaciji koja omogućuje inteligentno pretraživanje i pregled zakona.

---

## Ključni zaključci razgovora
1. Projekt nije scraping projekt ako je scraping samo faza izgradnje korpusa.
2. AI jezgra projekta su:
   - summarization
   - information extraction
   - embeddings
   - semantic retrieval
3. NextJS aplikacija je prezentacijski sloj, ne središnji dio projekta.
4. Za punu aplikaciju treba razdvojiti:
   - ingestion
   - normalization
   - enrichment
   - storage/indexing
   - search API
   - frontend
5. Najčišća i najpraktičnija arhitektura za projekt je:
   - FastAPI + PostgreSQL + pgvector + NextJS
6. Search treba biti **hybrid**, ne samo lexical i ne samo vector.
7. Teški NLP poslovi trebaju se raditi offline.
8. Segment embeddings su važni ako želiš kvalitetno pretraživanje po sadržaju zakona.
9. Projekt je dovoljno izazovan i ozbiljan kao puna aplikacija.
10. Najbolja službena formulacija teme je:
    **NLP sustav za sažimanje, izdvajanje ključnih informacija i semantičko pretraživanje državnih zakona**
