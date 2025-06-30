import subprocess
import cv2
import time

def capture_picture_from_api(save_path="../pictures/picture.jpg") -> str:
    """
    Nimmt ein Bild direkt mit libcamera-still auf.
    Rückgabe: Pfad zur Bilddatei
    """
    try:
        result = subprocess.run(
            ["libcamera-still", "-o", save_path, "--width", "1280", "--height", "720", "--nopreview"],
            check=True
        )
        print(f"📸 Bild gespeichert unter: {save_path}")
        return save_path
    except subprocess.CalledProcessError as e:
        print(f"❌ Fehler bei der Bildaufnahme: {e}")
        raise RuntimeError("Kamera konnte kein Bild aufnehmen.")

def capture_picture_from_cv2(save_path="../pictures/picture.jpg") -> str:
    print("start image capture")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Kamera konnte nicht geöffnet werden.")

    time.sleep(0.5)  # Give camera a short time to adjust exposure

    ret, frame = cap.read()
    cap.release()

    if not ret:
        raise RuntimeError("Konnte kein Bild erfassen.")

    cv2.imwrite(save_path, frame)
    print(f"📸 Bild gespeichert unter: {save_path}")
    return save_path