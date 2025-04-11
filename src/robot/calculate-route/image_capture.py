import cv2
import time
from datetime import datetime
import os
import requests

IMAGE_DIR = "/app/images"
os.makedirs(IMAGE_DIR, exist_ok=True)

def log_event(source, level, message, payload=None):
    try:
        requests.post("http://log-server:9000/log", json={
            "source": source,
            "level": level.upper(),
            "message": message,
            "payload": payload
        }, timeout=2)
    except Exception as e:
        print(f"[{source}] Logging failed: {e}")

def capture_image():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_path = os.path.join(IMAGE_DIR, f"capture_{timestamp}.jpg")

    try:
        subprocess.run([
            "libcamera-jpeg",
            "-o", image_path,
            "--width", "4608",
            "--height", "2592",
            "-t", "1"
        ], check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"libcamera-jpeg failed: {e}")

    frame = cv2.imread(image_path)
    if frame is None:
        raise RuntimeError("Failed to read image with OpenCV.")

    log_event(
        source="calculate-route",
        level="INFO",
        message="Image captured",
        payload={
            "filename": os.path.basename(image_path),
            "resolution": f"{frame.shape[1]}x{frame.shape[0]}"
        }
    )

    return image_path