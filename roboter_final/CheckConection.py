import cv2
import numpy as np
import os
from shapely.geometry import LineString, box


# Eine Dummy-Klasse, um Ihre 'Objekt'-Klasse für das Beispiel zu simulieren
# In Ihrem Projekt würden Sie 'from roboter_final.ErkannteObjekte import Objekt' verwenden
class DummyObjekt:
    def __init__(self, typ, bbox, center):
        self.typ = typ
        self.bbox = bbox
        self.center = center

    def __repr__(self):
        return f"Objekt(typ='{self.typ}', center={self.center})"


# HILFSFUNKTION: Parst die Objektdaten aus einem String (simuliert das Lesen aus einer .txt-Datei)
def parse_objects_from_string(data_string):
    """
    Parst einen mehrzeiligen String im Format 'typ;%;bbox;area;center;'
    und gibt eine Liste von DummyObjekt-Instanzen zurück.
    """
    parsed_objects = []
    for line in data_string.strip().split('\n'):
        line = line.strip()
        if not line:
            continue

        try:
            parts = line.strip(';').split(';')
            if len(parts) < 5:
                continue

            typ = parts[0]

            # Bounding Box: (x1, y1, x2, y2)
            bbox_str = parts[2].strip('()')
            bbox = tuple(map(int, bbox_str.split(',')))

            # Zentrum: (cx, cy) - Konvertiert von Float zu Integer für cv2-Funktionen
            center_str = parts[4].strip('()')
            center = tuple(int(float(c)) for c in center_str.split(','))

            parsed_objects.append(DummyObjekt(typ=typ, bbox=bbox, center=center))
        except (ValueError, IndexError) as e:
            print(f"Warnung: Konnte Zeile nicht parsen: '{line}' - Fehler: {e}")

    return parsed_objects


