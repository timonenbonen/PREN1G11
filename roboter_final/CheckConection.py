# CheckConnection.py
import os
import cv2
import numpy as np
# Stellen Sie sicher, dass der Import-Pfad korrekt ist
from roboter_final.ErkannteObjekte import Objekt
from roboter_final.YoloDetector import YoloDetector


class CheckConnection:
    def __init__(self, image_path: str, txt_path: str):
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

        self.last_punkt1 = None
        self.last_punkt2 = None

    def _lade_objekte_aus_datei(self) -> list:
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

        quadrate = [x + 5 for x in range(0, self.width - 10, 10) if np.sum(
            self.gray_image[self.height - 10:self.height, x:x + 10] < pixel_helligkeit) / 100.0 >= quadrat_threshold]
        if not quadrate:
            self.last_punkt1, self.last_punkt2 = None, None
            return 0
        punkt1 = np.array([min(quadrate, key=lambda x: abs(x - self.width / 2)), self.height - 5])

        gueltige_klassen = {"point", "pointa", "pointb", "pointc"}
        gueltige_objekte = [obj for obj in self.object_list if
                            obj.klasse in gueltige_klassen or obj.klasse == "barrier"]
        if not gueltige_objekte:
            self.last_punkt1, self.last_punkt2 = None, None
            return 0

        mittigstes_objekt = min(gueltige_objekte, key=lambda o: np.linalg.norm(
            np.array(o.zentrum) - np.array([self.width / 2, self.height / 2])))

        if mittigstes_objekt.klasse == 'barrier':
            self.last_punkt1 = punkt1
            self.last_punkt2 = np.array(mittigstes_objekt.zentrum)
            # ANNAHME: Barrier ist ein Sonderfall und wird als Status 3 zurückgegeben
            return 3

        punkt2 = np.array(mittigstes_objekt.zentrum)
        self.last_punkt1 = punkt1
        self.last_punkt2 = punkt2

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

    def get_turn_direction(self, toleranz_pixel=1000) -> str:
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
        # Kopie des Bildes erstellen, auf der wir zeichnen
        vis_image = self.image.copy()

        # --- NEU: Alle erkannten Objekte auf das Bild zeichnen ---
        # Farb-Mapping für verschiedene Objektklassen (BGR-Format)
        color_map = {
            'point': (255, 150, 0),  # Hellblau
            'pointa': (255, 150, 0),
            'pointb': (255, 150, 0),
            'pointc': (255, 150, 0),
            'barrier': (0, 100, 255),  # Dunkles Orange
            'wall': (128, 128, 128)  # Grau
        }
        default_color = (255, 0, 255)  # Magenta für unbekannte Klassen

        # Iteriere durch alle geladenen Objekte
        for obj in self.object_list:
            color = color_map.get(obj.klasse, default_color)
            x1, y1, x2, y2 = map(int, obj.bounding_box)  # In Integer umwandeln

            # Zeichne das Rechteck (Bounding Box)
            cv2.rectangle(vis_image, (x1, y1), (x2, y2), color, 2)

            # Schreibe den Klassennamen über das Rechteck
            label = obj.klasse
            label_pos = (x1, y1 - 10)
            cv2.putText(vis_image, label, label_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        # --- Ende des neuen Teils ---

        # Vorhandene Logik zum Zeichnen der Verbindungslinie (bleibt gleich)
        if self.last_punkt1 is not None:
            p1_int = self.last_punkt1.astype(int)
            # Startpunkt (unten) hervorheben
            cv2.rectangle(vis_image, (p1_int[0] - 5, p1_int[1] - 5), (p1_int[0] + 5, p1_int[1] + 5), (0, 255, 0), 2)
            cv2.circle(vis_image, tuple(p1_int), 5, (0, 255, 0), -1)

        if self.last_punkt2 is not None:
            p2_int = self.last_punkt2.astype(int)
            # Endpunkt (Zielobjekt) hervorheben
            cv2.circle(vis_image, tuple(p2_int), 10, (255, 0, 0), 2)  # Größerer Kreis für Ziel

        if self.last_punkt1 is not None and self.last_punkt2 is not None:
            line_color = {
                0: (0, 0, 255),  # Rot: Keine Verbindung
                1: (0, 255, 0),  # Grün: Verbindung OK
                2: (0, 165, 255),  # Orange: Wand blockiert
                3: (0, 255, 255)  # Gelb: Barriere als Ziel
            }.get(status_code, (0, 0, 255))  # Default auf Rot
            cv2.line(vis_image, tuple(self.last_punkt1.astype(int)), tuple(self.last_punkt2.astype(int)), line_color, 2)

        status_map = {0: "Keine Verbindung", 1: "Verbindung OK", 2: "Wand blockiert", 3: "Barriere als Ziel"}
        status_text = f"Status: {status_code} ({status_map.get(status_code, 'Unbekannt')})"

        # Text mit schwarzem Rand für bessere Lesbarkeit
        cv2.putText(vis_image, status_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(vis_image, status_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

        self._show_image("Verbindungs-Analyse", vis_image, max_display_height)

    def _show_image(self, window_title: str, image: np.ndarray, max_height: int):
        h, w = image.shape[:2]
        if h > max_height:
            ratio = w / h
            new_h = max_height
            new_w = int(new_h * ratio)
            image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        cv2.imshow(window_title, image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    # BITTE PFADE ANPASSEN
    base_path = "C:/Users/marin/PycharmProjects/PREN1G11/roboter_final/dummy_data"
    model_path = "C:/Users/marin/PycharmProjects/PREN1G11/roboter_final/my_model.pt" # Modellpfad hier definieren

    txt_path = os.path.join(base_path, "detected_objects.txt")
    img_path = os.path.join(base_path, "1a0c5f09-25ad-40fb-9b1a-a5d92b5bbb16.jpg")
    edited_path = os.path.join(base_path, "bearbeitet_1a0c5f09-25ad-40fb-9b1a-a5d92b5bbb16.png")

    # 1. BESSERER VARIABLENNAME: Nenne die Instanz z.B. "detector" statt "YoloDetector"
    detector = YoloDetector(model_path=model_path)

    # 2. KORRIGIERTER AUFRUF: Übergib nur die notwendigen Argumente.
    #    Hinweis: "object" ist ein eingebauter Name in Python, besser "detected_objects" verwenden.
    detected_objects = detector.detect(img_path)
    detector.save_to_txt(detected_objects, txt_path)


    try:
        pruefer = CheckConnection(image_path=edited_path, txt_path=txt_path)

        print("--- Analyse wird gestartet ---")
        verbindungs_status = pruefer.check_connection()
        status_map = {0: "Keine Verbindung", 1: "Verbindung OK", 2: "Wand blockiert", 3: "Barriere als Ziel"}
        print(f"Verbindungsstatus: {verbindungs_status} ({status_map.get(verbindungs_status, 'Unbekannt')})")

        print("INFO: Visualisierung der Analyse wird angezeigt...")
        pruefer.visualize_connection_analysis(verbindungs_status)

        print("\n--- Analyse abgeschlossen ---")

    except FileNotFoundError as e:
        print(f"FEHLER: Datei nicht gefunden. Bitte überprüfe die Pfade. Details: {e}")
    except Exception as e:
        print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")