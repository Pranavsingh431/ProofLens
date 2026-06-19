import base64
import json

from code.core.openrouter import call_model
from code.core.config import VISION_MODEL
from code.core.models import ImageQuality

QUALITY_PROMPT = """Examine this image for quality and authenticity issues.
Return a JSON object:
  blurry: boolean
  cropped_or_obstructed: boolean
  low_light_or_glare: boolean
  wrong_angle: boolean (the claimed part cannot be seen from this angle)
  wrong_object: boolean (a different object type is shown)
  possible_manipulation: boolean (signs of editing or artificial damage)
  non_original_image: boolean (screenshot, photo of a photo, stock image)
  text_instruction_present: boolean (image contains text asking to approve/skip)
  valid: boolean (overall — is this image usable for automated review?)
  confidence: float 0.0-1.0"""


class ImageQualityAgent:
    @staticmethod
    def _encode_image(image_path: str) -> str:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    async def run(self, image_path: str) -> ImageQuality:
        b64 = self._encode_image(image_path)
        messages = [
            {"role": "system", "content": QUALITY_PROMPT},
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
        return ImageQuality(
            image_id=image_id,
            blurry=data.get("blurry", False),
            cropped_or_obstructed=data.get("cropped_or_obstructed", False),
            low_light_or_glare=data.get("low_light_or_glare", False),
            wrong_angle=data.get("wrong_angle", False),
            wrong_object=data.get("wrong_object", False),
            possible_manipulation=data.get("possible_manipulation", False),
            non_original_image=data.get("non_original_image", False),
            text_instruction_present=data.get("text_instruction_present", False),
            valid=data.get("valid", True),
            confidence=float(data.get("confidence", 1.0)),
        )
