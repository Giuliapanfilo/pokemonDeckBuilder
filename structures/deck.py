from structures.card import Carta, Pokémon, Trainer
from enum import Enum
from structures.energy import Energy
from structures.expansion import Expansion
from pathlib import Path
import re
from settings import *
from typing import Callable, Dict, List, Any, Optional, Tuple
from structures.similarity import Similarity
import hashlib

# Per quanto mi piacerebbe mettere questa funzione in embedding, le lambda non permettono un caricamento lineare
# quindi o la metto fuori oppure creo una classe apposita
def _stat_embedding(m: "Deck", extractor: Callable[[Pokémon], list[int]]) -> list[float]:
	"""
	Calcola media, min, max e deviazione standard di un valore numerico estratto dai Pokémon del mazzo.

	Args:
		m (Deck): Il mazzo da analizzare.
		extractor (Callable): Funzione che prende una carta Pokémon e restituisce una lista di valori numerici.

	Returns:
		list[float]: [media, minimo, massimo, deviazione standard]
	"""
	import statistics
	valori = []
	for carta, qty in m.carte.items():
		if not hasattr(carta, "hp"):
			continue
		# if not isinstance(carta, Pokémon):
		# 	continue
		valori.extend(extractor(carta) * qty)

	if not valori:
		return [0.0, 0.0, 0.0, 0.0]

	return [
		statistics.mean(valori),
		min(valori),
		max(valori),
		statistics.pstdev(valori)
	]


