from enum import Enum
import math


class Similarity(Enum):
    """Metriche di similarità tra due mazzi."""

    def coseno(v1: list[float], v2: list[float]) -> float:
        """Similitudine coseno tra due vettori."""
        if len(v1) != len(v2):
            raise ValueError("I vettori devono avere la stessa lunghezza.")

        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a**2 for a in v1))
        norm2 = math.sqrt(sum(b**2 for b in v2))

        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)


    def overlap(v1: list[int], v2: list[int]) -> float:
        """Similitudine di overlap: somma dei minimi sui massimi."""
        if len(v1) != len(v2):
            raise ValueError("I vettori devono avere la stessa lunghezza.")

        intersezione = sum(min(a, b) for a, b in zip(v1, v2))
        tot_massimo = max(sum(v1), sum(v2))

        if tot_massimo == 0:
            return 0.0
        return intersezione / tot_massimo


    def jaccard(v1: list[int], v2: list[int]) -> float:
        """Indice di Jaccard per vettori binari o interi."""
        if len(v1) != len(v2):
            raise ValueError("I vettori devono avere la stessa lunghezza.")

        intersezione = sum(1 for a, b in zip(v1, v2) if a > 0 and b > 0)
        unione = sum(1 for a, b in zip(v1, v2) if a > 0 or b > 0)

        if unione == 0:
            return 0.0
        return intersezione / unione
    

    def manhattan(v1: list[float], v2: list[float]) -> float:
        """Distanza di Manhattan: somma delle differenze assolute tra i componenti."""
        if len(v1) != len(v2):
            raise ValueError("I vettori devono avere la stessa lunghezza.")
        return sum(abs(a - b) for a, b in zip(v1, v2))
    

    def euclidea(v1: list[float], v2: list[float]) -> float:
        """Distanza Euclidea: radice quadrata della somma dei quadrati delle differenze."""
        if len(v1) != len(v2):
            raise ValueError("I vettori devono avere la stessa lunghezza.")
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2)))
    

    def weighted_jaccard(v1: list[float], v2: list[float]) -> float:
        """Weighted Jaccard: somma dei minimi diviso la somma dei massimi elemento per elemento."""
        if len(v1) != len(v2):
            raise ValueError("I vettori devono avere la stessa lunghezza.")

        intersection = sum(min(a, b) for a, b in zip(v1, v2))
        union = sum(max(a, b) for a, b in zip(v1, v2))

        if union == 0:
            return 0.0
        return intersection / union
    

    def chebyshev(v1: list[float], v2: list[float]) -> float:
        """Distanza di Chebyshev: massimo valore assoluto tra le differenze dei componenti."""
        if len(v1) != len(v2):
            raise ValueError("I vettori devono avere la stessa lunghezza.")
        return max(abs(a - b) for a, b in zip(v1, v2))


    def pearson(v1: list[float], v2: list[float]) -> float:
        """Correlazione di Pearson: misura la correlazione lineare tra i due vettori."""
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
        return num / (den1 * den2)


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

    def __call__(self, mazzo1, mazzo2) -> float:
        return self.value(mazzo1, mazzo2)