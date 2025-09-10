from enum import Enum
class Energy(Enum):
	COLORLESS = "Colorless"
	LIGHTNING = "Lightning"
	FIGHTING = "Fighting"
	DARKNESS = "Darkness"
	PSYCHIC = "Psychic"
	DRAGON = "Dragon"
	GRASS = "Grass"
	WATER = "Water"
	METAL = "Metal"
	FAIRY = "Fairy"
	FIRE = "Fire"

	@classmethod
	def from_str(cls, value: str) -> "Energy":
		for member in cls:
			if member.value == value:
				return member
		raise ValueError (f"'{value}' non è un'energia valida.")