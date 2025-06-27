import cv2
import numpy as np
import os


def isolate_color(img: np.ndarray,
                  bgr_color: tuple,
                  tol: int) -> np.ndarray:
    """
    Isoliert eine bestimmte Farbe im Bild und macht alle anderen Pixel weiß.

    Args:
        img: Das Eingabebild (BGR).
        bgr_color: Die zu isolierende Farbe im BGR-Format.
        tol: Die Toleranz für den Farbbereich.

    Returns:
        Das verarbeitete Bild.
    """
    # Erstelle die untere und obere Grenze für den Farbbereich, den wir BEHALTEN wollen
    low = np.array([max(c - tol, 0) for c in bgr_color], dtype=np.uint8)
    high = np.array([min(c + tol, 255) for c in bgr_color], dtype=np.uint8)

    # Erstelle eine Maske für die gewünschte Farbe.
    # Pixel innerhalb des Farbbereichs sind weiß (255), der Rest ist schwarz (0).
    keep_mask = cv2.inRange(img, low, high)

    # Um alles ANDERE zu entfernen, invertieren wir die Maske.
    # Jetzt sind alle Pixel, die NICHT die gewünschte Farbe haben, weiß (255).
    remove_mask = cv2.bitwise_not(keep_mask)

    # Erstelle eine Kopie des Bildes
    out = img.copy()
    # Wende die "Entfernen"-Maske an: Setze alle nicht-gewünschten Pixel auf weiß
    out[remove_mask != 0] = (255, 255, 255)

    return out


def process_image(input_path: str,
                  # Neuer Standard: BGR-Wert für #87b5cf
                  bgr_color=(135, 181, 207),
                  # Toleranz ggf. anpassen, 50 ist ein guter Startwert
                  tol=100):
    """
    Liest ein Bild, isoliert eine Farbe und speichert das Ergebnis.
    """
    if not os.path.isfile(input_path):
        print(f"❌ Datei nicht gefunden: {input_path}")
        return

    img = cv2.imread(input_path)
    if img is None:
        print("❌ Fehler beim Einlesen des Bildes!")
        return

    # Rufe die neue Funktion auf
    result = isolate_color(img, bgr_color, tol)

    input_dir, input_file = os.path.split(input_path)
    name, _ = os.path.splitext(input_file)
    output_path = os.path.join(input_dir, f"bearbeitet_{name}.jpg")

    if cv2.imwrite(output_path, result):
        print(f"✔ Ergebnis gespeichert unter: {output_path}")
    else:
        print("❌ Fehler beim Speichern!")

    return output_path

# Beispiel für die Verwendung (kannst du auskommentieren, wenn du das Skript anders aufrufst)
if __name__ == '__main__':
    # Ersetze 'dein_bild.jpg' mit dem Pfad zu deinem Bild
    image_to_process = 'C:/Users/marin/PycharmProjects/PREN1G11/roboter_final/dummy_data/ab7d90b3-0352-48e0-8947-e80d40e8f4a8.jpg'
    if os.path.exists(image_to_process):
        process_image(image_to_process)
    else:
        print(f"Bitte erstelle eine Datei namens '{image_to_process}' im selben Ordner"
              " oder ändere den Pfad im Code.")