import json
import os

# Funzione per verificare se una stringa contiene solo numeri
def is_numeric(value):
    return value.isdigit()

# Funzione per correggere il setnumero
def correct_set_number(card, set_path):
    """
    Corregge il campo 'setnumero' di una carta cercando il valore corretto nel file del set.
    """
    set_id = card["setnumero"]
    card_name = card["nome"]

    # Percorso del file del set
    set_file = os.path.join(set_path, f"{set_id}.json")

    try:
        # Apri il file del set
        with open(set_file, "r", encoding="utf-8") as f:
            set_data = json.load(f)

        # Cerca la carta nel file del set
        for set_card in set_data:
            if set_card["name"].strip() == card_name.strip():
                # Aggiorna il setnumero con il valore corretto
                card["setnumero"] = set_card["number"]
                print(f"Corretto 'setnumero' per '{card_name}': {card['setnumero']}")
                return

        print(f"Errore: Carta '{card_name}' non trovata nel set '{set_id}'.")

    except FileNotFoundError:
        print(f"Errore: File del set '{set_id}' non trovato.")
    except Exception as e:
        print(f"Errore durante la correzione di '{card_name}': {e}")

# Funzione principale per trovare e correggere i setnumero non numerici
def process_archetype_decks(file_path, set_path):
    # Carica il file archetypeDecks.json
    with open(file_path, "r", encoding="utf-8") as f:
        archetype_decks = json.load(f)

    # Itera attraverso i mazzi e le carte
    for deck_name, deck_lists in archetype_decks.items():
        for deck_list in deck_lists:
            for card in deck_list:
                setnumero = card.get("setnumero", "")
                if not is_numeric(setnumero):  # Controlla se "setnumero" non è numerico
                    correct_set_number(card, set_path)

    # Salva il file aggiornato
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(archetype_decks, f, indent=2, ensure_ascii=False)

    print("Correzione completata e file salvato.")

# Percorsi dei file
archetype_decks_file = "data/archetypeDecks.json"
set_files_path = "data/cards/en"

# Esegui lo script
process_archetype_decks(archetype_decks_file, set_files_path)