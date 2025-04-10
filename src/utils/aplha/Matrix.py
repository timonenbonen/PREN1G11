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
    def assign_letters(cls, objekte_liste):
        """
        Finale Zuordnungslogik:
        1. Filtere nur Punkte und Barrieren (ignoriere Wände)
        2. Oberstes Objekt (Punkt/Barriere) wird B
        3. Nächste 3 Objekte: A (links), H (mitte), C (rechts)
        4. Rest bleibt unmarkiert
        """
        if not objekte_liste:
            return

        # 1. Filtere nur Punkte und Barrieren (keine Wände)
        relevante_objekte = [
            obj for obj in objekte_liste
            if obj.klasse in ['point', 'pointa', 'pointb', 'pointc', 'barrier']
        ]

        # 2. Sortiere nach Y (aufsteigend) und X (aufsteigend)
        sorted_objekte = sorted(relevante_objekte,
                                key=lambda obj: (obj.zentrum[1], obj.zentrum[0]))

        # 3. Oberstes Objekt als B markieren (falls nicht wall und kein Buchstabe)
        if len(sorted_objekte) > 0 and not sorted_objekte[0].buchstabe:
            sorted_objekte[0].set_buchstabe('B')

        # 4. Nächste 3 Objekte als A, H, C markieren
        if len(sorted_objekte) > 1:
            next_objects = sorted(sorted_objekte[1:4],
                                  key=lambda obj: obj.zentrum[0])  # Sortiere nur nach X

            # Linkestes -> A
            if len(next_objects) > 0 and not next_objects[0].buchstabe:
                next_objects[0].set_buchstabe('A')

            # Mittleres -> H (falls genau 3 Objekte)
            if len(next_objects) >= 3 and not next_objects[1].buchstabe:
                next_objects[1].set_buchstabe('H')

            # Rechtsestes -> C
            if len(next_objects) >= 2 and not next_objects[-1].buchstabe:
                next_objects[-1].set_buchstabe('C')

            # 3. Normale Zuordnung für den Rest (E, G, D, F)
            # E - unterster Punkt
            point_objekte = [obj for obj in objekte_liste if obj.klasse == 'point']
            if point_objekte:
                unterster = max(point_objekte, key=lambda obj: obj.zentrum[1])
                if not unterster.buchstabe:
                    unterster.set_buchstabe('E')

            # G - nächstes Objekt zu E
            e_obj = next((obj for obj in objekte_liste if getattr(obj, 'buchstabe', None) == 'E'), None)
            if e_obj:
                freie_objekte = [obj for obj in objekte_liste
                                 if not getattr(obj, 'buchstabe', None) and obj != e_obj]
                if freie_objekte:
                    g_obj = min(freie_objekte,
                                key=lambda obj: abs(obj.zentrum[0] - e_obj.zentrum[0]))
                    g_obj.set_buchstabe('G')

            # D/F - übrige Punkte
            freie = [obj for obj in objekte_liste if not getattr(obj, 'buchstabe', None)]
            if len(freie) == 1:
                freie[0].set_buchstabe('D')
            elif len(freie) >= 2:
                freie.sort(key=lambda obj: obj.zentrum[0])  # Sort by X
                freie[0].set_buchstabe('F')
                freie[-1].set_buchstabe('D')

            # Konsistenzprüfung
            buchstaben = [getattr(obj, 'buchstabe', None) for obj in objekte_liste]
            if len([b for b in buchstaben if b]) != len(set(b for b in buchstaben if b)):
                print("Warnung: Doppelte Buchstaben erkannt!")

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
if __name__ == "__main__":
    try:
        # 1. Objekte laden
        with open(r'/src/utils/tests/Bilder/Bodenlinien/objekte1.txt') as file:
            objekte = Objekt.parse_text_to_objects(file.read())

        # 2. Buchstaben zuweisen
        Objekt.assign_letters(objekte)

        # 3. Objekte ausgeben
        for obj in objekte:
            print(obj)


        # 4. Adjazenzmatrix erstellen
        connection_img_path = r"/src/utils/tests/Bilder/Bodenlinien/bild1.jpg"
        adj_matrix, matrix_buchstaben = Objekt.create_adjacency_matrix(objekte, connection_img_path)

        # 5. Bild markieren
        img_path = r"/src/utils/tests/Bilder/Bodenlinien/bild1.jpg"
        output_path = r"/src/utils/tests/Bilder/Bodenlinien/Bild_markiert.jpg"
        Objekt.draw_objects_on_image(img_path, objekte, output_path)

        print("\nAdjazenzmatrix:")
        print("   " + " ".join(matrix_buchstaben))
        for i, row in enumerate(adj_matrix):
            print(f"{matrix_buchstaben[i]} {list(row)}")

    except Exception as e:
        print(f"Fehler: {str(e)}")