class CheckConnection:
    """
    Diese Klasse analysiert ein Bild auf eine Verbindung zwischen einem Startpunkt
    am Boden und einem der erkannten Objekte. Sie kann das Ergebnis auch visualisieren.
    """

    def __init__(self, image_with_lines_path, original_image_path, object_list):
        self.image_with_lines_path = image_with_lines_path
        self.original_image_path = original_image_path
        self.image_for_analysis = cv2.imread(self.image_with_lines_path, cv2.IMREAD_GRAYSCALE)
        if self.image_for_analysis is None:
            raise FileNotFoundError(f"Analyse-Bild konnte nicht geladen werden: {self.image_with_lines_path}")
        self.image_for_visualization = cv2.imread(self.original_image_path)
        if self.image_for_visualization is None:
            raise FileNotFoundError(f"Visualisierungs-Bild konnte nicht geladen werden: {self.original_image_path}")
        self.height, self.width = self.image_for_analysis.shape
        self.all_objects = self._parse_objects(object_list)
        self._reset_analysis_state()

    def _reset_analysis_state(self):
        self.start_point = None
        self.candidate_objects = []
        self.winning_object = None
        self.is_wall_collision = False
        self.bottom_grid_squares = []

    def _parse_objects(self, object_list):
        parsed = []
        for obj in object_list:
            if isinstance(obj, dict):
                parsed.append(obj)
            else:
                parsed.append({
                    'type': obj.typ if hasattr(obj, 'typ') else obj.type,
                    'bbox': obj.bbox,
                    'center': obj.center
                })
        return parsed

    def _find_bottom_target_point(self, weiss_schwelle):
        self.bottom_grid_squares = []
        bottom_search_area_height = 50
        search_y_start = self.height - bottom_search_area_height
        square_size = bottom_search_area_height
        non_white_mask = self.image_for_analysis < weiss_schwelle
        candidate_squares = []
        for x in range(0, self.width, square_size):
            x_start, x_end = x, min(x + square_size, self.width)
            y_start, y_end = search_y_start, self.height
            square_roi = non_white_mask[y_start:y_end, x_start:x_end]
            non_white_pixel_count = np.count_nonzero(square_roi)
            center_point = (x_start + (x_end - x_start) // 2, y_start + (y_end - y_start) // 2)
            grid_square_info = {'rect': (x_start, y_start, x_end, y_end), 'is_candidate': non_white_pixel_count > 50}
            self.bottom_grid_squares.append(grid_square_info)
            if grid_square_info['is_candidate']:
                candidate_squares.append({'center': center_point, 'pos_x': center_point[0]})
        if not candidate_squares: return None
        image_center_x = self.width / 2
        candidate_squares.sort(key=lambda sq: abs(sq['pos_x'] - image_center_x))
        winner_center_x = candidate_squares[0]['pos_x']
        for sq in self.bottom_grid_squares:
            sq_center_x = sq['rect'][0] + (sq['rect'][2] - sq['rect'][0]) // 2
            if sq_center_x == winner_center_x: sq['is_winner'] = True
        return candidate_squares[0]['center']

    def _find_candidate_objects(self):
        candidate_types = ['point', 'pointa', 'pointb', 'pointc', 'barrier']
        candidates = [obj for obj in self.all_objects if obj['type'] in candidate_types]
        if not candidates: return []
        image_center_x = self.width / 2
        candidates.sort(key=lambda obj: abs(obj['center'][0] - image_center_x))
        return candidates[:2]

    def _is_line_present(self, point1, point2, weiss_schwelle, linien_schwelle, balken_breite):
        mask = np.zeros_like(self.image_for_analysis)
        cv2.line(mask, point1, point2, 255, thickness=balken_breite)
        total_pixels_in_line = np.count_nonzero(mask)
        if total_pixels_in_line == 0: return False
        non_white_mask = (self.image_for_analysis < weiss_schwelle).astype(np.uint8) * 255
        intersection = cv2.bitwise_and(non_white_mask, mask)
        non_white_pixels_on_line = np.count_nonzero(intersection)
        return (non_white_pixels_on_line / total_pixels_in_line) > linien_schwelle

    def _check_wall_collision(self, point1, point2):
        connection_line = LineString([point1, point2])
        wall_objects = [obj for obj in self.all_objects if obj['type'] == 'wall']
        for wall in wall_objects:
            wall_bbox = wall['bbox']
            wall_polygon = box(wall_bbox[0], wall_bbox[1], wall_bbox[2], wall_bbox[3])
            if connection_line.intersects(wall_polygon): return True
        return False

    def check_connection(self, linien_schwelle=0.05, weiss_schwelle=240, balken_breite=15):
        self._reset_analysis_state()
        self.start_point = self._find_bottom_target_point(weiss_schwelle)
        if self.start_point is None: return 0
        self.candidate_objects = self._find_candidate_objects()
        if not self.candidate_objects: return 0
        for candidate in self.candidate_objects:
            if self._is_line_present(self.start_point, candidate['center'], weiss_schwelle, linien_schwelle,
                                     balken_breite):
                self.winning_object = candidate
                break
        if self.winning_object is None: return 0
        if self.winning_object['type'] == 'barrier': return 3
        self.is_wall_collision = self._check_wall_collision(self.start_point, self.winning_object['center'])
        if self.is_wall_collision:
            return 2
        else:
            return 1

    def visualize_connection_analysis(self, final_status, show_grid=True):
        vis_img = cv2.imread(self.image_with_lines_path)
        colors = {'wall': (0, 0, 255), 'barrier': (0, 165, 255), 'point': (255, 0, 0), 'grid_candidate': (0, 255, 0),
                  'grid_winner': (0, 0, 255), 'line_success': (0, 255, 0), 'line_blocked': (0, 0, 255),
                  'line_barrier': (0, 165, 255), 'text': (255, 255, 255)}
        if show_grid and self.bottom_grid_squares:
            for sq in self.bottom_grid_squares:
                if sq.get('is_winner', False):
                    color, thickness = colors['grid_winner'], 2
                elif sq['is_candidate']:
                    color, thickness = colors['grid_candidate'], 1
                else:
                    continue
                cv2.rectangle(vis_img, (sq['rect'][0], sq['rect'][1]), (sq['rect'][2], sq['rect'][3]), color, thickness)
        for obj in self.all_objects:
            obj_type = obj['type'];
            color = colors.get(obj_type, (200, 200, 200));
            bbox = obj['bbox']
            cv2.rectangle(vis_img, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
            cv2.putText(vis_img, obj_type, (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        if self.start_point:
            cv2.circle(vis_img, self.start_point, 10, (255, 0, 255), -1)
            cv2.putText(vis_img, "Start", (self.start_point[0] + 15, self.start_point[1] + 5), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (255, 0, 255), 2)
        if self.winning_object:
            line_color = colors['line_success']
            if final_status == 2: line_color = colors['line_blocked']
            if final_status == 3: line_color = colors['line_barrier']
            cv2.line(vis_img, self.start_point, self.winning_object['center'], line_color, 3)
        status_map = {0: "Keine Linie gefunden", 1: "Linie zu Punkt gefunden", 2: "Linie gefunden, aber Wand blockiert",
                      3: "Linie zu Barriere gefunden"}
        status_text = f"Ergebnis: {final_status} - {status_map.get(final_status, 'Unbekannt')}"
        cv2.putText(vis_img, status_text, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(vis_img, status_text, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, colors['text'], 2, cv2.LINE_AA)
        cv2.imshow("Analyse-Visualisierung", vis_img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    # --- BITTE PFADE HIER ANPASSEN ---
    try:
        base_path = "C:/Users/marin/PycharmProjects/PREN1G11/roboter_final/dummy_data"
        edited_img_path = os.path.join(base_path, "bearbeitet_1a0c5f09-25ad-40fb-9b1a-a5d92b5bbb16.png")
        original_img_path = edited_img_path# ANPASSEN
    except Exception as e:
        print(f"FEHLER bei der Pfadkonfiguration: {e}")
        exit()
    # --- ENDE DER PFAD-KONFIGURATION ---

    # --- SIMULATION DER OBJEKTERKENNUNG AUS .TXT-DATEI ---
    # Hier wird der Inhalt Ihrer `detected_objects.txt` direkt als String verwendet.
    print("--- Lese Objektdaten für den Test ---")
    detected_objects_string_content = """
    wall;94.0%;(759, 260, 882, 323);7749;(820.5, 291.5);
    point;72.7%;(814, 80, 854, 96);640;(834.0, 88.0);
    """

    # Die Hilfsfunktion parst den String und erstellt die Objektliste
    detected_objects = parse_objects_from_string(detected_objects_string_content)
    print(f"{len(detected_objects)} Objekte geparst.")
    for obj in detected_objects:
        print(f"  - {obj}")
    # --- ENDE DER SIMULATION ---

    try:
        # Schritt 2: Verbindungsanalyse starten
        print("\n--- Schritt 2: Starte Verbindungsanalyse ---")
        pruefer = CheckConnection(
            image_with_lines_path=edited_img_path,
            original_image_path=original_img_path,
            object_list=detected_objects
        )

        verbindungs_status = pruefer.check_connection(
            linien_schwelle=0.05,
            weiss_schwelle=240,
            balken_breite=15
        )

        status_bedeutung = {
            0: "Keine Linie gefunden",
            1: "Linie zu Punkt gefunden",
            2: "Linie gefunden, aber Wand blockiert",
            3: "Linie zu Barriere gefunden"
        }

        print(f"\nFinaler Verbindungsstatus: {verbindungs_status}")
        print(f"Bedeutung: {status_bedeutung.get(verbindungs_status, 'Unbekannt')}")

        # Schritt 3: Ergebnis visualisieren
        print("\n--- Schritt 3: Visualisiere Ergebnis ---")
        pruefer.visualize_connection_analysis(
            final_status=verbindungs_status,
            show_grid=True
        )
        print("--- Analyse abgeschlossen ---")

    except FileNotFoundError as e:
        print(f"\nFEHLER: Eine Datei wurde nicht gefunden. Bitte überprüfen Sie die Pfade.")
        print(f"Detail: {e}")
    except Exception as e:
        import traceback

        print(f"\nEin unerwarteter Fehler ist aufgetreten:")
        traceback.print_exc()