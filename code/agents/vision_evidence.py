import base64
import json

from code.core.openrouter import call_model
from code.core.config import VISION_MODEL
from code.core.models import ImageFindings

VISION_PROMPT = """You are a visual inspection system. Your ONLY job is to describe what you observe in this image. Do NOT decide if a claim is valid.

The claim object type is: {claim_object}
The claimed damage type is: {claimed_issue}
The claimed part is: {claimed_part}

Examine the image and return a JSON object:
  object_visible: boolean (is a {claim_object} visible?)
  visible_parts: list of strings (which parts of the object are visible?)
  issue_detected: string or null (what damage is visible, if any?)
  issue_severity: "none" | "low" | "medium" | "high" | "unknown"
  confidence: float 0.0-1.0 (how clearly can you see the claimed part?)

Return ONLY the JSON. No explanations."""


class VisionEvidenceAgent:
    @staticmethod
    def _encode_image(image_path: str) -> str:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    async def run(
        self, image_path: str, claim_object: str, claimed_issue: str, claimed_part: str
    ) -> ImageFindings:
        b64 = self._encode_image(image_path)
        messages = [
            {
                "role": "system",
                "content": VISION_PROMPT.format(
                    claim_object=claim_object,
                    claimed_issue=claimed_issue,
                    claimed_part=claimed_part,
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                    }
                ],
            },
        ]
        response = await call_model(VISION_MODEL, messages, temperature=0.1)
        data = json.loads(response)
        image_id = image_path.split("/")[-1].split(".")[0]
        return ImageFindings(
            image_id=image_id,
            object_visible=data.get("object_visible", False),
            visible_parts=data.get("visible_parts", []),
            issue_detected=data.get("issue_detected"),
            issue_severity=data.get("issue_severity", "unknown"),
            confidence=float(data.get("confidence", 0.0)),
        )
