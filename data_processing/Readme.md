# Narodne novine - Obrada podataka

Ovaj modul sadrži kod za obradu podataka iz Narodnih novina. Podaci su preuzeti sa službene web stranice Narodnih novina i obrađeni kako bi se dobili strukturirani podaci o zakonima, uredbama i drugim pravnim aktima.

# Modules

## Initialization

Preuzimanje modula sa Hugging Face Hub-a u lokalni cache direktorij kako bi modeli radili bez potrebe za API pozivima. Ovaj korak je važan za smanjenje latencije, povećanje brzine obrade podataka i uklanjanje ograničenja poziva prema HuggingFace API-ima.

## Scraping

Preuzimanje podataka sa web stranice Narodnih novina. Ovaj proces uključuje slanje HTTP zahtjeva, parsiranje HTML sadržaja i ekstrakciju relevantnih informacija o zakonima, uredbama i drugim pravnim aktima.

## Normalization

Čišćenje i standardizacija podataka kako bi se osigurala konzistentnost i kvaliteta. Ovaj korak uključuje uklanjanje nepotrebnih znakova, ispravljanje formata datuma, standardizaciju naziva zakona i drugih relevantnih informacija. U ovom se koraku radi i segmentacija teksta na manje dijelove, što je važno za daljnju obradu i analizu podataka.

## Summarization

Korištenje modela za sažimanje teksta kako bi se dobili sažeci zakona, uredbi i drugih pravnih akata.

## Extraction

Izvlačenje ključnih informacija iz zakona, uredbi i drugih pravnih akata, kao što su nazivi, datumi, relevantne odredbe i slično.

## Embedding

Izračunavanje vektorskih reprezentacija zakona, uredbi i drugih pravnih akata kako bi se omogućila semantička pretraga i analiza podataka.

## Storage

Spremanje obrađenih podataka u bazu podataka. Ovaj korak uključuje organizaciju podataka na način koji omogućava jednostavan pristup i pretragu, kao i osiguravanje sigurnosti i integriteta podataka.
