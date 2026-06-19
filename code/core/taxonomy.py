from code.core.config import VALID_ISSUE_TYPES, VALID_CAR_PARTS, VALID_LAPTOP_PARTS, VALID_PACKAGE_PARTS

# ---------------------------------------------------------------------------
# Issue normalizer — slang/synonym → canonical issue_type
# ---------------------------------------------------------------------------

ISSUE_NORMALIZER = {
    # passthrough — already canonical
    "dent": "dent", "scratch": "scratch", "crack": "crack",
    "glass_shatter": "glass_shatter", "broken_part": "broken_part",
    "missing_part": "missing_part", "torn_packaging": "torn_packaging",
    "crushed_packaging": "crushed_packaging", "water_damage": "water_damage",
    "stain": "stain", "none": "none", "unknown": "unknown",
    # dent
    "dented": "dent", "dents": "dent", "ding": "dent", "dings": "dent",
    "hail": "dent", "dented area": "dent",
    # scratch
    "scratched": "scratch", "scratches": "scratch", "scrape": "scratch",
    "scraped": "scratch", "scrapes": "scratch", "scuff": "scratch",
    "scuffed": "scratch", "mark": "scratch", "marks": "scratch",
    "paint scrape": "scratch", "paint chipped": "scratch",
    "paint damage": "scratch", "paint": "scratch",
    # crack
    "cracked": "crack", "cracks": "crack", "fracture": "crack",
    "fractured": "crack", "hairline crack": "crack", "fractures": "crack",
    "broken screen": "crack", "broken display": "crack",
    "shattered screen": "crack", "display crack": "crack",
    # glass shatter
    "shatter": "glass_shatter", "shattered": "glass_shatter",
    "shattered glass": "glass_shatter", "shattered windshield": "glass_shatter",
    "glass crack": "glass_shatter", "glass broken": "glass_shatter",
    "front glass broken": "glass_shatter",
    # broken_part
    "broken": "broken_part", "broke": "broken_part", "break": "broken_part",
    "bent": "broken_part", "bent frame": "broken_part",
    "broken hinge": "broken_part", "broken part": "broken_part",
    "chipped": "broken_part", "chip": "broken_part",
    "smashed": "broken_part", "damaged": "broken_part",
    "damage": "broken_part", "display broken": "broken_part",
    "won't open": "broken_part", "not opening": "broken_part",
    "won't turn on": "broken_part", "not working": "broken_part",
    "malfunction": "broken_part", "defective": "broken_part",
    "faulty": "broken_part",
    # missing_part
    "missing": "missing_part", "gone": "missing_part",
    "detached": "missing_part", "fell off": "missing_part",
    "missing key": "missing_part", "missing keys": "missing_part",
    "missing part": "missing_part",
    # torn_packaging
    "torn": "torn_packaging", "tear": "torn_packaging",
    "ripped": "torn_packaging", "ripped open": "torn_packaging",
    "torn packaging": "torn_packaging", "torn seal": "torn_packaging",
    "torn open": "torn_packaging", "opened": "torn_packaging",
    # crushed_packaging
    "crushed": "crushed_packaging", "crush": "crushed_packaging",
    "crushed box": "crushed_packaging", "crushed package": "crushed_packaging",
    "crushed corner": "crushed_packaging", "badly crushed": "crushed_packaging",
    "crease": "crushed_packaging", "creasing": "crushed_packaging",
    # water_damage
    "water": "water_damage", "water damage": "water_damage",
    "water damaged": "water_damage", "wet": "water_damage",
    "moisture": "water_damage", "soaked": "water_damage",
    "liquid damage": "water_damage", "water stain": "water_damage",
    "flood": "water_damage",
    # stain
    "stained": "stain", "stains": "stain", "sticky": "stain",
    "coffee stain": "stain", "oil stain": "stain", "ink stain": "stain",
    # none
    "no damage": "none", "nothing": "none", "fine": "none", "ok": "none",
    # unknown
    "unclear": "unknown", "not sure": "unknown",
}

# Word-level priority list for substring fallback (longer phrases first)
_ISSUE_WORD_FALLBACK = [
    ("water stain", "water_damage"), ("water damage", "water_damage"),
    ("liquid damage", "water_damage"), ("broken screen", "crack"),
    ("broken display", "crack"), ("broken hinge", "broken_part"),
    ("broken part", "broken_part"), ("glass shatter", "glass_shatter"),
    ("shattered glass", "glass_shatter"), ("torn packaging", "torn_packaging"),
    ("crushed packaging", "crushed_packaging"),
    ("fell off", "missing_part"), ("missing key", "missing_part"),
    ("crushed corner", "crushed_packaging"), ("bent frame", "broken_part"),
    ("paint chipped", "scratch"), ("paint scrape", "scratch"),
    ("fracture", "crack"), ("scraped", "scratch"), ("scuffed", "scratch"),
    ("detached", "missing_part"), ("crushed", "crushed_packaging"),
    ("missing", "missing_part"), ("shattered", "glass_shatter"),
    ("soaked", "water_damage"), ("stain", "stain"), ("scratch", "scratch"),
    ("crack", "crack"), ("dent", "dent"), ("torn", "torn_packaging"),
    ("ripped", "torn_packaging"), ("broken", "broken_part"),
    ("bent", "broken_part"), ("water", "water_damage"),
    ("damage", "broken_part"),
]


