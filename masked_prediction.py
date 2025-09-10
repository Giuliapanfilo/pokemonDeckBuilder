#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modulo per implementare un approccio di masked prediction per mazzi di carte Pokémon.
Questo modulo estende il test di rimozione delle carte con ottimizzazioni specifiche
per la predizione di carte mascherate.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time
import random
import pickle
import json
import os
from typing import List, Dict, Any, Optional, Tuple, Union, Callable, Set
from collections import Counter, defaultdict

# Algoritmi di clustering
from sklearn.cluster import KMeans, AgglomerativeClustering, DBSCAN, SpectralClustering, Birch
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Importazioni specifiche del progetto
from structures.deck import Deck
from structures.similarity import Similarity
from structures.card import Card


# Funzioni di utilità
def _safe_matrix(sample, emb_or_embs):
    """
    Costruisce X per un embedding o una lista di embeddings, filtrando eventuali errori per singolo deck.
    
    Args:
        sample: Lista di mazzi
        emb_or_embs: Un singolo embedding o una lista di embeddings
        
    Returns:
        Tuple con la matrice X e il numero di mazzi scartati
    """
    # Se è una lista di embeddings, combina i vettori
    if isinstance(emb_or_embs, list):
        return combine_embeddings(sample, emb_or_embs)
    
    # Altrimenti, procedi con un singolo embedding
    rows = []
    bad = 0
    
    for d in sample:
        try:
            vec = emb_or_embs(d)
            
            # controlli base
            if vec is None: 
                bad += 1
                continue
                
            rows.append([float(x) for x in vec])
        except Exception:
            bad += 1
            
    if not rows:
        return None, bad
        
    X = np.array(rows, dtype=float)
    return X, bad


def _has_variance(X: np.ndarray) -> bool:
    """Ritorna True se almeno una colonna ha varianza > 0."""
    if X.ndim != 2 or X.shape[0] < 2:
        return False
    return np.any(np.var(X, axis=0) > 0.0)


def combine_embeddings(decks: List[Deck], embeddings: List[Deck.Embedding], normalize: bool = True) -> Tuple[Optional[np.ndarray], int]:
    """
    Combina più embeddings per una lista di mazzi.
    
    Args:
        decks: Lista di mazzi
        embeddings: Lista di embeddings da combinare
        normalize: Se normalizzare gli embeddings prima di combinarli
        
    Returns:
        Tuple contenente:
        - Matrice di embedding combinata
        - Numero di mazzi scartati
    """
    if not embeddings:
        raise ValueError("La lista di embeddings non può essere vuota")
    
    # Statistiche
    total_decks = len(decks)
    successful_decks = 0
    skipped_decks = 0
    
    # Estrai embeddings per ogni mazzo
    embedding_vectors = {emb: [] for emb in embeddings}
    valid_indices = []
    
    for i, deck in enumerate(decks):
        valid = True
        deck_vectors = {}
        
        # Prova ad estrarre tutti gli embeddings per questo mazzo
        for emb in embeddings:
            try:
                vec = emb(deck)
                
                # Controlla validità
                if vec is None:
                    valid = False
                    break
                    
                # Converti a float e salva
                deck_vectors[emb] = [float(x) for x in vec]
                
            except Exception:
                valid = False
                break
        
        # Se tutti gli embeddings sono validi, aggiungi ai risultati
        if valid:
            for emb in embeddings:
                embedding_vectors[emb].append(deck_vectors[emb])
            valid_indices.append(i)
            successful_decks += 1
        else:
            skipped_decks += 1
    
    # Controlla se abbiamo embeddings validi
    if successful_decks == 0:
        return None, total_decks
    
    # Converti a numpy arrays
    X_list = []
    
    for emb in embeddings:
        X = np.array(embedding_vectors[emb], dtype=float)
        
        # Normalizza se richiesto
        if normalize and np.any(np.var(X, axis=0) > 0):
            scaler = StandardScaler()
            X = scaler.fit_transform(X)
            
        X_list.append(X)
    
    # Combina gli embeddings
    X_combined = np.hstack(X_list)
    
    return X_combined, skipped_decks


