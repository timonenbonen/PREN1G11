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
        """Erstellt eine Adjazenzmatrix mit Analyse eines breiten Balkens zwischen Punkten."""
        # Buchstaben-Liste für das Original-Schema
        buchstaben = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']

        # Original Matrix als Vorlage
        original_matrix = np.array([
            # A B C D E F G H
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
        print("Vorhandene Buchstaben:", vorhandene_buchstaben)

        # Neue Matrix für vorhandene Buchstaben
        n = len(vorhandene_buchstaben)
        adjacency_matrix = np.zeros((n, n), dtype=int)

        # Mapping zu Original-Indizes
        buchstaben_zu_original_index = {b: buchstaben.index(b) for b in vorhandene_buchstaben if b in buchstaben}

        try:
            # Bild laden und in Graustufen umwandeln
            connection_image = cv2.imread(connection_image_path)
            if connection_image is None:
                raise FileNotFoundError(f"Verbindungsbild nicht gefunden: {connection_image_path}")
            gray = cv2.cvtColor(connection_image, cv2.COLOR_BGR2GRAY)

            # Alle möglichen Verbindungen prüfen
            for i, b1 in enumerate(vorhandene_buchstaben):
                for j, b2 in enumerate(vorhandene_buchstaben):
                    if i >= j:  # Nur obere Dreiecksmatrix prüfen
                        continue

                    # Prüfen, ob in Original-Matrix eine Verbindung vorhanden ist
                    orig_i = buchstaben_zu_original_index.get(b1)
                    orig_j = buchstaben_zu_original_index.get(b2)
                    if orig_i is None or orig_j is None or original_matrix[orig_i][orig_j] != 1:
                        continue

                    punkt1 = punkt_dict[b1]
                    punkt2 = punkt_dict[b2]
                    p1 = (int(punkt1.zentrum[0]), int(punkt1.zentrum[1]))
                    p2 = (int(punkt2.zentrum[0]), int(punkt2.zentrum[1]))

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

                    # Pixel im Balken analysieren
                    non_white_count = 0
                    total_pixels = 0

                    # Durch die Länge der Linie gehen
                    for t in range(length):
                        # Mittelpunkt der Linie bei diesem t
                        x = int(p1[0] + t * dx / length)
                        y = int(p1[1] + t * dy / length)

                        # Durch die Breite des Balkens gehen
                        for w in range(-bar_width // 2, bar_width // 2 + 1):
                            wx = int(x + w * nx)
                            wy = int(y + w * ny)

                            # Sicherstellen, dass die Koordinaten im Bild liegen
                            if 0 <= wx < gray.shape[1] and 0 <= wy < gray.shape[0]:
                                total_pixels += 1
                                if gray[wy, wx] < 245:  # Nicht weiß
                                    non_white_count += 1

                    if total_pixels == 0:
                        print(f"Warnung: Keine Pixel im Balken zwischen {b1}-{b2}")
                        continue

                    # Verhältnis berechnen
                    connection_ratio = non_white_count / total_pixels

                    # Verbindung basierend auf dem Verhältnis bestimmen
                    if connection_ratio >= connection_threshold:
                        adjacency_matrix[i][j] = 1
                        adjacency_matrix[j][i] = 1  # Symmetrie einhalten
                        print(f"Verbindung bestätigt: {b1}-{b2} (Ratio: {connection_ratio:.2f})")
                    else:
                        print(f"Keine Verbindung: {b1}-{b2} (Ratio: {connection_ratio:.2f})")

        except Exception as e:
            print(f"Fehler bei Matrix-Erstellung: {str(e)}")
            import traceback
            traceback.print_exc()

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
    def assignment_F(cls, objekte_liste):
        """
        Zuordnungslogik für F, A, H und G:
        1. F - Punkt, der am nächsten zur Mitte des unteren Bildrandes ist
        2. Die untersten drei Punkte werden nach X-Position sortiert und zugewiesen:
           - A (links)
           - H (mitte)
           - G (rechts)
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

        # Wenn keine Objekte gefunden wurden, leere Liste zurückgeben
        if not relevante_objekte:
            return []

        # Bildgröße abschätzen (maximale Koordinaten als Näherung)
        max_x = max(obj.bounding_box[2] for obj in relevante_objekte)
        max_y = max(obj.bounding_box[3] for obj in relevante_objekte)

        # 1. F - Punkt am nächsten zur Mitte des unteren Bildrands
        unterer_bildrand_mitte = (max_x / 2, max_y)

        # Nehme den Punkt mit der kleinsten Distanz zur Bildmitte unten
        f_punkt = min(relevante_objekte,
                      key=lambda obj: ((obj.zentrum[0] - unterer_bildrand_mitte[0]) ** 2 +
                                       (obj.zentrum[1] - unterer_bildrand_mitte[1]) ** 2) ** 0.5)
        f_punkt.set_buchstabe('F')
        erkannte_punkte.append(f_punkt)

        # 2. Die drei untersten Punkte (ohne F)
        unterste_punkte = [obj for obj in relevante_objekte if obj != f_punkt]
        unterste_punkte.sort(key=lambda obj: obj.zentrum[1], reverse=True)  # Nach Y absteigend (unterste zuerst)
        unterste_drei = unterste_punkte[:3]

        # Nach X-Position sortieren (aufsteigend)
        if unterste_drei:
            unterste_drei.sort(key=lambda obj: obj.zentrum[0])

            # A - Links
            if len(unterste_drei) >= 1:
                unterste_drei[0].set_buchstabe('A')
                erkannte_punkte.append(unterste_drei[0])

            # H - Mitte
            if len(unterste_drei) >= 2:
                if len(unterste_drei) == 2:
                    # Bei nur zwei Punkten: den zweiten auf G setzen
                    unterste_drei[1].set_buchstabe('G')
                    erkannte_punkte.append(unterste_drei[1])
                else:
                    # Bei drei Punkten: den mittleren auf H setzen
                    unterste_drei[1].set_buchstabe('H')
                    erkannte_punkte.append(unterste_drei[1])

            # G - Rechts
            if len(unterste_drei) >= 3:
                unterste_drei[2].set_buchstabe('G')
                erkannte_punkte.append(unterste_drei[2])

        # Konsistenzprüfung
        buchstaben = [getattr(obj, 'buchstabe', None) for obj in erkannte_punkte]
        if len([b for b in buchstaben if b]) != len(set(b for b in buchstaben if b)):
            print("Warnung: Doppelte Buchstaben erkannt!")

        return erkannte_punkte

    @classmethod
    def assignment_G(cls, objekte_liste):
        """
        Zuordnungslogik für G und H:
        1. G - Unterster Punkt von den Punkten, die am nächsten zur vertikalen Mittellinie des Bildes sind.
        2. H - Punkt, der am nächsten zu G ist.
        3. Danach: Punkte mit Klassen pointa, pointb und pointc werden zu A, B, C zugewiesen.
        4. Gibt eine Liste der erkannten Punkte zurück.
        """
        if not objekte_liste:
            return []

        erkannte_punkte = []

        relevante_objekte = [
            obj for obj in objekte_liste
            if obj.klasse in ['point', 'pointa', 'pointb', 'pointc', 'barrier']
        ]

        if not relevante_objekte:
            return []

        max_x = max(obj.bounding_box[2] for obj in relevante_objekte)
        vertikale_mittellinie_x = max_x / 2

        # Nur Punkte, die noch keinen Buchstaben haben
        verfuegbare_punkte = relevante_objekte.copy()

        # Berechne Abstand zur Mittellinie
        for obj in verfuegbare_punkte:
            obj.abstand_zur_mittellinie = abs(obj.zentrum[0] - vertikale_mittellinie_x)

        # Sortiere nach Abstand zur Mittellinie
        verfuegbare_punkte.sort(key=lambda obj: obj.abstand_zur_mittellinie)

        nahe_punkte = verfuegbare_punkte[:min(len(verfuegbare_punkte), 3)]

        if nahe_punkte:
            g_punkt = max(nahe_punkte, key=lambda obj: obj.zentrum[1])
            g_punkt.set_buchstabe('G')
            erkannte_punkte.append(g_punkt)

            verfuegbare_punkte.remove(g_punkt)

            if verfuegbare_punkte:
                h_punkt = min(
                    verfuegbare_punkte,
                    key=lambda obj: ((obj.zentrum[0] - g_punkt.zentrum[0]) ** 2 + (
                                obj.zentrum[1] - g_punkt.zentrum[1]) ** 2) ** 0.5
                )
                h_punkt.set_buchstabe('H')
                erkannte_punkte.append(h_punkt)

                verfuegbare_punkte.remove(h_punkt)

        # Danach: pointa, pointb, pointc zu A, B, C zuweisen
        for obj in verfuegbare_punkte:
            if obj.klasse == 'pointa':
                obj.set_buchstabe('A')
                erkannte_punkte.append(obj)
            elif obj.klasse == 'pointb':
                obj.set_buchstabe('B')
                erkannte_punkte.append(obj)
            elif obj.klasse == 'pointc':
                obj.set_buchstabe('C')
                erkannte_punkte.append(obj)

        # Konsistenzprüfung
        buchstaben = [getattr(obj, 'buchstabe', None) for obj in erkannte_punkte]
        if len([b for b in buchstaben if b]) != len(set(b for b in buchstaben if b)):
            print("Warnung: Doppelte Buchstaben erkannt!")

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
    try:
        # === 1. Eingaben einlesen für E, F und G ===
        base_dir = r'C:\Users\marin\PycharmProjects\PREN1G11\src\utils\aplha\Dataset'

        # Pfade für alle drei Szenarien definieren
        objekte_paths = {
            'E': os.path.join(base_dir, 'objekte_E.txt'),
            'F': os.path.join(base_dir, 'objekte_F.txt'),
            'G': os.path.join(base_dir, 'objekte_G.txt')
        }

        img_paths = {
            'E': os.path.join(base_dir, 'bildE.jpg'),
            'F': os.path.join(base_dir, 'bildF.jpg'),
            'G': os.path.join(base_dir, 'bildG.jpg')
        }

        # === 2. Verarbeitung für Szenario E ===
        with open(objekte_paths['E']) as file:
            objekte_E = Objekt.parse_text_to_objects(file.read())

        erkannte_E = Objekt.assignment_E(objekte_E)

        # Matrix erstellen (nur Linien)
        matrix_E, buchstaben_E = Objekt.create_adjacency_matrix(objekte_E, img_paths['E'])

        print("\nMatrix nach Assignment E (nur Linien):")
        print("   " + " ".join(buchstaben_E))
        for i, row in enumerate(matrix_E):
            print(f"{buchstaben_E[i]} {list(row)}")

        # Walls prüfen
        matrix_E_mit_walls = Objekt.find_wall(objekte_E, matrix_E, buchstaben_E)

        print("\nMatrix nach Assignment E (mit Walls geprüft – 0=keine, 1=Linie, 2=Wall):")
        print("   " + " ".join(buchstaben_E))
        for i, row in enumerate(matrix_E_mit_walls):
            print(f"{buchstaben_E[i]} {list(row)}")

        # Ergebnisbild für E erstellen
        output_path_E = os.path.join(base_dir, 'output_E.jpg')
        Objekt.draw_objects_on_image(img_paths['E'], objekte_E, output_path_E)

        # === 3. Verarbeitung für Szenario F ===
        with open(objekte_paths['F']) as file:
            objekte_F = Objekt.parse_text_to_objects(file.read())

        erkannte_F = Objekt.assignment_F(objekte_F)

        # Matrix erstellen (nur Linien)
        matrix_F, buchstaben_F = Objekt.create_adjacency_matrix(objekte_F, img_paths['F'])

        print("\nMatrix nach Assignment F (nur Linien):")
        print("   " + " ".join(buchstaben_F))
        for i, row in enumerate(matrix_F):
            print(f"{buchstaben_F[i]} {list(row)}")

        # Walls prüfen
        matrix_F_mit_walls = Objekt.find_wall(objekte_F, matrix_F, buchstaben_F)

        print("\nMatrix nach Assignment F (mit Walls geprüft – 0=keine, 1=Linie, 2=Wall):")
        print("   " + " ".join(buchstaben_F))
        for i, row in enumerate(matrix_F_mit_walls):
            print(f"{buchstaben_F[i]} {list(row)}")

        # Ergebnisbild für F erstellen
        output_path_F = os.path.join(base_dir, 'output_F.jpg')
        Objekt.draw_objects_on_image(img_paths['F'], objekte_F, output_path_F)

        # === 4. NEU: Verarbeitung für Szenario G ===
        with open(objekte_paths['G']) as file:
            objekte_G = Objekt.parse_text_to_objects(file.read())

        erkannte_G = Objekt.assignment_G(objekte_G)

        # Matrix erstellen (nur Linien)
        matrix_G, buchstaben_G = Objekt.create_adjacency_matrix(objekte_G, img_paths['G'])

        print("\nMatrix nach Assignment G (nur Linien):")
        print("   " + " ".join(buchstaben_G))
        for i, row in enumerate(matrix_G):
            print(f"{buchstaben_G[i]} {list(row)}")

        # Walls prüfen
        matrix_G_mit_walls = Objekt.find_wall(objekte_G, matrix_G, buchstaben_G)

        print("\nMatrix nach Assignment G (mit Walls geprüft – 0=keine, 1=Linie, 2=Wall):")
        print("   " + " ".join(buchstaben_G))
        for i, row in enumerate(matrix_G_mit_walls):
            print(f"{buchstaben_G[i]} {list(row)}")

        # Ergebnisbild für G erstellen
        output_path_G = os.path.join(base_dir, 'output_G.jpg')
        Objekt.draw_objects_on_image(img_paths['G'], objekte_G, output_path_G)

        # === 5. Finale Matrix mit kombinierten Punkten aus allen Szenarien ===
        print("\nKombinierte Objekte aus allen Szenarien:")
        alle_objekte = objekte_E + objekte_F + objekte_G
        unique_objekte = {}
        for obj in alle_objekte:
            if obj.buchstabe and obj.buchstabe not in unique_objekte:
                unique_objekte[obj.buchstabe] = obj
        combined_objekte = list(unique_objekte.values())

        # Ausgabe der kombinierten Objekte
        for obj in combined_objekte:
            print(f"Buchstabe {obj.buchstabe}: {obj.klasse} bei {obj.zentrum}")

    except Exception as e:
        print(f"Fehler: {str(e)}")
        import traceback

        traceback.print_exc()

