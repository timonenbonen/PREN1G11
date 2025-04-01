from sympy.strategies.core import switch
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os


class Objekt:
    def __init__(self, klasse, vertrauen, bounding_box):
        """
        Erstellt ein neues Objekt mit automatischer Buchstaben-Zuweisung für pointa/b/c.
        """
        self.klasse = klasse
        self.vertrauen = vertrauen
        self.bounding_box = bounding_box
        self.flaeche = self._berechne_flaeche()
        self.zentrum = self._berechne_zentrum()
        self.buchstabe = None

        # Automatische Buchstaben für pointa/b/c
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
    def draw_objects_on_image(cls, image_path, objekte_liste, output_path="output.jpg"):
        """
        Zeichnet alle Objekte mit Buchstaben auf das Bild (kompatibel mit Pillow >= 8.0.0)
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
                'default': (255, 255, 255)  # Weiß
            }

            # Linienstärke
            thickness = max(2, int(image.width / 400))

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


# Beispielverwendung
if __name__ == "__main__":
    try:
        # 1. Objekte aus Textdatei parsen
        with open('objekte.txt') as file:
            objekte = Objekt.parse_text_to_objects(file.read())

        # 2. Buchstaben zuweisen
        Objekt.assign_letters(objekte)

        # 3. Auf Bild zeichnen
        Objekt.draw_objects_on_image(
            "eingabe.jpg",
            objekte,
            "ausgabe/resultat.jpg"
        )

        # 4. Ergebnisse anzeigen
        for obj in objekte:
            print(obj)

    except Exception as e:
        print(f"Fehler: {str(e)}")
# Verwendung
if __name__ == "__main__":
    try:
        with open(r'C:\Users\marin\PycharmProjects\PREN1G11\src\utils\tests\Bilder\Bodenlinien\objekte.txt') as file:
            text = file.read()

        objekte = Objekt.parse_text_to_objects(text)
        Objekt.assign_letters(objekte)

        for obj in objekte:
            print(obj)


    except Exception as e:
        print(f"Fehler: {str(e)}")

    img_path = r"C:\Users\marin\PycharmProjects\PREN1G11\src\utils\tests\Bilder\Bodenlinien\bearbeitet_Test2.jpg"
    Objekt.draw_objects_on_image(img_path, objekte,
                                 r"C:\Users\marin\PycharmProjects\PREN1G11\src\utils\tests\Bilder\Bodenlinien\Bild_markiert.jpg")