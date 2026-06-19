import base64
import json

from code.core.openrouter import call_model
from code.core.config import VISION_MODEL
from code.core.models import ImageFindings

VISION_PROMPT = """You are an insurance claims image analyst. Be precise and decisive.

CLAIM: A {claim_object} has a {claimed_issue} on the {claimed_part}.

Examine the image carefully and answer:
1. Is a {claim_object} visible?
2. Is the {claimed_part} visible? Look carefully — it may be partially in frame.
3. Is there any damage visible on the {claimed_part}?
4. If damage is visible, what type is it?

Return ONLY this JSON object:
{{
  "object_visible": true or false,
  "visible_parts": [list every visible part using these exact names: front_bumper, rear_bumper, door, hood, windshield, side_mirror, headlight, taillight, fender, quarter_panel, body, screen, keyboard, trackpad, hinge, lid, corner, port, base, box, package_corner, package_side, seal, label, contents, item],
  "issue_detected": "use exactly one of: dent, scratch, crack, glass_shatter, broken_part, missing_part, torn_packaging, crushed_packaging, water_damage, stain, none",
  "issue_severity": "none, low, medium, or high",
  "confidence": 0.0 to 1.0
}}

Critical rules:
- Use "none" for issue_detected when the part is visible but undamaged — NEVER use null
- Use null for issue_detected ONLY if the image is too dark/blurry to see anything meaningful
- If damage is present, pick the single closest match — do not use null
- Reflect uncertainty in the confidence score, not by returning null
- visible_parts MUST use the exact part names listed above (underscores, not spaces)"""


def _encode_image(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _mime_type(path: str) -> str:
    ext = path.lower().rsplit(".", 1)[-1]
    return {"jpg": "image/jpeg", "jpeg": "image/jpeg",
            "png": "image/png", "webp": "image/webp"}.get(ext, "image/jpeg")


def _normalize_issue(raw: str | None) -> str | None:
    """Map Gemini free-text back to a canonical issue type."""
    if raw is None:
        return None
    raw_lower = raw.lower().replace("-", " ").replace("_", " ")
    ISSUE_MAP = {
        "dent": "dent", "dented": "dent", "ding": "dent", "hail": "dent",
        "scratch": "scratch", "scratched": "scratch", "scrape": "scratch", "scuff": "scratch",
        "crack": "crack", "cracked": "crack", "fracture": "crack", "hairline": "crack",
        "glass shatter": "glass_shatter", "shatter": "glass_shatter", "shattered": "glass_shatter",
        "broken part": "broken_part", "broken": "broken_part", "snapped": "broken_part",
        "missing part": "missing_part", "missing": "missing_part", "detached": "missing_part",
        "torn packaging": "torn_packaging", "torn": "torn_packaging", "ripped": "torn_packaging",
        "crushed packaging": "crushed_packaging", "crushed": "crushed_packaging",
        "water damage": "water_damage", "water": "water_damage", "wet": "water_damage",
        "stain": "stain", "stained": "stain", "mark": "stain",
        "none": "none", "no damage": "none", "undamaged": "none",
    }
    for k, v in ISSUE_MAP.items():
        if k in raw_lower:
            return v
    # Last resort: return the raw value if it's already canonical
    CANONICAL = {"dent","scratch","crack","glass_shatter","broken_part","missing_part",
                 "torn_packaging","crushed_packaging","water_damage","stain","none"}
    canonical_attempt = raw.lower().replace(" ", "_")
    if canonical_attempt in CANONICAL:
        return canonical_attempt
    return None  # truly unrecognisable → treat as missing


class VisionEvidenceAgent:
    async def run(self, image_path: str, claim_object: str,
                  claimed_issue: str, claimed_part: str) -> ImageFindings:
        image_id = image_path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        prompt = VISION_PROMPT.format(
            claim_object=claim_object,
            claimed_issue=claimed_issue,
            claimed_part=claimed_part,
        )
        try:
            b64  = _encode_image(image_path)
            mime = _mime_type(image_path)
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url",
                         "image_url": {"url": f"data:{mime};base64,{b64}"}},
                    ],
                }
            ]
            response = await call_model(VISION_MODEL, messages, temperature=0.1,
                                        json_response=False)
            # Strip markdown code fences if Gemini wraps the JSON
            text = response.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            data = json.loads(text.strip())

            raw_issue = data.get("issue_detected")
            normalized = _normalize_issue(raw_issue)

            # Normalize visible_parts: replace spaces with underscores
            visible_parts = [
                p.strip().lower().replace(" ", "_")
                for p in data.get("visible_parts", [])
            ]

            return ImageFindings(
                image_id=image_id,
                object_visible=bool(data.get("object_visible", False)),
                visible_parts=visible_parts,
                issue_detected=normalized,
                issue_severity=data.get("issue_severity", "unknown"),
                confidence=float(data.get("confidence", 0.5)),
            )
        except Exception:
            return ImageFindings(
                image_id=image_id,
                object_visible=False,
                visible_parts=[],
                issue_detected=None,
                issue_severity="unknown",
                confidence=0.0,
            )

