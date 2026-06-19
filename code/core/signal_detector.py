import re
from dataclasses import dataclass


INJECTION_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"(?i)system\s*prompt\s*:",
    r"(?i)you\s+are\s+a\s+claims?",
    r"(?i)approve\s+(this|the|my)\s+claim",
    r"(?i)output\s*(only|just)\s*(supported|approved)",
    r"(?i)skip\s+(manual\s+|the\s+)?(review|approval)",
    r"(?i)mark\s+(this\s+)?(row|claim)\s+(as\s+)?(supported|approved)",
    r"(?i)\bjust\s+approve\b",
    r"(?i)(any\s+)?system\s+reading\s+this\s+should",
]

THREAT_PATTERNS = [
    r"(?i)escalate\s+(publicly|to\s+social\s+media)",
    r"(?i)legal\s+action",
    r"(?i)report\s+(you|this)\s+to\s+\w+",
    r"(?i)sue|lawyer|attorney",
    r"(?i)keep\s+reopening",
]

LANGUAGE_HINTS = {
    "hi": [r"(?i)\b(hai|hain|ka|ki|ko|mein|se|par|tha|thi|the|kar|hua|huyi|kya|aap|mera|meri|hum|yeh|woh|nahi|bhi|toh|photo|photos|image|images)\b"],
    "es": [r"(?i)\b(el|la|los|las|un|una|que|por|para|con|del|está|estaba|fue|tengo|tiene|había|foto|fotos|imagen|daño|dañado)\b"],
    "zh": [r"[\u4e00-\u9fff]", r"(?i)\b(qing|ni\s+hao|wo\s+de|xie\s+xie|tai\s+hao)\b"],
}


def detect_prompt_injection(text: str) -> bool:
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text):
            return True
    return False


def detect_threat_language(text: str) -> bool:
    for pattern in THREAT_PATTERNS:
        if re.search(pattern, text):
            return True
    return False


def detect_language(text: str) -> str:
    scores = {}
    for lang, patterns in LANGUAGE_HINTS.items():
        score = 0
        for pattern in patterns:
            score += len(re.findall(pattern, text))
        if score > 0:
            scores[lang] = score
    if len(scores) >= 2:
        return "mixed"
    if scores:
        return max(scores, key=scores.get)
    return "en"


@dataclass
class SignalResult:
    prompt_injection: bool
    threat_language: bool
    language: str


class SignalDetector:
    def scan(self, text: str) -> SignalResult:
        return SignalResult(
            prompt_injection=detect_prompt_injection(text),
            threat_language=detect_threat_language(text),
            language=detect_language(text),
        )
