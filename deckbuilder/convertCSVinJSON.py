import csv
import json
import os
from collections import defaultdict

# 📁 PATH AI FILE (modifica se necessario)
CSV_PATH = "data/tournaments.csv"
SETS_PATH = "data/sets/en.json"
OUTPUT_PATH = "data/DecksFromCSV.json"
INCOMPLETE_PATH = "data/mazzi_incompleti.json"

# 🔎 Carica i dati dei set per ptcgoCode → (name, id)
def load_sets_data():
    with open(SETS_PATH, encoding="utf-8") as f:
        sets_data = json.load(f)
    mapping = {}
    for s in sets_data:
        ptcgo = s.get("ptcgoCode")
        if ptcgo:  # solo se il ptcgoCode è presente
            mapping[ptcgo.lower()] = {
                "name": s["name"],
                "id": s["id"].lower()
            }
    return mapping

# 🧠 Estrai codice set e numero da una card_id tipo "NVI83"
def split_card_id(card_id, sets_map):
    card_id = card_id.strip().lower()
    # Cerca ptcgoCode più lungo che combacia
    for code in sorted(sets_map.keys(), key=len, reverse=True):
        if card_id.startswith(code):
            set_info = sets_map[code]
            num = card_id[len(code):]
            return {
                "setesteso": set_info["name"],
                "setid": set_info["id"],
                "setnumero": num
            }
    return None

# 🛠️ Costruzione dizionari
def parse_csv():
    sets_map = load_sets_data()
    archetype_decks = defaultdict(list)
    mazzi_incompleti = {}

    seen_decks = set()

    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        mazzi_temp = defaultdict(list)

        for row in reader:
            deck_id = f'{row["id_player"].strip()}-{row["id_tournament"].strip()}'
            if deck_id not in mazzi_temp:
                mazzi_temp[deck_id] = {
                    "archetype": row["combo_type_name"].strip(),
                    "cards": []
                }

            parsed = split_card_id(row["id_card"], sets_map)
            if not parsed:
                mazzi_temp[deck_id]["incomplete"] = True
                continue

            carta = {
                "quantità": row["amount_card"].strip(),
                "nome": row["name_card"].strip(),
                "setesteso": parsed["setesteso"],
                "setnumero": parsed["setnumero"]
            }
            mazzi_temp[deck_id]["cards"].append(carta)

    # Organizza per archetipo
    counter = defaultdict(int)
    for deck_id, data in mazzi_temp.items():
        archetype = data["archetype"]
        cards = data["cards"]
        is_incomplete = data.get("incomplete", False)

        if is_incomplete:
            mazzi_incompleti[deck_id] = cards
        else:
            counter[archetype] += 1
            mazzo_name = f"{archetype}-{counter[archetype]}"
            archetype_decks[archetype].append(cards)

    # Salva file
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(archetype_decks, f, indent=2, ensure_ascii=False)

    with open(INCOMPLETE_PATH, "w", encoding="utf-8") as f:
        json.dump(mazzi_incompleti, f, indent=2, ensure_ascii=False)

    print(f"✅ Mazzi completi salvati in {OUTPUT_PATH}")
    print(f"⚠️  Mazzi incompleti salvati in {INCOMPLETE_PATH}")

if __name__ == "__main__":
    parse_csv()
