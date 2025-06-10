import json

def setIdByName(setnome):
    setnome = setnome.strip().lower()
    aliases = {
        "base1": ["base set", "tcg", "expansion pack", "basic", "special", "", "TCG"],
        "base2": ["pokémon jungle"],
        "base5": ["rocket gang"],
        "ecard2":["aquapolis h", "aquapolis"],
        "ecard1": ["expedition", "skyridge"], #sky suggerito da copilot
        "basep" : ["wizards promo"],
        "hgss2" : ["unleashed"],
        "hgss4" : ["triumphant"],
        "pl1" : ["platinum sh"],
        "hgss3" : ["undaunted"],
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


def cardIdByDict(nome, setesteso, setNumero):

    try:
        setId = setIdByName(setesteso)
    except ValueError as e:
        print(f"Errore: {e}")
        return None

    if not setNumero:
        with open(f"data/cards/en/{setId}.json", "r", encoding="utf-8") as f:
            cards = json.load(f)
        for card in cards:
            if card["name"].strip().lower() == nome.strip().lower():
                return card["id"]
    else:
        return f"{setId}-{setNumero}"    
