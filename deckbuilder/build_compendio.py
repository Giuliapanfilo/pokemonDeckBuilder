import json
from fetch_card_id import setIdByName, cardIdByDict


with open("data/archetypeDecks.json", "r", encoding="utf-8") as f:
    archetipi = json.load(f)

compendio = set()
output = {}

for nomeArchetipo, mazzi in archetipi.items():
    archetypesCards = {}
    for j,mazzo in enumerate(mazzi):
        for i,carta in enumerate(mazzo):
            cardId = cardIdByDict(
                carta["nome"], 
                carta["setesteso"], 
                carta["setnumero"]
                )
            
            compendio.add(cardId)
            archetypesCards[cardId] = carta["quantità"]
        mazzo[i] = { cardId: carta["quantità"] }

    output[nomeArchetipo] = archetypesCards
            



print(f"Carte uniche trovate: {len(compendio)}")

compendio = list(compendio)

with open("data/archetypesMap.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

with open("data/compendio.json", "w", encoding="utf-8") as f:
    json.dump(compendio, f, indent=2, ensure_ascii=False)
