import json

with open("data/archetypeDecks.json", "r", encoding="utf-8") as f:
    mazzi = json.load(f)

carte_uniche = set()
#carte_uniche  = []

def setIdByName(setnome):
    setnome = setnome.strip().lower()
    aliases = {
        "base1": ["base set", "tcg", "expansion pack"],
        "base2": ["pokémon jungle"],
        "base5": ["rocket gang"],
        "ecard2":["aquapolis h", "aquapolis"],
        "ecard1": ["expedition", "skyridge"], #sky suggerito da copilot
        "basep" : ["wizards promo"], 
        # "ex5": ["ex hidden legends", "hidden legends"],
        # "ex2": ["ex sandstorm", "sandstorm"],
        # "ex3": ["ex dragon", "dragon"],
        # "ex4": ["ex team magma vs team aqua", "team magma vs team aqua"],
        # "ex6": ["ex fire red & leaf green", "fire red & leaf green"],
        # "ex7": ["ex deoxys", "deoxys"],
        # "ex8": ["ex emerald", "emerald"],
        # "ex9": ["ex unseen forces", "unseen forces"],
        # "ex10": ["ex delta species", "delta species"],
        # "ex11": ["ex legend maker", "legend maker"],
        # "ex12": ["ex holon phantoms", "holon phantoms"],
        # "ex13": ["ex crystal guardians", "crystal guardians"],
        # "ex14": ["ex power keepers", "power keepers"],  
        # 
        # dp promo ->     
    }
    for alias, names in aliases.items():
        if setnome in names:
            return alias
        
    # "dp promo" -> "dpp" per esempio
    if "promo" == setnome[-5:]:
        return setnome[:-5].strip() + "p"
    
    # "ex hidden legends" -> "hidden legends"
    if setnome[:3] in ["ex ", "ex-"]:    
        setnome = setnome[3:].strip()
    
    # cerca l'id del set in base al nome
    with open("data/sets/en.json", "r", encoding="utf-8") as f:
        sets = json.load(f)
        for set_info in sets:
            if set_info["name"].strip().lower() == setnome:
                return set_info["id"]
    # se non trova l'id, solleva un'eccezione
    raise ValueError(f"Set '{setnome}' non trovato.")

def cardIdByDict(nome, setId, setNumero):
    if not setNumero:
        with open(f"data/cards/en/{setId}.json", "r", encoding="utf-8") as f:
            cards = json.load(f)
        for card in cards:
            if card["name"].strip().lower() == nome.strip().lower():
                return card["id"]
    else:
        return f"{setId}-{setNumero}"    

for deck, liste in mazzi.items():
    for lista in liste:
        for carta in lista:
            carte_uniche.add(
                cardIdByDict(
                    carta["nome"], 
                    setIdByName(carta["setesteso"]), 
                    carta["setnumero"])
            )

print(f"Carte uniche trovate: {len(carte_uniche)}")

with open("data/archetypesCardsById.json", "w", encoding="utf-8") as f:
    json.dump(carte_uniche, f, indent=2, ensure_ascii=False)
