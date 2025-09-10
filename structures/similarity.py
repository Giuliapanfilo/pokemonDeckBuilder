from enum import Enum
import math


class Similarity(Enum):
    """Metriche di similarità tra due mazzi."""

    def coseno(v1: list[float] = None, v2: list[float] = None) -> float | str:
        """Similitudine coseno tra due vettori. Normalizzata in [0,1]."""
        if v1 is None and v2 is None:
            return "COSENO"
            
        if len(v1) != len(v2):
            raise ValueError("I vettori devono avere la stessa lunghezza.")

        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a**2 for a in v1))
        norm2 = math.sqrt(sum(b**2 for b in v2))

        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Coseno è già in [0,1] se i vettori hanno componenti non negative
        # Altrimenti, normalizza da [-1,1] a [0,1]
        similarity = dot / (norm1 * norm2)
        if min(v1) < 0 or min(v2) < 0:  # Se ci sono componenti negative
            similarity = (similarity + 1) / 2
        
        return similarity


    def overlap(v1: list[int] = None, v2: list[int] = None) -> float | str:
        """Similitudine di overlap: somma dei minimi sui massimi. Normalizzata in [0,1]."""
        if v1 is None and v2 is None:
            return "OVERLAP"
            
        if len(v1) != len(v2):
            raise ValueError("I vettori devono avere la stessa lunghezza.")

        intersezione = sum(min(a, b) for a, b in zip(v1, v2))
        tot_massimo = max(sum(v1), sum(v2))

        if tot_massimo == 0:
            return 0.0
            
        # Assicuriamoci che il risultato sia nel range [0,1]
        similarity = intersezione / tot_massimo
        return min(1.0, max(0.0, similarity))


    def jaccard(v1: list[int] = None, v2: list[int] = None) -> float | str:
        """Indice di Jaccard per vettori binari o interi."""
        if v1 is None and v2 is None:
            return "JACCARD"
            
        if len(v1) != len(v2):
            raise ValueError("I vettori devono avere la stessa lunghezza.")

        intersezione = sum(1 for a, b in zip(v1, v2) if a > 0 and b > 0)
        unione = sum(1 for a, b in zip(v1, v2) if a > 0 or b > 0)

        if unione == 0:
            return 0.0
        return intersezione / unione
    

    def manhattan(v1: list[float] = None, v2: list[float] = None) -> float | str:
        """Distanza di Manhattan: somma delle differenze assolute tra i componenti. Normalizzata in [0,1]."""
        if v1 is None and v2 is None:
            return "MANHATTAN"
            
        if len(v1) != len(v2):
            raise ValueError("I vettori devono avere la stessa lunghezza.")
        
        # Calcola la distanza di Manhattan
        distance = sum(abs(a - b) for a, b in zip(v1, v2))
        
        # Converti la distanza in similarità normalizzata [0,1]
        # Usa una funzione di decadimento esponenziale
        return math.exp(-distance)
    

    def euclidea(v1: list[float] = None, v2: list[float] = None) -> float | str:
        """Distanza Euclidea: radice quadrata della somma dei quadrati delle differenze. Normalizzata in [0,1]."""
        if v1 is None and v2 is None:
            return "EUCLIDEA"
            
        if len(v1) != len(v2):
            raise ValueError("I vettori devono avere la stessa lunghezza.")
        
        # Calcola la distanza euclidea
        distance = math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2)))
        
        # Converti la distanza in similarità normalizzata [0,1]
        # Usa una funzione di decadimento esponenziale
        return math.exp(-distance)
    

    def weighted_jaccard(v1: list[float] = None, v2: list[float] = None) -> float | str:
        """Weighted Jaccard: somma dei minimi diviso la somma dei massimi elemento per elemento. Normalizzata in [0,1]."""
        if v1 is None and v2 is None:
            return "WEIGHTED_JACCARD"
            
        if len(v1) != len(v2):
            raise ValueError("I vettori devono avere la stessa lunghezza.")

        # Assicuriamoci che i valori siano non-negativi
        v1_non_neg = [max(0.0, x) for x in v1]
        v2_non_neg = [max(0.0, x) for x in v2]
        
        intersection = sum(min(a, b) for a, b in zip(v1_non_neg, v2_non_neg))
        union = sum(max(a, b) for a, b in zip(v1_non_neg, v2_non_neg))

        if union == 0:
            return 0.0
            
        # Assicuriamoci che il risultato sia nel range [0,1]
        similarity = intersection / union
        return min(1.0, max(0.0, similarity))
    

    def chebyshev(v1: list[float] = None, v2: list[float] = None) -> float | str:
        """Distanza di Chebyshev: massimo valore assoluto tra le differenze dei componenti. Normalizzata in [0,1]."""
        if v1 is None and v2 is None:
            return "CHEBYSHEV"
            
        if len(v1) != len(v2):
            raise ValueError("I vettori devono avere la stessa lunghezza.")
        
        # Calcola la distanza di Chebyshev
        distance = max(abs(a - b) for a, b in zip(v1, v2))
        
        # Converti la distanza in similarità normalizzata [0,1]
        # Usa una funzione di decadimento esponenziale
        return math.exp(-distance)


    def pearson(v1: list[float] = None, v2: list[float] = None) -> float | str:
        """Correlazione di Pearson: misura la correlazione lineare tra i due vettori. Normalizzata in [0,1]."""
        if v1 is None and v2 is None:
            return "PEARSON"
            
        if len(v1) != len(v2):
            raise ValueError("I vettori devono avere la stessa lunghezza.")
        if len(v1) < 2:
            return 0.0  # Pearson richiede almeno due valori

        mean1 = sum(v1) / len(v1)
        mean2 = sum(v2) / len(v2)

        num = sum((a - mean1) * (b - mean2) for a, b in zip(v1, v2))
        den1 = math.sqrt(sum((a - mean1) ** 2 for a in v1))
        den2 = math.sqrt(sum((b - mean2) ** 2 for b in v2))

        if den1 == 0 or den2 == 0:
            return 0.0
            
        # Pearson è in [-1,1], normalizza a [0,1]
        correlation = num / (den1 * den2)
        return (correlation + 1) / 2


    OVERLAP = staticmethod(overlap)
    """Similarità di Overlap: misura la proporzione di carte comuni tra i due mazzi, rispetto alla somma minima delle quantità."""

    COSENO = staticmethod(coseno)
    """Similarità Coseno: calcola il coseno dell’angolo tra i due vettori di embedding, utile per confrontare distribuzioni."""

    JACCARD = staticmethod(jaccard)
    """Indice di Jaccard: rapporto tra l’intersezione e l’unione degli insiemi di carte presenti nei due mazzi."""

    MANHATTAN = staticmethod(manhattan)
    """Distanza di Manhattan: somma delle differenze assolute tra i componenti dei vettori."""

    EUCLIDEA = staticmethod(euclidea)
    """Distanza Euclidea tra due vettori (radice della somma dei quadrati delle differenze)."""

    WEIGHTED_JACCARD = staticmethod(weighted_jaccard)
    """Indice di Jaccard ponderato: rapporto tra somma dei minimi e somma dei massimi per ogni elemento."""

    CHEBYSHEV = staticmethod(chebyshev)
    """Distanza di Chebyshev: massima differenza assoluta tra elementi corrispondenti."""

    PEARSON = staticmethod(pearson)
    """Coefficiente di Pearson: misura la correlazione lineare tra i due vettori (da -1 a 1)."""

    def __call__(self, mazzo1=None, mazzo2=None) -> float | str:
        """
        Se chiamata con due mazzi, calcola la similarità.
        Se chiamata senza argomenti, restituisce il nome della metrica.
        """
        if mazzo1 is None and mazzo2 is None:
            return self.name
        return self.value(mazzo1, mazzo2)