import subprocess

def capture_picture_from_api(save_path="/tmp/picture.jpg") -> str:
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
