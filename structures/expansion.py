from settings import PROJECT_ROOT
import json, re

SETS_PATH = PROJECT_ROOT / "data" / "sets.json"

class Expansion:
    name: str
    code: str
    ptcgoCode: str
    printed : int
    # release: date

    def __init__(self, data_or_code: str | dict, use_ptcgo:bool=False, number:str|None=None):
        """
        Se data_or_code è str, fa lookup su en.json, altrimenti lo usa come dict.
        """
        
        if isinstance(data_or_code, dict):
            data = data_or_code
        else:
            code = data_or_code.upper()
            # A) override set raw (es. "SVP" → "PR-SV")
            if use_ptcgo and code in SET_OVERRIDE:
                code = SET_OVERRIDE[code]
            # B) override da numero (es. raw_set="PR", number="SWSH250")
            if use_ptcgo and number:
                m = re.match(r"^([A-Za-z]+)(\d+)$", number)
                if m:
                    pref, num = m.group(1).upper(), m.group(2)
                    if pref in PROMO_MAP:
                        code   = PROMO_MAP[pref]
                        number = num
            # ricerca effettiva (solo uno dei due rami)
            if use_ptcgo:
                data = self.search_by_ptcgo(code)
            else:
                data = self.search(code)
        self.extract(data)

    
    @staticmethod
    def load_all_sets() -> list[dict]:
        with open(SETS_PATH, encoding="utf-8") as f:
            return json.load(f)


    @staticmethod
    def search(code: str) -> dict:
        """
        Cerca nel file sets.json il set con stesso id | ptcgo | name 
        """
        norm  = _normalize_set_title(code)
        for s in Expansion.load_all_sets():

            for candidate in {
                s.get("id", ""),
                s.get("ptcgoCode", ""),  
                # s.get("ptcgoCode", "").replace("-", ""),
                # s.get("ptcgoCode", "").lower()+'c',  
                # s.get("ptcgoCode", "").lower()+'p',  
            }:
                if norm == candidate.lower():
                    return s

        raise ValueError(f"Nessun set trovato con code '{code}'")


    @staticmethod
    def search_by_ptcgo(ptcgo: str) -> dict:
        """
        Cerca nel file sets.json il set con stesso ptcgo  
        """
        for s in Expansion.load_all_sets():
            if ptcgo == s.get("ptcgoCode", ""):
                return s

        raise ValueError(f"Nessun set trovato con ptcgo '{ptcgo}'")



    def extract(self, data: dict):
        """Popola gli attributi a partire dal dict trovato."""
        self.ptcgoCode = data.get("ptcgoCode")
        self.name = data["name"]
        try:
            self.printed = data["printedTotal"]
        except:
            self.printed = data['printed']
        
        try:
            self.code = data["code"]
        except:
            self.code = data['id']


    def generate_ids(self):
        return [f"{self.code}-{x}" for x in range(1, self.printed + 1)]


    @classmethod
    def generate_all_ids(cls) -> list[str]:
        from utils import load_or_build_cache

        def builder() -> list[str]:
            with open(SETS_PATH, encoding="utf-8") as f:
                sets_data = json.load(f)

            all_ids: list[str] = []
            for set_dict in sets_data:
                all_ids.extend(Expansion(set_dict).generate_ids())
            return all_ids

        return load_or_build_cache("all_ids", builder)
    
    # ----------  SERIALIZZAZIONE ----------- #

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "ptcgoCode": self.ptcgoCode,
            "name": self.name,
            "printed": self.printed,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Expansion":
        return Expansion(d)


    def __str__(self) -> str:
        return f"Espansione {self.name}.   codici:{self.code}/{self.ptcgoCode}.   cards:{self.printed}"
	

	# def __repr__(self) -> str:
	# 	"""utile in console/debug."""
	# 	return f"<Attack name={self.name!r} text={self.text!r}>"
    

def _normalize_set_title(title: str) -> str:
    """Rimuove prefissi/suffissi e pulisce la stringa."""
    s = title.lower()
    s = re.sub(r"^ex\s+", "", s) # rimuovi 'ex ' all’inizio
    s = re.sub(r"\s+set$", "", s) # rimuovi ' set' alla fine
    s = re.sub(r"[^a-z0-9]+", "", s) # lascia solo alphanumeric
    return s







PROMO_MAP = {
    "DPP":  "PR-DPP",
    "HS":   "PR-HS",
    "NP":   "PR-NP",
    "BLW":  "PR-BLW",
    "XY":   "PR-XY",
    "SM":   "PR-SM",
    "SWSH": "PR-SW",
    "SV":   "PR-SV",
}

# 2) raw set code → ptcgo completo (per casi come "SVP")
SET_OVERRIDE = {
    "SVP": "PR-SV",
    # aggiungi altri se necessario
}