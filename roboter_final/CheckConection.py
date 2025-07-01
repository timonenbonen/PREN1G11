import cv2
import numpy as np
import os
from shapely.geometry import LineString, box


class CheckConnection:
    """
    Analysiert und visualisiert eine Verbindung auf einem einzigen, bearbeiteten Bild.
    Benötigt nur den Pfad zum bearbeiteten Bild und die Objektliste.
    """

    def __init__(self, image_path, object_list):
        """
        Initialisiert den Prüfer.
        :param image_path: Pfad zum bearbeiteten Bild (z.B. das PNG mit den Linien).
        :param object_list: Eine Liste von erkannten Objekten (rohe Strings, Dicts oder Instanzen).
        """
        self.image_path = image_path

        # Lade das Bild für die Analyse (in Graustufen)
        self.image_for_analysis = cv2.imread(self.image_path, cv2.IMREAD_GRAYSCALE)
        if self.image_for_analysis is None:
            raise FileNotFoundError(f"Bild konnte nicht geladen werden: {self.image_path}")

        self.height, self.width = self.image_for_analysis.shape

        # Diese Methode verarbeitet intelligent die übergebene Objektliste
        self.all_objects = self._parse_objects(object_list)

        self._reset_analysis_state()

    # --- Der Rest der Klasse bleibt identisch, da die Logik sich nicht ändert ---

    def _reset_analysis_state(self):
        self.start_point = None;
        self.candidate_objects = [];
        self.winning_object = None
        self.is_wall_collision = False;
        self.bottom_grid_squares = []

    def _parse_objects(self, object_list):
        if not object_list: return []
        parsed_list = []
        first_item = object_list[0]
        if isinstance(first_item, str):
            for line in object_list:
                line = line.strip()
                if not line: continue
                try:
                    parts = line.strip(';').split(';');
                    typ = parts[0]
                    bbox = tuple(map(int, parts[2].strip('()').split(',')))
                    center = tuple(int(float(c)) for c in parts[4].strip('()').split(','))
                    parsed_list.append({'type': typ, 'bbox': bbox, 'center': center})
                except Exception as e:
                    print(f"Warnung: Konnte String nicht parsen: '{line}' - {e}")
            return parsed_list
        elif isinstance(first_item, dict):
            return object_list
        else:
            for obj in object_list:
                try:
                    parsed_list.append({'type': obj.typ, 'bbox': obj.bbox, 'center': obj.center})
                except AttributeError as e:
                    print(f"Warnung: Objekt {obj} fehlerhaft. {e}")
            return parsed_list

    def _find_bottom_target_point(self, weiss_schwelle):
        self.bottom_grid_squares = []
        search_y_start = self.height - 50;
        square_size = 50
        non_white_mask = self.image_for_analysis < weiss_schwelle
        candidate_squares = []
        for x in range(0, self.width, square_size):
            x_start, x_end = x, min(x + square_size, self.width);
            y_start, y_end = search_y_start, self.height
            square_roi = non_white_mask[y_start:y_end, x_start:x_end];
            non_white_pixel_count = np.count_nonzero(square_roi)
            center_point = (x_start + (x_end - x_start) // 2, y_start + (y_end - y_start) // 2)
            grid_square_info = {'rect': (x_start, y_start, x_end, y_end), 'is_candidate': non_white_pixel_count > 50}
            self.bottom_grid_squares.append(grid_square_info)
            if grid_square_info['is_candidate']: candidate_squares.append(
                {'center': center_point, 'pos_x': center_point[0]})
        if not candidate_squares: return None
        image_center_x = self.width / 2;
        candidate_squares.sort(key=lambda sq: abs(sq['pos_x'] - image_center_x))
        winner_center_x = candidate_squares[0]['pos_x']
        for sq in self.bottom_grid_squares:
            if (sq['rect'][0] + (sq['rect'][2] - sq['rect'][0]) // 2) == winner_center_x: sq['is_winner'] = True
        return candidate_squares[0]['center']

    def _find_candidate_objects(self):
        candidate_types = ['point', 'pointa', 'pointb', 'pointc', 'barrier'];
        candidates = [obj for obj in self.all_objects if obj['type'] in candidate_types]
        if not candidates: return []
        image_center_x = self.width / 2;
        candidates.sort(key=lambda obj: abs(obj['center'][0] - image_center_x))
        return candidates[:2]

    def _is_line_present(self, p1, p2, weiss_schwelle, linien_schwelle, balken_breite):
        mask = np.zeros_like(self.image_for_analysis);
        cv2.line(mask, p1, p2, 255, thickness=balken_breite)
        total_pixels = np.count_nonzero(mask)
        if total_pixels == 0: return False
        non_white_mask = (self.image_for_analysis < weiss_schwelle).astype(np.uint8) * 255
        intersection = cv2.bitwise_and(non_white_mask, mask);
        non_white_pixels = np.count_nonzero(intersection)
        return (non_white_pixels / total_pixels) > linien_schwelle

    def _check_wall_collision(self, p1, p2):
        line = LineString([p1, p2]);
        wall_objects = [obj for obj in self.all_objects if obj['type'] == 'wall']
        for wall in wall_objects:
            if line.intersects(box(wall['bbox'][0], wall['bbox'][1], wall['bbox'][2], wall['bbox'][3])): return True
        return False

    def check_connection(self, linien_schwelle=0.05, weiss_schwelle=240, balken_breite=15):
        self._reset_analysis_state();
        self.start_point = self._find_bottom_target_point(weiss_schwelle)
        if self.start_point is None: return 0
        self.candidate_objects = self._find_candidate_objects()
        if not self.candidate_objects: return 0
        for candidate in self.candidate_objects:
            if self._is_line_present(self.start_point, candidate['center'], weiss_schwelle, linien_schwelle,
                                     balken_breite):
                self.winning_object = candidate;
                break
        if self.winning_object is None: return 0
        if self.winning_object['type'] == 'barrier': return 3
        if self._check_wall_collision(self.start_point, self.winning_object['center']):
            return 2
        else:
            return 1

    def visualize_connection_analysis(self, final_status, show_grid=True):
        # Lädt das Bild für die Visualisierung direkt vom gespeicherten Pfad
        vis_img = cv2.imread(self.image_path)
        if vis_img is None: print("Fehler: Visualisierungsbild konnte nicht geladen werden."); return

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
            color = colors.get(obj['type'], (200, 200, 200));
            bbox = obj['bbox']
            cv2.rectangle(vis_img, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
            cv2.putText(vis_img, obj['type'], (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        if self.start_point:
            cv2.circle(vis_img, self.start_point, 10, (255, 0, 255), -1)
            cv2.putText(vis_img, "Start", (self.start_point[0] + 15, self.start_point[1] + 5), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (255, 0, 255), 2)
        if self.winning_object:
            line_color = colors['line_success']
            if final_status == 2: line_color = colors['line_blocked']
            if final_status == 3: line_color = colors['line_barrier']
            cv2.line(vis_img, self.start_point, self.winning_object['center'], line_color, 3)
        status_map = {0: "Keine Linie", 1: "Linie zu Punkt", 2: "Linie zu Punkt (blockiert)", 3: "Linie zu Barriere"}
        status_text = f"Ergebnis: {final_status} - {status_map.get(final_status, 'Unbekannt')}"
        cv2.putText(vis_img, status_text, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(vis_img, status_text, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, colors['text'], 2, cv2.LINE_AA)
        cv2.imshow("Analyse-Visualisierung", vis_img);
        cv2.waitKey(0);
        cv2.destroyAllWindows()


if __name__ == "__main__":

    # --- BITTE ANPASSEN ---
    # Der Pfad zu Ihrem bearbeiteten Bild
    processed_image_path = r"C:\Users\marin\PycharmProjects\PREN1G11\roboter_final\dummy_data\bearbeitet_1a0c5f09-25ad-40fb-9b1a-a5d92b5bbb16.png"

    # --- Ihre Objektdaten (rohe Strings) ---
    objects = [
        "wall;94.0%;(759, 260, 882, 323);7749;(820.5, 291.5);",
        "point;72.7%;(814, 80, 854, 96);640;(834.0, 88.0);"
    ]
    # --- ENDE DER ANPASSUNGEN ---

    try:
        print("--- Starte Verbindungsanalyse ---")
        print(f"Verwende Bild: {processed_image_path}")
        print(f"Verwende {len(objects)} Objekte.")

        # Vereinfachter Aufruf: Nur noch der Bildpfad und die Objektliste werden benötigt.
        check_connection = CheckConnection(processed_image_path, objects)

        # Führe die Analyse mit Standardwerten durch
        line_status = check_connection.check_connection()

        print(f"\n---> Finaler Linien-Status: {line_status}")

        # Visualisiere das Ergebnis
        print("--> Starte Visualisierung...")
        check_connection.visualize_connection_analysis(line_status)
        print("--- Analyse abgeschlossen ---")

    except FileNotFoundError as e:
        print(f"\nFEHLER: Das Bild wurde nicht gefunden. Bitte überprüfen Sie den Pfad.")
        print(f"Pfad: {processed_image_path}")
    except Exception as e:
        import traceback

        print(f"\nEin unerwarteter Fehler ist aufgetreten:")
        traceback.print_exc()