def normalize_issue(raw_issue: str) -> str:
    """Normalise a free-text issue description to a canonical issue_type."""
    raw = raw_issue.lower().strip().rstrip(".")

    # 1. Exact dict lookup
    if raw in ISSUE_NORMALIZER:
        return ISSUE_NORMALIZER[raw]

    # 2. Substring scan — longer phrases first
    for phrase, canonical in _ISSUE_WORD_FALLBACK:
        if phrase in raw:
            return canonical

    return "unknown"


# ---------------------------------------------------------------------------
# Part normalizer — slang/synonym → canonical object_part
# ---------------------------------------------------------------------------

_PART_NORMALIZER_BASE = {
    # --- car ---
    "front bumper": "front_bumper", "bumper front": "front_bumper",
    "front": "front_bumper",
    "rear bumper": "rear_bumper", "back bumper": "rear_bumper",
    "back": "rear_bumper", "bumper rear": "rear_bumper",
    "bumper": "unknown",
    "door": "door", "door panel": "door", "side door": "door",
    "car door": "door",
    "hood": "hood", "bonnet": "hood", "top panel": "hood",
    "windshield": "windshield", "windscreen": "windshield",
    "front glass": "windshield", "front window": "windshield",
    "side mirror": "side_mirror", "wing mirror": "side_mirror",
    "mirror": "side_mirror",
    "headlight": "headlight", "headlamp": "headlight",
    "head light": "headlight", "front light": "headlight",
    "taillight": "taillight", "tail light": "taillight",
    "back light": "taillight", "rear light": "taillight",
    "fender": "fender",
    "quarter panel": "quarter_panel", "quarter": "quarter_panel",
    "body": "body", "car body": "body",
    # --- laptop ---
    "screen": "screen", "display": "screen", "monitor": "screen",
    "keyboard": "keyboard", "keys": "keyboard",
    "trackpad": "trackpad", "touchpad": "trackpad", "pad": "trackpad",
    "hinge": "hinge",
    "lid": "lid", "cover": "lid",
    "laptop corner": "corner",
    "port": "port", "usb": "port",
    "base": "base", "bottom": "base",
    "laptop body": "body",
    # --- package ---
    "box": "box", "package": "box", "package box": "box",
    "shipping box": "box", "delivery box": "box", "outside box": "box",
    "cardboard box": "box",
    "package corner": "package_corner", "box corner": "package_corner",
    "package side": "package_side", "surface": "package_side",
    "package surface": "package_side",
    "seal": "seal", "tape": "seal", "seal area": "seal",
    "label": "label",
    "contents": "contents", "inside": "contents",
    "item inside": "contents", "product inside": "contents",
    "product": "item", "item": "item",
}

# Parts that depend on object_type context
_CONTEXT_PARTS = {
    "corner": {"package": "package_corner", "laptop": "corner", "car": "unknown"},
    "side": {"package": "package_side", "laptop": "unknown", "car": "unknown"},
}

_VALID_PARTS_BY_OBJECT = {
    "car": VALID_CAR_PARTS,
    "laptop": VALID_LAPTOP_PARTS,
    "package": VALID_PACKAGE_PARTS,
}


def normalize_part(raw_part: str, object_type: str = "unknown") -> str:
    """Normalise a free-text part description to a canonical object_part.

    Args:
        raw_part:    Free-text part name from LLM or signal detector.
        object_type: "car" | "laptop" | "package" — used for context-sensitive parts.
    """
    raw = raw_part.lower().strip().rstrip(".")

    # 1. Already a canonical value for this object type → passthrough
    valid_parts = _VALID_PARTS_BY_OBJECT.get(object_type, set())
    if raw in valid_parts:
        return raw

    # 2. Context-sensitive parts (e.g. "corner")
    if raw in _CONTEXT_PARTS:
        return _CONTEXT_PARTS[raw].get(object_type, "unknown")

    # 3. Base dictionary lookup
    if raw in _PART_NORMALIZER_BASE:
        return _PART_NORMALIZER_BASE[raw]

    # 4. Try stripping object_type prefix (e.g. "car_door" → "door")
    for prefix in ("car_", "laptop_", "package_"):
        if raw.startswith(prefix):
            stripped = raw[len(prefix):]
            if stripped in _PART_NORMALIZER_BASE:
                result = _PART_NORMALIZER_BASE[stripped]
                if result in valid_parts:
                    return result

    return "unknown"
