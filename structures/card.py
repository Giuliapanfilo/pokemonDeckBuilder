
from structures.energy import Energy as EnergyTypes
from structures.expansion import Expansion
import re
import json
from settings import *
from typing import Optional
from pathlib import Path


# Enciclopedia in memoria: { "swsh8-254": { ... }, ... }
_CARD_ENCYCLOPEDIA: Optional[dict[str, dict]] = None

def configure_card_cache(source: dict[str, dict] | str | Path):
	"""
	Inietta/Carica una cache locale delle carte.
	- Se passi un dict, lo usa direttamente.
	- Se passi un path (str/Path), carica il JSON da lì.
	"""
	global _CARD_ENCYCLOPEDIA
	if isinstance(source, (str, Path)):
		p = Path(source)
		with p.open(encoding="utf-8") as f:
			_CARD_ENCYCLOPEDIA = json.load(f)
	else:
		_CARD_ENCYCLOPEDIA = source

def _get_cached_card_dict(card_id: str) -> Optional[dict]:
	"""
	Ritorna il dict della carta se presente in _CARD_ENCYCLOPEDIA.
	Se la cache è None, prova a caricare 'cache/cards.json' una volta.
	"""
	global _CARD_ENCYCLOPEDIA
	if _CARD_ENCYCLOPEDIA is None:
		p = Path("cache/cards.json")
		if p.exists():
			with p.open(encoding="utf-8") as f:
				_CARD_ENCYCLOPEDIA = json.load(f)
		else:
			return None
	return _CARD_ENCYCLOPEDIA.get(card_id)


def parse_code(code_string: str) -> tuple[str, str, str]:
    """
    Estrapola l'espansione e il numero di una carta dai formati:

    A) "{idSet}-[decoratore]{numeroCarta}"
        - "base1-023" → prefix="base1", number="023"
        - "SV1-TG02"  → prefix="SV1",   number="02", decorator="TG"

    B) "{ptcgoCode}{numeroCarta}"
        - "SVI178"    → prefix="SVI",   number="178"
    """
    # Caso A: prefix - (decorator letters) number
    m = re.match(r"^([^-]+)-([A-Za-z]*)(\d+)$", code_string)
    if m:
        prefix, decorator, number = m.groups()
        # se hai un decorator tipo "TG", puoi decidere se includerlo o no
        # es: "SV1-TG02" → decorator="TG", number="02"
        return Expansion(prefix), decorator, number

    # Caso B: letters + number senza dash
    m = re.match(r"^([A-Za-z]+)(\d+)$", code_string)
    if m:
        ptcgo_code, number = m.groups()
        return Expansion(ptcgo_code), None, number

    raise ValueError(f"Codice carta non valido: {code_string}")


def smart_card_lookup(card_id: str) -> dict:
    """
    Cerca una carta usando strategie multiple:
    1. Lookup diretto nell'enciclopedia
    2. Parse e lookup con/senza decoratore
    3. Tentativi con zero-padding diversi
    
    Args:
        card_id (str): ID della carta (es. "SV1-TG02", "base1-4")
        
    Returns:
        dict: Dati della carta trovata
        
    Raises:
        KeyError: Se la carta non viene trovata con nessuna strategia
    """
    # 1. Prova lookup diretto
    card_data = _get_cached_card_dict(card_id)
    if card_data:
        return card_data
    
    # 2. Parse e lookup con strategie multiple
    try:
        expansion, decorator, number = parse_code(card_id)
        
        # 2.1 Prova con il numero originale
        alt_id = f"{expansion.code}-{number}"
        card_data = _get_cached_card_dict(alt_id)
        if card_data:
            return card_data
        
        # 2.2 Se c'è un decoratore, prova senza
        if decorator:
            alt_id = f"{expansion.code}-{number}"
            card_data = _get_cached_card_dict(alt_id)
            if card_data:
                return card_data
        
        # 2.3 Prova con diversi zero-padding
        for i in range(3):
            padded_number = f"{'0'*i}{number}"
            alt_id = f"{expansion.code}-{padded_number}"
            card_data = _get_cached_card_dict(alt_id)
            if card_data:
                return card_data
        
        # 3. Ultimo tentativo: fetch diretto dal file JSON
        return _fetch_data(expansion.code, number)
        
    except Exception as e:
        raise KeyError(f"Carta {card_id} non trovata: {str(e)}")



