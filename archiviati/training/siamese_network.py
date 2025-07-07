import json
import random

def get_base_label(label: str) -> str:
    """Rimuove lo spazio e l'ultimo carattere dal nome, es: 'Mew/Accelgor 0' -> 'Mew/Accelgor'"""
    return label[:-2]

def create_pairs(encoded_data: dict):
    """
    Genera coppie positive e negative per Siamese Network.

    Args:
        encoded_data: dict {label_completo: vettore}

    Returns:
        pairs: lista di tuple (vettore1, vettore2)
        labels: lista di 0/1
    """
    base_label_map = {}
    for label, vector in encoded_data.items():
        base = get_base_label(label)
        base_label_map.setdefault(base, []).append((label, vector))

    pairs = []
    labels = []

    # Coppie positive (stesso archetipo, suffissi diversi)
    for base, examples in base_label_map.items():
        if len(examples) < 2:
            continue
        # Creazione coppie tra tutti gli esempi (es. tra "Mew/Accelgor 0" e "Mew/Accelgor 1")
        for i in range(len(examples)):
            for j in range(i + 1, len(examples)):
                pairs.append((examples[i][1], examples[j][1]))
                labels.append(1)

    # Coppie negative (archetipi diversi)
    base_labels = list(base_label_map.keys())
    num_positive = sum(labels)
    for _ in range(num_positive):
        base1, base2 = random.sample(base_labels, 2)
        vec1 = random.choice(base_label_map[base1])[1]
        vec2 = random.choice(base_label_map[base2])[1]
        pairs.append((vec1, vec2))
        labels.append(0)

    return pairs, labels

if __name__ == "__main__":
    # Carica i vettori encodati
    with open("data/encodedDecks.json", "r", encoding="utf-8") as f:
        encoded_data = json.load(f)

    pairs, labels = create_pairs(encoded_data)

    print(f"Coppie totali create: {len(pairs)}")
    print(f"Coppie positive: {sum(labels)}")
    print(f"Coppie negative: {len(labels) - sum(labels)}")

    # Salvo i dati nel formato corretto
    pair_data = {"pairs": [[v1, v2, lbl] for (v1, v2), lbl in zip(pairs, labels)]}

    with open("training/trainingData/pairs.json", "w", encoding="utf-8") as f:
        json.dump(pair_data, f)

