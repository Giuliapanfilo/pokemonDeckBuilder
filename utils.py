import json
import pickle
from pathlib import Path
from typing import Callable, Any
from settings import PROJECT_ROOT

def load_or_build_cache(name: str, builder: Callable[[], Any], binary: bool = False) -> Any:
    """
    Carica da cache o costruisce i dati e li salva.

    Args:
        name (str): nome del file cache senza estensione
        builder (Callable): funzione che genera i dati se non esiste cache
        binary (bool): True -> pickle .pkl, False -> JSON .json

    Returns:
        Any: dati caricati o generati
    """
    cache_dir = PROJECT_ROOT / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    ext = ".pkl" if binary else ".json"
    cache_path = cache_dir / f"{name}{ext}"

    if cache_path.exists():
        mode = "rb" if binary else "r"
        with open(cache_path, mode) as f:
            return pickle.load(f) if binary else json.load(f)

    data = builder()
    mode = "wb" if binary else "w"
    with open(cache_path, mode) as f:
        if binary:
            pickle.dump(data, f)
        else:
            json.dump(data, f, indent=2)
    return data
