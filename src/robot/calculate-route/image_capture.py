import cv2
import time
from datetime import datetime
import os
import requests

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

    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

    if not cap.isOpened():
        raise RuntimeError("Could not open camera.")

    # Set full resolution supported by Camera Module 3
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 4608)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 2592)

    # Warm up (autofocus, exposure)
    for _ in range(15):
        cap.read()

    time.sleep(0.2)  # Allow autofocus to settle

    ret, frame = cap.read()
    cap.release()

    if not ret:
        raise RuntimeError("Failed to capture image.")

    cv2.imwrite(image_path, frame)

    log_event(
        source="calculate-route",
        level="INFO",
        message="Image captured",
        payload={"filename": os.path.basename(image_path), "resolution": f"{frame.shape[1]}x{frame.shape[0]}"}
    )

    return image_path