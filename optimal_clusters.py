#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modulo per determinare il numero ottimale di cluster utilizzando il metodo del gomito (elbow method)
e l'analisi della silhouette.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time
import random
import json
import itertools
from typing import List, Dict, Any, Optional, Tuple, Callable, Union
from collections import Counter
from scipy.sparse import csr_matrix

# Algoritmi di clustering
from sklearn.cluster import KMeans, AgglomerativeClustering, DBSCAN, SpectralClustering, Birch
# from sklearn.mixture import GaussianMixture

# Metriche e preprocessing
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from sklearn.preprocessing import StandardScaler

# Importazioni specifiche del progetto
from structures.deck import Deck
from structures.similarity import Similarity


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


# Funzione per caricare i dati
def csr_load(path: str="cache/decks_csr.npz"):
    z = np.load(path, allow_pickle=True)
    X = csr_matrix(
        (z["data"], z["indices"], z["indptr"]),
        shape=tuple(z["shape"])
    )
    return X, z["deck_ids"], z["card_ids"]


def load_decks():
    """Carica i mazzi dal file cache."""
    # Carica i dati
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
    return decks


def determine_optimal_clusters(X: np.ndarray, max_clusters: int = 10, random_state: int = 42):
    """
    Determina il numero ottimale di cluster utilizzando una combinazione di metodo del gomito
    e analisi della silhouette.
    
    Args:
        X: Matrice di dati
        max_clusters: Numero massimo di cluster da considerare
        random_state: Seed per la riproducibilità
        
    Returns:
        Numero ottimale di cluster
    """
    # Assicurati che max_clusters non superi il numero di campioni
    max_clusters = min(max_clusters, X.shape[0] - 1)
    
    # Limita a un minimo di 2 cluster
    if max_clusters < 2:
        return 2
    
    # Range di cluster da valutare
    range_n_clusters = range(2, max_clusters + 1)
    
    # Calcola l'inerzia (per il metodo del gomito)
    inertia = []
    silhouette_scores = []
    
    for n_clusters in range_n_clusters:
        # Applica K-Means
        kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
        kmeans.fit(X)
        inertia.append(kmeans.inertia_)
        
        # Calcola il silhouette score
        if n_clusters > 1:  # Silhouette richiede almeno 2 cluster
            labels = kmeans.labels_
            silhouette_avg = silhouette_score(X, labels)
            silhouette_scores.append(silhouette_avg)
        else:
            silhouette_scores.append(0)
    
    # Metodo del gomito: calcola la derivata seconda dell'inerzia
    if len(inertia) > 2:
        # Calcola le differenze (prima derivata)
        deltas = np.diff(inertia)
        # Calcola le differenze delle differenze (seconda derivata)
        delta_deltas = np.diff(deltas)
        # Il punto di massima curvatura è dove la seconda derivata è massima
        elbow_point = np.argmax(np.abs(delta_deltas)) + 2  # +2 perché abbiamo perso due indici con le due diff
    else:
        elbow_point = 2  # Default se non abbiamo abbastanza punti
    
    # Metodo della silhouette: trova il massimo silhouette score
    if silhouette_scores:
        silhouette_point = np.argmax(silhouette_scores) + 2  # +2 perché iniziamo da 2 cluster
    else:
        silhouette_point = 2  # Default
    
    # Combina i risultati: se sono vicini, prendi il valore della silhouette
    # altrimenti prendi il valore più grande per precisione
    if abs(elbow_point - silhouette_point) <= 2:
        optimal_clusters = silhouette_point
    else:
        optimal_clusters = max(elbow_point, silhouette_point)
    
    print(f"Numero ottimale di cluster determinato: {optimal_clusters}")
    print(f"- Metodo del gomito: {elbow_point}")
    print(f"- Metodo della silhouette: {silhouette_point}")
    
    # Visualizza il grafico del metodo del gomito
    plt.figure(figsize=(10, 6))
    plt.plot(range_n_clusters, inertia, 'bo-')
    plt.axvline(x=elbow_point, color='r', linestyle='--', label=f'Elbow point: {elbow_point}')
    plt.xlabel('Numero di cluster')
    plt.ylabel('Inerzia')
    plt.title('Metodo del gomito per determinare il numero ottimale di cluster')
    plt.legend()
    plt.grid(True)
    plt.savefig("elbow_method.png")
    plt.show()
    
    # Visualizza il grafico del silhouette score
    plt.figure(figsize=(10, 6))
    plt.plot(range_n_clusters, silhouette_scores, 'go-')
    plt.axvline(x=silhouette_point, color='r', linestyle='--', label=f'Silhouette point: {silhouette_point}')
    plt.xlabel('Numero di cluster')
    plt.ylabel('Silhouette Score')
    plt.title('Silhouette Score per determinare il numero ottimale di cluster')
    plt.legend()
    plt.grid(True)
    plt.savefig("silhouette_method.png")
    plt.show()
    
    return optimal_clusters


