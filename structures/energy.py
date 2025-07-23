from enum import Enum
class Energy(Enum):
	COLORLESS = "Colorless"
	GRASS = "Grass"
	FIRE = "Fire"
	WATER = "Water"
	LIGHTNING = "Lightning"
	PSYCHIC = "Psychic"
	FIGHTING = "Fighting"
	DARKNESS = "Darkness"
	METAL = "Metal"
	FAIRY = "Fairy"
	DRAGON = "Dragon"

	def from_str(cls, value: str) -> "Energy":
		for member in cls:
			if member.value == value:
				return member
		raise ValueError (f"'{value}' non è un'energia valida.")