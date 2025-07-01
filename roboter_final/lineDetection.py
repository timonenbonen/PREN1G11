import cv2
import numpy as np
import os
import roboter_final.YoloDetector as YoloDetector
import roboter_final.ErkannteObjekte as ErkannteObjekte
import roboter_final.lineDetection as lineDetection




class CheckConnection:
    def __init__(self, image_with_lines_path: str, original_image_path: str, object_list: list):
        self.object_list = object_list
        if not self.object_list:
            print("WARNUNG: Eine leere Objektliste wurde an CheckConnection übergeben.")

        self.image_with_lines = cv2.imread(image_with_lines_path)
        if self.image_with_lines is None:
            raise FileNotFoundError(
                f"Bild für Linienanalyse konnte nicht unter '{image_with_lines_path}' geladen werden.")

        self.image_for_visualization = cv2.imread(original_image_path)
        if self.image_for_visualization is None:
            self.image_for_visualization = self.image_with_lines.copy()

        self.height, self.width, _ = self.image_with_lines.shape
        self.gray_image = cv2.cvtColor(self.image_with_lines, cv2.COLOR_BGR2GRAY)

        self.last_start_area = None  # Für die Visualisierung des Suchquadrats
        self.last_punkt1 = None
        self.last_punkt2 = None

    def _finde_startpunkt_dynamisch(self, quadrat_groesse=10, helligkeits_schwelle=240) -> np.ndarray:
        """
        Sucht dynamisch nach dem besten Startpunkt am unteren Bildrand.

        Args:
            quadrat_groesse (int): Die Seitenlänge des Suchquadrats in Pixeln.
            helligkeits_schwelle (int): Grauwert (0-255), unter dem ein Pixel als "dunkel" gilt.

        Returns:
            np.ndarray: Die (x, y)-Koordinaten des besten Startpunkts.
        """
        # 1. Bereich des Suchquadrats definieren
        x_start = int(self.width / 2 - quadrat_groesse / 2)
        x_end = x_start + quadrat_groesse
        y_start = self.height - quadrat_groesse
        y_end = self.height

        # Für die Visualisierung speichern
        self.last_start_area = (x_start, y_start, x_end, y_end)

        # Region of Interest (ROI) aus dem Graustufenbild extrahieren
        roi = self.gray_image[y_start:y_end, x_start:x_end]

        # 2. Alle "dunklen" Pixel im ROI finden
        kandidaten_y_roi, kandidaten_x_roi = np.where(roi < helligkeits_schwelle)

        # 3. Wenn keine dunklen Pixel gefunden wurden, Fallback verwenden
        if kandidaten_y_roi.size == 0:
            print("WARNUNG: Kein dunkler Startpunkt im Suchquadrat gefunden. Nutze Fallback-Punkt.")
            return np.array([self.width / 2, self.height - 5])

        # 4. Den dunkelsten Pixel finden, der am zentralsten im ROI liegt
        kandidaten_punkte_roi = np.stack((kandidaten_y_roi, kandidaten_x_roi), axis=1)
        roi_mitte = np.array([quadrat_groesse / 2, quadrat_groesse / 2])

        # Euklidische Distanz jedes Kandidaten zur ROI-Mitte berechnen
        distanzen = np.linalg.norm(kandidaten_punkte_roi - roi_mitte, axis=1)

        # Den Index des Kandidaten mit der geringsten Distanz finden
        bester_index = np.argmin(distanzen)
        bester_punkt_roi = kandidaten_punkte_roi[bester_index]

        # 5. ROI-Koordinaten in globale Bildkoordinaten umrechnen
        # Wichtig: NumPy-Koordinaten sind (y, x), wir geben aber (x, y) zurück
        global_x = x_start + bester_punkt_roi[1]
        global_y = y_start + bester_punkt_roi[0]

        return np.array([global_x, global_y])

    def _ist_pfad_hell_genug(self, p1: np.ndarray, p2: np.ndarray, balken_breite: int, helligkeits_schwelle: int,
                             verbindungs_schwelle: float) -> bool:
        vektor = p2 - p1
        laenge = np.linalg.norm(vektor)
        if laenge < 1: return False

        winkel_rad = np.arctan2(vektor[1], vektor[0])
        winkel_grad = np.degrees(winkel_rad)

        rotations_matrix = cv2.getRotationMatrix2D(tuple(p1.astype(float)), winkel_grad, 1.0)
        rotiertes_bild = cv2.warpAffine(self.gray_image, rotations_matrix, (self.width, self.height))
        rotiertes_p1 = np.dot(rotations_matrix, np.append(p1, 1)).astype(int)

        x_start, y_start = rotiertes_p1[0], rotiertes_p1[1] - balken_breite // 2
        y_end, x_end = y_start + balken_breite, x_start + int(laenge)

        if x_start < 0 or y_start < 0 or x_end > self.width or y_end > self.height: return False

        balken_ausschnitt = rotiertes_bild[y_start:y_end, x_start:x_end]
        if balken_ausschnitt.size == 0: return False

        helle_pixel = np.sum(balken_ausschnitt >= helligkeits_schwelle)
        return (helle_pixel / balken_ausschnitt.size) >= verbindungs_schwelle

    def check_connection(self, balken_threshold=0.4, pixel_helligkeit=200, balken_breite=15) -> int:
        # --- MODIFIZIERUNG: Dynamischen Startpunkt ermitteln ---
        start_punkt = self._finde_startpunkt_dynamisch(quadrat_groesse=10, helligkeits_schwelle=240)

        kandidaten_klassen = {'point', 'pointa', 'pointb', 'pointc', 'barrier'}
        kandidaten = [obj for obj in self.object_list if obj.klasse in kandidaten_klassen]

        if not kandidaten:
            self.last_punkt1 = start_punkt
            return 0

        bild_zentrum_px = np.array([self.width / 2, self.height / 2])
        kandidaten.sort(key=lambda o: np.linalg.norm(np.array(o.zentrum) - bild_zentrum_px))

        ziel_objekt = None
        for kandidat in kandidaten[:2]:
            if self._ist_pfad_hell_genug(start_punkt, np.array(kandidat.zentrum),
                                         balken_breite, pixel_helligkeit, balken_threshold):
                ziel_objekt = kandidat
                break

        self.last_punkt1 = start_punkt
        self.last_punkt2 = np.array(ziel_objekt.zentrum if ziel_objekt else kandidaten[0].zentrum)

        if not ziel_objekt: return 0
        if ziel_objekt.klasse == 'barrier': return 3
        if self.check_wall_on_track(self.last_punkt1, self.last_punkt2): return 2
        return 1

    def _linien_schneiden(self, p1, p2, q1, q2) -> bool:
        def ccw(A, B, C): return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

        return ccw(p1, q1, q2) != ccw(p2, q1, q2) and ccw(p1, p2, q1) != ccw(p1, p2, q2)

    def check_wall_on_track(self, punkt1: np.ndarray, punkt2: np.ndarray) -> bool:
        walls = [obj for obj in self.object_list if obj.klasse == 'wall']
        for wall in walls:
            wall_ecken = [np.array([wall.bounding_box[0], wall.bounding_box[1]]),
                          np.array([wall.bounding_box[2], wall.bounding_box[1]]),
                          np.array([wall.bounding_box[2], wall.bounding_box[3]]),
                          np.array([wall.bounding_box[0], wall.bounding_box[3]])]
            wall_kanten = [(wall_ecken[i], wall_ecken[(i + 1) % 4]) for i in range(4)]
            for kante_start, kante_end in wall_kanten:
                if self._linien_schneiden(punkt1, punkt2, kante_start, kante_end):
                    return True
        return False

    def visualize_connection_analysis(self, status_code: int, max_display_height=800):
        vis_image = self.image_for_visualization.copy()
        color_map = {'point': (255, 150, 0), 'pointa': (255, 150, 0), 'pointb': (255, 150, 0), 'pointc': (255, 150, 0),
                     'barrier': (0, 100, 255), 'wall': (128, 128, 128)}

        for obj in self.object_list:
            color = color_map.get(obj.klasse, (255, 0, 255))
            x1, y1, x2, y2 = map(int, obj.bounding_box)
            cv2.rectangle(vis_image, (x1, y1), (x2, y2), color, 2)
            label = f"{obj.klasse}" + (f" [{obj.buchstabe}]" if obj.buchstabe else "")
            cv2.putText(vis_image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # --- NEU: Suchquadrat für Startpunkt visualisieren ---
        if self.last_start_area:
            x1, y1, x2, y2 = self.last_start_area
            cv2.rectangle(vis_image, (x1, y1), (x2, y2), (255, 255, 0), 1)  # Cyan-farbenes Rechteck

        line_color = {0: (0, 0, 255), 1: (0, 255, 0), 2: (0, 165, 255), 3: (0, 255, 255)}.get(status_code, (0, 0, 255))
        if self.last_punkt1 is not None and self.last_punkt2 is not None:
            p1_int = tuple(self.last_punkt1.astype(int))
            p2_int = tuple(self.last_punkt2.astype(int))
            cv2.line(vis_image, p1_int, p2_int, line_color, 3)
            # Startpunkt mit einem ausgefüllten Kreis hervorheben
            cv2.circle(vis_image, p1_int, 8, (0, 255, 0), -1)
            cv2.circle(vis_image, p1_int, 10, (0, 0, 0), 1)  # Schwarzer Rand für Sichtbarkeit
            # Endpunkt mit einem Ring hervorheben
            cv2.circle(vis_image, p2_int, 12, (255, 0, 0), 3)

        status_map = {0: "Keine Verbindung", 1: "Verbindung OK", 2: "Wand blockiert", 3: "Barriere als Ziel"}
        status_text = f"Status: {status_code} ({status_map.get(status_code, 'Unbekannt')})"
        cv2.putText(vis_image, status_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(vis_image, status_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

        self._show_image("Verbindungs-Analyse", vis_image, max_display_height)

    def _show_image(self, title, image, max_h):
        h, w = image.shape[:2]
        if h > max_h: image = cv2.resize(image, (int(max_h * w / h), max_h))
        cv2.imshow(title, image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


# ==============================================================================
# HAUPTPROGRAMM (bleibt unverändert)
# ==============================================================================
if __name__ == "__main__":

    try:
        base_path = "C:/Users/marin/PycharmProjects/PREN1G11/roboter_final/dummy_data"
        model_path = "C:/Users/marin/PycharmProjects/PREN1G11/roboter_final/my_model.pt"
        original_img_path = os.path.join(base_path, "1a0c5f09-25ad-40fb-9b1a-a5d92b5bbb16.jpg")
        edited_img_path = os.path.join(base_path, "bearbeitet_1a0c5f09-25ad-40fb-9b1a-a5d92b5bbb16.png")
        txt_output_path = os.path.join(base_path, "detected_objects.txt")
    except Exception as e:
        print(f"FEHLER bei der Pfadkonfiguration: {e}")
        exit()

    try:
        print("--- Schritt 1: Starte Objekterkennung ---")

        detector = YoloDetector(model_path=model_path)
        detected_objects = detector.detect(original_img_path)
        detector.save_to_txt(detected_objects, txt_output_path)
        print("--- Objekterkennung abgeschlossen ---\n")

        print("--- Schritt 2: Starte Verbindungsanalyse ---")
        pruefer = CheckConnection(
            image_with_lines_path=edited_img_path,
            original_image_path=original_img_path,
            object_list=detected_objects
        )

        verbindungs_status = pruefer.check_connection(balken_threshold=0.5, pixel_helligkeit=150, balken_breite=20)

        status_map = {0: "Keine Verbindung", 1: "Verbindung OK", 2: "Wand blockiert", 3: "Barriere als Ziel"}
        print(
            f"ERGEBNIS: Verbindungsstatus ist {verbindungs_status} ({status_map.get(verbindungs_status, 'Unbekannt')})")

        print("\n--- Schritt 3: Visualisiere Ergebnis ---")
        pruefer.visualize_connection_analysis(verbindungs_status)
        print("--- Analyse abgeschlossen ---")

    except FileNotFoundError as e:
        print(f"\nFEHLER: Eine Datei wurde nicht gefunden. Bitte überprüfen Sie die oben konfigurierten Pfade.")
        print(f"Detail: {e}")
    except Exception as e:
        import traceback

        print(f"\nEin unerwarteter Fehler ist aufgetreten:")
        traceback.print_exc()