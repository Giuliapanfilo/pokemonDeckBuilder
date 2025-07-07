import os
import json

# === 1. Leggi tutti gli ID unici dalle decklist base ===
base_decks_dir = "data/decks/en"
base_card_ids = set()

for filename in os.listdir(base_decks_dir):
    if filename.endswith(".json"):
        file_path = os.path.join(base_decks_dir, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                decks = json.load(f)
                for deck in decks:
                    for card in deck.get("cards", []):
                        card_id = card.get("id")
                        if card_id:
                            base_card_ids.add(card_id)
        except Exception as e:
            print(f"Errore nel file {filename}: {e}")

print(f"Carte uniche nei mazzi base: {len(base_card_ids)}")

# === 2. Leggi gli ID delle carte dagli archetipi (compendio.json) ===
compendio_path = "data/compendio.json"
try:
    with open(compendio_path, "r", encoding="utf-8") as f:
        archetype_card_ids = set(json.load(f))
except Exception as e:
    print(f"Errore nel file compendio.json: {e}")
    archetype_card_ids = set()

print(f"Carte uniche negli archetipi: {len(archetype_card_ids)}")

# === 3. Confronto e Unione ===
all_unique_cards = base_card_ids.union(archetype_card_ids)
common_cards = base_card_ids.intersection(archetype_card_ids)
only_in_base = base_card_ids.difference(archetype_card_ids)
only_in_archetypes = archetype_card_ids.difference(base_card_ids)

print(f"Totale carte uniche (archetipi + base): {len(all_unique_cards)}")
print(f"Carte presenti sia nei mazzi base che negli archetipi: {len(common_cards)}")
print(f"Carte solo nei mazzi base: {len(only_in_base)}")
print(f"Carte solo negli archetipi: {len(only_in_archetypes)}")
