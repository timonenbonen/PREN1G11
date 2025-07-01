# --- START OF FILE CheckConection.py ---

import cv2
import numpy as np
from shapely.geometry import LineString, box
# Stellen Sie sicher, dass dieser Import für Ihre Projektstruktur korrekt ist
from roboter_final.ErkannteObjekte import Objekt


class CheckConnection:
    """
    Analysiert und visualisiert eine Verbindung auf einem einzigen, bearbeiteten Bild.
    Benötigt nur den Pfad zum bearbeiteten Bild und die Objektliste.
    """

    def __init__(self, image_path, object_list):
        self.image_path = image_path
        self.image_for_analysis = cv2.imread(self.image_path, cv2.IMREAD_GRAYSCALE)
        if self.image_for_analysis is None:
            raise FileNotFoundError(f"Bild konnte nicht geladen werden: {self.image_path}")

        self.height, self.width = self.image_for_analysis.shape
        self.all_objects = self._parse_objects(object_list)
        self._reset_analysis_state()

    def _reset_analysis_state(self):
        self.start_point = None
        self.candidate_objects = []
        self.winning_object = None
        self.is_wall_collision = False
        self.bottom_grid_squares = []
        self.last_line_check_details = {}

    def _parse_objects(self, object_list):
        """
        Parst eine Liste von Objekten in ein einheitliches Dictionary-Format.
        Diese Methode kann drei Arten von Listen verarbeiten:
        1. Eine Liste von rohen Strings aus einer Textdatei.
        2. Eine bereits geparste Liste von Dictionaries.
        3. Eine Liste von `Objekt`-Instanzen aus ErkannteObjekte.py.
        """
        if not object_list:
            return []

        parsed_list = []
        first_item = object_list[0]

        # Fall 1: Die Liste enthält rohe Strings
        if isinstance(first_item, str):
            for line in object_list:
                line = line.strip()
                if not line: continue
                try:
                    parts = line.strip(';').split(';')
                    typ = parts[0]
                    # Bbox wird bereits als int geparst
                    bbox = tuple(map(int, parts[2].strip('()').split(',')))
                    # Zentrum wird bereits als int geparst
                    center = tuple(int(float(c)) for c in parts[4].strip('()').split(','))
                    parsed_list.append({'type': typ, 'bbox': bbox, 'center': center})
                except Exception as e:
                    print(f"Warnung: Konnte String nicht parsen: '{line}' - {e}")
            return parsed_list

        # Fall 2: Die Liste enthält bereits Dictionaries
        elif isinstance(first_item, dict):
            # Wir nehmen an, das Format ist bereits korrekt und geben es direkt zurück.
            return object_list

        # Fall 3: Die Liste enthält Instanzen der 'Objekt'-Klasse
        else:
            for obj in object_list:
                try:
                    # KORREKTUR 1: Wandle das Zentrum-Tupel von float in int um.
                    # Dies ist entscheidend, um den cv2.line-Fehler zu verhindern.
                    center_as_int = (int(obj.zentrum[0]), int(obj.zentrum[1]))

                    # KORREKTUR 2: Verwende die korrekten Attributnamen aus der Objekt-Klasse.
                    parsed_list.append({
                        'type': obj.klasse,  # Statt 'obj.typ'
                        'bbox': obj.bounding_box,  # Statt 'obj.bbox'
                        'center': center_as_int  # Statt 'obj.center'
                    })
                except AttributeError as e:
                    print(f"Warnung: Attribut-Fehler beim Parsen der Objekt-Instanz. {e}")
                except (ValueError, TypeError) as e:
                    print(f"Warnung: Typ-Fehler beim Umwandeln der Zentrum-Koordinaten für {obj}: {e}")
            return parsed_list

    def _find_bottom_target_point(self, weiss_schwelle):
        self.bottom_grid_squares = []
        search_y_start = self.height - 150  # Robusterer, größerer Suchbereich
        square_size = 50
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
            if (sq['rect'][0] + (sq['rect'][2] - sq['rect'][0]) // 2) == winner_center_x:
                sq['is_winner'] = True
        return candidate_squares[0]['center']

    def _find_candidate_objects(self):
        candidate_types = ['point', 'pointa', 'pointb', 'pointc', 'barrier']
        candidates = [obj for obj in self.all_objects if obj['type'] in candidate_types]
        if not candidates: return []
        image_center_x = self.width / 2
        candidates.sort(key=lambda obj: abs(obj['center'][0] - image_center_x))
        return candidates[:2]

    def _is_line_present(self, p1, p2, weiss_schwelle, linien_schwelle, balken_breite):
        mask = np.zeros_like(self.image_for_analysis)
        cv2.line(mask, p1, p2, 255, thickness=balken_breite)
        total_pixels = np.count_nonzero(mask)
        if total_pixels == 0: return False
        non_white_mask = (self.image_for_analysis < weiss_schwelle).astype(np.uint8) * 255
        intersection = cv2.bitwise_and(non_white_mask, mask)
        non_white_pixels = np.count_nonzero(intersection)
        ratio = (non_white_pixels / total_pixels) if total_pixels > 0 else 0
        if not self.last_line_check_details:
            self.last_line_check_details = {
                'p1': p1, 'p2': p2, 'balken_breite': balken_breite,
                'total_pixels': total_pixels, 'non_white_pixels': non_white_pixels,
                'calculated_ratio': ratio, 'required_threshold': linien_schwelle
            }
        return ratio > linien_schwelle

    def _check_wall_collision(self, p1, p2):
        line = LineString([p1, p2])
        wall_objects = [obj for obj in self.all_objects if obj['type'] == 'wall']
        for wall in wall_objects:
            if line.intersects(box(wall['bbox'][0], wall['bbox'][1], wall['bbox'][2], wall['bbox'][3])):
                return True
        return False

    def check_connection(self, linien_schwelle=0.05, weiss_schwelle=255, balken_breite=10):
        self._reset_analysis_state()
        self.start_point = self._find_bottom_target_point(weiss_schwelle)
        if self.start_point is None: return 0
        self.candidate_objects = self._find_candidate_objects()
        if not self.candidate_objects: return 0
        for candidate in self.candidate_objects:
            if self._is_line_present(self.start_point, candidate['center'], weiss_schwelle, linien_schwelle, balken_breite):
                self.winning_object = candidate
                break
        if self.winning_object is None: return 0
        if self.winning_object['type'] == 'barrier': return 3
        if self._check_wall_collision(self.start_point, self.winning_object['center']):
            return 2
        else:
            return 1


    def visualize_connection_analysis(self, final_status, show_grid=True):
        vis_img = cv2.imread(self.image_path)
        if vis_img is None:
            print("Fehler: Visualisierungsbild konnte nicht geladen werden.")
            return

        # --- BILD-SKALIERUNG ---
        max_height = 720  # Maximale Höhe für das Fenster
        h, w, _ = vis_img.shape
        scale_factor = 1.0  # Standard-Skalierungsfaktor ist 1 (keine Änderung)

        if h > max_height:
            scale_factor = max_height / h
            new_w = int(w * scale_factor)
            vis_img_display = cv2.resize(vis_img, (new_w, max_height), interpolation=cv2.INTER_AREA)
            print(f"Info: Bild wurde mit Faktor {scale_factor:.2f} skaliert.")
        else:
            vis_img_display = vis_img.copy()  # Arbeite auf einer Kopie

        # Hilfsfunktion, um Koordinaten zu skalieren
        def scale_pt(pt):
            if pt is None: return None
            return (int(pt[0] * scale_factor), int(pt[1] * scale_factor))

        def scale_rect(rect):
            if rect is None: return None
            return (int(rect[0] * scale_factor), int(rect[1] * scale_factor),
                    int(rect[2] * scale_factor), int(rect[3] * scale_factor))

        colors = {'wall': (0, 0, 255), 'barrier': (0, 165, 255), 'point': (255, 0, 0), 'grid_candidate': (0, 255, 0),
                  'grid_winner': (0, 0, 255), 'line_success': (0, 255, 0), 'line_blocked': (0, 0, 255),
                  'line_barrier': (0, 165, 255), 'text': (255, 255, 255)}

        # Zeichne den Analysebalken mit skalierten Koordinaten
        details = self.last_line_check_details
        if details and details.get('p1') and details.get('p2'):
            overlay = vis_img_display.copy()
            p1_scaled = scale_pt(details['p1'])
            p2_scaled = scale_pt(details['p2'])
            # Skaliere auch die Balkenbreite, damit sie proportional bleibt
            balken_breite_scaled = max(1, int(details['balken_breite'] * scale_factor))

            cv2.line(overlay, p1_scaled, p2_scaled, (255, 255, 0), thickness=balken_breite_scaled)
            alpha = 0.4
            vis_img_display = cv2.addWeighted(overlay, alpha, vis_img_display, 1 - alpha, 0)

            # Text bleibt an fester Position, muss nicht skaliert werden
            ratio = details.get('calculated_ratio', 0)
            threshold = details.get('required_threshold', 0)
            is_success = ratio > threshold
            text_color = colors['line_success'] if is_success else colors['line_blocked']
            info_texts = [
                f"Analyse-Balken: {details.get('non_white_pixels')} / {details.get('total_pixels')} Pixel",
                f"Berechnetes Verhaeltnis: {ratio:.4f}", f"Benoetigte Schwelle: > {threshold:.4f}"
            ]
            for i, text in enumerate(info_texts):
                pos = (20, 60 + i * 25)
                cv2.putText(vis_img_display, text, pos, cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3)
                cv2.putText(vis_img_display, text, pos, cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 1)

        if show_grid and self.bottom_grid_squares:
            for sq in self.bottom_grid_squares:
                rect_scaled = scale_rect(sq['rect'])
                if sq.get('is_winner', False):
                    color, thickness = colors['grid_winner'], 2
                elif sq['is_candidate']:
                    color, thickness = colors['grid_candidate'], 1
                else:
                    continue
                cv2.rectangle(vis_img_display, (rect_scaled[0], rect_scaled[1]), (rect_scaled[2], rect_scaled[3]),
                              color, thickness)

        for obj in self.all_objects:
            color = colors.get(obj['type'], (200, 200, 200))
            bbox_scaled = scale_rect(obj['bbox'])
            cv2.rectangle(vis_img_display, (bbox_scaled[0], bbox_scaled[1]), (bbox_scaled[2], bbox_scaled[3]), color, 2)
            cv2.putText(vis_img_display, obj['type'], (bbox_scaled[0], bbox_scaled[1] - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, color, 2)

        start_point_scaled = scale_pt(self.start_point)
        if start_point_scaled:
            cv2.circle(vis_img_display, start_point_scaled, 10, (255, 0, 255), -1)
            cv2.putText(vis_img_display, "Start", (start_point_scaled[0] + 15, start_point_scaled[1] + 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)

        if self.winning_object:
            winning_center_scaled = scale_pt(self.winning_object['center'])
            if start_point_scaled and winning_center_scaled:
                line_color = colors['line_success']
                if final_status == 2: line_color = colors['line_blocked']
                if final_status == 3: line_color = colors['line_barrier']
                cv2.line(vis_img_display, start_point_scaled, winning_center_scaled, line_color, 5)

        status_map = {0: "Keine Linie", 1: "Linie zu Punkt", 2: "Linie zu Punkt (blockiert)", 3: "Linie zu Barriere"}
        status_text = f"Ergebnis: {final_status} - {status_map.get(final_status, 'Unbekannt')}"
        cv2.putText(vis_img_display, status_text, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(vis_img_display, status_text, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, colors['text'], 2, cv2.LINE_AA)

        window_name = "Analyse-Visualisierung"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.imshow(window_name, vis_img_display)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def get_turn_direction(self, center_zone_width_pixels=50):
        if self.winning_object is None:
            return "keine Richtung"

        object_center_x = self.winning_object['center'][0]
        image_center_x = self.width / 2

        # Berechne die halbe Breite der "Mitte"-Zone in Pixeln
        half_center_zone_width = center_zone_width_pixels / 2

        # Definiere die Grenzen basierend auf dem Bildzentrum und der Pixelbreite
        left_zone_end = image_center_x - half_center_zone_width
        right_zone_start = image_center_x + half_center_zone_width

        if object_center_x < left_zone_end:
            return "links"
        elif object_center_x > right_zone_start:
            return "rechts"
        else:
            return "mitte"


if __name__ == "__main__":
    processed_image_path = r"C:\Users\marin\PycharmProjects\PREN1G11\roboter_final\dummy_data\bearbeitet_Test2_C.jpg"
    objects_txt_path = r"C:\Users\marin\PycharmProjects\PREN1G11\roboter_final\dummy_data\F.txt"

    try:
        print(f"Lese Objekt-Datei: {objects_txt_path}")
        with open(objects_txt_path, 'r') as f:
            file_content = f.read()
        if not file_content.strip():
            print("WARNUNG: Die Objekt-Datei ist leer.")
            objects = []
        else:
            objects = Objekt.parse_text_to_objects(file_content)
        print(f"{len(objects)} Objekte erfolgreich aus Datei geparst.")
        if not objects:
            print("WARNUNG: Keine Objekte nach dem Parsen vorhanden. Bitte Inhalt der .txt-Datei prüfen.")
    except FileNotFoundError:
        print(f"FEHLER: Die Objekt-Definitionsdatei wurde nicht gefunden unter: {objects_txt_path}")
        exit()
    except Exception as e:
        print(f"FEHLER beim Parsen der Objekt-Datei: {e}")
        exit()

    if objects:
        try:
            print("--- Starte Verbindungsanalyse ---")
            check_connection = CheckConnection(processed_image_path, objects)
            line_status = check_connection.check_connection(
                weiss_schwelle=254,
                linien_schwelle=0.10,
                balken_breite=20
            )
            print(f"\n---> Finaler Linien-Status: {line_status}")
            check_connection.visualize_connection_analysis(line_status)
            turn_direction = check_connection.get_turn_direction()
            print(turn_direction)
            print("--- Analyse abgeschlossen ---")

        except FileNotFoundError:
            print(f"\nFEHLER: Das Bild wurde nicht gefunden: {processed_image_path}")
        except Exception as e:
            import traceback
            print(f"\nEin unerwarteter Fehler ist aufgetreten:")
            traceback.print_exc()

