import json

# Funzione per creare una mappa delle carte da archetypeCards.json
def create_card_index_map(archetype_cards):

    #Crea una mappa che associa ogni carta al suo indice nel file archetypeCards.json.
    card_index_map = {}
    for index, card in enumerate(archetype_cards):
        card_name, card_set, card_number = card
        card_id = f"{card_set}-{card_number}"
        card_index_map[card_id] = index
    return card_index_map

# Funzione per codificare i mazzi
def encode_decks(archetype_decks, card_index_map, num_cards):

    #Codifica i mazzi in archetypeDecks.json come vettori di dimensione n.
    encoded_decks = {}

    for deck_name, deck_lists in archetype_decks.items():
        deck_counter = 1  # Contatore per mazzi con lo stesso nome

        for deck_list in deck_lists:
            # Inizializza un vettore di dimensione n con tutti zeri
            deck_vector = [0] * num_cards

            for card in deck_list:
                card_name = card["nome"]
                card_set = card["setesteso"]
                card_number = card["setnumero"]
                card_id = f"{card_set}-{card_number}"

                # Trova l'indice della carta nel vettore
                if card_id in card_index_map:
                    index = card_index_map[card_id]
                    deck_vector[index] = card["quantità"]
                else:
                    print(f"Errore: Carta '{card_name}' ({card_set}-{card_number}) non trovata in archetypeCards.json")

            # Gestisci mazzi con lo stesso nome
            if deck_name in encoded_decks:
                encoded_decks[f"{deck_name} {deck_counter}"] = deck_vector
                deck_counter += 1
            else:
                encoded_decks[deck_name] = deck_vector

    return encoded_decks

# Percorsi dei file
archetype_decks_file = "data/archetypeDecks.json"
archetype_cards_file = "data/archetypeCards.json"
output_file = "data/encodedDecks.json"

# Carica i file JSON
with open(archetype_decks_file, "r", encoding="utf-8") as f:
    archetype_decks = json.load(f)

with open(archetype_cards_file, "r", encoding="utf-8") as f:
    archetype_cards = json.load(f)

# Crea la mappa delle carte e ottieni il numero totale di carte
card_index_map = create_card_index_map(archetype_cards)
num_cards = len(archetype_cards)

# Codifica i mazzi
encoded_decks = encode_decks(archetype_decks, card_index_map, num_cards)

# Salva il file codificato
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(encoded_decks, f, indent=2, ensure_ascii=False)

print(f"File '{output_file}' generato con successo!")