class Deck:
	archetipo: str
	carte : dict[Carta, int] # carta:quantità
	name : str
	# format : str

	def __init__(self, name: str, items: list[tuple[str, int]], archetipo: str = ""):
		"""
		Costruisce un Deck dato:
			- name: il nome del mazzo
			- items: lista di (code_string, quantità)
			- archetipo: opzionale
		"""
		self.name = name
		self.archetipo = archetipo
		self.carte = {}
		for code, qty in items:
			if qty > 0:
				self.add(Carta(code), qty)


	@classmethod
	def from_map(cls, 
			deck_data: dict[str, dict[str, str]], 
			archetipo: str = ""
		) -> "Deck":
		"""
		Formato 1:
			{ deck_name: { code_string: qty_str, … } }
		"""
		if len(deck_data) != 1:
			raise ValueError("deck_data deve contenere un solo mazzo")
		name, cards_map = next(iter(deck_data.items()))
		items = []
		for code_str, qty_str in cards_map.items():
			try:
				qty = int(qty_str)
			except (ValueError, TypeError):
				qty = 0
			items.append((code_str, qty))
		return cls(name, items, archetipo)
	



	@classmethod
	def from_archetype_data(
		cls,
		data: dict[str, list[list[dict[str, str]]]]
	) -> list["Deck"]:
		"""
		Formato 3:
			{ archetipo: [ [ {quantità, setesteso, setnumero}, … ], … ], … }
		"""
		result: list[Deck] = []
		for arch, decks in data.items():
			for idx, deck_list in enumerate(decks, start=1):
				m = cls.__new__(cls)
				m.name = f"{arch} #{idx}"
				m.archetipo = arch
				m.carte = {}

				for card_info in deck_list:
					qty = int(card_info.get("quantità", 0))
					if qty <= 0:
						continue
					# qui usi la factory che prende il dict e restituisce la Carta
					carta = Carta.from_info_dict(card_info)
					m.add(carta, qty)

				result.append(m)
		return result
	
	@classmethod
	def from_tournament_data(
		cls,
		data: list[dict]
	) -> list["Deck"]:
		"""
		Formato file:
			[
			{
				'name': str,
				'category': str,
				'decklist': {
					'pokemon': [
						{ 'count': str|int, 'name': str, 'number': str, 'set': str }, …
					],
					'trainer': [ … ],
					'energy':  [ … ]
				},
				… altri campi ignorati …
			},
			…
			]
		"""
		result: list[Deck] = []
		for entry in data:
			m = cls.__new__(cls)
			m.name = entry.get("name", "")
			# m.category = entry.get("category", "")
			m.carte = {}

			decklist = entry.get("decklist", {})
			if decklist in ['', {}] : continue
			do_append = True
			# Per ogni sezione del mazzo (pokemon, trainer, energy)
			for section in ("pokemon", "trainer", "energy"):
				for card_info in decklist.get(section, []):
					# se non ci sono segnate zero presenze di una carta, skippa
					qty = int(card_info.get("count", 0))
					if qty <= 0:
						continue

					# Creiamo la carta e la aggiungiamo al mazzo
					try:
						carta = Carta.from_info_dict({
							"setesteso": card_info.get("set", ""),
							"setnumero": card_info.get("number", "")
						}, use_ptcgo=True)
						m.add(carta, qty)
					except Exception as e:
						print(e)
						print(f'{card_info.get("name", "")} non trovato in {card_info.get("set", "")}, scarto il mazzo')
						do_append = False
						break  # esci dal ciclo interno
				if not do_append:
					break  # esci anche dalla sezione se già fallito

			result.append(m)
		return result


	@classmethod
	def from_sparse_row( cls,
			row,                         # csr_matrix (1 × n_cards) o 'csr' row
			card_ids: "np.ndarray[str]", # colonne della matrice (ordine coerente!)
			cards_encyclopedia: dict[str, dict],
			name: str = "Deck ricostruito",
			archetipo: str = ""
		) -> "Deck":
		"""
			Ricrea un Deck a partire da:
			- una riga CSR 
			- l'array card_ids
			- l'enciclopedia carte (id -> dict) per rigenerare Carta
		"""
		# normalizzo row ad una riga CSR (se qualcuno passasse l'intera X o vecchi wrapper)
		# try:
		# 	r = row if row.shape[0] == 1 else row.getrow(0)
		# except Exception:
		# 	r = row
		r = row

		deck = Deck.__new__(Deck)   # costruzione "manuale" senza __init__ se serve
		deck.name = name
		deck.archetipo = archetipo
		deck.carte = {}

		for j, qty in zip(r.indices, r.data):
			if qty <= 0:
				continue
			cid = card_ids[j]
			card_dict = cards_encyclopedia[cid]
			carta = Carta.from_dict(card_dict)  
			deck.add(carta, int(qty))           

		return deck


	@classmethod
	def from_csv(
		cls,
		csv_path: str | Path,
		deck_name: str | None = None,
		archetipo: str = ""
	) -> "Deck":
		"""
		Crea un Deck leggendo un CSV con colonne:
		id_card,name_card,amount_card,...

		Args:
			csv_path: percorso al file CSV
			deck_name: nome da dare al mazzo (se None, usa il primo
					valore di combo_type_name nel CSV)
			archetipo: archetipo facoltativo

		Returns:
			Deck: popolato con le quantità lette da 'amount_card'
		"""
		import csv
		items: dict[str,int] = {}
		inferred_name = None

		with Path(csv_path).open(newline="", encoding="utf-8") as f:
			reader = csv.DictReader(f)
			for row in reader:
				code = row["id_card"]
				qty = int(row.get("amount_card", 0) or 0)
				if qty > 0:
					items[code] = items.get(code, 0) + qty
				if inferred_name is None and deck_name is None:
					inferred_name = row.get("combo_type_name")

		name = deck_name or inferred_name or "Deck"
		return cls(name, items.items(), archetipo)

	@classmethod
	def from_deck_dict(cls, 
			deck_dict: dict, 
			archetipo: str = ""
		) -> "Deck":
		"""
		Formato 2:
			{
				"id": ..., "name": ...,
				"cards": [ { "id":..., "count":... }, … ]
			}
		"""
		name = deck_dict["name"]
		items = [
			(c["id"], int(c.get("count", 0)))
			for c in deck_dict.get("cards", [])
		]
		return cls(name, items, archetipo)


	@classmethod
	def from_dict(cls, d: dict) -> "Deck":
		deck = Deck(d['name'], [])
		for card_info in d['cards']:
			deck.add(
				Carta.from_dict(card_info['card']), 
				card_info['count'])
		return deck

	def to_dict(self) -> dict:
		return {
		"name": self.name,
		"cards": [
			{"card": card.to_dict(), "count": qty}
			for card, qty in self.carte.items()
		],
	}

	def mask(self, n_masks:int = 5) -> Tuple["Deck", List[Tuple[Carta, int]]]:
		"""
		Crea una copia del mazzo con alcune carte mascherate (rimosse).

		Args:
			deck: Mazzo originale
			n_masks: Numero di carte da mascherare
			
		Returns:
			Tuple contenente:
			- Mazzo con carte mascherate
			- Lista di tuple (carta, quantità) mascherate
		"""
		import random
		masked_deck = Deck(self.name, [])
		cards = list(self.carte.items())
		
		# Assicurati di non mascherare più carte di quelle disponibili
		# n_masks = min(n_masks, len(cards))
		
		# Seleziona carte da mascherare
		mask_indices = random.sample(range(len(cards)), n_masks)
		masked_cards = [cards[i] for i in mask_indices]
		
		# Crea il mazzo mascherato
		for i, (card, qty) in enumerate(cards):
			if i not in mask_indices:
				masked_deck.add(card, qty)
		
		return masked_deck, masked_cards


	def add(self, carta:Carta, quantità:int=1):
		"""aggiunge quantità di carta al mazzo"""
		if quantità == 0:
			return
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

	def uid(self) -> str:
		"""
		Restituisce un identificativo deterministico e stabile del mazzo, basato sul contenuto.
		"""
		items = [(carta.get_id(), int(qty)) for carta, qty in self.carte.items()]
		items.sort()
		payload = ";".join(f"{cid}:{qty}" for cid, qty in items).encode("utf-8")
		h = hashlib.blake2b(payload, digest_size=16).hexdigest()
		return h


	def __repr__(self) -> str:
		"""
		Rappresentazione concisa di un Deck.
		Mostra nome, archetipo (se presente), numero di carte,
		e le prime 5 carte con quantità.
		"""
		text = f"<Deck {self.name!r}"
		text += f"{self.archetipo}" if self.archetipo != '' else ""
		preview = ", ".join(
			f"{carta.get_id()}×{qty}"
			for i, (carta, qty) in enumerate(self.carte.items())
			if i < 5
		)
		return text + f', {self.len()} carte [{preview} ", ..." ]'




	class Embedding(Enum): 
		"""La rappresentazione del mazzo, i commenti sono direttamente sotto all'elenco"""

		QUANTITY     = "QUANTITY"
		"""Vettore con il numero di copie per ciascuna carta, in ordine fisso. (vettore giganorme)"""
		# QUANTITY_FROM_CSR = "QUANTITY_FROM_CSR"
		# """Vettore con il numero di copie per ciascuna carta, in ordine fisso basato su card_ids.npy. Dimensioni fisse."""
		KEYWORDS     = "KEYWORDS"
		"""Frequenza di parole chiave specifiche (es. paralizza, pesca, scarta) nei testi delle carte Pokémon."""
		SUPERTYPES   = "SUPERTYPES"
		"""Distribuzione dei supertipi delle carte nel mazzo: Pokémon, Trainer, Energy."""
		SUBTYPES     = "SUBTYPES"
		"""Distribuzione dei sottotipi tra le carte nel mazzo (es. EX, V, Radiant, Supporter, Tool, ecc.)."""
		PKMN_TYPES   = "PKMN_TYPES"
		"""Percentuale dei Pokémon del mazzo per tipo di energia (Fire, Water, Psychic, ecc.)."""
		EVO_STATS    = "EVO_STATS"
		"""Percentuale di Pokémon con pre-evoluzione, evoluzione o nessuna delle due nel mazzo."""
		WEAKNESS     = "WEAKNESS"
		"""Percentuale di Pokémon nel mazzo deboli a ciascun tipo di energia."""
		RESISTANCE   = "RESISTANCE"
		"""Percentuale di Pokémon nel mazzo resistenti a ciascun tipo di energia."""
		HP           = "HP"
		"""Statistiche sugli HP dei Pokémon nel mazzo: media, minimo, massimo, deviazione standard."""
		ATTACKS_DMG  = "ATTACKS_DMG"
		"""statistiche sui danni degli attacchi: media, minimo, massimo, deviazione standard."""
		ATTACKS_COSTS= "ATTACKS_COSTS"
		"""statistiche dei costi degli attacchi: media, minimo, massimo, deviazione standard."""

		def _func(self):
			E = self.__class__  # <- alias per Deck.Embedding
			return {
				E.QUANTITY:          E._quantity,
				# E.QUANTITY_FROM_CSR: E._quantity_from_csr,
				E.KEYWORDS:          E._keywords,
				E.SUPERTYPES:        E._supertipi,
				E.SUBTYPES:          E._sottotipi,
				E.PKMN_TYPES:        E._energie,
				E.EVO_STATS:         E._evoluzione_stats,
				E.WEAKNESS:          E._debolezze,
				E.RESISTANCE:        E._resistenze,
				E.HP:             (lambda m: _stat_embedding(m, lambda c: [getattr(c, "hp", 0) or 0])),
				E.ATTACKS_DMG:    (lambda m: _stat_embedding(
									m, lambda p: [a.damage for a in getattr(p, "attacks", []) if isinstance(a.damage, (int, float))]
								)),
				E.ATTACKS_COSTS:  (lambda m: _stat_embedding(
									m, lambda p: [getattr(a, "cost_converted", 0) for a in getattr(p, "attacks", [])] or [0]
								)),
			}[self]

		def __call__(self, mazzo: "Deck") -> list[float]:
			return self._func()(mazzo)
		

		# def _quantità(m:"Deck") -> list[int]:
		# 	v = {k: 0 for k in Expansion.generate_all_ids()}
		# 	for carta, count in m.carte.items():
		# 		v[carta.get_id()] = count
		# 	return list(v.values())


		def _sottotipi(m:"Deck") -> list[int]:
			# Hardcoded common subtypes instead of using build_all_subtypes
			common_subtypes = ["Basic", "Stage 1", "Stage 2", "EX", "V", "VMAX", "VSTAR",
							  "GX", "Item", "Supporter", "Stadium", "Tool", "Special"]
			v = {sb: 0 for sb in common_subtypes}

			for carta, qty in m.carte.items():
				if not hasattr(carta, "subtypes"):
					continue

				for sottotipo in carta.subtypes:
					if sottotipo in v:
						v[sottotipo] += qty

			return list(v.values())


		def _supertipi(m: "Deck") -> list[int]:
			# Hardcoded supertypes instead of using build_all_supertypes
			supertypes = ["Pokémon", "Trainer", "Energy"]
			v = {st: 0 for st in supertypes}

			for carta, qty in m.carte.items():
				if hasattr(carta, "supertype") and carta.supertype in v:
					v[carta.supertype] += qty

			return list(v.values())


		def _keywords(m:"Deck") -> list[int]:
			# Hardcoded common keywords instead of using build_all_keywords
			common_keywords = ["draw", "search", "discard", "damage", "heal", "switch",
							  "energy", "attach", "evolve", "shuffle", "retreat", "bench",
							  "attack", "ability", "stadium", "tool", "supporter", "item"]
			v = {kw: 0 for kw in common_keywords}
			
			for carta, qty in m.carte.items():
				testo = ""
				if hasattr(carta, "attacks"): 
				# if isinstance(carta, Pokémon) and hasattr(carta, "attacks") and hasattr(carta, "abilities"):
					attacks_text = [str(a) for a in carta.attacks if hasattr(a, "text")]
					abilities_text = [str(a) for a in carta.abilities if hasattr(a, "text")]
					testo += " ".join(attacks_text + abilities_text).lower()
				if hasattr(carta, "rules"):
					testo += " ".join(str(r) for r in carta.rules).lower()

				# tokenizziamo in parole
				for token in re.findall(r"\b\w+\b", testo):
					if token in v:
						v[token] += qty

			return list(v.values())


		def _energie(m: "Deck") -> list[float]:
			v = {e: 0 for e in Energy}
			tot = 0

			for carta, qty in m.carte.items():
				# if not isinstance(carta, Pokémon):
				# 	continue
				
				# Ensure the type is valid
				if hasattr(carta, 'type') and carta.type in v:
					v[carta.type] += qty
					tot += qty

			# Add a small constant to ensure variance
			result = []
			for e in Energy:
				# If no Pokémon, use a small random value to ensure variance
				if tot == 0:
					result.append(0.01 * (1 + (hash(str(e)) % 10) / 100))
				else:
					# Add a tiny amount of noise to ensure variance
					result.append((v[e] / tot) + 0.0001 * (hash(str(e)) % 10))
			
			return result


		def _evoluzione_stats(m: "Deck") -> list[float]:
			pokemons = {carta:qty for carta, qty in m.carte.items() if isinstance(carta, Pokémon)}
			pre = post = base = tot_pokemon = 0

			for carta, qty in pokemons.items():
				# Safely check attributes
				has_evolves_from = hasattr(carta, 'evolves_from') 
				has_evolves_to = hasattr(carta, 'evolves_to')
				
				if has_evolves_from:
					pre += qty
				else:
					base += qty
				if has_evolves_to:
					post += qty
				tot_pokemon += qty

			# Add small random values to ensure variance
			if tot_pokemon == 0:
				return [0.01, 0.02, 0.03]  # Small different values for variance
			
			# Add tiny noise to ensure variance
			return [
				(pre / tot_pokemon) + 0.0001,
				(post / tot_pokemon) + 0.0002,
				(base / tot_pokemon) + 0.0003
			]


		def _debolezze(m:"Deck") -> list[float]:
			v = {e: 0 for e in Energy}
			tot = 0
			for carta, qty in m.carte.items():
				if not isinstance(carta, Pokémon):
					continue
				tot += qty
				
				# Safely access weaknesses
				if hasattr(carta, 'weaknesses'):
					for wk in carta.weaknesses:
						if wk in v:  # Ensure the weakness is a valid Energy type
							v[wk] += qty
			
			# Add small random values to ensure variance
			result = []
			for i, e in enumerate(Energy):
				if tot == 0:
					# Small different values for variance when no Pokémon
					result.append(0.01 * (1 + i * 0.1))
				else:
					# Add tiny noise to ensure variance
					result.append((v[e] / tot) + 0.0001 * (i + 1))
			
			return result


		def _resistenze(m: "Deck") -> list[float]:
			v = {e: 0 for e in Energy}
			tot = 0
			for carta, qty in m.carte.items():
				if not isinstance(carta, Pokémon):
					continue
				tot += qty
				
				# Safely access resistances
				if hasattr(carta, 'resistances'):
					for wk in carta.resistances:
						if wk in v:  # Ensure the resistance is a valid Energy type
							v[wk] += qty
			
			# Add small random values to ensure variance
			result = []
			for i, e in enumerate(Energy):
				if tot == 0:
					# Small different values for variance when no Pokémon
					result.append(0.01 * (1 + i * 0.1))
				else:
					# Add tiny noise to ensure variance
					result.append((v[e] / tot) + 0.0001 * (i + 1))
			
			return result


		def _quantity(m: "Deck") -> list[int]:
			"""
			Crea un vettore di quantità basato sull'ordine fisso di card_ids.npy.
			Garantisce dimensioni fisse e ordine coerente tra tutti i mazzi.
			
			Args:
				m (Deck): Il mazzo da analizzare
				
			Returns:
				list[int]: Vettore di quantità con dimensioni fisse
			"""
			# Carica card_ids se non è già in memoria
			if not hasattr(Deck.Embedding, "_card_ids_cache"):
				try:
					# Carica card_ids.npy
					from scipy.sparse import load_npz
					import numpy as np
					
					# Carica la matrice CSR e card_ids
					z = np.load("cache/decks_csr.npz", allow_pickle=True)
					Deck.Embedding._card_ids_cache = z["card_ids"]
				except Exception as e:
					print(f"Errore nel caricamento di card_ids: {e}")
					# Fallback: usa generate_all_ids
					Deck.Embedding._card_ids_cache = np.array(Expansion.generate_all_ids())
			
			# Crea un dizionario con indice per ogni card_id
			if not hasattr(Deck.Embedding, "_card_ids_index"):
				Deck.Embedding._card_ids_index = {
					card_id: idx for idx, card_id in enumerate(Deck.Embedding._card_ids_cache)
				}
			
			# Inizializza vettore di zeri con dimensione fissa
			v = [0] * len(Deck.Embedding._card_ids_cache)
			
			# Popola il vettore con le quantità del mazzo
			for carta, qty in m.carte.items():
				card_id = carta.get_id()
				if card_id in Deck.Embedding._card_ids_index:
					idx = Deck.Embedding._card_ids_index[card_id]
					v[idx] = qty
			
			return v






	def similarity(
			self, 
			other:"Deck", 
			metrica: Similarity = Similarity.COSENO, 
			embedding: Embedding | list[Embedding] = Embedding.QUANTITY
		) -> float:
		"""
			Questa funzione applica uno o più embedding ai due mazzi forniti e calcola la similarità
			tra i vettori risultanti usando la metrica specificata. Se viene passato un solo embedding,
			verrà usato direttamente. Se viene fornita una lista di embedding, i vettori generati verranno
			concatenati in ordine per produrre un vettore unico per ciascun mazzo.

			Args:
				mazzo2 (Deck): Il secondo mazzo da confrontare.
				metrica (Similarity, optional): La funzione/metrica da usare per il confronto.
					Di default viene usata la similarità coseno.
				embedding (Embedding or list[Embedding], optional): Uno o più metodi di embedding
					da applicare ai mazzi. Ogni embedding produce un vettore che verrà usato
					per il confronto. Se una lista, i vettori verranno concatenati.

			Returns:
				float: Un valore numerico che rappresenta la similarità tra i due mazzi.
					Il valore dipende dalla metrica scelta (es. 1.0 per identici nel caso
					di similarità coseno).

			Raises:
				ValueError: Se `embedding` non è né un `Embedding` né una lista di `Embedding`.

			Example:
				>>> m1.similarity(m2, embedding=[Embedding.QUANTITÀ, Embedding.SOTTOTIPI])
				0.847
		"""
		return Deck.similarity(self, other, metrica, embedding)


	@staticmethod
	def similarity(
			mazzo1:"Deck", 
			mazzo2:"Deck", 
			metrica:Similarity = Similarity.COSENO, 
			embedding:Embedding | list[Embedding] = Embedding.QUANTITY
		) -> float:
		"""
				Questa funzione applica uno o più embedding ai due mazzi forniti e calcola la similarità
				tra i vettori risultanti usando la metrica specificata. Se viene passato un solo embedding,
				verrà usato direttamente. Se viene fornita una lista di embedding, i vettori generati verranno
				concatenati in ordine per produrre un vettore unico per ciascun mazzo.

				Args:
					mazzo1 (Deck): Il primo mazzo da confrontare.
					mazzo2 (Deck): Il secondo mazzo da confrontare.
					metrica (Similarity, optional): La funzione/metrica da usare per il confronto.
						Di default viene usata la similarità coseno.
					embedding (Embedding or list[Embedding], optional): Uno o più metodi di embedding
						da applicare ai mazzi. Ogni embedding produce un vettore che verrà usato
						per il confronto. Se una lista, i vettori verranno concatenati.

				Returns:
					float: Un valore numerico che rappresenta la similarità tra i due mazzi.
						Il valore dipende dalla metrica scelta (es. 1.0 per identici nel caso
						di similarità coseno).

				Raises:
					ValueError: Se `embedding` non è né un `Embedding` né una lista di `Embedding`.

				Example:
					>>> Deck.similarity(m1, m2, embedding=[Embedding.QUANTITÀ, Embedding.SOTTOTIPI])
					0.847
			"""
		if not isinstance(embedding, list):
			embedding = [embedding]

		v1 = [x for e in embedding for x in e(mazzo1)]
		v2 = [x for e in embedding for x in e(mazzo2)]

		return metrica(v1, v2)
		# con un solo embedding fa:
		# return metrica(embedding(m1), embedding(m2))
		
	class Diagnostic:
		"""Classe per la diagnostica degli embedding di un mazzo."""
		
		@staticmethod
		def diagnose_embedding(
			deck: "Deck",
			embedding: "Deck.Embedding"
		) -> Dict[str, Any]:
			"""
			Diagnostica perché un embedding fallisce o produce vettori zero per un mazzo.
			
			Args:
				deck: Il mazzo da analizzare
				embedding: L'embedding da diagnosticare
				
			Returns:
				Dizionario con i risultati della diagnostica
			"""
			import numpy as np
			import inspect
			
			results = {
				"deck_name": deck.name,
				"embedding": embedding.name,
				"success": False,
				"vector": None,
				"error": None,
				"error_type": None,
				"is_zero_vector": None,
				"vector_stats": None,
				"problematic_cards": []
			}
			
			try:
				# Prova ad applicare l'embedding
				vector = embedding(deck)
				results["success"] = True
				results["vector"] = vector
				
				# Controlla se è un vettore zero
				if vector is not None:
					is_zero = not np.any(vector)
					results["is_zero_vector"] = is_zero
					
					# Statistiche sul vettore
					results["vector_stats"] = {
						"length": len(vector),
						"min": float(np.min(vector)) if not is_zero else 0,
						"max": float(np.max(vector)) if not is_zero else 0,
						"mean": float(np.mean(vector)) if not is_zero else 0,
						"nonzero": int(np.count_nonzero(vector))
					}
					
					# Se è un vettore zero, analizza il perché
					if is_zero:
						results["error"] = "Vettore tutto zero"
						results["problematic_cards"] = Deck.Diagnostic.analyze_zero_vector_cause(deck, embedding)
				else:
					results["error"] = "L'embedding ha restituito None"
					results["is_zero_vector"] = None
					
			except Exception as e:
				# Gestisci l'errore
				results["success"] = False
				results["error"] = str(e)
				results["error_type"] = type(e).__name__
				results["problematic_cards"] = Deck.Diagnostic.analyze_embedding_error(deck, embedding, e)
			
			return results
		
		@staticmethod
		def analyze_zero_vector_cause(
			deck: "Deck",
			embedding: "Deck.Embedding"
		) -> List[Dict[str, Any]]:
			"""
			Analizza perché un embedding produce un vettore tutto zero.
			
			Args:
				deck: Il mazzo da analizzare
				embedding: L'embedding che produce vettori zero
				
			Returns:
				Lista di carte problematiche con dettagli
			"""
			problematic_cards = []
			
			# Analisi specifica per tipo di embedding
			if embedding == Deck.Embedding.QUANTITY:
				# Controlla se le carte del mazzo sono nell'indice
				for card, qty in deck.carte.items():
					card_id = card.get_id()
					try:
						# Verifica se l'ID è valido per l'embedding
						all_ids = Deck.Embedding._quantità.__globals__.get('Expansion').generate_all_ids()
						if card_id not in all_ids:
							problematic_cards.append({
								"card_id": card_id,
								"quantity": qty,
								"issue": "ID non presente nell'indice di QUANTITY"
							})
					except Exception as e:
						problematic_cards.append({
							"card_id": card_id,
							"quantity": qty,
							"issue": f"Errore durante la verifica: {str(e)}"
						})
			
			elif embedding == Deck.Embedding.QUANTITY_FROM_CSR:
				# Controlla se le carte del mazzo sono nell'indice
				for card, qty in deck.carte.items():
					card_id = card.get_id()
					try:
						# Verifica se l'ID è valido per l'embedding
						if hasattr(Deck.Embedding, "_card_ids_index"):
							if card_id not in Deck.Embedding._card_ids_index:
								problematic_cards.append({
									"card_id": card_id,
									"quantity": qty,
									"issue": "ID non presente nell'indice di QUANTITY_FROM_CSR"
								})
					except Exception as e:
						problematic_cards.append({
							"card_id": card_id,
							"quantity": qty,
							"issue": f"Errore durante la verifica: {str(e)}"
						})
			
			elif embedding == Deck.Embedding.PKMN_TYPES:
				# Controlla se ci sono Pokémon nel mazzo
				from structures.card import Pokémon
				pokemon_count = sum(qty for card, qty in deck.carte.items() if isinstance(card, Pokémon))
				if pokemon_count == 0:
					problematic_cards.append({
						"issue": "Nessun Pokémon nel mazzo"
					})
				else:
					# Controlla se i Pokémon hanno tipi validi
					for card, qty in deck.carte.items():
						if isinstance(card, Pokémon):
							if not hasattr(card, 'type') or card.type is None:
								problematic_cards.append({
									"card_id": card.get_id(),
									"quantity": qty,
									"issue": "Pokémon senza tipo"
								})
			
			elif embedding == Deck.Embedding.ATTACKS_DMG:
				# Controlla se i Pokémon hanno attacchi con danni validi
				from structures.card import Pokémon
				has_valid_attacks = False
				for card, qty in deck.carte.items():
					if isinstance(card, Pokémon):
						if not hasattr(card, 'attacks') or not card.attacks:
							problematic_cards.append({
								"card_id": card.get_id(),
								"quantity": qty,
								"issue": "Pokémon senza attacchi"
							})
						else:
							valid_damages = [a for a in card.attacks if hasattr(a, 'damage') and isinstance(a.damage, (int, float))]
							if not valid_damages:
								problematic_cards.append({
									"card_id": card.get_id(),
									"quantity": qty,
									"issue": "Pokémon senza danni validi negli attacchi"
								})
							else:
								has_valid_attacks = True
				
				if not has_valid_attacks:
					problematic_cards.append({
						"issue": "Nessun Pokémon con attacchi validi nel mazzo"
					})
			
			# Aggiungi altri casi specifici per altri embedding...
			
			return problematic_cards
		
		@staticmethod
		def analyze_embedding_error(
			deck: "Deck",
			embedding: "Deck.Embedding",
			error: Exception
		) -> List[Dict[str, Any]]:
			"""
			Analizza perché un embedding genera un errore.
			
			Args:
				deck: Il mazzo da analizzare
				embedding: L'embedding che genera l'errore
				error: L'eccezione sollevata
				
			Returns:
				Lista di carte problematiche con dettagli
			"""
			problematic_cards = []
			
			# Analisi basata sul tipo di errore
			if isinstance(error, KeyError):
				# Cerca la chiave mancante
				key_str = str(error)
				problematic_cards.append({
					"issue": f"Chiave mancante: {key_str}"
				})
				
				# Prova a identificare la carta problematica
				for card, qty in deck.carte.items():
					try:
						card_id = card.get_id()
						problematic_cards.append({
							"card_id": card_id,
							"quantity": qty,
							"card_type": type(card).__name__,
							"attributes": {k: v for k, v in vars(card).items() if not k.startswith('_')}
						})
					except Exception:
						pass
			
			elif isinstance(error, AttributeError):
				# Cerca l'attributo mancante
				attr_str = str(error)
				problematic_cards.append({
					"issue": f"Attributo mancante: {attr_str}"
				})
				
				# Prova a identificare la carta problematica
				for card, qty in deck.carte.items():
					try:
						card_id = card.get_id()
						problematic_cards.append({
							"card_id": card_id,
							"quantity": qty,
							"card_type": type(card).__name__,
							"attributes": {k: v for k, v in vars(card).items() if not k.startswith('_')}
						})
					except Exception:
						pass
			
			elif isinstance(error, TypeError):
				# Errore di tipo
				type_str = str(error)
				problematic_cards.append({
					"issue": f"Errore di tipo: {type_str}"
				})
				
				# Prova a identificare la carta problematica
				for card, qty in deck.carte.items():
					try:
						card_id = card.get_id()
						problematic_cards.append({
							"card_id": card_id,
							"quantity": qty,
							"card_type": type(card).__name__,
							"attributes": {k: v for k, v in vars(card).items() if not k.startswith('_')}
						})
					except Exception:
						pass
			
			# Aggiungi altri casi specifici per altri tipi di errore...
			
			return problematic_cards
		
		@staticmethod
		def diagnose_all_embeddings(
			deck: "Deck"
		) -> "pd.DataFrame":
			"""
			Diagnostica tutti gli embedding per un mazzo.
			
			Args:
				deck: Il mazzo da analizzare
				
			Returns:
				DataFrame con i risultati della diagnostica
			"""
			import pandas as pd
			import logging
			
			logger = logging.getLogger(__name__)
			results = []
			
			for emb in Deck.Embedding:
				logger.info(f"Diagnostica embedding {emb.name} per mazzo {deck.name}")
				result = Deck.Diagnostic.diagnose_embedding(deck, emb)
				
				# Semplifica il risultato per il DataFrame
				simplified = {
					"embedding": emb.name,
					"success": result["success"],
					"error": result["error"],
					"error_type": result["error_type"],
					"is_zero_vector": result["is_zero_vector"],
					"vector_length": result["vector_stats"]["length"] if result["vector_stats"] else None,
					"nonzero_count": result["vector_stats"]["nonzero"] if result["vector_stats"] else None,
					"problematic_cards_count": len(result["problematic_cards"])
				}
				
				results.append(simplified)
			
			# Crea DataFrame
			df = pd.DataFrame(results)
			return df
		
		@staticmethod
		def print_embedding_diagnosis(
			diagnosis: Dict[str, Any]
		):
			"""
			Stampa i risultati della diagnostica in formato leggibile.
			
			Args:
				diagnosis: Risultato della diagnostica
			"""
			print(f"\n=== DIAGNOSTICA EMBEDDING {diagnosis['embedding']} ===")
			print(f"Mazzo: {diagnosis['deck_name']}")
			print(f"Successo: {diagnosis['success']}")
			
			if diagnosis['error']:
				print(f"Errore: {diagnosis['error']}")
				if diagnosis['error_type']:
					print(f"Tipo errore: {diagnosis['error_type']}")
			
			if diagnosis['vector'] is not None:
				print(f"Lunghezza vettore: {len(diagnosis['vector'])}")
				print(f"Vettore zero: {diagnosis['is_zero_vector']}")
				
				if diagnosis['vector_stats']:
					stats = diagnosis['vector_stats']
					print(f"Statistiche: min={stats['min']:.4f}, max={stats['max']:.4f}, media={stats['mean']:.4f}")
					print(f"Elementi non zero: {stats['nonzero']}/{stats['length']}")
			
			if diagnosis['problematic_cards']:
				print("\nCarte problematiche:")
				for i, card in enumerate(diagnosis['problematic_cards'], 1):
					print(f"  {i}. ", end="")
					if 'card_id' in card:
						print(f"ID: {card['card_id']}", end="")
						if 'quantity' in card:
							print(f", Quantità: {card['quantity']}", end="")
						print()
					
					if 'issue' in card:
						print(f"     Problema: {card['issue']}")
					
					if 'attributes' in card:
						print(f"     Attributi: {card['attributes']}")
					
					print()
		
		@staticmethod
		def run_deck_diagnostics(
			deck: "Deck",
			embedding: Optional["Deck.Embedding"] = None
		):
			"""
			Esegue la diagnostica completa per un mazzo e stampa i risultati.
			
			Args:
				deck: Il mazzo da analizzare
				embedding: L'embedding specifico da diagnosticare (se None, diagnostica tutti)
			"""
			if embedding:
				# Diagnostica un solo embedding
				diagnosis = Deck.Diagnostic.diagnose_embedding(deck, embedding)
				Deck.Diagnostic.print_embedding_diagnosis(diagnosis)
				return diagnosis
			else:
				# Diagnostica tutti gli embedding
				results = []
				for emb in Deck.Embedding:
					diagnosis = Deck.Diagnostic.diagnose_embedding(deck, emb)
					Deck.Diagnostic.print_embedding_diagnosis(diagnosis)
					results.append(diagnosis)
				
				# Crea e stampa un riepilogo
				df = Deck.Diagnostic.diagnose_all_embeddings(deck)
				print("\n=== RIEPILOGO DIAGNOSTICA ===")
				print(df)
				
				return df
