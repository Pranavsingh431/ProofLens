import base64
import json

from code.core.openrouter import call_model
from code.core.config import VISION_MODEL
from code.core.models import ImageFindings

VISION_PROMPT = """You are analyzing an image for an insurance damage claim.

Object: {claim_object}
Claimed damage: {claimed_issue} on {claimed_part}

Examine the image carefully and return ONLY a JSON object with:
{{
  "object_visible": boolean,
  "visible_parts": [list of visible part names],
  "issue_detected": string or null (one of: dent, scratch, crack, glass_shatter, broken_part, missing_part, torn_packaging, crushed_packaging, water_damage, stain, none — null if nothing detected),
  "issue_severity": string (none/low/medium/high/unknown),
  "confidence": float 0.0-1.0
}}

Do NOT decide whether the claim is valid. Only describe what is visually present."""


def _encode_image(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _mime_type(path: str) -> str:
    ext = path.lower().rsplit(".", 1)[-1]
    return {"jpg": "image/jpeg", "jpeg": "image/jpeg",
            "png": "image/png", "webp": "image/webp"}.get(ext, "image/jpeg")


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
            b64 = _encode_image(image_path)
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
            data = json.loads(response)
            return ImageFindings(
                image_id=image_id,
                object_visible=bool(data.get("object_visible", False)),
                visible_parts=data.get("visible_parts", []),
                issue_detected=data.get("issue_detected"),
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
