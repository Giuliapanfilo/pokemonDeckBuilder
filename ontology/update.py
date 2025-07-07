from owlready2 import *

onto = get_ontology("http://example.org/pokemonOntology.owl")

with onto:
    # Classi principali
    class Card(Thing): pass
    class Pokemon(Card): pass
    class Move(Thing): pass
    class Type(Thing): pass
    class Archetype(Thing): pass
    class Species(Thing): pass
    
    # Per permettere a hasType di avere come dominio sia Pokemon che Move,
    # definiamo una classe intermedia 'HasTypeDomain'
    class HasTypeDomain(Thing): pass
    HasTypeDomain.is_a.append(Pokemon)
    HasTypeDomain.is_a.append(Move)
    
    # Proprietà oggetto
    class hasType(ObjectProperty):
        domain = [HasTypeDomain]
        range = [Type]

    # Proprietà inverse
    class evolvesFrom(ObjectProperty):
        domain = [Species]
        range = [Species]
        inverse_property = None

    class evolvesTo(ObjectProperty):
        domain = [Species]
        range = [Species]
        inverse_property = evolvesFrom

    # Esempio di proprietà funzionale (univoca)
    class entryNumber(DataProperty, FunctionalProperty):
        domain = [Species]
        range = [int]

    # Disjointness di classi
    AllDifferent([Pokemon, Move, Archetype, Species, Type])

    # Restrizioni esempio
    Species.is_a.append(hasType.min(1))

    # Altre proprietà
    class hasCard(ObjectProperty):
        domain = [Archetype]
        range = [Card]

    # Cardinalità massima (esempio)
    Species.is_a.append(entryNumber.max(1))

# Salva
onto.save(file="pokemonOntologyFinal.owl", format="rdfxml")
print("Ontologia finale salvata.")
