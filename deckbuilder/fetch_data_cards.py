import requests
import pandas as pd
import time
import json

from pokemontcgsdk import Card
from pokemontcgsdk import Set
from pokemontcgsdk import Type
from pokemontcgsdk import Supertype
from pokemontcgsdk import Subtype
from pokemontcgsdk import Rarity

#Utile a convertire una carta in un dizionario
def card_to_dict(card):
    return {
        "name": card.name,
        "id": card.id,
        "supertype": card.supertype,
        "subtypes": card.supertype or [],
        "types": card.types or [],
        "hp": int(card.hp) if card.hp and card.hp.isdigit() else None,
        #Capisci perché non funziona attacks, weaknesses, resistances, retreatCost, legalities
        #"attacks": card.attacks or [],
        #"weaknesses": card.weaknesses or [],
        #"resistances": card.resistances or [],
        #"retreatCost": card.retreatCost or [],
        "evolvesFrom": card.evolvesFrom,
        "set": card.set.name, # if "set" in card else None, RIVEDI SET
        "setCode": card.set.id.lower(), # if "set" in card and card.set.get("id") else None,
        "setNumber": card.number,
        "rarity": card.rarity,
        #"legalities": card.legalities or {}
    }

def fetch_data_card(setName, n): #Modifica parametro con la lista di tuple composte ognuna da 2 stringe
    card = []

    print(f"\n🔍 Inizio scaricamento: {setName} - Numero {n}")

    query = f'set.name:"{setName}" number:{n}'
    card = Card.where(q=query)

    if not card:
        print(f"❌ Nessuna carta trovata per il set {setName} e il numero {n}")
        return []

    return card

if __name__ == "__main__":
    list_cards = [
        ("Shining Fates", "1"),
        ("Battle Styles", "2"),
        ("Kalos Starter Set", "34"),
        ("Base", "100")
        ]
    cards_data = []

    for setName, n in list_cards:
        cards_data += fetch_data_card(setName, n)
    
    set_cards_ids = {card.id:card for card in cards_data}

    #Struttura composta da carte senza duplicati filtrate tramite il loro ID
    cards_to_save = [card_to_dict(card) for card in set_cards_ids.values()]

    with open('./data/cards_data_set.json', 'w') as f:
        json.dump(cards_to_save, f, indent=4)
    print(f"✅ {len(cards_to_save)} carte salvate in 'cards_data.json'")

