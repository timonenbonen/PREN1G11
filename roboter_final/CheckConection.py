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

    def extract_blue_lines(self, image_bgr):
        hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
        # Pale greenish/cyan lines (first color)
        lower1 = np.array([65, 20, 200])
        upper1 = np.array([95, 60, 255])

        # Pale turquoise/gray-green lines (second color)
        lower2 = np.array([25, 20, 190])
        upper2 = np.array([40, 70, 235])

        mask1 = cv2.inRange(hsv, lower1, upper1)
        mask2 = cv2.inRange(hsv, lower2, upper2)

        # Combine both
        combined_mask = cv2.bitwise_or(mask1, mask2)
        return cv2.inRange(hsv, lower1, upper1)

    def detect_lines(self, mask):
        edges = cv2.Canny(mask, 50, 150)
        return cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=50, minLineLength=30, maxLineGap=10)

    def line_to_angle_and_center(self, x1, y1, x2, y2):
        angle = np.degrees(np.arctan2(y2 - y1, x2 - x1)) % 180
        center = ((x1 + x2) / 2, (y1 + y2) / 2)
        return angle, center

    def merge_similar_lines(self, lines, angle_thresh=5.0, dist_thresh=1000.0):
        if lines is None:
            return []

        merged = []
        used = [False] * len(lines)

        for i in range(len(lines)):
            if used[i]:
                continue

            x1_i, y1_i, x2_i, y2_i = lines[i][0]
            angle_i, center_i = self.line_to_angle_and_center(x1_i, y1_i, x2_i, y2_i)
            group = [(x1_i, y1_i, x2_i, y2_i)]
            used[i] = True

            for j in range(i + 1, len(lines)):
                if used[j]:
                    continue

                x1_j, y1_j, x2_j, y2_j = lines[j][0]
                angle_j, center_j = self.line_to_angle_and_center(x1_j, y1_j, x2_j, y2_j)

                angle_diff = min(abs(angle_i - angle_j), 180 - abs(angle_i - angle_j))
                dist = np.hypot(center_i[0] - center_j[0], center_i[1] - center_j[1])

                if angle_diff < angle_thresh and dist < dist_thresh:
                    group.append((x1_j, y1_j, x2_j, y2_j))
                    used[j] = True

            # Fit a line through all points in the group
            points = []
            for x1, y1, x2, y2 in group:
                points.append((x1, y1))
                points.append((x2, y2))
            points = np.array(points, dtype=np.int32)

            if len(points) >= 2:
                [vx, vy, x0, y0] = cv2.fitLine(points, cv2.DIST_L2, 0, 0.01, 0.01)
                vx, vy = float(vx), float(vy)
                x0, y0 = float(x0), float(y0)

                # Project line far in both directions using the bounding box of points
                left = min(points[:, 0])
                right = max(points[:, 0])
                top = min(points[:, 1])
                bottom = max(points[:, 1])

                # Extend line horizontally
                x1 = int(left)
                y1 = int(y0 + (x1 - x0) * (vy / vx))

                x2 = int(right)
                y2 = int(y0 + (x2 - x0) * (vy / vx))

                merged.append((x1, y1, x2, y2))

        return merged

    def draw_lines(self, image, lines):
        output = image.copy()
        for x1, y1, x2, y2 in lines:
            cv2.line(output, (x1, y1), (x2, y2), (0, 0, 255), 2)
        return output

    def do_lines_intersect(self, p1, p2, q1, q2):
        def ccw(a, b, c):
            return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])

        return ccw(p1, q1, q2) != ccw(p2, q1, q2) and ccw(p1, p2, q1) != ccw(p1, p2, q2)

    def do_line_and_box_intersect(self, line, box):
        """
        Check if a line (x1, y1, x2, y2) intersects a box (x1, y1, x2, y2)
        """
        lx1, ly1, lx2, ly2 = line
        bx1, by1, bx2, by2 = box

        # Four edges of the box as line segments
        box_edges = [
            (bx1, by1, bx2, by1),  # Top
            (bx2, by1, bx2, by2),  # Right
            (bx2, by2, bx1, by2),  # Bottom
            (bx1, by2, bx1, by1),  # Left
        ]

        for ex1, ey1, ex2, ey2 in box_edges:
            if self.do_lines_intersect((lx1, ly1), (lx2, ly2), (ex1, ey1), (ex2, ey2)):
                return True
        return False

    def check_connection(self, original_image):
        original = cv2.imread(original_image)
        height, width = original.shape[:2]
        mask = self.extract_blue_lines(self.image)
        raw_lines = self.detect_lines(mask)
        merged_lines = self.merge_similar_lines(raw_lines)
        bottom_threshold = int(height * 0.9)  # Only lines with a point below this y-coordinate

        filtered_lines = []

        for x1, y1, x2, y2 in merged_lines:
            if y1 >= bottom_threshold or y2 >= bottom_threshold:
                filtered_lines.append((x1, y1, x2, y2))
        # Step 3: Scan intersections
        point_hit = False
        wall_hit = False

        for obj in self.object_list:
            obj_type = obj.klasse

            box = obj.bounding_box
            print(f"object_type: {obj_type} bounding_box: {box}")
            # Barrier on a point (check for complete overlap)
            if obj_type == "barrier":
                for point_obj in self.object_list:
                    print(f"point{point_obj}")
                    if point_obj.klasse.startswith("point"):
                        px1, py1, px2, py2 = point_obj.bounding_box
                        print(f"point coordinates{px1, py1, px2, py2}")
                        bx1, by1, bx2, by2 = box
                        print(f"point coordinates{bx1, by1, bx2, by2}")


                        if (
                                bx1 <= px1 <= bx2 and bx1 <= px2 <= bx2 and
                                by1 <= py1 <= by2 and by1 <= py2 <= by2
                        ):
                            return 3  # Barrier overlaps a point

            # Check line intersections
            if obj_type.startswith("point") or obj_type == "wall":
                for line in filtered_lines:
                    if self.do_line_and_box_intersect(line, box):
                        if obj_type.startswith("point"):
                            point_hit = True
                        elif obj_type == "wall":
                            wall_hit = True

        # Final logic based on flags
        if point_hit and wall_hit:
            return 2  # Point + Wall intersect with line
        elif point_hit:
            return 1  # Only point intersects with line
        else:
            return 0  # Nothing intersects


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
        verbindungs_status = pruefer.check_connection(img_path)
        status_map = {0: "Keine Verbindung", 1: "Verbindung OK", 2: "Wand blockiert", 3: "Barriere als Ziel"}
        print(f"Verbindungsstatus: {verbindungs_status} ({status_map.get(verbindungs_status, 'Unbekannt')})")

        print("INFO: Visualisierung der Analyse wird angezeigt...")
        pruefer.visualize_connection_analysis(verbindungs_status)

        print("\n--- Analyse abgeschlossen ---")

    except FileNotFoundError as e:
        print(f"FEHLER: Datei nicht gefunden. Bitte überprüfe die Pfade. Details: {e}")
    except Exception as e:
        print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")