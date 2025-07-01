import cv2
import numpy as np
import os


def replace_color_with_white(img, bgr_color, tol):
    """
    Findet eine bestimmte Farbe in einem Bild und ersetzt sie durch Weiß.

    Args:
        img: Das Eingabebild (BGR-Format von OpenCV).
        bgr_color: Die zu entfernende Farbe als BGR-Tupel (Blau, Grün, Rot).
        tol: Die Toleranz, wie stark andere Farben abweichen dürfen.

    Returns:
        Ein neues Bild im BGR-Format, bei dem die Farbe durch Weiß ersetzt wurde.
    """
    # Berechne die untere und obere Farbgrenze für die Maske
    # np.clip stellt sicher, dass die Werte im gültigen Bereich [0, 255] bleiben
    untere_grenze = np.clip(np.array(bgr_color) - tol, 0, 255)
    obere_grenze = np.clip(np.array(bgr_color) + tol, 0, 255)

    # Erstelle eine Maske: Pixel im Farbbereich werden weiß (255), der Rest schwarz (0)
    maske = cv2.inRange(img, untere_grenze, obere_grenze)

    # Erstelle eine Kopie, um das Originalbild nicht zu verändern
    result_img = img.copy()

    # NEU: Überall, wo die Maske nicht-null ist (d.h. die Farbe gefunden wurde),
    # werden die Pixel im Ergebnisbild auf Weiß gesetzt.
    # Weiß in BGR ist (255, 255, 255)
    result_img[maske > 0] = [255, 255, 255]

    return result_img


def process_image(input_path: str,
                  # Dein BGR-Wert für RGB(128, 64, 0)
                  # OpenCV verwendet BGR, also ist RGB(128, 64, 0) -> BGR(0, 64, 128)
                  # Ich lasse deinen Wert (128, 64, 0) drin, falls das gewollt ist.
                  bgr_color=(0, 64, 128),
                  # Toleranz wie gewünscht
                  tol=150):
    """
    Liest ein Bild, ruft die Funktion zum Ersetzen der Farbe auf und speichert das Ergebnis.
    """
    if not os.path.isfile(input_path):
        print(f"❌ Datei nicht gefunden: {input_path}")
        return

    img = cv2.imread(input_path)
    if img is None:
        print("❌ Fehler beim Einlesen des Bildes!")
        return

    # Rufe die Funktion auf, um die Farbe durch Weiß zu ersetzen
    resultat = replace_color_with_white(img, bgr_color, tol)

    input_dir, input_file = os.path.split(input_path)
    name, ext = os.path.splitext(input_file)

    # Du kannst jetzt auch als .jpg speichern, da keine Transparenz mehr nötig ist.
    # PNG funktioniert aber weiterhin problemlos.
    output_path = os.path.join(input_dir, f"bearbeitet_{name}.png")

    if cv2.imwrite(output_path, resultat):
        print(f"✔ Ergebnis mit weiß ersetzter Farbe gespeichert unter: {output_path}")
    else:
        print("❌ Fehler beim Speichern!")

    return output_path


# Beispiel für die Verwendung
if __name__ == '__main__':
    image_to_process = 'C:/Users/marin/PycharmProjects/PREN1G11/roboter_final/dummy_data/1a0c5f09-25ad-40fb-9b1a-a5d92b5bbb16.jpg'
    if os.path.exists(image_to_process):
        # Wichtiger Hinweis zur Farbe:
        # Dein Kommentar sagte RGB(128, 64, 0).
        # OpenCV liest Bilder im BGR-Format.
        # RGB(128, 64, 0) ist also BGR(0, 64, 128).
        # Ich habe das im Funktionsaufruf unten korrigiert.
        process_image(image_to_process, bgr_color=(0, 64, 128), tol=150)
    else:
        print(f"Bitte erstelle eine Datei namens '{image_to_process}' im selben Ordner"
              " oder ändere den Pfad im Code.")