import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATASET_DIR = os.path.join(REPO_ROOT, "dataset")

CLAIMS_CSV = os.path.join(DATASET_DIR, "claims.csv")
SAMPLE_CLAIMS_CSV = os.path.join(DATASET_DIR, "sample_claims.csv")
USER_HISTORY_CSV = os.path.join(DATASET_DIR, "user_history.csv")
EVIDENCE_REQUIREMENTS_CSV = os.path.join(DATASET_DIR, "evidence_requirements.csv")

VISION_MODEL = "google/gemini-2.5-flash"

VALID_OBJECT_TYPES = {"car", "laptop", "package"}

VALID_CLAIM_STATUS = {"supported", "contradicted", "not_enough_information"}

VALID_ISSUE_TYPES = {
    "dent", "scratch", "crack", "glass_shatter", "broken_part",
    "missing_part", "torn_packaging", "crushed_packaging",
    "water_damage", "stain", "none", "unknown"
}

VALID_CAR_PARTS = {
    "front_bumper", "rear_bumper", "door", "hood", "windshield",
    "side_mirror", "headlight", "taillight", "fender",
    "quarter_panel", "body", "unknown"
}

VALID_LAPTOP_PARTS = {
    "screen", "keyboard", "trackpad", "hinge", "lid",
    "corner", "port", "base", "body", "unknown"
}

VALID_PACKAGE_PARTS = {
    "box", "package_corner", "package_side", "seal",
    "label", "contents", "item", "unknown"
}

VALID_RISK_FLAGS = {
    "none", "blurry_image", "cropped_or_obstructed", "low_light_or_glare",
    "wrong_angle", "wrong_object", "wrong_object_part", "damage_not_visible",
    "claim_mismatch", "possible_manipulation", "non_original_image",
    "text_instruction_present", "user_history_risk", "manual_review_required"
}

VALID_SEVERITY = {"none", "low", "medium", "high", "unknown"}
