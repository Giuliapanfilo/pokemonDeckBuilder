#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json
import os
import sys

# Directory dello script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BASE_URL   = "https://www.pokedata.ovh/standings/"
CATEGORIES = ["juniors", "masters", "seniors"]

def get_standings_list():
    """Estrae tutti gli ID di standing dalla pagina index."""
    resp = requests.get(BASE_URL)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    standings = set()
    for btn in soup.select("div.flex-parent.jc-center button[onclick]"):
        onclick = btn.get("onclick", "")
        if "location.href" in onclick:
            num = onclick.split("location.href='", 1)[1].split("/'", 1)[0]
            standings.add(num)
    return sorted(standings)

def fetch_and_save():
    """Scarica i JSON per ogni standing e categoria, aggiunge 'category' e salva."""
    standings = get_standings_list()
    for standing in standings:
        out_path = os.path.join(BASE_DIR, f"{standing}.json")
        # Se esiste già, salta questo standing
        if os.path.isfile(out_path):
            print(f"[→] {standing}.json già presente, skip.")
            continue

        all_decks = []
        for category in CATEGORIES:
            filename = f"{standing}_{category.capitalize()}.json"
            url = f"{BASE_URL}{standing}/{category}/{filename}"

            try:
                r = requests.get(url)
                if r.status_code == 200:
                    data = r.json()
                    for deck in data:
                        deck["category"] = category
                        all_decks.append(deck)
                else:
                    print(f"[!] {url} → HTTP {r.status_code}, skip.")
            except Exception as e:
                print(f"[!] Errore fetching {url}: {e}")

        # Se non ci sono mazzi o il primo non ha 'decklist', skip e rimuovi eventuale file vuoto
        if not all_decks or not all_decks[0].get("decklist"):
            print(f"[!] {standing}.json: mazzi senza senza 'decklist', skip save.")
            # Rimuovo un file eventualmente creato da precedenti esecuzioni
            if os.path.isfile(out_path):
                os.remove(out_path)
                print(f"[!] Rimosso {out_path}")
            continue

        # Salva solo la lista dei mazzi con category
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(all_decks, f, ensure_ascii=False, indent=2)
        print(f"[✓] Salvato {standing}.json ({len(all_decks)} deck)")

if __name__ == "__main__":
    try:
        fetch_and_save()
    except KeyboardInterrupt:
        sys.exit("\nInterrotto dall'utente")