def load_decks(cache_path: str = "cache/decks.pkl"):
    """
    Carica i mazzi dal file cache.
    
    Args:
        cache_path: Percorso del file cache
        
    Returns:
        Lista di mazzi
    """
    # Controlla se esiste il file cache
    if os.path.exists(cache_path):
        print(f"Caricamento mazzi da {cache_path}...")
        with open(cache_path, "rb") as f:
            decks = pickle.load(f)
        print(f"Caricati {len(decks)} mazzi dal file cache")
        return decks
    
    # Altrimenti, carica i mazzi dal file CSR
    print("File cache non trovato, caricamento mazzi da CSR...")
    
    # Carica i dati
    from scipy.sparse import csr_matrix
    
    def csr_load(path: str="cache/decks_csr.npz"):
        z = np.load(path, allow_pickle=True)
        X = csr_matrix(
            (z["data"], z["indices"], z["indptr"]),
            shape=tuple(z["shape"])
        )
        return X, z["deck_ids"], z["card_ids"]
    
    X, deck_ids, card_ids = csr_load()
    
    with open("cache/cards.json", encoding="utf-8") as f:
        encyclopedia = json.load(f)
    
    # Crea i mazzi
    decks = [
        Deck.from_sparse_row(
            X.getrow(i), 
            card_ids=card_ids, 
            cards_encyclopedia=encyclopedia,
            name=str(deck_ids[i])
        )
        for i in range(X.shape[0])
    ]
    
    print(f"Caricati {len(decks)} mazzi")
    
    # Salva i mazzi nel file cache
    with open(cache_path, "wb") as f:
        pickle.dump(decks, f)
    
    return decks


# Cache per i vettori di embedding
_embedding_cache = {}

def get_embedding_vector(deck: Deck, embedding: Union[Deck.Embedding, List[Deck.Embedding]]) -> List[float]:
    """
    Ottiene il vettore di embedding per un mazzo, utilizzando una cache per migliorare le prestazioni.
    
    Args:
        deck: Il mazzo
        embedding: L'embedding o lista di embeddings da utilizzare
        
    Returns:
        Il vettore di embedding
    """
    # Crea una chiave per la cache
    cache_key = (deck.uid(), embedding if not isinstance(embedding, list) else tuple(embedding))
    
    # Controlla se il vettore è già in cache
    if cache_key in _embedding_cache:
        return _embedding_cache[cache_key]
    
    # Calcola il vettore
    if isinstance(embedding, list):
        # Combina più embeddings
        vectors = []
        for emb in embedding:
            vectors.extend(emb(deck))
        result = vectors
    else:
        # Singolo embedding
        result = embedding(deck)
    
    # Salva in cache e restituisci
    _embedding_cache[cache_key] = result
    return result


def calculate_context_weight(masked_deck: Deck, reference_deck: Deck) -> float:
    """
    Calcola un peso contestuale basato sulla composizione del mazzo utilizzando
    direttamente gli embedding esistenti e le funzioni di similarità.
    Ottimizzato per le prestazioni.
    
    Args:
        masked_deck: Mazzo con carte mascherate
        reference_deck: Mazzo di riferimento
        
    Returns:
        Peso contestuale tra 0 e 1
    """
    # Calcola la similarità dei tipi di Pokémon usando PKMN_TYPES
    # Utilizziamo la cache per evitare di ricalcolare gli embeddings
    masked_types = get_embedding_vector(masked_deck, Deck.Embedding.PKMN_TYPES)
    ref_types = get_embedding_vector(reference_deck, Deck.Embedding.PKMN_TYPES)
    type_similarity = Similarity.OVERLAP(masked_types, ref_types)
    
    # Per ottimizzare le prestazioni, utilizziamo solo la similarità dei tipi
    # che è la più significativa per il contesto
    return type_similarity



