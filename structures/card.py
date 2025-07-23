
from energy import Energy
from set_carte import SetCarte
import re
import json
from settings import PROJECT_ROOT


def parse_code(code_string:str) -> tuple[SetCarte, str]:
	"""Estrapola il set e il numero di una carta
		Examples:
			SWSH10TG-TG02 -> (swsh10, 02)
			SWSH011 -> (swsh1, 011)
	"""
	not_ptcgo = re.match(r"^([A-Z0-9]+)-([A-Z]*\d+)$", code_string)
	if not_ptcgo:
		return SetCarte(not_ptcgo.group(1), False), not_ptcgo.group(2)
	
	ptcgo = re.match(r"^([A-Z]+)([0-9]{3,})$", code_string)
	if ptcgo:
		return SetCarte(ptcgo.group(1), True), ptcgo.group(2)

	raise ValueError("Codice carta non valido")


def search(set_code: str, number: str) -> dict:
	"""Cerca i dati di una carta in base al suo set e numero"""
	file_path = PROJECT_ROOT / "data" / "cards" / "en" / f"{set_code}.json"
	if not file_path.exists():
		raise FileNotFoundError(f"File set non trovato: {file_path}")
	
	with open(file_path) as f:
		dati_set = json.load(f)
	
	id_carta = f"{set_code}-{number}"
	if id_carta not in dati_set:
		raise KeyError(f"Carta {id_carta} non trovata nel set {file_path.name}")
	
	return dati_set[id_carta]




class Carta:
	expansion: SetCarte
	number: str
	name: str
	# rarità: str

	def __init__(self,	code_string: str):
		self.expansion, self.number = parse_code(code_string)
		dati = search(self.expansion.code, self.number)
		self.estrai(dati)


	def estrai(self, dati):
		self.name = dati.get("name")
		self.supertype = dati.get("supertype")
		# self.rarità = dati.get("rarity")


	def get_id(self):
		return f"{self.expansion.code}-{self.number}"
	

	def to_facts(self) -> list[str]:
		"""Trasforma una carta in fatti OWL usando introspezione

			Example Output:
				:charizard_4_102 rdf:type :Pokémon .
				:charizard_4_102 :name "Charizard" .
				:charizard_4_102 :expansion "base1" .
				:charizard_4_102 :number "4" .
				:charizard_4_102 :type "Fire" .
				:charizard_4_102 :evolvesFrom "Charmeleon" .
		
		"""
		from enum import Enum
		iri = f":{self.get_id().replace('/', '_')}"
		facts = []

		# Aggiungi il tipo OWL
		facts.append(f"{iri} rdf:type :{self.supertype} .")

		for attr, value in vars(self).items():
			if attr.startswith("_") or value is None:
				continue

			# Normalizza valore
			if isinstance(value, Enum):
				facts.append(f'{iri} :{attr} "{value.value}" .')

			elif isinstance(value, list):
				for item in value:
					if item is None: continue
					val = item.value if isinstance(item, Enum) else item
					facts.append(f'{iri} :{attr} "{val}" .')

			elif isinstance(value, SetCarte):
				facts.append(f'{iri} :{attr} "{value.code}" .')

			else:
				facts.append(f'{iri} :{attr} "{value}" .')

		return facts





### serializzazione
	def _chiave(self):
		return (self.expansion.code, self.number)

	def __hash__(self):
		return hash(self._chiave())

	def __eq__(self, other):
		return isinstance(other, Carta) and self._chiave() == other._chiave()




class Pokémon(Carta):
	supertype = "Pokémon"
	subtypes : list[str]
	type: Energy
	# nomi di pokemon, non carte
	evolves_from: str 
	evolves_to: list[str]

	# weaknesses: list[Energy]
	# resistances: list[Energy]
	# hp: int #da trasformare perché non sono int
	# attacks: list[Attack]
	# abilities: list[Abilities]
	# retreat_cost: int # costo convertito
	
	def estrai(self, dati):
		self.type = Energy.from_str(dati.get("types"))
		self.evolves_from = dati.get("evolvesFrom", None) 
		self.evolves_to = dati.get("evolvesTo", []) 
		return super().estrai(dati)




class Trainer(Carta):
	supertype = "Trainer"
	pass




class Energy(Carta):
	supertype = "Energy"
	pass