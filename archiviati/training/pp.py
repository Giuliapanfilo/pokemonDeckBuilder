import json

def load_encoded_archetypes(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    X = []
    y = []

    for archetype_name, vector in data.items():
        X.append(vector)
        y.append(archetype_name)

    return X, y

# Esempio di utilizzo:
if __name__ == "__main__":
    X, y = load_encoded_archetypes("data/encodedDecks.json")
    print(f"{len(X)} vettori caricati.")
    print(f"Ogni vettore ha dimensione: {len(X[0])}")
