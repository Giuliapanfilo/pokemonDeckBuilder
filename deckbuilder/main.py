import os
import sys
import json
import time

# Path alla cartella principale (che contiene 'deckbuilder' e 'data')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(BASE_DIR, "deckbuilder")
DATA_DIR = os.path.join(BASE_DIR, "data")
sys.path.append(SCRIPTS_DIR)

# Crea la cartella 'data' se non esiste
os.makedirs(DATA_DIR, exist_ok=True)

is_working = True

def stampa_menu():
    print("----------------------------------------")
    print("🧠  BENVENUT* NEL POKÉMON DECK BUILDER!")
    print("----------------------------------------")
    print("1️⃣  Scarica i dati dei set")
    print("2️⃣  Scarica le carte legali standard")
    print("3️⃣  Scarica i mazzi dai tornei")
    print("4️⃣  Esci")
    print("----------------------------------------")

while is_working:
    stampa_menu()
    scelta = input("👉 Inserisci un numero per continuare: ")

    if scelta == "1":
        print("\n📦 Avvio download set...\n")
        from fetch_sets import fetch_all_sets, fetch_set_details

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

        with open(os.path.join(DATA_DIR, "sets_data.json"), "w") as f:
            json.dump(all_sets_data, f, indent=2)
        print(f"\n✅ Set salvati in data/sets_data.json\n")

    elif scelta == "2":
        print("\n🃏 Avvio download carte legali...\n")
        from fetch_cards import fetch_cards

        all_cards = []
        for stype in ["Pokémon", "Trainer", "Energy"]:
            all_cards += fetch_cards(stype)

        with open(os.path.join(DATA_DIR, "cards_data.json"), "w") as f:
            json.dump(all_cards, f, indent=2)
        print(f"\n✅ Carte salvate in data/cards_data.json\n")

    elif scelta == "3":
        print("\n📊 Avvio download tornei...\n")
        import archiviati.fetch_championships as fetch_championships
        fetch_championships.main()

    elif scelta == "4":
        print("\n👋 Uscita dal programma. Alla prossima!\n")
        is_working = False

    else:
        print("\n❌ Scelta non valida. Riprova.\n")
