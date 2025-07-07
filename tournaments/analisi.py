import pandas as pd
import matplotlib.pyplot as plt

csv_path = "/home/gp/Scrivania/tournaments/tournaments.csv"

df = pd.read_csv(csv_path)
print(df.head())

deck_counts = (
    df.groupby('combo_type_id')
    .apply(lambda g: g[['id_player', 'id_tournament']].drop_duplicates().shape[0], include_groups=False)
    .reset_index(name='num_decks')
)

deck_counts = deck_counts.sort_values(by='num_decks', ascending=False)

print("Top 20 archetipi per numero di deck:")
print(deck_counts.head(40 ))

plt.figure(figsize=(10,6))
plt.hist(deck_counts['num_decks'], bins=30, color='skyblue', edgecolor='black')
plt.title('Distribuzione del numero di deck per archetipo')
plt.xlabel('Numero di deck')
plt.ylabel('Numero di archetipi')
plt.grid(axis='y')
plt.show()
