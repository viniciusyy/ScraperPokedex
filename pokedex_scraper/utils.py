import re
from urllib.parse import urljoin

BASE = "https://pokemondb.net"

TYPE_CHART = {
    # attacker -> defender -> multiplier
    "normal": {"rock":0.5,"ghost":0.0,"steel":0.5},
    "fire": {"fire":0.5,"water":0.5,"grass":2,"ice":2,"bug":2,"rock":0.5,"dragon":0.5,"steel":2},
    "water": {"fire":2,"water":0.5,"grass":0.5,"ground":2,"rock":2,"dragon":0.5},
    "electric": {"water":2,"electric":0.5,"grass":0.5,"ground":0,"flying":2,"dragon":0.5},
    "grass": {"fire":0.5,"water":2,"grass":0.5,"poison":0.5,"ground":2,"flying":0.5,"bug":0.5,"rock":2,"dragon":0.5,"steel":0.5},
    "ice": {"fire":0.5,"water":0.5,"grass":2,"ice":0.5,"ground":2,"flying":2,"dragon":2,"steel":0.5},
    "fighting": {"normal":2,"ice":2,"poison":0.5,"flying":0.5,"psychic":0.5,"bug":0.5,"rock":2,"ghost":0,"dark":2,"steel":2,"fairy":0.5},
    "poison": {"grass":2,"poison":0.5,"ground":0.5,"rock":0.5,"ghost":0.5,"steel":0,"fairy":2},
    "ground": {"fire":2,"electric":2,"grass":0.5,"poison":2,"flying":0,"bug":0.5,"rock":2,"steel":2},
    "flying": {"electric":0.5,"grass":2,"fighting":2,"bug":2,"rock":0.5,"steel":0.5},
    "psychic": {"fighting":2,"poison":2,"psychic":0.5,"dark":0,"steel":0.5},
    "bug": {"fire":0.5,"grass":2,"fighting":0.5,"poison":0.5,"flying":0.5,"psychic":2,"ghost":0.5,"dark":2,"steel":0.5,"fairy":0.5},
    "rock": {"fire":2,"ice":2,"flying":2,"bug":2,"fighting":0.5,"ground":0.5,"steel":0.5},
    "ghost": {"normal":0,"psychic":2,"ghost":2,"dark":0.5},
    "dragon": {"dragon":2,"steel":0.5,"fairy":0},
    "dark": {"fighting":0.5,"psychic":2,"ghost":2,"dark":0.5,"fairy":0.5},
    "steel": {"fire":0.5,"water":0.5,"electric":0.5,"ice":2,"rock":2,"fairy":2,"steel":0.5},
    "fairy": {"fire":0.5,"fighting":2,"poison":0.5,"dragon":2,"dark":2,"steel":0.5}
}

TYPE_ALIASES = {
    "electric": ["eletric"],  # resilient for typos
}

def to_slug(url: str) -> str:
    return url.rstrip("/").split("/")[-1]

def compute_type_effectiveness(types):
    """Return attacking-type -> multiplier (float), given defending types (1 or 2)."""
    types = [t.lower() for t in (types or [])]
    def mult_from(attacker):
        m = 1.0
        for d in types:
            m *= TYPE_CHART.get(attacker, {}).get(d, 1.0)
        return m
    all_types = sorted(TYPE_CHART.keys())
    return {t: round(mult_from(t), 2) for t in all_types}

def parse_float_from_text(text, unit_char):
    # e.g. text='0.7 m (2′04″)' with unit_char='m' -> 0.7
    if not text: return None
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*" + re.escape(unit_char), text)
    return float(m.group(1)) if m else None

def detect_form_from_row_text(text):
    if not text: return None
    text = text.strip()
    # common forms explicitly mentioned on the list page
    for key in ["Mega", "Alolan", "Galarian", "Hisuian", "Partner", "Totem", "Primal", "Therian", "Origin", "Paldean"]:
        if key.lower() in text.lower():
            # Return the phrase containing the form
            m = re.search(rf"({key}[^\s,]*\s?[^,]*)", text, re.IGNORECASE)
            return m.group(1) if m else key
    return None

def absolutize(href: str) -> str:
    if not href: return None
    return urljoin(BASE, href)
