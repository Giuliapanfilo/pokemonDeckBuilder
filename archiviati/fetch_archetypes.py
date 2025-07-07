import requests
from bs4 import BeautifulSoup
import json, re

BASE_URL = "https://bulbapedia.bulbagarden.net"
INDEX_URL = f"{BASE_URL}/wiki/Deck_archetype_(TCG)"


def extractArchetypes():
    response = requests.get(INDEX_URL)
    soup = BeautifulSoup(response.text, "html.parser")

    archetype_urls = {}

    for li in soup.find("div", attrs={"role": "main"}).find_all("li"):
        a = li.find("a")
        if not a or not a.has_attr("title"):
            continue
        href = a["href"]
        title = a["title"]
        arch_name = a.text.strip()

        if "#" in href or ":" in href or "(page does not exist)" in title:
            continue

        archetype_urls[arch_name] = BASE_URL + href

    return archetype_urls


def selectTables(soup) -> list[BeautifulSoup]:
    tables = []
    # Cerca tutte le tabelle con classe roundy
    for table in soup.find_all("table", class_="roundy"):
        headers = [th.text.strip().lower() for th in table.find_all("th")]
        if all(k in headers for k in ["quantity", "card", "type", "rarity"]):
            tables.append(table)
    return tables


def extractDecksFromTable(url):
    print(f"Estraggo mazzo da: {url}")
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    tables = selectTables(soup)
    mazzi = []

    if len(tables)==0:
        print(f"Tabella decklist non trovata per {url}")
        return None
    
    for table in tables:
        mazzo = []
        for row in table.find_all("tr")[1:]:  # salta l'header
            cols = row.find_all("td")
            if len(cols)<2:
                continue
            quantità = cols[0].text.strip()[:-1]  # rimuove l'ultimo carattere (spazio o simbolo)
            nomesetnum = next((child for child in cols[1].children if child.name == "a"), None)["title"]
            id = extractIdentifier(nomesetnum)

            if not id:
                raise ValueError(f"Formato non riconosciuto per nomesetnum: {nomesetnum}")
                print(f"[!] Identificatore non valido per nomesetnum: {nomesetnum}")
                continue
            
            mazzo.append({
                "quantità": int(quantità),
                "nome": id[0],
                "setesteso": id[1] if len(id) > 0 else None, 
                "setnumero": id[2] if len(id) > 0 else None,
            })
        mazzi.append(mazzo) 

    return mazzi


import re

def extractIdentifier(nomesetnum: str):
    regexes = [
        r'^(.*?)\s*\((.*?)\s*(\d+)?\)$',  # Con numero opzionale
        r'^(.*?)\s*\((.*?)\)$',           # Senza numero
    ]
    # Caso con numero nel set (es. "Seismitoad-EX (Furious Fists 20)")
    match = re.match(regexes[0], nomesetnum)
    if match:
        nome = match.group(1)
        set_nome = match.group(2)
        numero = match.group(3)
        return (nome, set_nome, numero)

    # Caso senza numero nel set (es. "Water Energy (TCG)")
    match = re.match(regexes[1], nomesetnum)
    if match:
        nome = match.group(1).strip()
        set_nome = match.group(2).strip()
        return (nome, set_nome, '')

    # Formato non riconosciuto
    return (nomesetnum, '', '')



def main():
    archetype_urls = extractArchetypes()
    archetype_decks = {}

    for nome, url in archetype_urls.items():
        mazzi = extractDecksFromTable(url)
        if mazzi:
            archetype_decks[nome] = mazzi

    with open("archetypeDecks.json", "w", encoding="utf-8") as f:
        json.dump(archetype_decks, f, indent=2, ensure_ascii=False)

    print(" archetypeDecks.json creato con successo.")

if __name__ == "__main__":
    main()
