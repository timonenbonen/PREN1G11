# image_processor.py

import os
import cv2
import numpy as np

def remove_color(img: np.ndarray,
                 bgr_color: tuple,
                 tol: int,
                 bright_thresh: int) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, bright_mask = cv2.threshold(gray, bright_thresh, 255, cv2.THRESH_BINARY)

    low = np.array([max(c - tol, 0) for c in bgr_color], dtype=np.uint8)
    high = np.array([min(c + tol, 255) for c in bgr_color], dtype=np.uint8)
    color_mask = cv2.inRange(img, low, high)

    combined = cv2.bitwise_or(color_mask, cv2.bitwise_not(bright_mask))

    out = img.copy()
    out[combined != 0] = (255, 255, 255)
    return out

def process_image(input_path: str,
                  bgr_color=(128, 64, 0),
                  tol=100,
                  bright=178) -> str:
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"❌ Datei nicht gefunden: {input_path}")

    img = cv2.imread(input_path)
    if img is None:
        raise RuntimeError("❌ Fehler beim Einlesen des Bildes!")

    result = remove_color(img, bgr_color, tol, bright)

    input_dir, input_file = os.path.split(input_path)
    name, _ = os.path.splitext(input_file)
    output_path = os.path.join(input_dir, f"bearbeitet_{name}.jpg")

    if not cv2.imwrite(output_path, result):
        raise RuntimeError("❌ Fehler beim Speichern des bearbeiteten Bildes!")

    return output_path