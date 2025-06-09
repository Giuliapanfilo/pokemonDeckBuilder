import json

with open("data/archetypeDecks.json", "r", encoding="utf-8") as f:
    mazzi = json.load(f)

chiavi_uniche = set()
carte_uniche  = []

for deck, liste in mazzi.items():
    for lista in liste:
        for carta in lista:
            chiave = (
                carta["nome"].strip().lower(),
                carta["setesteso"].strip().lower(),
                carta["setnumero"]
            )
            if chiave not in chiavi_uniche:
                chiavi_uniche.add(chiave)
                carte_uniche.append(chiave)

print(f"Carte uniche trovate: {len(carte_uniche)}")

with open("data/archetypesCards.json", "w", encoding="utf-8") as f:
    json.dump(carte_uniche, f, indent=2, ensure_ascii=False)
