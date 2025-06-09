import requests
import pandas as pd
import time
import json

API_KEY = "401527f9-d485-4689-84a5-3a700a908096"
url = "https://api.pokemontcg.io/v2/cards"
headers = {"X-Api-Key": API_KEY}
page_size = 250

def fetch_cards(supertype):
    cards = []
    page = 1
    print(f"\nInizio scaricamento: {supertype}")

    while True:
        params = {
            "q": f"supertype:{supertype} legalities.standard:legal",
            "pageSize": page_size,
            "page": page
        }
        print(f"➡️  {supertype} - Pagina {page}")
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"Errore: {response.status_code}")
            break

        data = response.json().get("data", [])
        if not data:
            break

        for card in data:
            name = card.get("name")
            set_code = card["set"]["id"].upper() if "set" in card and card["set"].get("id") else None
            number = card.get("number")

            cards.append({
                "name": name,
                "id": card.get("id"),
                "supertype": card.get("supertype"),
                "subtypes": card.get("subtypes") or [],
                "types": card.get("types") or [],
                "hp": int(card["hp"]) if card.get("hp") and card["hp"].isdigit() else None,
                "attacks": card.get("attacks") or [],
                "weaknesses": card.get("weaknesses") or [],
                "resistances": card.get("resistances") or [],
                "retreatCost": card.get("retreatCost") or [],
                "evolvesFrom": card.get("evolvesFrom"),
                "evolvesTo": card.get("evolvesTo") or [],
                "set": card["set"]["name"] if "set" in card else None,
                "setCode": card["set"]["id"].lower() if "set" in card and card["set"].get("id") else None,
                "setNumber": number,
                "rarity": card.get("rarity"),
                "imageUrl": card.get("images", {}).get("large"),
                "legalities": card.get("legalities") or {},
                "match_keys": {
                    "name": name.lower().strip() if name else None,
                    "set": set_code,
                    "number": number,
                }
            })

        page += 1
        time.sleep(0.25)

    return cards

if __name__ == "__main__":
    all_cards = []
    for stype in ["Pokémon", "Trainer", "Energy"]:
        all_cards += fetch_cards(stype)

    # Salvo tutto in JSON
    with open("../data/cards_data.json", "w") as f:
        json.dump(all_cards, f, indent=2)

    print(f"\nCompletato: {len(all_cards)} carte salvate in ../data/cards_data.json")
