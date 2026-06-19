from code.core.config import ALLOWED_ISSUE_TYPES, ALLOWED_CAR_PARTS, ALLOWED_LAPTOP_PARTS, ALLOWED_PACKAGE_PARTS


ISSUE_NORMALIZER = {
    "shattered": "glass_shatter",
    "shattered glass": "glass_shatter",
    "broken glass": "glass_shatter",
    "cracked glass": "glass_shatter",
    "glass shatter": "glass_shatter",
    "shatter": "glass_shatter",
    "fracture": "crack",
    "fractured": "crack",
    "hairline crack": "crack",
    "hairline": "crack",
    "broken screen": "crack",
    "broken display": "crack",
    "display crack": "crack",
    "screen crack": "crack",
    "scraped": "scratch",
    "scrape": "scratch",
    "scratched": "scratch",
    "scratching": "scratch",
    "scratch mark": "scratch",
    "paint scrape": "scratch",
    "paint scratch": "scratch",
    "paint chipped": "scratch",
    "paint chip": "scratch",
    "scuff": "scratch",
    "scuffed": "scratch",
    "dented": "dent",
    "dent": "dent",
    "denting": "dent",
    "ding": "dent",
    "dinged": "dent",
    "bent": "broken_part",
    "bent frame": "broken_part",
    "bent part": "broken_part",
    "detached": "missing_part",
    "fell off": "missing_part",
    "missing": "missing_part",
    "missing key": "missing_part",
    "missing part": "missing_part",
    "came off": "missing_part",
    "ripped": "torn_packaging",
    "torn": "torn_packaging",
    "tear": "torn_packaging",
    "torn open": "torn_packaging",
    "torn-open": "torn_packaging",
    "torn packaging": "torn_packaging",
    "crushed": "crushed_packaging",
    "crushed corner": "crushed_packaging",
    "crushed box": "crushed_packaging",
    "crushing": "crushed_packaging",
    "crush": "crushed_packaging",
    "liquid damage": "water_damage",
    "water stain": "water_damage",
    "water damaged": "water_damage",
    "water damage": "water_damage",
    "soaked": "water_damage",
    "wet": "water_damage",
    "coffee spill": "stain",
    "coffee stain": "stain",
    "oil stain": "stain",
    "oil mark": "stain",
    "stain": "stain",
    "stained": "stain",
    "liquid stain": "stain",
    "broken hinge": "broken_part",
    "broken part": "broken_part",
    "broken": "broken_part",
    "broke": "broken_part",
    "faulty": "broken_part",
    "damaged": "broken_part",
    "damage": "broken_part",
}

PART_NORMALIZER = {
    "back bumper": "rear_bumper",
    "rear": "rear_bumper",
    "front": "front_bumper",
    "front glass": "windshield",
    "back glass": "windshield",
    "back light": "taillight",
    "side view mirror": "side_mirror",
    "mirror": "side_mirror",
    "left mirror": "side_mirror",
    "right mirror": "side_mirror",
    "display": "screen",
    "laptop screen": "screen",
    "laptop keyboard": "keyboard",
    "keys": "keyboard",
    "keycaps": "keyboard",
    "key cap": "keyboard",
    "palm rest": "trackpad",
    "track pad": "trackpad",
    "package box": "box",
    "cardboard box": "box",
    "shipping box": "box",
    "delivery box": "box",
    "box corner": "package_corner",
    "corner": "package_corner",
    "package side": "package_side",
    "side": "package_side",
    "shipping label": "label",
    "inside": "contents",
    "product": "item",
    "item inside": "item",
    "inside item": "item",
    "broken item": "item",
    "hinge area": "hinge",
    "lid area": "lid",
    "outer lid": "lid",
    "body panel": "body",
    "outer body": "body",
    "side edge": "body",
    "car body": "body",
    "laptop body": "body",
}


def normalize_issue(raw):
    raw_lower = raw.lower().strip() if raw else ""
    if raw_lower in ISSUE_NORMALIZER:
        normalized = ISSUE_NORMALIZER[raw_lower]
        if normalized in ALLOWED_ISSUE_TYPES:
            return normalized
    if raw_lower in ALLOWED_ISSUE_TYPES:
        return raw_lower
    return "unknown"


def normalize_part(raw, claim_object):
    raw_lower = raw.lower().strip() if raw else ""
    if raw_lower in PART_NORMALIZER:
        normalized = PART_NORMALIZER[raw_lower]
        return normalized

    allowed = set()
    if claim_object == "car":
        allowed = ALLOWED_CAR_PARTS
    elif claim_object == "laptop":
        allowed = ALLOWED_LAPTOP_PARTS
    elif claim_object == "package":
        allowed = ALLOWED_PACKAGE_PARTS

    if raw_lower in allowed:
        return raw_lower

    return "unknown"
