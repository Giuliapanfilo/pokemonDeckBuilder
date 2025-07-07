import torch
import torch.nn as nn
import torch.nn.functional as F

class SiameseNetwork(nn.Module):
    def __init__(self, input_dim=1209, hidden_dim=512):
        super(SiameseNetwork, self).__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU()
        )

    def forward_once(self, x):
        return self.encoder(x)

    def forward(self, input1, input2):
        out1 = self.forward_once(input1)
        out2 = self.forward_once(input2)
        return out1, out2

def contrastive_loss(out1, out2, label, margin=1.0):
    distance = F.pairwise_distance(out1, out2)
    loss = (label.float() * distance.pow(2)) + \
           ((1 - label.float()) * F.relu(margin - distance).pow(2))
    return loss.mean()
