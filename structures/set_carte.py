from datetime import date
from settings import PROJECT_ROOT
import json

class SetCarte:
    nome:str
    code: str
    ptcgoCode: str
    # release: date

    def __init__(self,
        code: str,
        # is_ptcgo: bool
    ):
        sets_path = PROJECT_ROOT / "data" / "sets" / "en.json"

        if not sets_path.exists():
            raise FileNotFoundError(f"File dei set non trovato: {sets_path}")

        with open(sets_path, encoding="utf-8") as f:
            sets = json.load(f)

        match = None
        for s in sets:
            if code in [s.get("ptcgoCode"), s.get("id")]:
            # if (is_ptcgo and s.get("ptcgoCode") == code) or (not is_ptcgo and s.get("id") == code):
                match = s
                break

        if not match:
            raise ValueError(f"Nessun set trovato con code '{code}'")

        self.code = match["id"]
        self.ptcgoCode = match.get("ptcgoCode")
        self.nome = match["name"]



    def __init__(self, 
        nome: str,
        code: str,
        ptcgoCode: str,
        # release: date = None
    ):
        self.nome = nome
        self.code = code
        self.ptcgoCode = ptcgoCode
        # self.release = release

    def __str__(self):
        return self.code