# Set-level cache: { "set_code": { "data": [...], "index": {"001": card_data, ...} } }
_SET_CACHE = {}

def _fetch_data(set_code: str, number: str) -> dict:
	"""Cerca i dati di una carta in base al suo set e numero, usando una cache in memoria"""
	global _SET_CACHE
	
	# Check if set is already in cache
	if set_code not in _SET_CACHE:
		file_path = PROJECT_ROOT / "data" / "cards_by_set" / f"{set_code}.json"
		if not file_path.exists():
			raise FileNotFoundError(f"File set non trovato: {file_path}")
		
		# Load set data
		with open(file_path) as f:
			set_data = json.load(f)
		
		# Create index for faster lookups
		index = {c["id"].split("-")[-1]: c for c in set_data}
		
		# Store in cache
		_SET_CACHE[set_code] = {
			"data": set_data,
			"index": index
		}
	
	# Try to find card with different zero-padding options
	candidates = [f'{'0'*i}{number}' for i in range(3)]
	for c in candidates:
		if c in _SET_CACHE[set_code]["index"]:
			return _SET_CACHE[set_code]["index"][c]
	
	# Fallback: cerca la prima carta con quel nome nel set
	try:
		# Prova a cercare la carta nel cache globale per ottenere il nome
		global_id = f"{set_code}-{number}"
		card_data = _get_cached_card_dict(global_id)
		if card_data and "name" in card_data:
			card_name = card_data["name"]
			
			# Cerca la prima carta con lo stesso nome nel set
			for card in _SET_CACHE[set_code]["data"]:
				if card.get("name") == card_name:
					return card
	except Exception:
		pass  # Se fallisce, continua con l'errore originale
	
	# Se non troviamo nessuna carta con quel nome, restituisci la prima carta del set
	if _SET_CACHE[set_code]["data"]:
		return _SET_CACHE[set_code]["data"][0]
	
	raise KeyError(f"Carta {set_code}-{number} non trovata nel set {set_code}")





