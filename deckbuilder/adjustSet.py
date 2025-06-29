import json

# === Carica i dati dei set ===
with open('data/sets/en.json', 'r', encoding='utf-8') as f:
    sets_data = json.load(f)

# Mappa ptcgoCode -> nome del set
code_to_name = {s['ptcgoCode']: s['name'] for s in sets_data if 'ptcgoCode' in s}

# === Carica i mazzi ===
with open('data/archetypeDecks2.json', 'r', encoding='utf-8') as f:
    archetype_decks = json.load(f)

# === DEBUG iniziale ===
print("Archetipi presenti:", len(archetype_decks))
esempio_nome = next(iter(archetype_decks))
esempio_mazzo = archetype_decks[esempio_nome][0]
print(json.dumps(esempio_mazzo[:2], indent=2, ensure_ascii=False))

# === Modifica i set ===
modificate = 0
non_modificate = 0
missing_codes = set()

for mazzi in archetype_decks.values():  # ogni valore è una lista di mazzi
    for mazzo in mazzi:  # ogni mazzo è una lista di carte
        for card in mazzo:
            if isinstance(card, dict) and 'setesteso' in card:
                old_code = card['setesteso']
                if old_code in code_to_name:
                    card['setesteso'] = code_to_name[old_code]
                    modificate += 1
                else:
                    non_modificate += 1
                    missing_codes.add(old_code)
            else:
                non_modificate += 1

# === Salva se ci sono modifiche ===
if modificate > 0:
    with open('data/archetypeDecks2.json', 'w', encoding='utf-8') as f:
        json.dump(archetype_decks, f, indent=2, ensure_ascii=False)
    print(f"\nFile aggiornato: {modificate} carte modificate.")
else:
    print("\nNessuna modifica effettuata. Controlla i codici o la struttura.")

print(f"Carte non modificate: {non_modificate}")
if missing_codes:
    print("\n🔎 Codici 'setesteso' non trovati in en.json:")
    for code in sorted(missing_codes):
        print(f" - {code}")
