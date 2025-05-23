from sympy.strategies.core import switch
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
from itertools import combinations


class Objekt:
    def __init__(self, klasse, vertrauen, bounding_box):
        """Erstellt ein neues Objekt mit automatischer Buchstaben-Zuweisung für pointa/b/c."""
        self.klasse = klasse
        self.vertrauen = vertrauen
        self.bounding_box = bounding_box
        self.flaeche = self._berechne_flaeche()
        self.zentrum = self._berechne_zentrum()
        self.buchstabe = None

        if self.klasse in ['pointa', 'pointb', 'pointc']:
            self.set_buchstabe_automatisch()

    def _berechne_flaeche(self):
        x1, y1, x2, y2 = self.bounding_box
        return (x2 - x1) * (y2 - y1)

    def _berechne_zentrum(self):
        x1, y1, x2, y2 = self.bounding_box
        return ((x1 + x2) / 2, (y1 + y2) / 2)

    def set_buchstabe(self, buchstabe):
        self.buchstabe = buchstabe
        return self

    def set_buchstabe_automatisch(self):
        buchstaben_mapping = {'pointa': 'A', 'pointb': 'B', 'pointc': 'C'}
        self.buchstabe = buchstaben_mapping.get(self.klasse)

    def ist_vertrauenswuerdig(self, schwellenwert=50.0):
        return self.vertrauen >= schwellenwert

    @staticmethod
    def create_adjacency_matrix(objekte_liste, connection_image_path, connection_threshold=0.15, bar_width=10):
        """Erstellt eine Adjazenzmatrix mit Analyse eines breiten Balkens zwischen Punkten.
        Ergänzt automatisch den Punkt, auf dem der Roboter steht (aus Bildname), falls nicht sichtbar.
        Speichert die Matrix in eine Datei unter Dataset/Matrix/Currentmatrix.txt."""
        import re
        import os

        # Buchstaben-Liste für das Original-Schema
        buchstaben = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']

        # Original Matrix als Vorlage
        original_matrix = np.array([
            [0, 1, 0, 0, 0, 1, 0, 1],  # A
            [1, 0, 1, 0, 0, 0, 0, 1],  # B
            [0, 1, 0, 1, 0, 0, 1, 1],  # C
            [0, 0, 1, 0, 1, 0, 1, 0],  # D
            [0, 0, 0, 1, 0, 1, 1, 0],  # E
            [1, 0, 0, 0, 1, 0, 1, 1],  # F
            [0, 0, 1, 1, 1, 1, 0, 1],  # G
            [1, 1, 1, 0, 0, 1, 1, 0]  # H
        ])

        # Dictionary für Objekte nach Buchstaben
        punkt_dict = {obj.buchstabe: obj for obj in objekte_liste if obj.buchstabe in buchstaben}
        vorhandene_buchstaben = sorted(list(punkt_dict.keys()))
        print("Vorhandene Buchstaben (vor Ergänzung):", vorhandene_buchstaben)

        # Bild laden, um Höhe/Breite zu bekommen
        connection_image = cv2.imread(connection_image_path)
        if connection_image is None:
            raise FileNotFoundError(f"Verbindungsbild nicht gefunden: {connection_image_path}")
        gray = cv2.cvtColor(connection_image, cv2.COLOR_BGR2GRAY)
        image_height, image_width = gray.shape

        # Extrahiere Roboterbuchstaben aus Dateiname
        match = re.search(r'_([A-Ha-h])(?:\.|_|\b)', os.path.basename(connection_image_path))
        roboter_buchstabe = match.group(1).upper() if match else None

        # Ergänze nur den geschätzten Punkt, falls er fehlt
        if roboter_buchstabe and roboter_buchstabe not in punkt_dict:
            dummy_zentrum = (image_width / 2, image_height + 50)
            dummy_obj = Objekt("point", 100.0, (
                int(dummy_zentrum[0]) - 5, int(dummy_zentrum[1]) - 5,
                int(dummy_zentrum[0]) + 5, int(dummy_zentrum[1]) + 5
            ))
            dummy_obj.zentrum = dummy_zentrum
            dummy_obj.set_buchstabe(roboter_buchstabe)
            punkt_dict[roboter_buchstabe] = dummy_obj
            objekte_liste.append(dummy_obj)  # <--- WICHTIG!
            print(f"Info: Dummy-Punkt für {roboter_buchstabe} ergänzt bei {dummy_zentrum}")

        # Neue Buchstabenliste nach Ergänzung
        vorhandene_buchstaben = sorted(list(punkt_dict.keys()))
        n = len(vorhandene_buchstaben)
        adjacency_matrix = np.zeros((n, n), dtype=int)

        # Mapping zu Original-Indizes
        buchstaben_zu_original_index = {b: buchstaben.index(b) for b in vorhandene_buchstaben if b in buchstaben}

        # Verbindungsanalyse
        for i, b1 in enumerate(vorhandene_buchstaben):
            for j, b2 in enumerate(vorhandene_buchstaben):
                if i >= j:
                    continue

                orig_i = buchstaben_zu_original_index.get(b1)
                orig_j = buchstaben_zu_original_index.get(b2)
                if orig_i is None or orig_j is None or original_matrix[orig_i][orig_j] != 1:
                    continue

                punkt1 = punkt_dict[b1]
                punkt2 = punkt_dict[b2]
                p1 = (int(punkt1.zentrum[0]), int(punkt1.zentrum[1]))
                p2 = (int(punkt2.zentrum[0]), int(punkt2.zentrum[1]))

                dx = p2[0] - p1[0]
                dy = p2[1] - p1[1]
                length = max(1, int(np.sqrt(dx * dx + dy * dy)))
                if dx == 0 and dy == 0:
                    continue

                nx = -dy / length
                ny = dx / length

                non_white_count = 0
                total_pixels = 0

                for t in range(length):
                    x = int(p1[0] + t * dx / length)
                    y = int(p1[1] + t * dy / length)
                    for w in range(-bar_width // 2, bar_width // 2 + 1):
                        wx = int(x + w * nx)
                        wy = int(y + w * ny)
                        if 0 <= wx < gray.shape[1] and 0 <= wy < gray.shape[0]:
                            total_pixels += 1
                            if gray[wy, wx] < 245:
                                non_white_count += 1

                if total_pixels == 0:
                    print(f"Warnung: Keine Pixel im Balken zwischen {b1}-{b2}")
                    continue

                connection_ratio = non_white_count / total_pixels
                if connection_ratio >= connection_threshold:
                    adjacency_matrix[i][j] = 1
                    adjacency_matrix[j][i] = 1
                    print(f"Verbindung bestätigt: {b1}-{b2} (Ratio: {connection_ratio:.2f})")
                else:
                    print(f"Keine Verbindung: {b1}-{b2} (Ratio: {connection_ratio:.2f})")


        return adjacency_matrix, vorhandene_buchstaben

    @staticmethod
    def find_wall(objekte_liste, adjacency_matrix, matrix_buchstaben):
        """
        Gibt eine Matrix zurück mit:
        0 = keine Verbindung
        1 = Verbindung ohne Wall
        2 = Verbindung mit Wall
        """
        walls = [obj for obj in objekte_liste if obj.klasse == "wall"]
        punkte = {obj.buchstabe: obj for obj in objekte_liste if obj.buchstabe in matrix_buchstaben}

        erweiterte_matrix = np.copy(adjacency_matrix)

        for i, b1 in enumerate(matrix_buchstaben):
            for j, b2 in enumerate(matrix_buchstaben):
                if i >= j or adjacency_matrix[i][j] != 1:
                    continue

                p1 = np.array(punkte[b1].zentrum)
                p2 = np.array(punkte[b2].zentrum)

                # Prüfe, ob irgendein Wall die Linie p1-p2 schneidet
                for wall in walls:
                    wx1, wy1, wx2, wy2 = wall.bounding_box
                    wall_bbox = [(wx1, wy1), (wx2, wy1), (wx2, wy2), (wx1, wy2)]
                    wall_edges = list(zip(wall_bbox, wall_bbox[1:] + [wall_bbox[0]]))

                    for w_start, w_end in wall_edges:
                        if Objekt._linien_schneiden(p1, p2, np.array(w_start), np.array(w_end)):
                            erweiterte_matrix[i][j] = 2
                            erweiterte_matrix[j][i] = 2
                            break
                    if erweiterte_matrix[i][j] == 2:
                        break

                # Matrix speichern verschoben von create_adjacency_matrix nach hier
                dataset_dir = os.path.join(os.path.dirname(os.path.dirname("dummy_path.jpg")), "Dataset")
                matrix_dir = os.path.join(dataset_dir, "Matrix")
                os.makedirs(matrix_dir, exist_ok=True)
                matrix_path = os.path.join(matrix_dir, "Currentmatrix.txt")

                buchstaben = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
                vollstaendige_matrix = np.zeros((8, 8), dtype=int)

                for i, b1 in enumerate(matrix_buchstaben):
                    if b1 in buchstaben:
                        orig_i = buchstaben.index(b1)
                        for j, b2 in enumerate(matrix_buchstaben):
                            if b2 in buchstaben:
                                orig_j = buchstaben.index(b2)
                                vollstaendige_matrix[orig_i][orig_j] = erweiterte_matrix[i][j]

                with open(matrix_path, 'w') as f:
                    f.write("adjacency_matrix = np.array([\n")
                    f.write("    # " + " ".join(buchstaben) + "\n")
                    for i, row in enumerate(vollstaendige_matrix):
                        simple_ints = [int(x) for x in row]
                        f.write(f"    {simple_ints},  # {buchstaben[i]}\n")
                    f.write("])")

                print(f"Matrix mit Walls gespeichert unter: {matrix_path}")

                return erweiterte_matrix

        return erweiterte_matrix

    @staticmethod
    def _linien_schneiden(p1, p2, q1, q2):
        """Hilfsmethode: prüft, ob zwei Liniensegmente sich schneiden"""

        def ccw(a, b, c):
            return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])

        return (ccw(p1, q1, q2) != ccw(p2, q1, q2)) and (ccw(p1, p2, q1) != ccw(p1, p2, q2))

    @staticmethod
    def parse_text_to_objects(text):
        """
        Parst Text und erstellt Objekt-Instanzen.
        """
        import re
        objekte = []
        pattern = re.compile(
            r'([^;]+);'  # Klasse
            r'([\d.]+)%?;'  # Vertrauen
            r'\(([^)]+)\);'  # Bounding Box
            r'([\d.]+);'  # Fläche
            r'\(([^)]+)\);?'  # Zentrum
        )

        for line in text.strip().split('\n'):
            match = pattern.match(line)
            if match:
                klasse = match.group(1).strip()
                vertrauen = float(match.group(2))
                bbox = tuple(map(int, [x.strip() for x in match.group(3).split(',')]))
                flaeche = float(match.group(4))
                zentrum = tuple(map(float, [x.strip() for x in match.group(5).split(',')]))

                obj = Objekt(klasse, vertrauen, bbox)
                obj.flaeche = flaeche
                obj.zentrum = zentrum
                objekte.append(obj)

        return objekte

    @classmethod
    def assignment_E(cls, objekte_liste):
        """
        Zuordnungslogik für E, D, F und G:
        1. E - unterster Punkt
        2. Die nächsten 3 untersten Punkte werden nach X-Position sortiert und zugewiesen:
           - F (links)
           - G (mitte)
           - D (rechts)
        3. Gibt eine Liste der erkannten Punkte zurück
        """
        if not objekte_liste:
            return []

        # Liste für erkannte Punkte erstellen
        erkannte_punkte = []

        # Relevante Objekte (nur Punkte und Barrieren)
        relevante_objekte = [
            obj for obj in objekte_liste
            if obj.klasse in ['point', 'pointa', 'pointb', 'pointc', 'barrier']
        ]

        # Nach Y-Position sortieren (absteigend, unterster zuerst)
        sortierte_objekte = sorted(relevante_objekte,
                                   key=lambda obj: obj.zentrum[1],
                                   reverse=True)

        # 1. E - unterster Punkt
        if sortierte_objekte:
            unterster = sortierte_objekte[0]
            unterster.set_buchstabe('E')
            erkannte_punkte.append(unterster)

        # 2. Die nächsten 3 untersten Punkte (ohne E)
        naechste_drei = [obj for obj in sortierte_objekte[1:] if obj not in erkannte_punkte][:3]

        # Nach X-Position sortieren (aufsteigend)
        if naechste_drei:
            naechste_drei.sort(key=lambda obj: obj.zentrum[0])

            # F - Links
            if len(naechste_drei) >= 1:
                naechste_drei[0].set_buchstabe('F')
                erkannte_punkte.append(naechste_drei[0])

            # G - Mitte
            if len(naechste_drei) >= 2:
                if len(naechste_drei) == 2:
                    # Bei nur zwei Punkten: den zweiten auf D setzen
                    naechste_drei[1].set_buchstabe('D')
                    erkannte_punkte.append(naechste_drei[1])
                else:
                    # Bei drei Punkten: den mittleren auf G setzen
                    naechste_drei[1].set_buchstabe('G')
                    erkannte_punkte.append(naechste_drei[1])

            # D - Rechts
            if len(naechste_drei) >= 3:
                naechste_drei[2].set_buchstabe('D')
                erkannte_punkte.append(naechste_drei[2])

        # Konsistenzprüfung
        buchstaben = [getattr(obj, 'buchstabe', None) for obj in erkannte_punkte]
        if len([b for b in buchstaben if b]) != len(set(b for b in buchstaben if b)):
            print("Warnung: Doppelte Buchstaben erkannt!")

        return erkannte_punkte

    @classmethod
    def assignment_D(cls, objekte_liste):
        """
        Zuordnungslogik für D (Roboter befindet sich auf Punkt D):
        1. C - rechtester Punkt
        2. G - nächster Punkt zu C
        3. Gibt eine Liste der erkannten Punkte zurück
        """
        if not objekte_liste:
            return []

        # Liste für erkannte Punkte erstellen
        erkannte_punkte = []

        # Relevante Objekte (nur Punkte und Barrieren)
        relevante_objekte = [
            obj for obj in objekte_liste
            if obj.klasse in ['point', 'pointa', 'pointb', 'pointc', 'barrier']
        ]

        # Nach X-Position sortieren (absteigend, rechtester zuerst)
        sortierte_objekte = sorted(relevante_objekte,
                                   key=lambda obj: obj.zentrum[0],
                                   reverse=True)

        # 1. C - rechtester Punkt
        if sortierte_objekte:
            rechtester = sortierte_objekte[0]
            rechtester.set_buchstabe('C')
            erkannte_punkte.append(rechtester)

        # 2. G - nächster Punkt zu C
        if erkannte_punkte:
            punkt_c = erkannte_punkte[0]
            verbleibende_punkte = [obj for obj in relevante_objekte if obj not in erkannte_punkte]

            if verbleibende_punkte:
                # Finde den nächsten Punkt zu C basierend auf euklidischer Distanz
                naechster_zu_c = min(verbleibende_punkte,
                                     key=lambda obj: np.sqrt((obj.zentrum[0] - punkt_c.zentrum[0]) ** 2 +
                                                             (obj.zentrum[1] - punkt_c.zentrum[1]) ** 2))
                naechster_zu_c.set_buchstabe('G')
                erkannte_punkte.append(naechster_zu_c)

        # Konsistenzprüfung
        buchstaben = [getattr(obj, 'buchstabe', None) for obj in erkannte_punkte]
        if len([b for b in buchstaben if b]) != len(set(b for b in buchstaben if b)):
            print("Warnung: Doppelte Buchstaben erkannt!")

        return erkannte_punkte

    @classmethod
    def assignment_F(cls, objekte_liste, image_width, image_height):
        """
        Zuordnungslogik für F (Roboter befindet sich auf Punkt F):
        1. A - linkster Punkt
        2. F wird angenommen als Mitte unten +50 Pixel
        3. G und H - zwei nächste Punkte zu F
           - H ist weiter links und oben
           - G ist mehr rechts und unten
        """
        if not objekte_liste:
            return []

        erkannte_punkte = []

        # Relevante Objekte
        relevante_objekte = [
            obj for obj in objekte_liste
            if obj.klasse in ['point', 'pointa', 'pointb', 'pointc', 'barrier']
        ]

        # 1. A - linkster Punkt
        if relevante_objekte:
            linkster = min(relevante_objekte, key=lambda obj: obj.zentrum[0])
            linkster.set_buchstabe('A')
            erkannte_punkte.append(linkster)

        # 2. F - angenommene Position
        f_zentrum = (image_width / 2, image_height + 50)
        print(f"Info: Verwende angenommene Position für F (Mitte unten +50): {f_zentrum}")

        # 3. Zwei nächste Punkte zu F
        verbleibende = [obj for obj in relevante_objekte if obj not in erkannte_punkte]
        if len(verbleibende) >= 2:
            verbleibende.sort(
                key=lambda obj: np.sqrt((obj.zentrum[0] - f_zentrum[0]) ** 2 +
                                        (obj.zentrum[1] - f_zentrum[1]) ** 2)
            )
            naechste_zwei = verbleibende[:2]

            # Sortiere die zwei: H = weiter links und oben (kleineres x+y), G = anderes
            naechste_zwei.sort(key=lambda obj: obj.zentrum[0] + obj.zentrum[1])
            naechste_zwei[0].set_buchstabe('H')
            naechste_zwei[1].set_buchstabe('G')
            erkannte_punkte.extend(naechste_zwei)

        # Konsistenzprüfung
        buchstaben = [obj.buchstabe for obj in erkannte_punkte]
        if len(buchstaben) != len(set(buchstaben)):
            print("Warnung: Doppelte Buchstaben in assignment_F erkannt!")

        return erkannte_punkte

    @classmethod
    def assignment_G(cls, objekte_liste, image_width, image_height):  # <-- NEUE PARAMETER
        """
        Zuordnungslogik für G (Roboter befindet sich auf Punkt G):
        1. H - nächster Punkt zu G (angenommene Position: untere Mitte)
        2. Die pointa, pointb, pointc-Objekte werden zu A, B, C
        3. Gibt eine Liste der erkannten Punkte zurück
        """
        # ... (Anfang der Methode bleibt gleich: if not objekte_liste, erkannte_punkte, Zuweisung A,B,C) ...
        if not objekte_liste:
            return []

        erkannte_punkte = []

        # Automatische Zuweisung für pointa, pointb, pointc
        for obj in objekte_liste:
            if obj.klasse == 'pointa':
                obj.set_buchstabe('A')
                erkannte_punkte.append(obj)
            elif obj.klasse == 'pointb':
                obj.set_buchstabe('B')
                erkannte_punkte.append(obj)
            elif obj.klasse == 'pointc':
                obj.set_buchstabe('C')
                erkannte_punkte.append(obj)

        # Relevante Objekte, die noch nicht zugeordnet wurden (nur Punkte und Barrieren)
        relevante_objekte = [
            obj for obj in objekte_liste
            if obj.klasse in ['point', 'barrier'] and obj not in erkannte_punkte
        ]


        # Annahme: Der Roboter steht auf G. G ist nicht sichtbar.
        # Verwende die Mitte des unteren Bildschirmrands als Referenzpunkt für G.
        if image_width > 0 and image_height > 0:
            # Y-Koordinate ist die Höhe (oder Höhe - 1, je nach Konvention, hier nehmen wir Höhe an)
            # X-Koordinate ist die halbe Breite
            g_zentrum = (image_width / 2, image_height)
            print(f"Info: Verwende angenommene Position für G (untere Mitte): {g_zentrum}")
        else:
            # Fallback oder Fehlerbehandlung, falls keine Bilddimensionen vorhanden sind
            print("Warnung: Keine Bilddimensionen für assignment_G erhalten. Kann G-Referenz nicht setzen.")
            g_zentrum = None  # Oder einen Standardwert, oder Fehler auslösen


        # 1. H - nächster Punkt zum angenommenen G-Zentrum
        if g_zentrum and relevante_objekte:
            # Finde den nächsten Punkt zum *angenommenen* G-Zentrum
            try:
                naechster_zu_g = min(relevante_objekte,
                                     key=lambda obj: np.sqrt((obj.zentrum[0] - g_zentrum[0]) ** 2 +
                                                             (obj.zentrum[1] - g_zentrum[1]) ** 2))
                naechster_zu_g.set_buchstabe('H')
                erkannte_punkte.append(naechster_zu_g)
                print(f"Info: H zugewiesen (nächster zu angenommener G-Position): {naechster_zu_g}")
            except ValueError:
                print("Warnung: Keine relevanten Objekte gefunden, um H relativ zu G zuzuordnen.")

        # Konsistenzprüfung
        buchstaben = [getattr(obj, 'buchstabe', None) for obj in erkannte_punkte]
        if len([b for b in buchstaben if b]) != len(set(b for b in buchstaben if b)):
            print("Warnung: Doppelte Buchstaben nach assignment_G erkannt!")

        return erkannte_punkte

    @classmethod
    def assignment_C(cls, objekte_liste):
        """
        Zuordnungslogik für C (Roboter befindet sich auf Punkt C):
        1. B - rechtester Punkt (wenn es pointb ist) oder einfach der rechteste Punkt generell
        2. H - nächster Punkt zu B
        3. Gibt eine Liste der erkannten Punkte zurück
        """
        if not objekte_liste:
            return []

        # Liste für erkannte Punkte erstellen
        erkannte_punkte = []

        # Relevante Objekte (alle Punkte und Barrieren)
        relevante_objekte = [
            obj for obj in objekte_liste
            if obj.klasse in ['point', 'pointa', 'pointb', 'pointc', 'barrier']
        ]

        # Nach X-Position sortieren (absteigend, rechtester zuerst)
        sortierte_objekte = sorted(relevante_objekte,
                                   key=lambda obj: obj.zentrum[0],
                                   reverse=True)

        # 1. B - rechtester Punkt mit Prüfung auf pointb
        if sortierte_objekte:
            # Prüfe, ob der rechteste Punkt ein pointb ist
            pointb_objekte = [obj for obj in sortierte_objekte if obj.klasse == 'pointb']

            if pointb_objekte and pointb_objekte[0] == sortierte_objekte[0]:
                # Der rechteste Punkt ist ein pointb
                punkt_b = pointb_objekte[0]
            else:
                # Nimm einfach den rechtesten Punkt
                punkt_b = sortierte_objekte[0]

            punkt_b.set_buchstabe('B')
            erkannte_punkte.append(punkt_b)

        # 2. H - nächster Punkt zu B
        if erkannte_punkte:
            punkt_b = erkannte_punkte[0]
            verbleibende_punkte = [obj for obj in relevante_objekte if obj not in erkannte_punkte]

            if verbleibende_punkte:
                # Finde den nächsten Punkt zu B basierend auf euklidischer Distanz
                naechster_zu_b = min(verbleibende_punkte,
                                     key=lambda obj: np.sqrt((obj.zentrum[0] - punkt_b.zentrum[0]) ** 2 +
                                                             (obj.zentrum[1] - punkt_b.zentrum[1]) ** 2))
                naechster_zu_b.set_buchstabe('H')
                erkannte_punkte.append(naechster_zu_b)

        # Konsistenzprüfung
        buchstaben = [getattr(obj, 'buchstabe', None) for obj in erkannte_punkte]
        if len([b for b in buchstaben if b]) != len(set(b for b in buchstaben if b)):
            print("Warnung: Doppelte Buchstaben erkannt!")

        return erkannte_punkte

    @classmethod
    def assignment_H(cls, objekte_liste):
        """
        Zuordnungslogik für H (Roboter befindet sich auf Punkt H):
        1. B - wenn ein Objekt als pointb erkannt wurde, sonst das nächste Objekt zu H
        2. Gibt eine Liste der erkannten Punkte zurück
        3. Position von H wird als unten in der Mitte des Bildes angenommen
        """
        if not objekte_liste:
            return []

        # Liste für erkannte Punkte erstellen
        erkannte_punkte = []

        # Relevante Objekte (alle Punkte und Barrieren)
        relevante_objekte = [
            obj for obj in objekte_liste
            if obj.klasse in ['point', 'pointa', 'pointb', 'pointc', 'barrier']
        ]

        # 1. Prüfen, ob ein Objekt als pointb klassifiziert wurde
        pointb_objekte = [obj for obj in relevante_objekte if obj.klasse == 'pointb']

        if pointb_objekte:
            # Verwende das als pointb erkannte Objekt
            punkt_b = pointb_objekte[0]
            punkt_b.set_buchstabe('B')
            erkannte_punkte.append(punkt_b)
        else:
            # Schätze die Position von H (unten in der Mitte des Bildes)
            # In einer realen Anwendung würde diese Information aus den Bilddimensionen oder
            # aus Sensorwerten kommen

            # Berechne die maximalen X- und Y-Koordinaten aus allen sichtbaren Objekten
            if relevante_objekte:
                max_x = max(obj.zentrum[0] for obj in relevante_objekte)
                max_y = max(obj.zentrum[1] for obj in relevante_objekte)
                min_x = min(obj.zentrum[0] for obj in relevante_objekte)

                # H ist am unteren Rand in der Mitte des Bildes
                h_position = ((min_x + max_x) / 2, max_y)

                # Finde das nächste Objekt zu dieser geschätzten H-Position
                naechster_zu_h = min(relevante_objekte,
                                     key=lambda obj: np.sqrt((obj.zentrum[0] - h_position[0]) ** 2 +
                                                             (obj.zentrum[1] - h_position[1]) ** 2))
                naechster_zu_h.set_buchstabe('B')
                erkannte_punkte.append(naechster_zu_h)

        # Konsistenzprüfung
        buchstaben = [getattr(obj, 'buchstabe', None) for obj in erkannte_punkte]
        if len([b for b in buchstaben if b]) != len(set(b for b in buchstaben if b)):
            print("Warnung: Doppelte Buchstaben erkannt!")

        return erkannte_punkte

    @classmethod
    def assignment_A(cls, objekte_liste):
        """
        Zuordnungslogik für A (Roboter befindet sich auf Punkt A):
        1. B - linkster Punkt
        2. H - nächster Punkt zu B
        3. Gibt eine Liste der erkannten Punkte zurück
        """
        if not objekte_liste:
            print("Warnung: Leere Objektliste an assignment_A übergeben.")
            return []

        erkannte_punkte = []
        punkt_b = None

        # Relevante Objekte filtern (z.B. Punkte und Barrieren)
        # Passe die Klassen bei Bedarf an.
        relevante_objekte = [
            obj for obj in objekte_liste
            if obj.klasse in ['point', 'pointa', 'pointb', 'pointc', 'barrier']
               and getattr(obj, 'buchstabe', None) is None  # Nur Objekte ohne Buchstaben berücksichtigen
        ]

        if not relevante_objekte:
            print("Warnung: Keine relevanten, nicht zugewiesenen Objekte für assignment_A gefunden.")
            return []  # Rückgabe leerer Liste, wenn keine relevanten Objekte da sind

        # --- 1. B - linkster Punkt ---
        try:
            # Sortiere nach X-Koordinate (aufsteigend), um den linkesten zu finden
            relevante_objekte.sort(key=lambda obj: obj.zentrum[0])
            punkt_b = relevante_objekte[0]
            punkt_b.set_buchstabe('B')
            erkannte_punkte.append(punkt_b)
            print(f"Info [assignment_A]: B zugewiesen (linkster Punkt): {punkt_b}")
        except IndexError:
            print("Fehler [assignment_A]: Konnte keinen linksten Punkt für B finden (Liste evtl. leer nach Filterung).")
            return erkannte_punkte  # B konnte nicht zugewiesen werden

        # --- 2. H - nächster Punkt zu B ---
        # Entferne B aus der Liste der Kandidaten für H
        verbleibende_punkte = [obj for obj in relevante_objekte if obj is not punkt_b]  # Identitätsvergleich

        if verbleibende_punkte:
            try:
                # Finde den nächsten Punkt zu B basierend auf euklidischer Distanz
                naechster_zu_b = min(verbleibende_punkte,
                                     key=lambda obj: np.sqrt((obj.zentrum[0] - punkt_b.zentrum[0]) ** 2 +
                                                             (obj.zentrum[1] - punkt_b.zentrum[1]) ** 2))
                naechster_zu_b.set_buchstabe('H')
                erkannte_punkte.append(naechster_zu_b)
                print(f"Info [assignment_A]: H zugewiesen (nächster zu B): {naechster_zu_b}")
            except ValueError:
                # Sollte nicht passieren, wenn verbleibende_punkte nicht leer ist, aber sicherheitshalber
                print("Warnung [assignment_A]: Fehler beim Finden des nächsten Punktes zu B.")
        else:
            print(
                "Warnung [assignment_A]: Keine verbleibenden Punkte nach Zuweisung von B gefunden, um H zu bestimmen.")

        # Konsistenzprüfung (optional, aber empfohlen)
        buchstaben_gefunden = [p.buchstabe for p in erkannte_punkte]
        if len(buchstaben_gefunden) != len(set(buchstaben_gefunden)):
            print(f"Warnung [assignment_A]: Doppelte Buchstaben erkannt: {buchstaben_gefunden}")

        return erkannte_punkte



    @classmethod
    def draw_objects_on_image(cls, image_path, objekte_liste, output_path="output.jpg", bar_width=20):
        """
        Zeichnet alle Objekte mit Buchstaben und Verbindungsbalken auf das Bild,
        aber nur Verbindungen, die in der tatsächlichen Adjazenzmatrix gefunden wurden.
        """
        try:
            # Bild laden
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Bilddatei nicht gefunden: {image_path}")

            image = Image.open(image_path)
            draw = ImageDraw.Draw(image)

            # Schriftart laden
            try:
                font_size = max(10, int(image.width / 50))
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()

            # Farbdefinitionen
            colors = {
                'A': (255, 0, 0),  # Rot
                'B': (0, 255, 0),  # Grün
                'C': (0, 0, 255),  # Blau
                'D': (255, 255, 0),  # Gelb
                'E': (255, 0, 255),  # Magenta
                'F': (0, 255, 255),  # Cyan
                'G': (255, 165, 0),  # Orange
                'H': (128, 0, 128),  # Lila
                'default': (0, 255, 255)  # Cyan
            }

            # Linienstärke
            thickness = max(2, int(image.width / 400))

            # Buchstaben für Punkte und Adjazenzmatrix erstellen
            buchstaben = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
            punkt_dict = {obj.buchstabe: obj for obj in objekte_liste if obj.buchstabe in buchstaben}
            vorhandene_buchstaben = sorted(list(punkt_dict.keys()))

            # Erstelle die Adjazenzmatrix basierend auf dem aktuellen Bild
            adj_matrix, matrix_buchstaben = cls.create_adjacency_matrix(objekte_liste, image_path)

            # Erstelle ein Mapping der Buchstaben-Indizes in der Matrix
            buchstaben_zu_matrix_index = {b: matrix_buchstaben.index(b) for b in matrix_buchstaben}

            # Alle gefundenen Verbindungen zeichnen (nur diejenigen, die in der Matrix auf 1 gesetzt sind)
            for i, b1 in enumerate(matrix_buchstaben):
                for j, b2 in enumerate(matrix_buchstaben):
                    if i >= j:  # Nur obere Dreiecksmatrix prüfen
                        continue

                    # Nur zeichnen, wenn in der tatsächlichen Adjazenzmatrix eine Verbindung besteht
                    if adj_matrix[i][j] != 1:
                        continue

                    punkt1 = punkt_dict[b1]
                    punkt2 = punkt_dict[b2]
                    p1 = (int(punkt1.zentrum[0]), int(punkt1.zentrum[1]))
                    p2 = (int(punkt2.zentrum[0]), int(punkt2.zentrum[1]))

                    # Farbe für die Verbindung (Mittelwert der beiden Punktfarben)
                    color1 = colors.get(b1, colors['default'])
                    color2 = colors.get(b2, colors['default'])
                    line_color = tuple((c1 + c2) // 2 for c1, c2 in zip(color1, color2))

                    # Vektor zwischen den Punkten berechnen
                    dx = p2[0] - p1[0]
                    dy = p2[1] - p1[1]
                    length = max(1, int(np.sqrt(dx * dx + dy * dy)))

                    # Normalvektor für die Breite des Balkens
                    if dx == 0 and dy == 0:  # Falls Punkte identisch sind
                        continue

                    # Normalisierter Richtungsvektor
                    nx = -dy / length
                    ny = dx / length

                    # Punkte für das Polygon des Balkens berechnen
                    polygon_points = []

                    # Obere Seite des Balkens
                    for t in [0, length]:
                        x = p1[0] + t * dx / length
                        y = p1[1] + t * dy / length
                        wx = int(x + (bar_width / 2) * nx)
                        wy = int(y + (bar_width / 2) * ny)
                        polygon_points.append((wx, wy))

                    # Untere Seite des Balkens (in umgekehrter Reihenfolge)
                    for t in [length, 0]:
                        x = p1[0] + t * dx / length
                        y = p1[1] + t * dy / length
                        wx = int(x - (bar_width / 2) * nx)
                        wy = int(y - (bar_width / 2) * ny)
                        polygon_points.append((wx, wy))

                    # Balken zeichnen (halbdurchsichtig)
                    draw.polygon(polygon_points, fill=line_color + (128,), outline=line_color)
                    print(f"Verbindung gezeichnet: {b1}-{b2}")

            # Dann alle Objekte zeichnen (über den Balken)
            for obj in objekte_liste:
                # Farbe bestimmen
                color = colors.get(
                    obj.buchstabe if obj.buchstabe else
                    obj.klasse[-1].upper() if obj.klasse in ['pointa', 'pointb', 'pointc'] else 'default',
                    colors['default'])

                # Bounding Box zeichnen
                x1, y1, x2, y2 = obj.bounding_box
                draw.rectangle([x1, y1, x2, y2], outline=color, width=thickness)

                # Textgröße berechnen (kompatibel mit Pillow >= 8.0.0)
                text = obj.buchstabe if obj.buchstabe else obj.klasse
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]

                # Textposition (zentriert über der Box)
                text_x = x1 + (x2 - x1 - text_width) / 2
                text_y = max(y1 - text_height - 5, 0)  # Verhindert negative Y-Position

                # Text-Hintergrund für bessere Lesbarkeit
                draw.rectangle(
                    [text_x - 2, text_y - 2,
                     text_x + text_width + 2, text_y + text_height + 2],
                    fill=(0, 0, 0))

                # Text zeichnen
                draw.text((text_x, text_y), text, font=font, fill=color)

                # Zentrumspunkt zeichnen
                cx, cy = obj.zentrum
                draw.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=color)

            # Ausgabeverzeichnis erstellen falls nötig
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            image.save(output_path)
            print(f"Ergebnisbild gespeichert unter: {os.path.abspath(output_path)}")

        except Exception as e:
            print(f"Fehler beim Zeichnen der Objekte: {str(e)}")
            raise

    def __str__(self):
        buchstabe_info = f", Buchstabe: {self.buchstabe}" if self.buchstabe else ""
        return f"Objekt: {self.klasse}, Vertrauen: {self.vertrauen}%, Zentrum: {self.zentrum}, Fläche: {self.flaeche}{buchstabe_info}"

    def __repr__(self):
        return f"Objekt(klasse='{self.klasse}', vertrauen={self.vertrauen}, bounding_box={self.bounding_box})"

