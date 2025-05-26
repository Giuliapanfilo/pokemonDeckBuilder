# 🧠 Progetto: Sistema Intelligente per la Costruzione di Mazzi Pokémon
## Basato su RDF/OWL + Machine Learning

---

## 🔹 FASE 1 – Preparazione Dati (Cards + Tournament Decks)

- [ ] **Pulizia e validazione del file `cards_data.json`**
  - Verificare che tutti i campi siano coerenti (`types`, `attacks`, `match_keys`, `evolvesTo`, ecc.)
  - Assicurarsi che ogni carta abbia un identificatore univoco: `name + set + number`
  - Correggere valori problematici (es. `"Pokémon"` scritto correttamente come supertype)
  - Uniformare nomi e formati di campi (es. attacchi: nome, costo, danno, testo)
  
- [ ] **Pulizia e validazione del file `tournament_decks.json`**
  - Verificare consistenza tra nomi/set/numero carte e quelli in `cards_data.json`
  - Uniformare i riferimenti per facilitare l'integrazione nei grafi RDF

---

## 🔹 FASE 2 – Costruzione Ontologia OWL/RDF (Obbligatoria)

- [ ] **Progettare l’ontologia base**
  - **Classi principali:**
    - `Card`, `PokemonCard`, `TrainerCard`, `EnergyCard`, `Attack`, `Deck`, `Tournament`, `Player`
  - **Proprietà (object/data):**
    - `hasType`, `hasAttack`, `evolvesTo`, `evolvesFrom`
    - `requiresEnergy`, `hasRarity`, `belongsToSet`, `includedInDeck`, `playedBy`

- [ ] **Creare file OWL (in Turtle o RDF/XML)**
  - Usare **Protégé** per creare e visualizzare l’ontologia
  - Esportare il file in formato compatibile con `rdflib` (es. `.ttl` o `.rdf`)

- [ ] **Popolare l’ontologia con i dati reali**
  - Scrivere uno script Python per:
    - Caricare `cards_data.json`
    - Creare istanze OWL per ogni carta e per ogni attacco come risorse RDF separate
    - Rappresentare ogni attacco con proprietà: nome, costo (lista), danno (numerico se possibile), testo descrittivo
    - Collegare gli attacchi alle carte tramite proprietà `hasAttack`
    - Aggiungere tutte le altre proprietà della carta (tipo, supertipo, evoluzioni, rarità, ecc.)

- [ ] **Inserire dati dei tornei**
  - Ogni mazzo diventa un’istanza della classe `Deck`
  - Le carte vengono collegate al mazzo tramite `includedInDeck`
  - Il mazzo viene associato a un `Player` e a un `Tournament`
  - Uniformare e collegare i riferimenti carte tra mazzi e knowledge base RDF

---

## 🔹 FASE 3 – Query e Inferenze con RDF

- [ ] **Caricare grafo RDF in Python**
  - Usare `rdflib.Graph()` per caricare il file OWL popolato

- [ ] **Scrivere query SPARQL**
  - Esempi:
    - Tutte le carte che evolvono da un certo Pokémon
    - Tutte le carte dello stesso tipo di una carta chiave
    - Le carte più frequentemente incluse insieme alla carta X (sinergie)
    - Recuperare gli attacchi di una carta con tutte le loro proprietà

- [ ] **Implementare regole di inferenza**
  - Definire regole OWL/RDFS personalizzate per inferenze (es. sinergie basate su frequenza d’uso nel mazzo)
  - Usare motori di inferenza come `owlrl` o simili in Python
  - Esempio: se due carte compaiono spesso insieme in mazzi vincenti, marcate come `sinergiche`

---

## 🔹 FASE 4 – Creazione Dataset per Machine Learning

- [ ] **Estrarre dati strutturati dal grafo RDF**
  - Ogni record = un mazzo (istanza `Deck`)
  - Features = one-hot encoding delle carte presenti nel mazzo, con chiara mappatura tra RDF e vettorializzazione
  - Target:
    - `Top8` (sì/no)
    - oppure `placing` (per regressione)

- [ ] **Preprocessing**
  - Uniformare e vettorializzare le carte in base agli ID RDF
  - Normalizzare i dati
  - Dividere in set di train e test

---

## 🔹 FASE 5 – Modello di Apprendimento Automatico

- [ ] **Scegliere modello**
  - Random Forest, Logistic Regression o altro classificatore interpretabile e semplice

- [ ] **Addestrare il modello**
  - Input: vettore binario delle carte + carta chiave
  - Output: probabilità che una carta sia utile nel mazzo

- [ ] **Valutare le performance**
  - Metriche: Accuracy, Precision, Recall, Confusion matrix

- [ ] **Salvare il modello**
  - Usare `joblib` o `pickle` per serializzazione

---

## 🔹 FASE 6 – Costruttore di Mazzi Automatizzato

- [ ] **Script `deck_builder.py`**
  - Input: nome della carta chiave
  - Step 1: query SPARQL per estrarre carte sinergiche e attacchi (da RDF)
  - Step 2: applica modello ML per ordinare e selezionare le migliori carte da aggiungere
  - Step 3: compone mazzo rispettando regole personalizzate (es. 20 Pokémon, 20 Trainer, 20 Energie)
  - Step 4: includere eventuali filtri o preferenze utente

- [ ] **Esportazione mazzo finale**
  - Output in `.json` o `.txt`
  - (Facoltativo) stampa leggibile su console o in file

- [ ] **(Facoltativo) Interfaccia CLI o GUI**
  - Interfaccia per scelta guidata della carta chiave e visualizzazione risultati

---

## 🔹 FASE 7 – Consegna Finale

- [ ] **Relazione tecnica**
  - In PDF: Obiettivo, Dati, Ontologia, RDF, SPARQL, ML, Risultati
  - Includere diagrammi (ontologia, architettura sistema, esempi query)
  - Spiegare scelte di modellazione RDF e ML

- [ ] **Demo funzionante**
  - Script pronto all’uso (da console)
  - Funzionalità: generazione mazzo da carta chiave + stampa risultati
  - Dimostrare inferenze e query RDF + performance ML

---

## 📎 Extra (facoltativi ma impressionanti)

- [ ] Interfaccia CLI interattiva con scelta guidata e spiegazioni
- [ ] Visualizzazioni grafiche sui tipi di mazzi e sinergie (clustering, heatmap)
- [ ] Supporto multilingua o spiegazioni interattive per l’utente
- [ ] Integrare meccanismi di feedback per migliorare il modello ML nel tempo
