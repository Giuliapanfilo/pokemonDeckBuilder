import json

# Carica archetypeDecks_updated.json
with open("data/archetypeDecks_updated.json", "r", encoding="utf-8") as f:
    archetipi = json.load(f)

# Funzione per creare archetypesCards_updated.json
def create_archetypes_cards(archetipi):
    unique_cards = set()  # Usa un set per evitare duplicati
    for nomeArchetipo, mazzi in archetipi.items():
        for mazzo in mazzi:
            for carta in mazzo:
                if carta["setnumero"]:  # Assicurati che il setnumero non sia null
                    card_tuple = (carta["nome"], carta["setesteso"], carta["setnumero"])
                    unique_cards.add(card_tuple)  # Aggiungi la carta al set

    # Converti il set in una lista ordinata
    unique_cards_list = sorted(list(unique_cards))

    # Salva il file archetypesCards_updated.json
    with open("data/archetypesCards_updated.json", "w", encoding="utf-8") as f:
        json.dump(unique_cards_list, f, indent=2, ensure_ascii=False)

    print("File archetypesCards_updated.json creato con successo!")

# Crea il file archetypesCards_updated.json
create_archetypes_cards(archetipi)