def predict_masked_cards_clustering(
    masked_deck: Deck,
    reference_decks: List[Deck],
    embedding: Union[Deck.Embedding, List[Deck.Embedding]] = Deck.Embedding.RESISTANCE,
    method: str = "K-Means",
    n_clusters: int = 4,
    top_n: int = 20,
    use_context_weights: bool = True
) -> List[Tuple[Card, float]]:
    """
    Predice le carte mascherate in un mazzo utilizzando un approccio basato su clustering.
    
    Args:
        masked_deck: Mazzo con carte mascherate
        reference_decks: Mazzi di riferimento
        embedding: Embedding o lista di embeddings da utilizzare
        method: Metodo di clustering da utilizzare
        n_clusters: Numero di cluster da utilizzare
        top_n: Numero di carte da predire
        use_context_weights: Se utilizzare pesi contestuali
        
    Returns:
        Lista di tuple (carta, score) ordinate per rilevanza
    """
    # Estrai gli embedding per tutti i mazzi
    all_decks = reference_decks + [masked_deck]
    X, bad = _safe_matrix(all_decks, embedding)
    
    if X is None or X.size == 0 or not np.any(X) or not _has_variance(X):
        emb_name = embedding.name if not isinstance(embedding, list) else "+".join([e.name for e in embedding])
        print(f"Embedding {emb_name} non valido per predizione")
        return []
    
    # Normalizza
    scaler = StandardScaler()
    X_norm = scaler.fit_transform(X)
    
    # Applica il clustering in base al metodo scelto
    if method == "K-Means":
        clusterer = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    elif method == "Agglomerative":
        clusterer = AgglomerativeClustering(n_clusters=n_clusters)
    elif method == "DBSCAN":
        clusterer = DBSCAN(eps=0.5, min_samples=5)
    elif method == "Spectral":
        clusterer = SpectralClustering(n_clusters=n_clusters, random_state=42)
    elif method == "BIRCH":
        clusterer = Birch(n_clusters=n_clusters)
    else:
        raise ValueError(f"Metodo di clustering non supportato: {method}")
    
    labels = clusterer.fit_predict(X_norm)
    
    # Trova il cluster del mazzo mascherato
    masked_idx = len(reference_decks)
    masked_cluster = labels[masked_idx]
    
    # Trova i mazzi nello stesso cluster
    same_cluster_indices = [i for i, label in enumerate(labels) if label == masked_cluster and i != masked_idx]
    
    if not same_cluster_indices:
        print("Nessun mazzo trovato nello stesso cluster")
        return []
    
    # Calcola la similarità con ogni mazzo nello stesso cluster
    similarities = []
    for i in same_cluster_indices:
        # Usa coseno come metrica base
        sim = Similarity.COSENO(X_norm[masked_idx].tolist(), X_norm[i].tolist())
        
        # Aggiungi peso contestuale se richiesto
        if use_context_weights:
            context_weight = calculate_context_weight(masked_deck, reference_decks[i])
            weighted_sim = sim * (0.7 + 0.3 * context_weight)  # Blend con peso contestuale
        else:
            weighted_sim = sim
        
        similarities.append((i, weighted_sim))
    
    # Ordina per similarità decrescente
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    # Prendi i mazzi più simili (top 30%)
    top_similar = similarities[:max(1, int(len(similarities) * 0.3))]
    
    # Raccogli le carte che non sono nel mazzo mascherato
    card_scores = defaultdict(float)
    masked_card_ids = {card.get_id() for card in masked_deck.carte.keys()}
    
    for idx, sim in top_similar:
        deck = reference_decks[idx]
        for card, count in deck.carte.items():
            if card.get_id() not in masked_card_ids:
                # Pesa il conteggio per la similarità
                card_scores[card] += count * sim
    
    # Normalizza gli score
    if card_scores:
        max_score = max(card_scores.values())
        if max_score > 0:
            card_scores = {card: score / max_score for card, score in card_scores.items()}
    
    # Ordina le carte per score
    predicted_cards = [(card, score) for card, score in card_scores.items()]
    predicted_cards.sort(key=lambda x: x[1], reverse=True)
    
    return predicted_cards[:top_n]