def evaluate_clustering_methods(
    X: np.ndarray,
    n_clusters: int = None,
    random_state: int = 42,
    metric: Similarity = Similarity.COSENO
):
    """
    Valuta diversi metodi di clustering su un dataset.
    
    Args:
        X: Matrice di dati
        n_clusters: Numero di cluster da utilizzare (se None, viene determinato automaticamente)
        random_state: Seed per la riproducibilità
        metric: Metrica di similarità da utilizzare
        
    Returns:
        DataFrame con i risultati della valutazione
    """
    # Determina il numero ottimale di cluster se non specificato
    if n_clusters is None:
        n_clusters = determine_optimal_clusters(X, max_clusters=10, random_state=random_state)
    
    # Definisci i metodi di clustering da valutare
    clustering_methods = {
        "K-Means": KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10),
        "Agglomerative": AgglomerativeClustering(n_clusters=n_clusters),
        "DBSCAN": DBSCAN(eps=0.5, min_samples=5),
        # "Spectral": SpectralClustering(n_clusters=n_clusters, random_state=random_state),
        # "Gaussian Mixture": GaussianMixture(n_components=n_clusters, random_state=random_state),
        "BIRCH": Birch(n_clusters=n_clusters)
    }
    
    results = []
    
    # Valuta ogni metodo
    for name, method in clustering_methods.items():
        print(f"Valutazione {name}...")
        
        try:
            # Applica il clustering
            start_time = time.time()
            labels = method.fit_predict(X)
            execution_time = time.time() - start_time
            
            # Calcola il numero effettivo di cluster
            n_clusters_actual = len(set(labels)) - (1 if -1 in labels else 0)
            
            # Calcola le metriche di valutazione
            if n_clusters_actual > 1:
                silhouette = silhouette_score(X, labels)
                try:
                    calinski = calinski_harabasz_score(X, labels)
                    davies = davies_bouldin_score(X, labels)
                except Exception as e:
                    print(f"Errore nel calcolo delle metriche per {name}: {e}")
                    calinski = None
                    davies = None
            else:
                silhouette = None
                calinski = None
                davies = None
                
            # Aggiungi ai risultati
            results.append({
                "method": name,
                "n_clusters": n_clusters_actual,
                "silhouette": silhouette,
                "calinski_harabasz": calinski,
                "davies_bouldin": davies,
                "execution_time": execution_time,
                "labels": labels
            })
            
        except Exception as e:
            print(f"Errore nell'applicazione di {name}: {e}")
            results.append({
                "method": name,
                "n_clusters": None,
                "silhouette": None,
                "calinski_harabasz": None,
                "davies_bouldin": None,
                "execution_time": None,
                "labels": None,
                "error": str(e)
            })
    
    # Crea DataFrame
    df = pd.DataFrame(results)
    return df


def evaluate_clustering_with_embeddings(
    decks: List[Deck],
    embeddings: List[Union[Deck.Embedding, List[Deck.Embedding]]],
    metrics: List[Similarity],
    n_clusters: int = None,
    sample_size: int = 500,
    random_state: int = 42
):
    """
    Valuta diversi metodi di clustering con diverse rappresentazioni e metriche.
    
    Args:
        decks: Lista di mazzi
        embeddings: Lista di embeddings da utilizzare (singoli o combinazioni)
        metrics: Lista di metriche di similarità da utilizzare
        n_clusters: Numero di cluster da utilizzare (se None, viene determinato automaticamente)
        sample_size: Dimensione del campione
        random_state: Seed per la riproducibilità
        
    Returns:
        DataFrame con i risultati della valutazione
    """
    # Campiona i mazzi
    random.seed(random_state)
    sample = random.sample(decks, min(sample_size, len(decks)))
    
    all_results = []
    
    # Per ogni embedding o combinazione di embeddings
    for emb in embeddings:
        # Determina il nome dell'embedding o della combinazione
        if isinstance(emb, list):
            emb_name = " + ".join([e.name for e in emb])
            # Usa la funzione combine_embeddings per combinare gli embeddings
            X, bad = combine_embeddings(sample, emb)
        else:
            emb_name = emb.name
            # Usa _safe_matrix per un singolo embedding
            X, bad = _safe_matrix(sample, emb)
            
        print(f"\n=== Valutazione con embedding {emb_name} ===")
        
        # Skip se non abbiamo righe utili
        if X is None or X.size == 0 or not np.any(X) or not _has_variance(X):
            print(f"Embedding {emb_name} non valido per valutazione")
            continue
        
        # Normalizza
        scaler = StandardScaler()
        X_norm = scaler.fit_transform(X)
        
        # Per ogni metrica
        for metric in metrics:
            print(f"\n--- Metrica: {metric.__name__} ---")
            
            # Valuta i metodi di clustering
            results_df = evaluate_clustering_methods(
                X_norm, 
                n_clusters=n_clusters, 
                random_state=random_state,
                metric=metric
            )
            
            # Aggiungi informazioni sull'embedding e la metrica
            results_df["embedding"] = emb_name
            results_df["metric"] = metric.__name__
            
            # Visualizza i risultati
            display_df = results_df.drop(columns=["labels"])
            print(display_df)
            
            # Aggiungi ai risultati complessivi
            all_results.append(results_df)
    
    # Combina tutti i risultati
    if all_results:
        combined_df = pd.concat(all_results, ignore_index=True)
        combined_df = combined_df.drop(columns=["labels"])
        return combined_df
    else:
        return pd.DataFrame()


