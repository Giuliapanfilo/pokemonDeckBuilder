from pokemontcgsdk import Card, Set
import json

def card_to_dict(card):
    return {
        "id": card.id,
        "name": card.name,
        "types": card.types,
        "rarity": card.rarity,
        "set": card.set.name if card.set else None
    }

# Recupera tutti i set disponibili
try:
    all_sets = Set.all()
except Exception as e:
    print(f"❌ Errore durante il recupero dei set: {e}")
    all_sets = []

# Preleva solo gli ID dei set
set_ids = [s.id for s in all_sets]

all_cards = []

for i, set_id in enumerate(set_ids, 1):
    print(f"🔍 Inizio scaricamento: {set_id} - Numero {i}")
    try:
        cards = Card.where(setId=set_id).all()
        for card in cards:
            all_cards.append(card_to_dict(card))
    except Exception as e:
        print(f"⚠️ Errore nel set {set_id}: {e}")

# Salva i dati in JSON
with open('./data/all_cards_data.json', 'w') as f:
    json.dump(all_cards, f, indent=4)

print(f"✅ {len(all_cards)} carte salvate in 'cards_data.json'")
