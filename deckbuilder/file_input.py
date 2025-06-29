import json

def load_input_from_file():
    file_path = input("Inserisci il percorso del file JSON: ")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            input_deck = json.load(f)
        return input_deck
    except FileNotFoundError:
        print(f"Errore: File '{file_path}' non trovato.")
        return None
    except json.JSONDecodeError:
        print(f"Errore: Il file '{file_path}' non è un JSON valido.")
        return None