# Verwendung
# In the main section, replace your current code with:
if __name__ == "__main__":
    import os
    import re

    try:
        base_dir = r'C:\Users\marin\PycharmProjects\PREN1G11\src\utils\aplha\Dataset'

        # Alle Bild-Text-Paare erkennen (z. B. bearbeitet_Test2_A.jpg + Test2_A.txt)
        szenarien = []
        for dateiname in os.listdir(base_dir):
            if dateiname.lower().endswith(".jpg"):
                match = re.search(r'_([A-Ha-h])\.', dateiname)
                if match:
                    buchstabe = match.group(1).upper()
                    bild_path = os.path.join(base_dir, dateiname)

                    # Versuche zugehörige .txt Datei zu finden
                    txt_candidates = [
                        f for f in os.listdir(base_dir)
                        if f.lower().endswith(".txt") and f"_{buchstabe}." in f
                    ]
                    if txt_candidates:
                        txt_path = os.path.join(base_dir, txt_candidates[0])
                        szenarien.append((buchstabe, txt_path, bild_path))

        alle_erkannten_objekte = []

        for buchstabe, txt_path, bild_path in szenarien:
            print(f"\n--- Verarbeitung für Punkt {buchstabe} ---")

            with open(txt_path, 'r') as file:
                objekte = Objekt.parse_text_to_objects(file.read())

            # Aufruf der passenden Assignment-Methode
            assignment_func = getattr(Objekt, f'assignment_{buchstabe}', None)
            if assignment_func:
                # Für assignment_G Bildgröße mitgeben
                if assignment_func.__name__ in ['assignment_G', 'assignment_F']:
                    image = cv2.imread(bild_path)
                    if image is None:
                        raise FileNotFoundError(f"Bild für assignment_G nicht gefunden: {bild_path}")
                    height, width = image.shape[:2]
                    erkannte = assignment_func(objekte, width, height)
                else:
                    erkannte = assignment_func(objekte)

            else:
                print(f"⚠️ Keine Assignment-Methode für Buchstabe {buchstabe} gefunden.")
                erkannte = []

            alle_erkannten_objekte += erkannte

            # Matrix (nur Linien)
            matrix, matrix_buchstaben = Objekt.create_adjacency_matrix(objekte, bild_path)

            print(f"\nMatrix nach Assignment {buchstabe} (nur Linien):")
            print("   " + " ".join(matrix_buchstaben))
            for i, row in enumerate(matrix):
                # Konvertiere np.int64 zu einfachen int-Werten
                simple_ints = [int(x) for x in row]
                print(f"{matrix_buchstaben[i]} {simple_ints}")

            # Walls prüfen
            matrix_mit_walls = Objekt.find_wall(objekte, matrix, matrix_buchstaben)

            print(f"\nMatrix nach Assignment {buchstabe} (mit Walls geprüft – 0=keine, 1=Linie, 2=Wall):")
            print("   " + " ".join(matrix_buchstaben))
            for i, row in enumerate(matrix_mit_walls):
                # Konvertiere np.int64 zu einfachen int-Werten
                simple_ints = [int(x) for x in row]
                print(f"{matrix_buchstaben[i]} {simple_ints}")

            # Bild ausgeben
            output_path = os.path.join(base_dir, f'output_{buchstabe}.jpg')
            Objekt.draw_objects_on_image(bild_path, objekte, output_path)

        # Einmalige Ausgabe aller eindeutigen Buchstaben
        print("\nKombinierte eindeutige Objekte aus allen Szenarien:")
        unique_objekte = {}
        for obj in alle_erkannten_objekte:
            if obj.buchstabe and obj.buchstabe not in unique_objekte:
                unique_objekte[obj.buchstabe] = obj
        for b, obj in unique_objekte.items():
            print(f"Buchstabe {b}: {obj.klasse} bei {obj.zentrum}")

    except Exception as e:
        print(f"Fehler: {str(e)}")
        import traceback
        traceback.print_exc()

