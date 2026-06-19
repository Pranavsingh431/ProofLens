import cv2
import numpy as np
from typing import Dict


def precheck_image(path: str) -> Dict:
    img = cv2.imread(path)
    if img is None:
        return {"valid": False, "reason": "corrupt_or_unreadable"}
    h, w = img.shape[:2]
    if h < 64 or w < 64:
        return {"valid": False, "reason": "too_small"}
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    if laplacian_var < 50:
        return {"valid": False, "reason": "extremely_blurry"}
    return {"valid": True, "reason": "passed", "dimensions": f"{w}x{h}"}