class Carta:
	expansion: Expansion
	number: str
	name: str
	supertype : str
	subtypes : list[str]
	# rarità: str

	def __new__(cls, code_string: str|None = None, *args, **kwargs):
		# Se è unpickling, chiama senza argomenti
		if code_string is None:
			return super().__new__(cls)

		# Se stiamo già costruendo una sottoclasse, non ridispatchare
		if cls is not Carta:
			return super().__new__(cls)

		# Usa smart_card_lookup per trovare i dati della carta
		try:
			dati = smart_card_lookup(code_string)
		except KeyError as e:
			# Se non troviamo la carta, solleva un'eccezione informativa
			raise KeyError(f"Carta {code_string} non trovata: {str(e)}")

		# Estrai expansion/number per consistenza
		expansion, decorator, number = parse_code(code_string)

		# Scegli la classe in base al supertype
		st = dati["supertype"].lower()
		if st == "pokémon":
			target_cls = Pokémon
		elif st == "trainer":
			target_cls = Trainer
		else:
			target_cls = Energy

		self = super().__new__(target_cls)

		# metti in cache i valori già calcolati
		self._cached_code      = code_string
		self._cached_expansion = expansion
		self._cached_number    = number
		self._cached_data      = dati

		return self


	def __init__(self, *args, **kwargs):
		self.expansion, self.number = self._cached_expansion, self._cached_number
		self.estrai(self._cached_data)
		del self._cached_data

	# Necessario per unpickling
	def __setstate__(self, state):
		self.__dict__.update(state)


	def __str__(self) -> str:
		return f"({self.get_id()})\t{self.name}"

	def __repr__(self) -> str:
		return self.__str__()

	def _read_encyclopedia(code:str):
		from pathlib import Path
		with Path("cache/cards.json").open(encoding="utf-8") as f:
			_ENCYCLOPEDIA = json.load(f)
		return ENCYCLOPEDIA[code]


	@classmethod
	def from_dict(cls, data: dict) -> "Carta":
		"""
		Crea una carta a partire da un dizionario prodotto da to_dict().
		"""
		# st = data.get("supertype", "").lower()
		target_classes = {
			"pokémon": Pokémon,
			"trainer": Trainer,
			"energy": Energy
		}
		target_class = target_classes[data.get("supertype", "").lower()]
		# if st == "pokémon":
		# 	target_cls = Pokémon
		# elif st == "trainer":
		# 	target_cls = Trainer
		# else:
		# 	target_cls = Energy

		# istanza vuota della sottoclasse
		self = target_class.__new__(target_class)
		# inizializza i campi base

		# self.expansion = Expansion.from_dict(data["expansion"])
		self.expansion = Expansion(data["expansion"])
		self.number = data["number"]
		self.name = data.get("name")
		self.supertype = data.get("supertype")
		self.subtypes = data.get("subtypes", [])

		# estrai dati specifici se servono
		self.estrai(data)
		return self


	
	@classmethod
	def from_info_dict(cls, info: dict, use_ptcgo:bool=False) -> "Carta":
		"""
		Crea una Carta a partire da un dict:
			{
				"quantità": "...",
				"nome": "...",
				"setesteso": "<nome esteso del set>",
				"setnumero": "<number>"
			}
		"""
		number = info["setnumero"]
		expansion = Expansion(info["setesteso"], use_ptcgo, number=number)
		code_string = f"{expansion.code}-{number}"
		carta =  cls(code_string)
		return carta


	def estrai(self, dati):
		self.name = dati.get("name")
		self.supertype = dati.get("supertype")
		self.subtypes = dati.get("subtypes", [])
		# self.rarità = dati.get("rarity")


	def get_id(self):
		return f"{self.expansion.code}-{self.number}"
	

	def to_facts(self) -> list[str]:
		"""Trasforma una carta in fatti OWL con sintassi Turtle

			Example Output:
				:base1-4 rdf:type :Pokémon .
				:base1-4 :hasName "Charizard" .
				:base1-4 :hasExpansion "base1" .
				:base1-4 :hasNumber "4" .
				:base1-4 :hasType "Fire" .
				:base1-4 :evolvesFrom "Charmeleon" .
		
		"""
		from enum import Enum
		iri = f":{self.get_id().replace('-', '_')}"
		facts = []

		# Aggiungi il tipo OWL
		facts.append(f"{iri} rdf:type :{self.supertype} .")

		for attr, value in vars(self).items():
			if attr.startswith("_") or value is None:
				continue

			# Normalizza nome proprietà
			attr = f"has{attr.capitalize()}" if "evolves" not in attr else attr

			match value:
				case list():
					for item in value:
						if item is None: continue
						val = item.value if isinstance(item, Enum) else item
						facts.append(f'{iri} :{attr} "{val}" .')
				case Enum():
					facts.append(f'{iri} :{attr} "{value.value}" .')
				case Expansion():
					facts.append(f'{iri} :{attr} "{value.code}" .')
				case _:
					facts.append(f'{iri} :{attr} "{value}" .')

		return facts


### serializzazione
	def _chiave(self):
		return (self.expansion.code, self.number)

	def __hash__(self):
		return hash(self._chiave())

	def __eq__(self, other):
		return isinstance(other, Carta) and self._chiave() == other._chiave()

	def to_dict(self) -> dict:
		return	{
            "id": self.get_id(),               # es: "SV1-178" o "base1-4"
            "name": getattr(self, "name", None),
            "supertype": getattr(self, "supertype", None),
            "subtypes": getattr(self, "subtypes", []),
            "expansion": self.expansion.code, #self.expansion.to_dict(),
            "number": self.number,
        }
	

### Metodi di Classe
	@classmethod
	def build_all_cards(cls) -> list["Carta"]:
		from utils import load_or_build_cache
		ids = load_or_build_cache("all_ids", Expansion.generate_all_ids)
		builder = lambda: [cls(code) for code in ids]
		return load_or_build_cache("all_cards", builder, binary=True)


	@classmethod
	def build_all_subtypes(cls) -> list[str]:
		from utils import load_or_build_cache
		def builder():
			cards = cls.build_all_cards()
			return list({st for c in cards for st in getattr(c, "subtypes", [])})
		return load_or_build_cache("subtypes", builder)


	@classmethod
	def build_all_supertypes(cls) -> list[str]:
		from utils import load_or_build_cache
		def builder():
			cards = cls.build_all_cards()
			return list({c.supertype for c in cards})
		return load_or_build_cache("supertypes", builder)


	@classmethod
	def build_all_keywords(cls, top_k: int = 200) -> list[str]:
		from utils import load_or_build_cache
		def builder():
			from sklearn.feature_extraction.text import TfidfVectorizer
			cards = cls.build_all_cards()
			corpus = []
			for c in cards:
				if isinstance(c, Pokémon):
					parts = c.attacks + c.abilities
				elif isinstance(c, Trainer):
					parts = c.rules
				else:
					parts = []
				corpus.append(" ".join(str(a) for a in parts).lower())
			vec = TfidfVectorizer(stop_words="english", max_features=top_k)
			vec.fit(corpus)
			return vec.get_feature_names_out().tolist()
		return load_or_build_cache("keywords", builder)




