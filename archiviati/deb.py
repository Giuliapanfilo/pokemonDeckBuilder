import json
import re

# Funzione per verificare se una stringa contiene solo numeri
def is_numeric(value):
    return bool(re.fullmatch(r'\d+', value))

# Carica il file JSON
with open('data/archetypeDecks.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# Lista per raccogliere le voci con "setnumero" non numerico
non_numeric_entries = []

# Itera attraverso i dati
for deck_name, deck_lists in data.items():
    for deck_list in deck_lists:
        for card in deck_list:
            setnumero = card.get("setnumero", "")
            if not is_numeric(setnumero):  # Controlla se "setnumero" non è numerico
                non_numeric_entries.append({
                    "deck": deck_name,
                    "card": card
                })

# Stampa i risultati
if non_numeric_entries:
    print("Voci con 'setnumero' non numerico:")
    for entry in non_numeric_entries:
        print(f"Deck: {entry['deck']}, Carta: {entry['card']}")
else:
    print("Tutte le voci hanno 'setnumero' numerico.")