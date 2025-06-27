# CheckConnection.py
import os
import cv2
import numpy as np
from ErkannteObjekte import Objekt


class CheckConnection:
    def __init__(self, image_path: str, txt_path: str):
        # ... (Konstruktor bleibt gleich) ...
        self.image_path = image_path
        self.txt_path = txt_path
        self.image = cv2.imread(self.image_path)
        if self.image is None:
            raise FileNotFoundError(f"Bild konnte nicht unter '{self.image_path}' geladen werden.")
        self.height, self.width, _ = self.image.shape
        self.gray_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        self.object_list = self._lade_objekte_aus_datei()
        if not self.object_list:
            print(f"WARNUNG: Keine Objekte aus '{self.txt_path}' geladen.")

        # KORREKTUR: Attribute hier initialisieren, um Fehler zu vermeiden
        self.last_punkt1 = None
        self.last_punkt2 = None

    def _lade_objekte_aus_datei(self) -> list:
        # ... (bleibt unverändert) ...
        try:
            with open(self.txt_path, 'r') as file:
                content = file.read()
            return Objekt.parse_text_to_objects(content)
        except Exception as e:
            print(f"FEHLER beim Laden der Objekte: {e}")
            return []

    def check_connection(self, quadrat_threshold=0.2, balken_threshold=0.4, pixel_helligkeit=255,
                         balken_breite=10) -> int:
        if not self.object_list:
            self.last_punkt1, self.last_punkt2 = None, None
            return 0

        # Finde das "gefüllteste" Quadrat unten im Bild
        quadrate = [x + 5 for x in range(0, self.width - 10, 10) if np.sum(
            self.gray_image[self.height - 10:self.height, x:x + 10] < pixel_helligkeit) / 100.0 >= quadrat_threshold]
        if not quadrate:
            self.last_punkt1, self.last_punkt2 = None, None
            return 0
        punkt1 = np.array([min(quadrate, key=lambda x: abs(x - self.width / 2)), self.height - 5])

        # Nur gültige Zielobjekte berücksichtigen
        gueltige_klassen = {"point", "pointa", "pointb", "pointc"}
        gueltige_objekte = [obj for obj in self.object_list if
                            obj.klasse in gueltige_klassen or obj.klasse == "barrier"]
        if not gueltige_objekte:
            self.last_punkt1, self.last_punkt2 = None, None
            return 0

        # Mittigstes gültiges Objekt finden
        mittigstes_objekt = min(gueltige_objekte, key=lambda o: np.linalg.norm(
            np.array(o.zentrum) - np.array([self.width / 2, self.height / 2])))

        # Falls es eine Barriere ist: Status 3
        if mittigstes_objekt.klasse == 'barrier':
            self.last_punkt1 = punkt1
            self.last_punkt2 = np.array(mittigstes_objekt.zentrum)
            return 3

        punkt2 = np.array(mittigstes_objekt.zentrum)
        self.last_punkt1 = punkt1
        self.last_punkt2 = punkt2

        # Verbindung prüfen
        vektor = punkt2 - punkt1
        laenge = np.linalg.norm(vektor)
        if laenge == 0:
            return 1
        einheitsvektor = vektor / laenge
        normalenvektor = np.array([-vektor[1], vektor[0]]) / laenge

        nicht_weisse_pixel = sum(
            1 for t in range(int(laenge)) for w in range(-balken_breite // 2, balken_breite // 2 + 1)
            if 0 <= int(punkt1[0] + t * einheitsvektor[0] + w * normalenvektor[0]) < self.width and
            0 <= int(punkt1[1] + t * einheitsvektor[1] + w * normalenvektor[1]) < self.height and
            self.gray_image[int(punkt1[1] + t * einheitsvektor[1] + w * normalenvektor[1]),
            int(punkt1[0] + t * einheitsvektor[0] + w * normalenvektor[0])] < pixel_helligkeit)

        balken_ratio = nicht_weisse_pixel / (int(laenge) * balken_breite) if laenge > 0 else 0
        if balken_ratio >= balken_threshold:
            return 2 if self.check_wall_on_track(punkt1, punkt2) else 1
        return 0

    def _linien_schneiden(self, p1, p2, q1, q2) -> bool:
        def ccw(A, B, C): return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

        return ccw(p1, q1, q2) != ccw(p2, q1, q2) and ccw(p1, p2, q1) != ccw(p1, p2, q2)

    def check_wall_on_track(self, punkt1: np.ndarray, punkt2: np.ndarray) -> bool:
        walls = [obj for obj in self.object_list if obj.klasse == 'wall']
        if not walls: return False
        for wall in walls:
            wx1, wy1, wx2, wy2 = wall.bounding_box
            wall_ecken = [np.array([wx1, wy1]), np.array([wx2, wy1]), np.array([wx2, wy2]), np.array([wx1, wy2])]
            wall_kanten = [(wall_ecken[i], wall_ecken[(i + 1) % 4]) for i in range(4)]
            for kante_start, kante_end in wall_kanten:
                if self._linien_schneiden(punkt1, punkt2, kante_start, kante_end): return True
        return False

    def get_turn_direction(self, toleranz_pixel=10) -> str:
        if not self.object_list: return "unbekannt"
        mittigstes_objekt = min(self.object_list, key=lambda o: np.linalg.norm(
            np.array(o.zentrum) - np.array([self.width / 2, self.height / 2])))
        objekt_x = mittigstes_objekt.zentrum[0]
        bildmitte_x = self.width / 2
        if objekt_x < bildmitte_x - (toleranz_pixel / 2):
            return "links"
        elif objekt_x > bildmitte_x + (toleranz_pixel / 2):
            return "rechts"
        else:
            return "mitte"

    def visualize_connection_analysis(self, status_code: int, max_display_height=600):
        if self.last_punkt1 is None and self.last_punkt2 is None:
            print("INFO: Keine Analyse zum Visualisieren vorhanden. Führe erst 'check_connection' aus.")
            return
        vis_image = self.image.copy()
        if self.last_punkt1 is not None:
            p1_int = self.last_punkt1.astype(int)
            cv2.rectangle(vis_image, (p1_int[0] - 5, p1_int[1] - 5), (p1_int[0] + 5, p1_int[1] + 5), (0, 255, 0), 2)
            cv2.circle(vis_image, tuple(p1_int), 5, (0, 255, 0), -1)
        if self.last_punkt2 is not None:
            p2_int = self.last_punkt2.astype(int)
            cv2.circle(vis_image, tuple(p2_int), 5, (255, 0, 0), -1)
        if self.last_punkt1 is not None and self.last_punkt2 is not None:
            line_color = {0: (0, 0, 255), 1: (0, 255, 0), 2: (0, 165, 255)}.get(status_code, (0, 0, 255))
            cv2.line(vis_image, tuple(self.last_punkt1.astype(int)), tuple(self.last_punkt2.astype(int)), line_color, 2)
        status_map = {0: "Keine Verbindung", 1: "Verbindung OK", 2: "Wand blockiert"}
        status_text = f"Status: {status_code} ({status_map.get(status_code, 'Unbekannt')})"
        cv2.putText(vis_image, status_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(vis_image, status_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        self._show_image("Verbindungs-Analyse", vis_image, max_display_height)

    def _show_image(self, window_title: str, image: np.ndarray, max_height: int):
        h, w, _ = image.shape
        if h > max_height:
            ratio = w / h
            new_h = max_height
            new_w = int(new_h * ratio)
            image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        cv2.imshow(window_title, image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    txt_path = "C:/Users/marin/PycharmProjects/PREN1G11/scripts/roboter_final/dummy_data/C.txt"
    img_path = "C:/Users/marin/PycharmProjects/PREN1G11/scripts/roboter_final/dummy_data/edited_C.jpg"

    try:
        pruefer = CheckConnection(image_path=img_path, txt_path=txt_path)

        print("--- Analyse wird gestartet ---")
        verbindungs_status = pruefer.check_connection()
        status_map = {0: "Keine Verbindung", 1: "Verbindung OK", 2: "Wand blockiert"}
        print(f"Verbindungsstatus: {verbindungs_status} ({status_map.get(verbindungs_status)})")

        print("INFO: Visualisierung der Analyse wird angezeigt...")
        pruefer.visualize_connection_analysis(verbindungs_status)

        print("\n--- Analyse abgeschlossen ---")

    except Exception as e:
        print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")