def predict_masked_cards_ensemble(
    masked_deck: Deck,
    reference_decks: List[Deck],
    embeddings: List[Union[Deck.Embedding, List[Deck.Embedding]]],
    methods: List[str],
    n_clusters_map: Dict[Tuple[str, str], int],
    top_n: int = 20
) -> List[Tuple[Card, float]]:
    """
    Predice le carte mascherate utilizzando un ensemble di predittori.
    
    Args:
        masked_deck: Mazzo con carte mascherate
        reference_decks: Mazzi di riferimento
        embeddings: Lista di embeddings da utilizzare
        methods: Lista di metodi di clustering da utilizzare
        n_clusters_map: Dizionario che mappa (embedding, metodo) al numero ottimale di cluster
        top_n: Numero di carte da predire
        
    Returns:
        Lista di tuple (carta, score) ordinate per rilevanza
    """
    all_predictions = []
    
    # Pesi ottimizzati per le combinazioni più efficaci
    weights = {
        (Deck.Embedding.RESISTANCE, "K-Means"): 1.0,
        (Deck.Embedding.RESISTANCE, "Agglomerative"): 0.9,
        (Deck.Embedding.RESISTANCE, "BIRCH"): 0.85,
        ((Deck.Embedding.KEYWORDS, Deck.Embedding.QUANTITY), "K-Means"): 0.8,
        ((Deck.Embedding.KEYWORDS, Deck.Embedding.QUANTITY), "Agglomerative"): 0.8,  # Aggiornato per Agglomerative
        ((Deck.Embedding.KEYWORDS, Deck.Embedding.QUANTITY), "BIRCH"): 0.7,
        (Deck.Embedding.ATTACKS_DMG, "K-Means"): 0.65,
        (Deck.Embedding.ATTACKS_DMG, "Agglomerative"): 0.6,
        (Deck.Embedding.ATTACKS_DMG, "BIRCH"): 0.55,
    }
    
    # Per ogni combinazione di embedding e metodo
    for emb in embeddings:
        emb_name = emb.name if not isinstance(emb, list) else "+".join([e.name for e in emb])
        
        for method in methods:
            # Determina il numero ottimale di cluster
            key = (emb_name, method)
            n_clusters = n_clusters_map.get(key, 4)  # Default a 4 se non trovato
            
            # Ottieni il peso per questa combinazione
            # Converti la lista di embeddings in tupla se necessario per renderla hashable
            if isinstance(emb, list):
                weight_key = (tuple(emb), method)
            else:
                weight_key = (emb, method)
            weight = weights.get(weight_key, 0.5)  # Default a 0.5 se non trovato
            
            # Predici le carte
            predictions = predict_masked_cards_clustering(
                masked_deck,
                reference_decks,
                embedding=emb,
                method=method,
                n_clusters=n_clusters,
                top_n=top_n * 2  # Prendi più carte per avere una buona copertura
            )
            
            # Aggiungi le predizioni pesate
            all_predictions.append((predictions, weight))
    
    # Combina le predizioni
    combined_scores = defaultdict(float)
    
    for predictions, weight in all_predictions:
        for card, score in predictions:
            combined_scores[card] += score * weight
    
    # Normalizza gli score
    if combined_scores:
        max_score = max(combined_scores.values())
        if max_score > 0:
            combined_scores = {card: score / max_score for card, score in combined_scores.items()}
    
    # Ordina le carte per score
    predicted_cards = [(card, score) for card, score in combined_scores.items()]
    predicted_cards.sort(key=lambda x: x[1], reverse=True)
    
    return predicted_cards[:top_n]


