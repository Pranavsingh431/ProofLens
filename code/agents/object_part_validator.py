VALID_OBJECT_PARTS = {
    "car": {"front_bumper", "rear_bumper", "door", "hood", "windshield",
            "side_mirror", "headlight", "taillight", "fender",
            "quarter_panel", "body", "unknown"},
    "laptop": {"screen", "keyboard", "trackpad", "hinge", "lid",
               "corner", "port", "base", "body", "unknown"},
    "package": {"box", "package_corner", "package_side", "seal",
                "label", "contents", "item", "unknown"}
}

VALID_ISSUES = {
    "dent", "scratch", "crack", "glass_shatter", "broken_part",
    "missing_part", "torn_packaging", "crushed_packaging",
    "water_damage", "stain", "none", "unknown"
}


def validate_part(object_type: str, part: str) -> str:
    valid_parts = VALID_OBJECT_PARTS.get(object_type, {"unknown"})
    return part if part in valid_parts else "unknown"


def validate_issue(object_type: str, issue: str) -> str:
    return issue if issue in VALID_ISSUES else "unknown"