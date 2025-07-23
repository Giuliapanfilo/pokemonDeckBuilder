import card
from enum import Enum
Carta = card.Carta

import math


class Mazzo:
    archetipo: str
    carte : dict[Carta, int] # carta:quantità
    # name : str
    # format : str

    def add(self, carta:Carta, quantità:int=1):
        """aggiunge quantità di carta al mazzo"""
        if carta in self.carte:
            self.carte[carta] += quantità
        else:
            self.carte[carta] = quantità


    def rem(self, carta:Carta, quantità:int=1):
        """rimuove quantità di carta dal mazzo"""
        if carta in self.carte:
            self.carte[carta] -= quantità
            if self.carte[carta] <= 0:
                del self.carte[carta]
    

    def len(self) -> int:
        """Restituisce il numero di carte presenti nel mazzo"""
        return sum(self.carte.values())
    

    def __hash__(self):
        carte_tuple = tuple(sorted((carta, qty) for carta, qty in self.carte.items()))
        return hash((carte_tuple))
    



    class Embedding(Enum): 
        """La rappresentazione del mazzo"""
        def quantità(m:"Mazzo") -> list:
            pass

        QUANTITÀ = staticmethod(quantità)


        def __call__(self, mazzo:"Mazzo") -> list[float]:
            return self.value(mazzo)



    class Similarità(Enum):

        def coseno(m1: list, m2: list) -> float:
            carte = set(m1.carte.keys()) | set(m2.carte.keys()) # unione
            v1 = [m1.carte.get(c,0) for c in carte]
            v2 = [m2.carte.get(c,0) for c in carte]

            dot = sum(a*b for a,b in zip(v1,v2))
            norm1 = math.sqrt(sum(a**2 for a in v1))
            norm2 = math.sqrt(sum(b**2 for b in v2))

            if norm1 == 0 or norm2 == 0 : return 0.0
            return dot / (norm1 * norm2)


        def overlap(m1:"Mazzo", m2:"Mazzo")-> float:
            intersezione = m1.carte.keys() & m2.carte.keys()
            tot_condiviso = sum(min(m1.carte[c], m2.carte[c]) for c in intersezione)
            tot_massimo = max(m1.len(), m2.len())

            if tot_massimo == 0 : return 0.0
            return tot_condiviso/tot_massimo


        def jaccard(m1:"Mazzo", m2:"Mazzo")-> float:
            i1 = {c.get_id() for c in m1.carte.keys()}
            i2 = {c.get_id() for c in m2.carte.keys()}
            intersez = i1 & i2
            unione = i1 | i2

            if not unione: return 0.0
            return len(intersez) / len(unione)
        
        OVERLAP = staticmethod(overlap)
        COSENO = staticmethod(coseno)
        JACCARD = staticmethod(jaccard)

        def __call__(self, mazzo1, mazzo2) -> float:
            return self.value(mazzo1, mazzo2)
    

    def similarity(
            self, 
            other:"Mazzo", 
            metrica: Similarità = Similarità.COSENO, 
            embedding: Embedding = Embedding.QUANTITÀ):
        """calcola similarità tra due mazzi"""
        return Mazzo.similarity(self, other, metrica, embedding)


    @staticmethod
    def similarity(
            mazzo1:"Mazzo", 
            mazzo2:"Mazzo", 
            metrica:Similarità = Similarità.COSENO, 
            embedding:Embedding = Embedding.QUANTITÀ) -> float:
        """calcola similarità tra due mazzi"""
        return metrica(embedding(mazzo1), embedding(mazzo2))
    







