import json
import torch
from torch.utils.data import Dataset

class DeckPairsDataset(Dataset):
    def __init__(self, json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            raw_pairs = json.load(f)["pairs"]
        # Filtra solo le coppie valide con 3 elementi
        self.pairs = [p for p in raw_pairs if len(p) == 3]

    def __len__(self):
        return len(self.pairs)

    def __getitem__(self, idx):
        vec1 = torch.tensor(self.pairs[idx][0], dtype=torch.float32)
        vec2 = torch.tensor(self.pairs[idx][1], dtype=torch.float32)
        label = torch.tensor(self.pairs[idx][2], dtype=torch.long)
        return vec1, vec2, label


# --- esempio rapido di come usarlo ---
if __name__ == "__main__":
    dataset = DeckPairsDataset("data/pairs.json")
    print(f"Dataset size: {len(dataset)}")
    v1, v2, lbl = dataset[0]
    print(f"Vector 1 shape: {v1.shape}")
    print(f"Vector 2 shape: {v2.shape}")
    print(f"Label: {lbl}")
