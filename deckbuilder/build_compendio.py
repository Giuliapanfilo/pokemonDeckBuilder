import json
from fetch_card_id import cardIdByDict

# Carica il file archetypeDecks.json
with open("data/archetypeDecks.json", "r", encoding="utf-8") as f:
    archetipi = json.load(f)

compendio = set()
archetypes_map = {}

# Itera attraverso gli archetipi e costruisce archetypesMap
for nomeArchetipo, mazzi in archetipi.items():
    archetypesCards = {}  # Dizionario per contenere cardId e quantità
    for mazzo in mazzi:
        for carta in mazzo:
            # Ottieni l'ID della carta
            cardId = cardIdByDict(
                carta["nome"],
                carta["setesteso"],
                carta["setnumero"]
            )
            if cardId:
                compendio.add(cardId)
                # Aggiungi o aggiorna la quantità della carta
                if cardId in archetypesCards:
                    archetypesCards[cardId] += carta["quantità"]
                else:
                    archetypesCards[cardId] = carta["quantità"]
            else:
                print(f"Errore: ID non trovato per la carta '{carta['nome']}' nel set '{carta['setesteso']}' con numero '{carta['setnumero']}'")

    # Aggiungi il dizionario delle carte all'archetipo
    archetypes_map[nomeArchetipo] = archetypesCards

# Salva archetypesMap.json
with open("data/archetypesMap.json", "w", encoding="utf-8") as f:
    json.dump(archetypes_map, f, indent=2, ensure_ascii=False)

# Salva compendio.json
compendio = list(compendio)
with open("data/compendio.json", "w", encoding="utf-8") as f:
    json.dump(compendio, f, indent=2, ensure_ascii=False)

print(f"Carte uniche trovate: {len(compendio)}")
print("File archetypeMap.json e compendio.json generati con successo!")