import cv2
import numpy as np

MIN_DIMENSION = 64   # pixels — below this the image is too small for any analysis
BLUR_THRESHOLD = 5.0  # Laplacian variance below this = extreme blur


def precheck_image(path: str) -> dict:
    """
    OpenCV pre-check before any VLM call.

    Returns a dict:
        valid      : bool
        reason     : str  ("passed" | "corrupt_or_unreadable" | "too_small" | "extreme_blur")
        dimensions : tuple (height, width)  — (0, 0) when unreadable
    """
    try:
        img = cv2.imread(path)
        if img is None:
            return {"valid": False, "reason": "corrupt_or_unreadable", "dimensions": (0, 0)}

        h, w = img.shape[:2]

        if h < MIN_DIMENSION or w < MIN_DIMENSION:
            return {"valid": False, "reason": "too_small", "dimensions": (h, w)}

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        if lap_var < BLUR_THRESHOLD:
            return {"valid": False, "reason": "extreme_blur", "dimensions": (h, w)}

        return {"valid": True, "reason": "passed", "dimensions": (h, w)}

    except Exception:
        return {"valid": False, "reason": "corrupt_or_unreadable", "dimensions": (0, 0)}
