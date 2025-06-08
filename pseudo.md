fetch archetipi -> k-v nomearchetipo- url
-> request -> k-v nomecarta-quantità (per ogni mazzo in listamazzi)

tutte le carte di tutti i k-v dei mazzi vanno in un grande set (senza ripetizioni)
-> trasformare set in lista per avere posizione

set tuttecarte
for mazzo in listamazzi
    tuttecarte.append(mazzo.keys)

funzione vettorizza(mazzo)
    return analizza(mazzo) + encode(mazzo)

funzione analizza(mazzo)

    vec (numPokemon, numItem, numStadi, numAllenatori ecc, numEnergie, PercFuoco, PercAcqua ecc,)

    for carta in mazzo
        cerca nel cards_data.json
            aggiorna contatori di vec
    
    aggiorna percentuali
    return vec

funzione encode(mazzo)
    vec = vuoto di dimensione tuttecarte

    per ogni carta in mazzo
        vec[carta] = mazzo(carta) #quantità della carta cercata in quel mazzo
    return vec