def evaluate_masked_prediction(
    decks: List[Deck],
    embeddings: List[Union[Deck.Embedding, List[Deck.Embedding]]],
    methods: List[str],
    n_clusters_map: Dict[Tuple[str, str], int],
    n_masks: int = 5,
    n_tests: int = 100,
    use_ensemble: bool = True
) -> pd.DataFrame:
    """
    Valuta l'accuratezza della predizione di carte mascherate.
    Ottimizzato per le prestazioni con timing e debug.
    
    Args:
        decks: Lista di mazzi
        embeddings: Lista di embeddings da utilizzare
        methods: Lista di metodi di clustering da utilizzare
        n_clusters_map: Dizionario che mappa (embedding, metodo) al numero ottimale di cluster
        n_masks: Numero di carte da mascherare
        n_tests: Numero di test da eseguire
        use_ensemble: Se utilizzare l'ensemble di predittori
        
    Returns:
        DataFrame con i risultati della valutazione
    """
    random.seed(42)
    results = []
    
    # Limita il numero di test per debug/sviluppo
    if n_tests > 10:
        print(f"ATTENZIONE: Esecuzione di {n_tests} test può richiedere molto tempo.")
        print(f"Considera di ridurre n_tests per test iniziali.")
    
    # Pulisci la cache prima di iniziare
    global _embedding_cache
    _embedding_cache = {}
    
    for i in range(n_tests):
        start_time = time.time()
        print(f"Test {i+1}/{n_tests}...")
        
        # Seleziona un mazzo casuale
        deck_index = random.randint(0, len(decks) - 1)
        complete_deck = decks[deck_index]
        
        # Crea mazzo mascherato
        mask_start = time.time()
        masked_deck, masked_cards = complete_deck.mask(n_masks)
        mask_time = time.time() - mask_start
        
        # Predici carte mascherate
        predict_start = time.time()
        if use_ensemble:
            predictions = predict_masked_cards_ensemble(
                masked_deck,
                [d for d in decks if d != complete_deck],
                embeddings=embeddings,
                methods=methods,
                n_clusters_map=n_clusters_map,
                top_n=20
            )
        else:
            # Usa solo la migliore combinazione
            predictions = predict_masked_cards_clustering(
                masked_deck,
                [d for d in decks if d != complete_deck],
                embedding=embeddings[0],
                method=methods[0],
                n_clusters=n_clusters_map.get((embeddings[0].name, methods[0]), 4),
                top_n=20
            )
        predict_time = time.time() - predict_start
        
        # Verifica accuratezza
        masked_card_ids = {card.get_id() for card, _ in masked_cards}
        predicted_card_ids = {card.get_id() for card, _ in predictions}
        
        correct = len(masked_card_ids.intersection(predicted_card_ids))
        
        result = {
            "masked_cards": len(masked_cards),
            "predicted_correctly": correct,
            "accuracy": correct / len(masked_cards) if masked_cards else 0,
            "deck_name": complete_deck.name,
            "total_time": time.time() - start_time,
            "mask_time": mask_time,
            "predict_time": predict_time
        }
        
        results.append(result)
        
        # Stampa risultati parziali per monitoraggio
        print(f"  Accuratezza: {result['accuracy']:.2%}, Tempo: {result['total_time']:.2f}s")
        print(f"  Dettagli: Mascheramento: {result['mask_time']:.2f}s, Predizione: {result['predict_time']:.2f}s")
        
        # Pulisci la cache dopo ogni test per evitare memory leak
        if i % 10 == 9:
            _embedding_cache = {}
    
    # Calcola statistiche
    results_df = pd.DataFrame(results)
    avg_accuracy = results_df["accuracy"].mean()
    avg_time = results_df["total_time"].mean()
    print(f"Accuratezza media: {avg_accuracy:.2%}")
    print(f"Tempo medio per test: {avg_time:.2f}s")
    
    return results_df


def parse_optimal_clusters_results(csv_path="optimal_clusters_score_results.csv"):
    """
    Analizza i risultati del file CSV per determinare il numero ottimale di cluster
    per ogni combinazione di embedding e metodo di clustering.
    
    Args:
        csv_path: Percorso del file CSV con i risultati
        
    Returns:
        Dizionario che mappa (embedding, metodo) al numero ottimale di cluster
    """
    # Carica il file CSV
    df = pd.read_csv(csv_path)
    
    # Filtra le righe con valori NaN
    df = df.dropna(subset=["silhouette", "calinski_harabasz", "davies_bouldin"])
    
    # Ordina per score decrescente
    df = df.sort_values("score", ascending=False)
    
    # Crea un dizionario per mappare (embedding, metodo) al numero ottimale di cluster
    n_clusters_map = {}
    
    # Per ogni combinazione di embedding e metodo, prendi il numero di cluster con lo score più alto
    for _, row in df.iterrows():
        key = (row["embedding"], row["method"])
        if key not in n_clusters_map:
            n_clusters_map[key] = int(row["n_clusters"])
    
    return n_clusters_map


def plot_prediction_results(results_df, output_dir="./plots"):
    """
    Crea grafici per visualizzare i risultati della predizione di carte mascherate.
    
    Args:
        results_df: DataFrame con i risultati della valutazione
        output_dir: Directory dove salvare i grafici
    """
    # Crea la directory se non esiste
    os.makedirs(output_dir, exist_ok=True)
    
    # Istogramma dell'accuratezza
    plt.figure(figsize=(10, 6))
    plt.hist(results_df["accuracy"], bins=10, alpha=0.7, color='blue')
    plt.axvline(results_df["accuracy"].mean(), color='red', linestyle='dashed', linewidth=2)
    plt.xlabel("Accuratezza")
    plt.ylabel("Frequenza")
    plt.title("Distribuzione dell'accuratezza nella predizione di carte mascherate")
    plt.grid(True, alpha=0.3)
    plt.savefig(f"{output_dir}/masked_prediction_accuracy.png")
    plt.close()
    
    # Grafico a barre del numero di carte predette correttamente
    plt.figure(figsize=(10, 6))
    counts = results_df["predicted_correctly"].value_counts().sort_index()
    plt.bar(counts.index, counts.values, alpha=0.7, color='green')
    plt.xlabel("Numero di carte predette correttamente")
    plt.ylabel("Frequenza")
    plt.title("Distribuzione del numero di carte predette correttamente")
    plt.xticks(range(results_df["masked_cards"].max() + 1))
    plt.grid(True, alpha=0.3, axis='y')
    plt.savefig(f"{output_dir}/masked_prediction_correct_counts.png")
    plt.close()


