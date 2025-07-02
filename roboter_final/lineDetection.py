import cv2
import numpy as np
import os


def replace_colors_with_white(img, bgr_colors, tol):
    """
    Ersetzt zuerst reine Weißpixel mit einem weicheren Farbton,
    dann ersetzt die angegebenen Farben durch echtes Weiß.

    Args:
        img: Das Eingabebild (BGR-Format von OpenCV).
        bgr_colors: Eine LISTE von zu entfernenden Farben,
                    jedes als BGR-Tupel (Blau, Grün, Rot).
        tol: Die Toleranz, wie stark andere Farben abweichen dürfen.

    Returns:
        Ein neues Bild im BGR-Format, bei dem die Farben durch Weiß ersetzt wurden.
    """

    # 1️⃣ Reines Weiß (255,255,255) zuerst durch soften Farbton ersetzen
    result_img = img.copy()
    white_pixels = np.all(result_img > 250, axis=-1)
    result_img[white_pixels] = [231,252,254]  # weichere Farbe

    # 2️⃣ Maske aufbauen für alle Ziel-Farben
    master_mask = np.zeros(result_img.shape[:2], dtype=np.uint8)

    for bgr_color in bgr_colors:
        lower = np.clip(np.array(bgr_color, dtype=np.int32) - tol, 0, 255).astype(np.uint8)
        upper = np.clip(np.array(bgr_color, dtype=np.int32) + tol, 0, 255).astype(np.uint8)

        temp_mask = cv2.inRange(result_img, lower, upper)
        master_mask = cv2.bitwise_or(master_mask, temp_mask)

    # 3️⃣ Ziel-Farben durch pures Weiß ersetzen
    result_img[master_mask > 0] = [255, 255, 255]

    return result_img


def process_image(input_path: str,
                  # NEU: Liste mit deinen zwei spezifischen Farben
                  bgr_colors=[
                      (135, 115, 100),    # BGR für RGB(109, 125, 148)
                      (51, 59, 76)         # BGR für RGB(76, 59, 51)
                  ],
                  # NEU: Viel kleinere, sinnvollere Standard-Toleranz
                  tol=95):
    """
    Liest ein Bild, ruft die Funktion zum Ersetzen der Farben auf und speichert das Ergebnis.
    """
    if not os.path.isfile(input_path):
        print(f"❌ Datei nicht gefunden: {input_path}")
        return

    img = cv2.imread(input_path)
    if img is None:
        print("❌ Fehler beim Einlesen des Bildes!")
        return

    resultat = replace_colors_with_white(img, bgr_colors, tol)

    input_dir, input_file = os.path.split(input_path)
    name, ext = os.path.splitext(input_file)

    output_path = os.path.join(input_dir, f"bearbeitet_{name}.png")

    if cv2.imwrite(output_path, resultat):
        print(f"✔ Ergebnis mit weiß ersetzten Farben gespeichert unter: {output_path}")
    else:
        print("❌ Fehler beim Speichern!")

    return output_path


# Beispiel für die Verwendung
if __name__ == '__main__':
    image_to_process = 'C:/Users/timon/hslu/4sem/Pren1/PREN1G11/roboter_final/dummy_data/G.jpg'
    if os.path.exists(image_to_process):
        # Der Aufruf verwendet jetzt die neuen Standardeinstellungen (deine Farben, kleine Toleranz).
        # Du kannst die Toleranz hier immer noch überschreiben, falls nötig.
        # z.B. process_image(image_to_process, tol=15)
        process_image(image_to_process)
    else:
        print(f"Bitte erstelle eine Datei namens '{os.path.basename(image_to_process)}'"
              " oder ändere den Pfad im Code.")