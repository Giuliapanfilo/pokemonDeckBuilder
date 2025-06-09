import requests
import pandas as pd
import time
import json
from pokemontcgsdk import Card, Set

""" # Funzione per convertire una carta in un dizionario semplificato
def card_to_dict(card):
    return {
        "name": card.name,
        "id": card.id,
        "supertype": card.supertype,
        "subtypes": card.subtypes or [],
        "types": card.types or [],
        "hp": int(card.hp) if card.hp and card.hp.isdigit() else None,
        "evolvesFrom": card.evolvesFrom,
        "set": card.set.name,
        "setCode": card.set.id.lower(),
        "setNumber": card.number,
        "rarity": card.rarity,
    }"""

# Scarica una carta specifica
""" def fetch_data_card(cardName, setName, number):
    #print(f"\n🔍 Inizio scaricamento: {cardName} in {setName} - Numero {number}")
    query = f'!name:"{cardName}" set.name:"{setName}" '
    query += f'number:{number}' if number else ''
    try:
        # Effettua la richiesta per ottenere i dati della carta
        card = Card.where(q=query)
    except Exception as e:
        print(query)
        return []
    time.sleep(0.05)  # Rispetta il rate limit
    if not card:
        print(f"Errore per {cardName} - {setName} num.{number}")
        return []

    return card """

def groupBySet(cardSet) -> dict:
    bySet = {}
    for card in cardSet:
        setName = card[1]
        if setName not in bySet:
            bySet[setName] = []
        bySet[setName].append({
            "nome": card[0],
            "setnumero": card[2]
        })
    return bySet

def queryBuilderBySet(setName, cards):
    setId = set.wh
    query = f"set.name:\"{setName}\" name:"
    for card in cards:
        query += f'{card["nome"]}, '
    return query

if __name__ == "__main__":
    # Carica archetypes_decks.json
    with open('./data/archetypeDecks.json', 'r') as f:
        archetypes = json.load(f)

    # Estrai tutte le tuple uniche di (setesteso, setnumero)
    cardSet = set()
    for deck_lists in archetypes.values():
        for deck in deck_lists:
            for card in deck:
                cardSet.add((card["nome"], card["setesteso"], card["setnumero"]))

    # Ordina le tuple per avere output ordinato
    #list_cards = sorted(list(list_cards))


    print(f"\nTotale carte uniche da scaricare: {len(cardSet)}")

    # Scarica e converte i dati
    cards_data = groupBySet(cardSet)
    cardSet = {}
    for setName, cards in cards_data.items():
        print(f"Inizio scaricamento set: {setName} con {len(cards)} carte")
        query = queryBuilderBySet(setName, cards)
        result = Card.where(q=query)
        if not result:
            print(f"Errore: nessuna carta trovata per il set {setName} con la query: {query}")
            continue
        for card in result:
            cardSet[card.id] = card
        time.sleep(0.25)
    


    #for cardName, setName, setNumber in cardSet:
    #    cards_data += fetch_data_card(cardName, setName, setNumber)

    #cardSet = {card.id: card for card in cards_data}
    #cards_to_save = [card_to_dict(card) for card in cardSet.values()]

    with open('./data/cardSet.json', 'w') as f:
        json.dump(cardSet, f, indent=4)

    print(f"\n{len(cardSet)} carte salvate in './data/cards_data_set.json'")
