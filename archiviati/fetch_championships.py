import requests
import json
import os

output_dir = "../data"
os.makedirs(output_dir, exist_ok=True)

# Lista URL tornei (aggiungi qui altri tornei se vuoi)
tournament_urls = [
    "https://www.pokedata.ovh/standings/0000161/masters/0000161_Masters.json?",
    "https://www.pokedata.ovh/standings/0000163/masters/0000163_Masters.json?",
    "https://www.pokedata.ovh/standings/0000156/seniors/0000156_Seniors.json?",
    "https://www.pokedata.ovh/standings/0000159/masters/0000159_Masters.json?",
    "https://www.pokedata.ovh/standings/0000156/masters/0000156_Masters.json?",
    "https://www.pokedata.ovh/standings/0000155/masters/0000155_Masters.json?",
    "https://www.pokedata.ovh/standings/0000154/masters/0000154_Masters.json?",
    "https://www.pokedata.ovh/standings/0000153/masters/0000153_Masters.json?",
]

def fetch_tournament_data(url):
    print(f"Scarico torneo: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Errore durante il download di {url}: {e}")
        return []

    data = response.json()
    tournament_id = url.split("/")[4]
    division = url.split("/")[5]

    players = []
    for player in data:
        players.append({
            "tournament_id": tournament_id,
            "division": division,
            "player": player.get("name"),
            "placing": player.get("placing"),
            "record": player.get("record"),
            "resistances": player.get("resistances"),
            "decklist": player.get("decklist")  # Già nel formato dict o da pulire col clean_tournament_decks.py
        })

    return players

def main():
    all_players = []
    for url in tournament_urls:
        all_players.extend(fetch_tournament_data(url))

    output_path = os.path.join(output_dir, "tournament_decks.json")
    with open(output_path, "w") as f:
        json.dump(all_players, f, indent=2)

    print(f"\n✅ Tornei scaricati e salvati in {output_path} ({len(all_players)} giocatori)")

if __name__ == "__main__":
    main()
