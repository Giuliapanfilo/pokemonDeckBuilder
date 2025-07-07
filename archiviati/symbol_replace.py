import os
import json

# Percorso della directory contenente i file JSON
cards_directory = "data/cards/en"

def replace_star_symbols(directory):
    """
    Sostituisce il simbolo '☆' con '★' in tutti i file JSON presenti nella directory specificata.
    """
    try:
        # Itera attraverso tutti i file nella directory
        for filename in os.listdir(directory):
            if filename.endswith(".json"):  # Considera solo i file JSON
                file_path = os.path.join(directory, filename)

                # Leggi il contenuto del file JSON
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Sostituisci il simbolo  '★' con '☆' ovunque nei dati
                def replace_stars(obj):
                    if isinstance(obj, str):
                        return obj.replace("★", "☆")
                    elif isinstance(obj, list):
                        return [replace_stars(item) for item in obj]
                    elif isinstance(obj, dict):
                        return {key: replace_stars(value) for key, value in obj.items()}
                    return obj

                updated_data = replace_stars(data)

                # Scrivi i dati aggiornati nel file
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(updated_data, f, indent=2, ensure_ascii=False)

                print(f"Simboli aggiornati nel file: {filename}")

    except Exception as e:
        print(f"Si è verificato un errore: {e}")

# Esegui la funzione
replace_star_symbols(cards_directory)