def main():
    """Funzione principale."""
    print("Inizio esecuzione...")
    start_time = time.time()
    
    # Carica i mazzi
    load_start = time.time()
    decks = load_decks()
    print(f"Caricamento mazzi completato in {time.time() - load_start:.2f}s")
    
    # Analizza i risultati per determinare il numero ottimale di cluster
    cluster_start = time.time()
    n_clusters_map = parse_optimal_clusters_results()
    print(f"Analisi cluster completata in {time.time() - cluster_start:.2f}s")
    
    # Seleziona i migliori embeddings e metodi di clustering
    # Versione ottimizzata: utilizziamo solo le combinazioni più efficaci
    top_embeddings = [
        # Deck.Embedding.RESISTANCE,  # Commentato per velocizzare i test
        [Deck.Embedding.KEYWORDS, Deck.Embedding.QUANTITY],  # Questa è la combinazione più efficace
        # Deck.Embedding.ATTACKS_DMG  # Commentato per velocizzare i test
    ]
    
    top_methods = [
        # "K-Means",  # Commentato per velocizzare i test
        "Agglomerative",  # Questo metodo funziona bene con KEYWORDS+QUANTITY
        # "BIRCH"  # Commentato per velocizzare i test
    ]
    
    # Valuta la predizione di carte mascherate
    # Ridotto il numero di test per debug/sviluppo
    eval_start = time.time()
    results = evaluate_masked_prediction(
        decks=decks,
        embeddings=top_embeddings,
        methods=top_methods,
        n_clusters_map=n_clusters_map,
        n_masks=5,
        n_tests=5,  # Ridotto per test iniziali
        use_ensemble=True
    )
    print(f"Valutazione completata in {time.time() - eval_start:.2f}s")
    
    # Salva i risultati in un file CSV
    results.to_csv("masked_prediction_results.csv", index=False)
    
    # Crea grafici per visualizzare i risultati
    plot_prediction_results(results)
    
    # Esempio di utilizzo
    print("\n=== ESEMPIO DI UTILIZZO ===")
    
    # Seleziona un mazzo casuale
    random.seed(42)
    deck_index = random.randint(0, len(decks) - 1)
    complete_deck = decks[deck_index]
    
    print(f"Mazzo selezionato: {complete_deck.name}")
    print(f"Numero di carte: {sum(complete_deck.carte.values())}")
    
    # Crea mazzo mascherato
    masked_deck, masked_cards = complete_deck.mask(5)
    
    print(f"Carte mascherate:")
    for card, qty in masked_cards:
        print(f"- {card.name} (x{qty})")
    
    # Predici carte mascherate
    predictions = predict_masked_cards_ensemble(
        masked_deck,
        [d for d in decks if d != complete_deck],
        embeddings=top_embeddings,
        methods=top_methods,
        n_clusters_map=n_clusters_map,
        top_n=10
    )
    
    print(f"\nCarte predette (top 10):")
    for i, (card, score) in enumerate(predictions[:10], 1):
        in_masked = "✓" if card.get_id() in {c.get_id() for c, _ in masked_cards} else " "
        print(f"{i}. {in_masked} {card.name} (Score: {score:.4f})")
    
    # Calcola l'accuratezza
    masked_card_ids = {card.get_id() for card, _ in masked_cards}
    predicted_card_ids = {card.get_id() for card, _ in predictions[:10]}
    correct = len(masked_card_ids.intersection(predicted_card_ids))
    
    print(f"\nAccuratezza: {correct}/{len(masked_cards)} ({correct/len(masked_cards):.2%})")


if __name__ == "__main__":
    main()