def generate_embedding_combinations(embeddings: List[Deck.Embedding]) -> List[Union[Deck.Embedding, List[Deck.Embedding]]]:
    """
    Genera tutte le combinazioni possibili di embeddings fino a 2 elementi.
    
    Args:
        embeddings: Lista di embeddings da combinare
        
    Returns:
        Lista contenente singoli embeddings e coppie di embeddings
    """
    result = []
    
    # Aggiungi singoli embeddings
    for emb in embeddings:
        result.append(emb)
    
    # Aggiungi coppie di embeddings
    for pair in itertools.combinations(embeddings, 2):
        result.append(list(pair))
    
    return result


def find_optimal_clusters_for_all_methods():
    """
    Trova il numero ottimale di cluster per ogni metodo di clustering
    utilizzando diversi embedding e metriche, incluse le combinazioni di embeddings.
    """
    # Carica i mazzi
    decks = load_decks()
    
    # Definisci gli embedding da utilizzare
    base_embeddings = [
        Deck.Embedding.ATTACKS_DMG,
        Deck.Embedding.ATTACKS_COSTS,
        Deck.Embedding.RESISTANCE,
        Deck.Embedding.PKMN_TYPES
    ]
    
    # Genera tutte le combinazioni di embeddings (singoli e coppie)
    embeddings_to_evaluate = generate_embedding_combinations(base_embeddings)
    
    # Definisci le metriche da utilizzare
    metrics_to_evaluate = [
        Similarity.COSENO,
        Similarity.OVERLAP,
        Similarity.PEARSON
    ]
    
    # Campiona i mazzi per efficienza
    random.seed(42)
    sample_size = 500
    sample = random.sample(decks, min(sample_size, len(decks)))
    
    results = []
    
    # Per ogni embedding o combinazione di embeddings
    for emb in embeddings_to_evaluate:
        # Determina il nome dell'embedding o della combinazione
        if isinstance(emb, list):
            emb_name = " + ".join([e.name for e in emb])
            # Usa la funzione combine_embeddings per combinare gli embeddings
            X, bad = combine_embeddings(sample, emb)
        else:
            emb_name = emb.name
            # Usa _safe_matrix per un singolo embedding
            X, bad = _safe_matrix(sample, emb)
            
        print(f"\n=== Valutazione con embedding {emb_name} ===")
        
        # Skip se non abbiamo righe utili
        if X is None or X.size == 0 or not np.any(X) or not _has_variance(X):
            print(f"Embedding {emb_name} non valido per valutazione")
            continue
        
        # Normalizza
        scaler = StandardScaler()
        X_norm = scaler.fit_transform(X)
        
        # Determina il numero ottimale di cluster
        optimal_n = determine_optimal_clusters(X_norm, max_clusters=15, random_state=42)
        
        # Aggiungi ai risultati
        results.append({
            "embedding": emb_name,
            "optimal_clusters": optimal_n
        })
    
    # Crea DataFrame con i risultati
    results_df = pd.DataFrame(results)
    print("\n=== RISULTATI NUMERO OTTIMALE DI CLUSTER ===")
    print(results_df)
    
    # Salva i risultati in un file CSV
    results_df.to_csv("optimal_clusters_results.csv", index=False)
    
    return results_df


if __name__ == "__main__":
    # Esegui la funzione principale
    find_optimal_clusters_for_all_methods()