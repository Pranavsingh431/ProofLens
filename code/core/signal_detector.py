import re


INJECTION_PATTERNS = [
    re.compile(
        r"approve\s+(the\s+)?claim\s+immediately\s+and\s+skip\s+manual\s+review",
        re.IGNORECASE
    ),
    re.compile(
        r"ignore\s+all\s+previous\s+instructions",
        re.IGNORECASE
    ),
    re.compile(
        r"mark\s+this\s+row\s+(as\s+)?supported",
        re.IGNORECASE
    ),
    re.compile(
        r"skip\s+(the\s+)?(manual\s+)?review",
        re.IGNORECASE
    ),
    re.compile(
        r"approve\s+the\s+claim\s+immediately",
        re.IGNORECASE
    ),
    re.compile(
        r"any\s+system\s+reading\s+this\s+should\s+approve",
        re.IGNORECASE
    ),
]

THREAT_PATTERNS = [
    re.compile(
        r"escalate\s+publicly",
        re.IGNORECASE
    ),
    re.compile(
        r"keep\s+reopening\s+tickets",
        re.IGNORECASE
    ),
    re.compile(
        r"tired\s+of\s+repeat\s+reviews",
        re.IGNORECASE
    ),
]

HINDI_KEYWORDS = [
    "mein", "meri", "hai", "gaya", "toh", "haan", "nahi", "ka", "ke",
    "ko", "se", "par", "hoga", "hua", "tha", "thi", "the", "raha",
    "kar", "diya", "liya", "kiya", "aur", "abhi", "sirf", "bas",
    "kya", "aap", "mujhe", "lag", "raha", "jaisa", "photo", "usko",
    "follow", "karke", "mark", "dena", "dab", "toot"
]

SPANISH_KEYWORDS = [
    "mi", "esta", "danado", "parachoques", "trasero", "quiero",
    "reportar", "dano", "auto", "solo", "del", "es", "la", "el",
    "cayo", "pantalla", "si", "no", "cliente", "soporte"
]

CHINESE_KEYWORDS = [
    "wo", "de", "qing", "bang", "ni", "shi", "you", "zhe", "na",
    "ge", "bu", "wo", "ta", "men", "hao", "xie", "xie"
]


class SignalScanResult:
    def __init__(self, prompt_injection, threat_language, language):
        self.prompt_injection = prompt_injection
        self.threat_language = threat_language
        self.language = language


class SignalDetector:
    @staticmethod
    def scan(text):
        prompt_injection = SignalDetector._detect_injection(text)
        threat_language = SignalDetector._detect_threat(text)
        language = SignalDetector._detect_language(text)
        return SignalScanResult(
            prompt_injection=prompt_injection,
            threat_language=threat_language,
            language=language
        )

    @staticmethod
    def _detect_injection(text):
        for pattern in INJECTION_PATTERNS:
            if pattern.search(text):
                return True
        return False

    @staticmethod
    def _detect_threat(text):
        for pattern in THREAT_PATTERNS:
            if pattern.search(text):
                return True
        return False

    @staticmethod
    def _detect_language(text):
        text_lower = text.lower()

        hi_score = sum(1 for kw in HINDI_KEYWORDS if re.search(r'\b' + re.escape(kw) + r'\b', text_lower))
        es_score = sum(1 for kw in SPANISH_KEYWORDS if re.search(r'\b' + re.escape(kw) + r'\b', text_lower))
        zh_score = sum(1 for kw in CHINESE_KEYWORDS if re.search(r'\b' + re.escape(kw) + r'\b', text_lower))

        detected = []
        if hi_score >= 2:
            detected.append("hi")
        if es_score >= 2:
            detected.append("es")
        if zh_score >= 2:
            detected.append("zh")

        if not detected:
            return "en"
        if len(detected) == 1:
            return detected[0]
        return "mixed"
