import json
import os
from fetch_card_id import setIdByName
from encoding import create_card_index_map  # Importa la funzione esistente

def load_input_from_file():
    """
    Permette all'utente di selezionare un file JSON contenente il mazzo incompleto.
    """
    file_path = input("Inserisci il percorso del file JSON: ")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            input_deck = json.load(f)
        return input_deck, file_path
    except FileNotFoundError:
        print(f"Errore: File '{file_path}' non trovato.")
        return None, None
    except json.JSONDecodeError:
        print(f"Errore: Il file '{file_path}' non è un JSON valido.")
        return None, None

def encode_single_deck(deck_name, deck_list, card_index_map, num_cards):
    """
    Codifica un singolo mazzo fornito come input JSON.
    """
    # Inizializza gli attributi del mazzo
    attributes = {
        "psychic": 0,
        "fire": 0,
        "grass": 0,
        "water": 0,
        "colorless": 0,
        "electric": 0,
        "fighting": 0,
        "lightning": 0,
        "metal": 0,
        "dragon": 0,
        "fairy": 0,
        "darkness": 0,
        "pokémon": 0,
        "item": 0,
        "trainer": 0,
        "stadium": 0,
        "helper": 0,
        "energy": 0
    }
    # Inizializza un vettore di dimensione n con tutti zeri
    deck_vector = [0] * num_cards
    total_cards = 0
    pkmn_count = 0

    for card in deck_list:
        card_name = card["nome"]
        card_set = card["setesteso"]
        card_number = card["setnumero"]
        card_id = f"{card_set}-{card_number}"

        # Trova l'indice della carta nel vettore
        if card_id in card_index_map:
            index = card_index_map[card_id]
            deck_vector[index] = card["quantità"]
            total_cards += card["quantità"]

            try:
                set_id = setIdByName(card_set)
                set_file = f"data/cards/en/{set_id}.json"
            except ValueError as e:
                print(f"Errore: {e}")
                continue

            try:
                with open(set_file, "r", encoding="utf-8") as f:
                    set_data = json.load(f)
                    for set_card in set_data:
                        if set_card["name"] == card_name and set_card["number"] == card_number:
                            # Incrementa i contatori per types e supertype
                            for card_type in set_card.get("types", []):
                                attributes[card_type.lower()] += card["quantità"]
                            attributes[set_card["supertype"].lower()] += card["quantità"]
                            if set_card["supertype"].lower() == "pokémon":
                                pkmn_count += card["quantità"]
                            break
            except FileNotFoundError:
                print(f"Errore: File del set '{set_file}' non trovato.")
        else:
            print(f"Errore: Carta '{card_name}' ({card_set}-{card_number}) non trovata in archetypeCards.json")

    # Trasforma gli attributi in percentuali
    if total_cards > 0:
        for key in attributes:
            if key in ["psychic", "fire", "grass", "water", "colorless", "electric",
                       "fighting", "lightning", "metal", "dragon", "fairy", "darkness"]:
                attributes[key] = round((attributes[key] / pkmn_count) * 100, 2) if pkmn_count > 0 else 0.0
            else:
                attributes[key] = round((attributes[key] / total_cards) * 100, 2)

    # Aggiungi gli attributi all'inizio del vettore
    deck_vector = list(attributes.values()) + deck_vector

    return {deck_name: deck_vector}

def encode_incomplete_deck(input_deck, archetype_cards_file):
    """
    Codifica un mazzo incompleto fornito come input JSON.
    """
    # Carica il file archetypeCards.json
    with open(archetype_cards_file, "r", encoding="utf-8") as f:
        archetype_cards = json.load(f)

    # Crea la mappa delle carte e ottieni il numero totale di carte
    card_index_map = create_card_index_map(archetype_cards)
    num_cards = len(archetype_cards)

    # Codifica il mazzo
    for deck_name, deck_lists in input_deck.items():
        for deck_list in deck_lists:
            encoded_deck = encode_single_deck(deck_name, deck_list, card_index_map, num_cards)
            return encoded_deck

def save_encoded_deck(encoded_deck, file_path):
    """
    Salva il file encodato nella cartella data/inputdecks.
    """
    # Crea la cartella inputdecks se non esiste
    inputdecks_dir = os.path.join("data", "inputdecks")
    os.makedirs(inputdecks_dir, exist_ok=True)

    # Usa il nome del file JSON per creare il file encodato
    file_name = os.path.basename(file_path).split(".")[0]
    encoded_path = os.path.join(inputdecks_dir, f"{file_name}_encoded.json")

    # Salva il file encodato
    with open(encoded_path, "w", encoding="utf-8") as f:
        json.dump(encoded_deck, f, indent=2, ensure_ascii=False)

    print(f"File encodato salvato in: {encoded_path}")

# Esempio di utilizzo
if __name__ == "__main__":
    # Carica il mazzo incompleto da file
    input_deck, file_path = load_input_from_file()
    if input_deck:
        # Percorso del file archetypeCards.json
        archetype_cards_file = "data/archetypeCards.json"

        # Codifica il mazzo incompleto
        encoded_deck = encode_incomplete_deck(input_deck, archetype_cards_file)

        # Salva il risultato
        save_encoded_deck(encoded_deck, file_path)