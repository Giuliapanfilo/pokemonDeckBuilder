import requests
import json
import time

API_KEY = "401527f9-d485-4689-84a5-3a700a908096"
BASE_URL = "https://api.pokemontcg.io/v2/sets"
HEADERS = {"X-Api-Key": API_KEY}

def fetch_all_sets():
    print("\n🔍 Inizio scaricamento lista set...")
    response = requests.get(BASE_URL, headers=HEADERS)
    
    if response.status_code != 200:
        print(f"❌ Errore durante il fetch della lista dei set: {response.status_code}")
        return []

    sets_list = response.json().get("data", [])
    return sets_list

def fetch_set_details(set_id):
    url = f"{BASE_URL}/{set_id}"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        print(f"❌ Errore nel fetch del set {set_id}: {response.status_code}")
        return None

    return response.json().get("data", {})

if __name__ == "__main__":
    all_sets_data = []

    sets_list = fetch_all_sets()
    print(f"📦 Trovati {len(sets_list)} set\n")

    for i, set_item in enumerate(sets_list, start=1):
        set_id = set_item.get("id")
        print(f"➡️  [{i}/{len(sets_list)}] Scaricamento set: {set_id}")

        details = fetch_set_details(set_id)
        if details:
            all_sets_data.append(details)

        time.sleep(0.25)

    # Salva in JSON
    with open("../data/sets_data.json", "w") as f:
        json.dump(all_sets_data, f, indent=2)

    print(f"\n✅ Completato: {len(all_sets_data)} set salvati in ../data/sets_data.json")
