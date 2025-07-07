import json
from fetch_card_id import setIdByName

# Funzione per creare una mappa delle carte da archetypeCards.json
def create_card_index_map(archetype_cards):
    card_index_map = {}
    for index, card in enumerate(archetype_cards):
        card_name, card_set, card_number = card
        card_id = f"{card_set}-{card_number}"
        card_index_map[card_id] = index
    return card_index_map

# Funzione per codificare i mazzi
def encode_decks(archetype_decks, card_index_map, num_cards):
    encoded_decks = {}

    for deck_name, deck_lists in archetype_decks.items():
        for i, deck_list in enumerate(deck_lists):
            # inizializza gli attributi del mazzo
            attributes = {
                "psychic": 0, "fire": 0, "grass": 0, "water": 0, "colorless": 0,
                "electric": 0, "fighting": 0, "lightning": 0, "metal": 0, "dragon": 0,
                "fairy": 0, "darkness": 0,
                "pokémon": 0, "item": 0, "trainer": 0, "stadium": 0, "helper": 0, "energy": 0
            }

            deck_vector = [0] * num_cards
            total_cards = 0
            pkmn_count = 0

            for card in deck_list:
                card_name = card["nome"]
                card_set = card["setesteso"]
                card_number = card["setnumero"]
                card_id = f"{card_set}-{card_number}"

                # Conversione sicura della quantità
                try:
                    quantita = int(card["quantità"])
                except ValueError:
                    print(f"⚠️  Quantità non valida: {card['quantità']} nella carta {card}")
                    continue

                if card_id in card_index_map:
                    index = card_index_map[card_id]
                    deck_vector[index] = quantita
                    total_cards += quantita

                    try:
                        set_id = setIdByName(card_set)
                        set_file = f"data/cards/en/{set_id}.json"
                    except ValueError as e:
                        print(f"Errore nel nome del set: {e}")
                        continue

                    try:
                        with open(set_file, "r", encoding="utf-8") as f:
                            set_data = json.load(f)
                            for set_card in set_data:
                                if set_card["name"] == card_name and set_card["number"] == card_number:
                                    for card_type in set_card.get("types", []):
                                        attributes[card_type.lower()] += quantita
                                    attributes[set_card["supertype"].lower()] += quantita
                                    if set_card["supertype"].lower() == "pokémon":
                                        pkmn_count += quantita
                                    break
                    except FileNotFoundError:
                        print(f"Errore: File del set '{set_file}' non trovato.")
                else:
                    print(f"⚠️  Carta '{card_name}' ({card_set}-{card_number}) non trovata in archetypeCards.json")

            # Calcolo percentuali
            if total_cards > 0:
                for key in attributes:
                    if key in ["psychic", "fire", "grass", "water", "colorless", "electric",
                               "fighting", "lightning", "metal", "dragon", "fairy", "darkness"]:
                        attributes[key] = round((attributes[key] / pkmn_count) * 100, 2) if pkmn_count > 0 else 0
                    else:
                        attributes[key] = round((attributes[key] / total_cards) * 100, 2)

            # Inserisci attributi all'inizio del vettore
            deck_vector = list(attributes.values()) + deck_vector
            encoded_decks[f"{deck_name} {i}"] = deck_vector

    return encoded_decks

# === MAIN ===
archetype_decks_file = "data/archetypeDecks.json"
archetype_cards_file = "data/archetypeCards.json"
output_file = "data/encodedDecks.json"

with open(archetype_decks_file, "r", encoding="utf-8") as f:
    archetype_decks = json.load(f)

with open(archetype_cards_file, "r", encoding="utf-8") as f:
    archetype_cards = json.load(f)

card_index_map = create_card_index_map(archetype_cards)
num_cards = len(archetype_cards)

encoded_decks = encode_decks(archetype_decks, card_index_map, num_cards)

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(encoded_decks, f, indent=2, ensure_ascii=False)

print(f"✅ File '{output_file}' generato con successo!")
