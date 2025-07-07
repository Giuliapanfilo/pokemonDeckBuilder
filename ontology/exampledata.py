import json
import os

CARDS_DIR = "data/cards/en"
OUTPUT_FILE = "examples_supertype_subtype_filtered.json"

def extract_relevant_fields(card):
    filtered = {
        "id": card.get("id"),
        "name": card.get("name"),
        "supertype": card.get("supertype"),
        "subtypes": card.get("subtypes"),
        "types": card.get("types"),
        "hp": card.get("hp"),
        "rarity": card.get("rarity"),
        "set": card.get("set"),
    }

    # Estraggo abilities con solo nome e testo effetto
    abilities = card.get("abilities")
    if abilities:
        filtered["abilities"] = []
        for ab in abilities:
            filtered["abilities"].append({
                "name": ab.get("name"),
                "text": ab.get("text")
            })

    # Estraggo attacchi con campi chiave
    attacks = card.get("attacks")
    if attacks:
        filtered["attacks"] = []
        for att in attacks:
            filtered["attacks"].append({
                "name": att.get("name"),
                "cost": att.get("cost"),
                "damage": att.get("damage"),
                "text": att.get("text")
            })

    # Debolezze, resistenze e costo ritirata
    if "weaknesses" in card:
        filtered["weaknesses"] = card["weaknesses"]
    if "resistances" in card:
        filtered["resistances"] = card["resistances"]
    if "retreatCost" in card:
        filtered["retreatCost"] = card["retreatCost"]

    return filtered

examples = {}  # (supertype, subtype) -> carta esempio filtrata

for filename in os.listdir(CARDS_DIR):
    if not filename.endswith(".json"):
        continue
    path = os.path.join(CARDS_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        try:
            cards = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Errore nel file {filename}: {e}")
            continue

        for card in cards:
            supertype = card.get("supertype")
            subtypes = card.get("subtypes", [])
            subtype = subtypes[0] if subtypes else None
            key = (supertype, subtype)
            if supertype and key not in examples:
                examples[key] = extract_relevant_fields(card)

output_list = []
for (supertype, subtype), card in examples.items():
    output_list.append({
        "supertype": supertype,
        "subtype": subtype,
        "card_example": card
    })

with open(OUTPUT_FILE, "w", encoding="utf-8") as f_out:
    json.dump(output_list, f_out, ensure_ascii=False, indent=2)

print(f"Esempi salvati in {OUTPUT_FILE}")
