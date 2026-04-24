# NLP sustav za sažimanje, izdvajanje ključnih informacija i semantičko pretraživanje državnih zakona, pravilnika i odluka

## O projektu

### Opis problema
Državni zakoni su dugi, formalni, teško pregledni i pretražuju se po ključnim riječima ili broju narodnih novina što otežava pronalazak releventnih zakona korisnicima koji nisu educirani u pravnom ili upravnom području. 

### Ciljevi projekta

Kreirati sustav koji će NLP cijevovodom (engl. pipeline) obogatiti postojeće zakone dostupne na stranicama Narodnih novina:
- sažetcima
- ključnim informacijama
- vektorskim reprezentacijama dokumenata

Kreirati aplikaciju koja će omogućiti:
- prikaz sažetaka i ključnih informacija
- semantičko pretraživanje
- pregled zakona (s bržim dohvatom dokumenata)

## Dataset

Podaci su preuzeti sa službenih stranica [Narodnih novina](https://narodne-novine.nn.hr/data_access_hr.aspx) te su poštivane upute za pristup i obradu podataka. Iz tog razloga se ne koristi API, već su podaci preuzeti pomoću skripti koja je dostupna u repozitoriju. Podaci su preuzeti u obliku JSON datoteka koje sadrže zakone, pravilnike i odluke.

Podaci sadrže službene objave zakona, pravilnika i odluka, uključujući naslove, datume donošenja, tekstove i druge relevantne informacije.

- Dio NN
- Vrsta dokumenta (Zakon | Pravilnik | Odluka)
- Izdanje (NN xx/yyyy)
- Broj dokumenta u izdanju
- Donositelj
- Datum tiskanog izdanja
- ELI (European Legislation Identifier)
- Tekst dokumenta

## Modeli

Za potrebe projekta nisu bili trenirani vlastiti modeli, već su korišteni već trenirani modeli dostupni na Hugging Face platformi. 

- Za sažimanje i izdvajanje ključnih informacija korišten je model [microsoft/deberta-v3-large](https://huggingface.co/microsoft/deberta-v3-large)
- za semantičko pretraživanje korišten model [sentence-transformers/all-mpnet-base-v2](https://huggingface.co/sentence-transformers/all-mpnet-base-v2)
- Ostali isprobani modeli:
  - Sažimanje:
    - [classla/bcms-bertic](https://huggingface.co/classla/bcms-bertic)
    - [FacebookAI/xlm-roberta-large](https://huggingface.co/FacebookAI/xlm-roberta-large)
    - [microsoft/deberta-v3-large](https://huggingface.co/microsoft/deberta-v3-large)
  - Semantičko pretraživanje:
    - [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
    - [sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)
    - [sentence-transformers/all-mpnet-base-v2](https://huggingface.co/sentence-transformers/all-mpnet-base-v2)


## Pokretanje

Za pokretanje projekta potrebno je imati instaliran Python 3 (rađeno na verziji 3.13, ali vjerojatno radi i sa starijim verzijama). Također je potrebno instalirati potrebne biblioteke koje su navedene u `requirements.txt` datotekama. To je najjednostavnije odraditi sa alatom [uv](https://docs.astral.sh/uv/getting-started/installation/).
Vektorske reprezentacije dokumenta su spremljene u pgvector bazi podataka, stoga je potrebno imati instaliran pgvector extension za PostgreSQL bazu podataka.
Najjednostavniji način pokretanja projekta je korištenje Docker-a, gdje su svi dijelovi projekta već konfigurirani i spremni za pokretanje. U tom slučaju je potrebno imati instaliran Docker te pokrenuti naredbu:

```bash
uv venv --clear && source .venv/bin/activate && uv pip install -r api/requirements.txt && uv pip install -r data_processing/requirements.txt
```
```bash
docker run pgvector/pgvector:pg18-trixie -p 8080:8080 -e POSTGRES_PASSWORD=mysecretpassword
```

Projekt se sastoji od tri dijela te je potrebno pokrenuti svaki od njih.

### Obrada podataka

Obrada podataka se vrši pomoću skripti koje su dostupne u `data_processing` direktoriju. Skripte su napisane u Pythonu te se pokreću pomoću naredbe:

```bash
cd data_processing && ./pipeline.sh && cd -
```

### API (FastAPI)

API je pisan u FastAPI frameworku i služi za dohvat vektorskih reprezentacija dokumenata. API se pokreće pomoću naredbe:

```bash
cd api && fastapi dev && cd -
```

### Web aplikacija (Next.js)

Web aplikacija je pisana u Next.js frameworku i služi za prikaz sažetaka, ključnih informacija i semantičko pretraživanje zakona. Web aplikacija se pokreće pomoću naredbe:

```bash
cd ui && bun run dev && cd -
```
