import torch
from torch.utils.data import DataLoader
import torch.nn as nn
import torch.optim as optim
from tqdm import tqdm
import os

from siamese_model import SiameseNetwork, contrastive_loss
from pt_database import DeckPairsDataset

# Parametri
BATCH_SIZE = 16
EPOCHS = 20
LEARNING_RATE = 0.001
MARGIN = 1.0  # per contrastive loss

# Usa CUDA se disponibile
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Training on: {device}")

# Dataset e DataLoader
dataset = DeckPairsDataset("data/pairs.json")
dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

# Modello e loss
model = SiameseNetwork(input_dim=1209).to(device)
optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

# Training loop
for epoch in range(EPOCHS):
    model.train()
    running_loss = 0.0

    for vec1, vec2, label in tqdm(dataloader, desc=f"Epoch {epoch+1}/{EPOCHS}"):
        vec1, vec2, label = vec1.to(device), vec2.to(device), label.to(device)

        optimizer.zero_grad()
        output1, output2 = model(vec1, vec2)
        loss = contrastive_loss(output1, output2, label.float(), margin=MARGIN)
        loss.backward()
        optimizer.step()

        running_loss += loss.item()

    avg_loss = running_loss / len(dataloader)
    print(f"Epoch {epoch+1} - Loss: {avg_loss:.4f}")

# Salvataggio del modello
os.makedirs("models", exist_ok=True)
torch.save(model.state_dict(), "models/siamese_model.pt")
print("Modello salvato in models/siamese_model.pt")