class Trainer(Carta):
	supertype = "Trainer"
	rules : list[str]

	def estrai(self, dati):
		self.rules = dati.get("rules", [])
		return super().estrai(dati)
	
	def to_dict(self) -> dict:
		d = super().to_dict()
		d.update({
			"rules": self.rules,
		})
		return d




class Energy(Carta):
	supertype = "Energy"
	
	# def estrai(self, dati):
	# 	return super().estrai(dati)

    # def to_dict(self) -> dict:
    #     return super().to_dict()




class Attack:
	name : str
	text : str
	damage : int
	cost_converted : int
	# cost : list[str]

	def to_dict(self) -> dict:
		return {
			"name": self.name,
			"text": self.text,
			"damage": self.damage,
			"convertedEnergyCost": self.cost_converted,
			# "cost" : self.cost
			}

	def __init__(self, data: dict):
		self.name = data.get("name", "")
		self.text = data.get("text", "")
		self.damage = _parse_int(data.get("damage"))
		self.cost_converted = data.get("convertedEnergyCost", 0)
		# self.cost_energy = [Energy(c) for c in data.get("cost", [])]



	def __str__(self) -> str:
		return self.text


	def __repr__(self) -> str:
		return f"<Attack name={self.name!r} text={self.text!r}>"




class Ability:
	name: str
	text: str

	def __init__(self, data: dict):
		self.name = data.get("name", "")
		self.text = data.get("text", "")


	def __str__(self) -> str:
		return self.text
	

	def __repr__(self) -> str:
		"""utile in console/debug."""
		return f"<Attack name={self.name!r} text={self.text!r}>"

	def to_dict(self) -> dict:
		return {
			"name": self.name,
			"text": self.text,
		}




class Pokémon(Carta):
	supertype = "Pokémon"
	type: Energy
	evolves_from: str 
	evolves_to: list[str]
	weaknesses: list[Energy]
	resistances: list[Energy]
	hp: int 
	attacks: list[Attack]
	abilities: list[Ability]
	retreat_cost: int

	
	def estrai(self, dati):
		try:
			self.type = EnergyTypes.from_str(dati['type'])
		except:
			self.type = EnergyTypes.from_str(dati['types'][0])
		# print(self.type)
		self.evolves_from = dati.get("evolvesFrom", None) 
		self.evolves_to = dati.get("evolvesTo", []) 
		self.hp = _parse_int(dati.get("hp",0))
		self.attacks = [Attack(a) for a in dati.get("attacks", [])]
		self.abilities = [Ability(a) for a in dati.get("abilities", [])]
		self.retreat_cost = dati.get("retreat_cost",0)
		try:
			self.weaknesses = [EnergyTypes.from_str(w['type']) for w in dati.get("weaknesses", [])]
			self.resistances = [EnergyTypes.from_str(w['type']) for w in dati.get("resistances", [])]
		except Exception as e:
			self.weaknesses = [EnergyTypes.from_str(w) for w in dati.get("weaknesses", [])]
			self.resistances = [EnergyTypes.from_str(w) for w in dati.get("resistances", [])]
		return super().estrai(dati)
	
	def to_dict(self) -> dict:
		d = super().to_dict()
		d.update({
			"type": self.type.value,
			"evolves_from": self.evolves_from,
			"evolves_to": list(self.evolves_to or []),
			"weaknesses": [w.value for w in self.weaknesses],
			"resistances": [r.value for r in self.resistances],
			"hp": self.hp,
			"attacks": [a.to_dict() for a in self.attacks],
			"abilities": [a.to_dict() for a in self.abilities],
			"retreat_cost": self.retreat_cost,
		})
		return d




def _parse_int(string: str) -> int:
	try:
		return int(string)
	except (ValueError, TypeError):
		return 0
	

