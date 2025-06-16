import json
import os
import unicodedata
from fetch_card_id import setIdByName

# Percorsi dei file
archetype_decks_file = "data/archetypeDecks.json"
cards_directory = "data/cards/en"
output_file = "data/archetypeCards.json"

def normalize_name(name):
    """
    Normalizza il nome della carta normalizzando i caratteri Unicode
    e trattando eventuali discrepanze nei simboli.
    """
    # Normalizza i caratteri Unicode senza rimuovere spazi extra
    normalized_name = unicodedata.normalize("NFKC", name.lower())
    return normalized_name

def generate_archetype_cards(archetype_decks_file, cards_directory, output_file):
    try:
        # Carica il file archetypeDecks.json
        with open(archetype_decks_file, "r", encoding="utf-8") as f:
            archetype_decks = json.load(f)

        # Set per contenere le carte senza duplicati
        archetype_cards = set()

        # Itera attraverso i mazzi e le carte
        for deck_name, deck_lists in archetype_decks.items():
            for deck_list in deck_lists:
                for card in deck_list:
                    card_name = card["nome"]
                    set_extended = card["setesteso"]
                    set_number = card["setnumero"]

                    try:
                        # Ottieni l'ID del set
                        set_id = setIdByName(set_extended)

                        # Percorso del file del set
                        set_file = os.path.join(cards_directory, f"{set_id}.json")

                        # Carica il file del set
                        with open(set_file, "r", encoding="utf-8") as set_f:
                            set_data = json.load(set_f)

                        # Cerca la carta nel file del set
                        for set_card in set_data:
                            if (
                                normalize_name(set_card["name"]) == normalize_name(card_name)
                                and set_card["number"] == set_number
                            ):
                                # Aggiungi la carta al set
                                archetype_cards.add((card_name, set_extended, set_number))
                                break
                        else:
                            print(f"Errore: Carta '{card_name}' ({set_extended}-{set_number}) non trovata nel set '{set_id}'.")
                            print(f"Set '{set_extended}' convertito in ID '{set_id}'")

                    except ValueError as e:
                        print(f"Errore: {e}")
                    except FileNotFoundError:
                        print(f"Errore: File del set '{set_extended}' non trovato.")
                    except Exception as e:
                        print(f"Errore durante l'elaborazione della carta '{card_name}': {e}")

        # Converti il set in una lista e ordina i risultati
        archetype_cards_list = sorted(list(archetype_cards))

        # Salva il risultato nel file archetypeCards.json
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(archetype_cards_list, f, indent=2, ensure_ascii=False)

        print(f"File '{output_file}' generato con successo!")

    except FileNotFoundError:
        print(f"Errore: Il file '{archetype_decks_file}' non è stato trovato.")
    except json.JSONDecodeError:
        print(f"Errore: Il file '{archetype_decks_file}' non è un JSON valido.")
    except Exception as e:
        print(f"Si è verificato un errore: {e}")

# Esegui la funzione
generate_archetype_cards(archetype_decks_file, cards_directory, output_file)