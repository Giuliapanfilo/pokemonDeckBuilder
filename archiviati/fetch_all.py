import requests
import time
import json
import os

API_KEY = "401527f9-d485-4689-84a5-3a700a908096"
url = "https://api.pokemontcg.io/v2/cards"
headers = {"X-Api-Key": API_KEY}
page_size = 250

def fetch_cards_pages(supertype, start_page, end_page):
    cards = []
    print(f"\nInizio scaricamento: {supertype} da pagina {start_page} a {end_page}")

    for page in range(start_page, end_page + 1):
        params = {
            "q": f"supertype:{supertype}",
            "pageSize": page_size,
            "page": page
        }
        print(f"➡️  {supertype} - Pagina {page}")
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 404:
            print(f"Pagina {page} non trovata (404), interrompo il ciclo.")
            break
        elif response.status_code != 200:
            print(f"Errore: {response.status_code}, interrompo il ciclo.")
            break

        data = response.json().get("data", [])
        if not data:
            print("Nessun dato ricevuto, interrompo il ciclo.")
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

        time.sleep(0.25)

    return cards

def load_existing_cards(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            try:
                existing_cards = json.load(f)
                print(f"Trovati {len(existing_cards)} carte esistenti in {filepath}")
                return existing_cards
            except json.JSONDecodeError:
                print(f"File {filepath} vuoto o corrotto, parto da zero.")
                return []
    return []

def save_cards(filepath, cards):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(cards, f, indent=2)
    print(f"Salvate {len(cards)} carte in {filepath}")

if __name__ == "__main__":
    start_page = 1
    end_page = 50
    supertype = "Pokémon"  # Cambia se vuoi "Trainer" o "Energy"

    file_path = "../data/all_cards.json"

    # Carico eventuali carte già salvate
    all_cards = load_existing_cards(file_path)

    # Scarico le nuove pagine
    new_cards = fetch_cards_pages(supertype, start_page, end_page)

    # Unisco senza duplicati basandomi sull'id
    existing_ids = {card['id'] for card in all_cards}
    combined_cards = all_cards + [c for c in new_cards if c['id'] not in existing_ids]

    save_cards(file_path, combined_cards)
