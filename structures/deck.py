from structures.card import Carta, Pokémon, Trainer
from enum import Enum
from structures.energy import Energy
from structures.expansion import Expansion
import re
from settings import *
from typing import Callable
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
		if not isinstance(carta, Pokémon):
			continue
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

		def _quantità(m:"Deck") -> list[int]:
			v = {k: 0 for k in Expansion.generate_all_ids()}
			for carta, count in m.carte.items():
				v[carta.get_id()] = count
			return list(v.values())


		def _sottotipi(m:"Deck") -> list[int]:
			v = {k: 0 for k in Carta.build_all_subtypes()}

			for carta, qty in m.carte.items():
				# if not hasattr(carta, "subtypes"):
				#	 continue

				for sottotipo in carta.subtypes:
					if sottotipo in v.values():
						v[sottotipo] += qty

			return list(v.values())


		def _supertipi(m: "Deck") -> list[int]:
			v = {k: 0 for k in Carta.build_all_supertypes()}

			for carta, qty in m.carte.items():
				if carta.supertype in v.values():
					v[carta.supertype] += qty

			return list(v.values())


		def _keywords(m:"Deck") -> list[int]:
			v = {k: 0 for k in Carta.build_all_keywords()}
			for carta, qty in m.carte.items():
				match carta:
					case Pokémon():
						testo = " ".join(carta.attacks + carta.abilities).lower()
					case Trainer():
						testo = " ".join(carta.rules).lower()
					case _:
						continue

				# tokenizziamo in parole 
				for token in re.findall(r"\b\w+\b", testo):
					if token in v.values():
						v[token] += qty

			return list(v.values())


		def _energie(m: "Deck") -> list[float]:
			v = {e: 0 for e in Energy}
			tot = 0

			for carta, qty in m.carte.items():
				if not isinstance(carta, Pokémon):
					continue
				v[carta.type] += qty
				tot += qty

			if tot == 0:
				return [0.0 for _ in Energy]

			return [v[e] / tot for e in Energy]


		def _evoluzione_stats(m: "Deck") -> list[float]:
			pokemons = {carta:qty for carta, qty in m.carte.items() if isinstance(carta, Pokémon)}
			pre = post = base = tot_pokemon = 0

			for carta, qty in pokemons.items():
				if carta.evolves_from:
					pre += qty
				if carta.evolves_to != []:
					post += qty
				if not carta.evolves_from and carta.evolves_to == []:
					base += qty
				tot_pokemon += qty

			if tot_pokemon == 0: return [0.0, 0.0, 0.0]
			return [
				pre / tot_pokemon,
				post / tot_pokemon,
				base / tot_pokemon
			]


		def _debolezze(m:"Deck") -> list[float]:
			v = {e: 0 for e in Energy}
			tot = 0
			for carta, qty in m.carte.items():
				if not isinstance(carta, Pokémon):
					continue
				tot += qty
				for wk in carta.weaknesses:
					v[wk] += qty
				
			return [v[e] / tot if tot else 0.0 for e in Energy]


		def _resistenze(m: "Deck") -> list[float]:
			v = {e: 0 for e in Energy}
			tot = 0
			for carta, qty in m.carte.items():
				if not isinstance(carta, Pokémon):
					continue
				tot += qty
				for wk in carta.resistances:
					v[wk] += qty
				
			return [v[e] / tot if tot else 0.0 for e in Energy]


		QUANTITY =   _quantità
		"""Vettore con il numero di copie per ciascuna carta, in ordine fisso. (vettore giganorme)"""

		KEYWORDS = _keywords
		"""Frequenza di parole chiave specifiche (es. paralizza, pesca, scarta) nei testi delle carte Pokémon."""

		SUPERTYPES = _supertipi
		"""Distribuzione dei supertipi delle carte nel mazzo: Pokémon, Trainer, Energy."""

		SUBTYPES = _sottotipi
		"""Distribuzione dei sottotipi tra le carte nel mazzo (es. EX, V, Radiant, Supporter, Tool, ecc.)."""

		PKMN_TYPES = _energie
		"""Percentuale dei Pokémon del mazzo per tipo di energia (Fire, Water, Psychic, ecc.)."""

		EVO_STATS = _evoluzione_stats
		"""Percentuale di Pokémon con pre-evoluzione, evoluzione o nessuna delle due nel mazzo."""

		WEAKNESS = _debolezze
		"""Percentuale di Pokémon nel mazzo deboli a ciascun tipo di energia."""

		RESISTANCE = _resistenze
		"""Percentuale di Pokémon nel mazzo resistenti a ciascun tipo di energia."""

		HP = lambda m: _stat_embedding(m, lambda c: [c.hp])
		"""Statistiche sugli HP dei Pokémon nel mazzo: media, minimo, massimo, deviazione standard."""

		ATTACKS_DMG = staticmethod(lambda m: _stat_embedding( m,
			lambda p: [a.damage for a in p.attacks if isinstance(a.damage, (int, float))]
		))
		"""statistiche sui danni degli attacchi: media, minimo, massimo, deviazione standard."""
		ATTACKS_COSTS = staticmethod(lambda m: _stat_embedding( m,
			lambda p: [a.cost for a in p.attacks]
		))
		"""statistiche dei costi degli attacchi: media, minimo, massimo, deviazione standard."""

		def __call__(self, mazzo:"Deck") -> list[float]:
			return self.value(mazzo)




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
