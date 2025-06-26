import os
import cv2
import numpy as np

from ErkannteObjekte import Objekt

# ... (Globale Variablen und Pfade) ...
YoloObjects = []
dummy_path = "C:/Users/marin/PycharmProjects/PREN1G11/scripts/roboter_final/dummy_data/F.txt"
dummy_picture = "C:/Users/marin/PycharmProjects/PREN1G11/scripts/roboter_final/dummy_data/edited_F.jpg"


def lade_objekte_in_globale_liste(filepath: str):
    global YoloObjects
    try:
        with open(filepath, 'r') as file:
            content = file.read()
        YoloObjects = Objekt.parse_text_to_objects(content)
        print(f"INFO: Globale Liste 'YoloObjects' wurde mit {len(YoloObjects)} Objekten gefüllt.")
    except Exception as e:
        print(f"FEHLER: {e}")
        YoloObjects = []



def _linien_schneiden(p1, p2, q1, q2) -> bool:
    """Prüft, ob sich die Liniensegmente p1-p2 und q1-q2 schneiden."""

    def ccw(A, B, C): return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

    return ccw(p1, q1, q2) != ccw(p2, q1, q2) and ccw(p1, p2, q1) != ccw(p1, p2, q2)


def check_wall_on_track(punkt1: np.ndarray, punkt2: np.ndarray, objekte_liste: list) -> bool:
    """
    Prüft, ob die direkte Linie zwischen punkt1 und punkt2 von einem 'wall'-Objekt gekreuzt wird.
    """
    walls = [obj for obj in objekte_liste if obj.klasse == 'wall']
    if not walls: return False

    for wall in walls:
        wx1, wy1, wx2, wy2 = wall.bounding_box
        wall_ecken = [np.array([wx1, wy1]), np.array([wx2, wy1]), np.array([wx2, wy2]), np.array([wx1, wy2])]
        wall_kanten = [(wall_ecken[i], wall_ecken[(i + 1) % 4]) for i in range(4)]
        for kante_start, kante_end in wall_kanten:
            if _linien_schneiden(punkt1, punkt2, kante_start, kante_end):
                print(f"INFO: Kollision! Verbindung wird von Wand bei {wall.zentrum} blockiert.")
                return True
    return False


# --- HAUPTFUNKTION ---

# Umbenannt nach deiner Vorgabe
def check_connection(
        image_path: str,
        objekte_liste: list,
        quadrat_threshold: float = 0.2,
        balken_threshold: float = 0.4,
        pixel_helligkeit: int = 255,
        balken_breite: int = 10
) -> int:
    image = cv2.imread(image_path)
    if image is None: return 0

    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    height, width = gray_image.shape

    # --- 1. Finde Punkt 1 (unten) ---
    gueltige_quadrate_x = [x + 5 for x in range(0, width - 10, 10) if np.sum(
        gray_image[height - 10:height, x:x + 10] < pixel_helligkeit) / 100.0 >= quadrat_threshold]
    if not gueltige_quadrate_x: return 0
    punkt1 = np.array([min(gueltige_quadrate_x, key=lambda x: abs(x - width / 2)), height - 5])

    # --- 2. Finde Punkt 2 (mittigstes Objekt) ---
    if not objekte_liste: return 0
    punkt2 = np.array(min(objekte_liste, key=lambda obj: np.linalg.norm(
        np.array(obj.zentrum) - np.array([width / 2, height / 2]))).zentrum)

    # --- 3. Prüfe den Verbindungbalken ---
    vektor = punkt2 - punkt1
    laenge = np.linalg.norm(vektor)
    if laenge == 0: return 1

    einheitsvektor, normalenvektor = vektor / laenge, np.array([-vektor[1], vektor[0]]) / laenge

    nicht_weisse_pixel = sum(1 for t in range(int(laenge)) for w in range(-balken_breite // 2, balken_breite // 2 + 1)
                             if 0 <= int(punkt1[0] + t * einheitsvektor[0] + w * normalenvektor[0]) < width and
                             0 <= int(punkt1[1] + t * einheitsvektor[1] + w * normalenvektor[1]) < height and
                             gray_image[int(punkt1[1] + t * einheitsvektor[1] + w * normalenvektor[1]), int(
                                 punkt1[0] + t * einheitsvektor[0] + w * normalenvektor[0])] < pixel_helligkeit)

    balken_ratio = nicht_weisse_pixel / (int(laenge) * balken_breite) if laenge > 0 else 0

    # --- 4. Entscheidung treffen ---
    if balken_ratio >= balken_threshold:
        if check_wall_on_track(punkt1, punkt2, objekte_liste):
            return 2  # Verbindung existiert, aber blockiert
        else:
            return 1  # Verbindung existiert und ist frei
    else:
        return 0


# --- Beispiel für die Verwendung ---
if __name__ == "__main__":
    lade_objekte_in_globale_liste(dummy_path)

    if YoloObjects:
        # Rufe die Funktion mit dem korrekten Namen auf
        verbindungs_status = check_connection(dummy_picture, YoloObjects)

        status_map = {0: "Keine Verbindung gefunden.", 1: "Verbindung OK.", 2: "Verbindung durch Wand blockiert."}
        print(f"\n--- ERGEBNIS ---\nStatus: {verbindungs_status} ({status_map.get(verbindungs_status, 'Unbekannt')})")