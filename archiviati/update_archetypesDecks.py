import json
from deckbuilder.fetch_card_id import cardIdByDict

# Carica archetypesDecks.json
with open("data/archetypeDecks.json", "r", encoding="utf-8") as f:
    archetipi = json.load(f)

# Funzione per aggiornare il setnumero
def update_setnumero(archetipi):
    for nomeArchetipo, mazzi in archetipi.items():
        for mazzo in mazzi:
            for carta in mazzo:
                if carta["setnumero"] is None:  # Controlla se il setnumero è None
                    try:
                        # Usa cardIdByDict per ottenere l'ID della carta
                        cardId = cardIdByDict(carta["nome"], carta["setesteso"], None)
                        
                        if cardId:
                            # Estrai il setnumero dall'ID della carta
                            setNumero = cardId.split("-")[-1]
                            carta["setnumero"] = setNumero
                            print(f"Aggiornato setnumero per {carta['nome']}: {carta['setnumero']}")
                        else:
                            print(f"Errore: ID non trovato per la carta {carta['nome']} nel set {carta['setesteso']}")
                    except Exception as e:
                        print(f"Errore durante l'aggiornamento di {carta['nome']}: {e}")

# Aggiorna archetypesDecks.json
update_setnumero(archetipi)

# Salva il file aggiornato in una copia
with open("data/archetypeDecks_updated.json", "w", encoding="utf-8") as f:
    json.dump(archetipi, f, indent=2, ensure_ascii=False)

print("Aggiornamento completato! Salvato in archetypeDecks_updated.json")