from owlready2 import *
from owlready2 import Thing

def get_class_names(c):
    # Per gestire anche union (Or) e intersection (And) di classi
    if isinstance(c, And) or isinstance(c, Or):
        names = []
        for op in c.Classes:
            names.extend(get_class_names(op))
        return names
    else:
        return [c.name]
    


# Percorso ontologia corretto (3 slash dopo file:)
onto = get_ontology("file:///home/gp/Scrivania/ontologyUpdated.owl").load()

if onto is None:
    print("Errore: ontologia non caricata")
    exit(1)

print("Struttura delle classi nell'ontologia:")

def print_classes(cls, level=0):
    print("  " * level + cls.name)
    for subclass in cls.subclasses():
        print_classes(subclass, level + 1)

print_classes(Thing)

print("\nProprietà oggetto:")
for prop in onto.object_properties():
    domains = []
    for d in prop.domain:
        domains.extend(get_class_names(d))
    ranges = []
    for r in prop.range:
        ranges.extend(get_class_names(r))
    print(f"- {prop.name}:")
    print(f"    Domain: {domains}")
    print(f"    Range: {ranges}")

print("\nProprietà dati:")
for prop in onto.data_properties():
    domains = []
    for d in prop.domain:
        domains.extend(get_class_names(d))
    print(f"- {prop.name}:")
    print(f"    Domain: {domains}")
