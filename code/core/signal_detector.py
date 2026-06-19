import re

INJECTION_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"(?i)system\s*prompt\s*:",
    r"(?i)you\s+are\s+a\s+claims?",
    r"(?i)approve\s+this\s+claim",
    r"(?i)output\s*(only|just)\s*(supported|approved)",
    r"(?i)skip\s+manual\s+review",
]

THREAT_PATTERNS = [
    r"(?i)escalate\s+(publicly|to\s+social\s+media)",
    r"(?i)legal\s+action",
    r"(?i)report\s+(you|this)\s+to\s+\w+",
    r"(?i)sue|lawyer|attorney",
]

LANGUAGE_HINTS = {
    "hi": [r"(?i)\b(hai|hain|ka|ki|ko|mein|se|par|tha|thi|the|kar|hua|huyi|kya|aap|mera|meri|hum|yeh|woh|nahi|bhi|toh|photo|photos|image|images)\b"],
    "es": [r"(?i)\b(el|la|los|las|un|una|que|por|para|con|del|las?|está|estaba|fue|tengo|tiene|había|foto|fotos|imagen|imágenes|daño|dañado)\b"],
    "zh": [r"[\u4e00-\u9fff]"],
}


def detect_prompt_injection(text):
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text):
            return True
    return False


def detect_threat_language(text):
    for pattern in THREAT_PATTERNS:
        if re.search(pattern, text):
            return True
    return False


def detect_language(text):
    scores = {}
    for lang, patterns in LANGUAGE_HINTS.items():
        score = 0
        for pattern in patterns:
            score += len(re.findall(pattern, text))
        if score > 0:
            scores[lang] = score
    if scores:
        return max(scores, key=scores.get)
    return "en"
