import ast
import numpy as np  # Wir importieren numpy, um Arrays zu erstellen
from PIL import Image, ImageDraw  # Für die Bildverarbeitung


class RootMatrix:

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

    def __init__(self):
        self.real_matrix = np.empty_like(RootMatrix.original_matrix, dtype=object)
        self.objekte_listen = []  # Liste zum Speichern von Objektlisten
        self.zugeordnete_punkte = []  # **Neue Liste für zugeordnete Punkte**

    def lade_objekte_aus_txt(self, dateipfad):
        """
        Lädt Objektdaten aus einer Textdatei und erstellt eine Liste von Objekt-Instanzen.

        :param dateipfad: Der Pfad zur Textdatei.
        :return: Eine Liste von Objekt-Instanzen.
        """
        objekte = []  # Lokale Liste für jedes Laden
        try:
            with open(dateipfad, 'r') as datei:
                for zeile in datei:
                    # Entferne Zeilenumbrüche und teile die Zeile anhand von ';'
                    daten = zeile.strip().split(';')
                    if len(daten) >= 4:  # Stelle sicher, dass wir genug Daten haben
                        klasse = daten[0]
                        vertrauen = float(daten[1].strip('%'))  # Entferne '%' und konvertiere zu float
                        bounding_box_str = daten[2].strip()
                        # Konvertiere den Bounding-Box-String in ein Tuple
                        bounding_box = ast.literal_eval(bounding_box_str)
                        # Erstelle ein Objekt und füge es der Liste hinzu
                        objekt = Objekt(klasse, vertrauen, bounding_box)
                        objekte.append(objekt)
                    else:
                        print(f"Ungültige Zeile in der Datei: {zeile}")
        except FileNotFoundError:
            print(f"Fehler: Datei nicht gefunden: {dateipfad}")
        self.objekte_listen.append(objekte)  # Speichere die Liste
        return objekte  # Gib die lokale Liste zurück

    def gib_original_matrix(self):
        """Gibt die Originalmatrix zurück."""
        return RootMatrix.original_matrix

    def gib_real_matrix(self):
        """Gibt die Realmatrix zurück."""
        return self.real_matrix

    def gib_alle_objekt_listen(self):
        """ Gibt alle gespeicherten Objektlisten zurück """
        return self.objekte_listen

    def gib_zugeordnete_punkte(self):
        """Gibt die Liste der zugeordneten Punkte zurück."""
        return self.zugeordnete_punkte

    def erste_zuordnung(self, dateipfad):
        """
        Führt die erste Zuordnung der Punkte E, F, G, D basierend auf den Daten in der Textdatei durch.

        :param dateipfad: Der Pfad zur Textdatei mit den Objektdaten.
        """

        objekt_liste = self.lade_objekte_aus_txt(dateipfad)  # Objekte laden und Liste erhalten

        # Filtere die Punkte und Barrieren heraus
        punkte = [
            obj
            for obj in objekt_liste
            if obj.klasse in ["point", "pointa", "pointb", "pointc", "barrier"]
        ]

        # Sortiere die Punkte nach der y-Koordinate (südlichste zuerst)
        punkte.sort(key=lambda punkt: punkt.zentrum[1])

        # Weise die Buchstaben zu, wenn genügend Punkte vorhanden sind
        if len(punkte) >= 4:
            punkte[0].set_buchstabe("E")  # Südlichster Punkt ist E
            self.zugeordnete_punkte.append(punkte[0])  # **Füge zugeordneten Punkt hinzu**

            # Sortiere die nächsten drei Punkte nach x-Koordinate (links nach rechts)
            naechste_drei_punkte = punkte[1:4]
            naechste_drei_punkte.sort(key=lambda punkt: punkt.zentrum[0])

            punkte[1].set_buchstabe("F")  # Linker Punkt ist F
            self.zugeordnete_punkte.append(punkte[1])  # **Füge zugeordneten Punkt hinzu**

            punkte[2].set_buchstabe("G")  # Mittlerer Punkt ist G
            self.zugeordnete_punkte.append(punkte[2])  # **Füge zugeordneten Punkt hinzu**

            punkte[3].set_buchstabe("D")  # Rechter Punkt ist D
            self.zugeordnete_punkte.append(punkte[3])  # **Füge zugeordneten Punkt hinzu**
        else:
            print(
                "Nicht genügend Punkte für die Zuordnung E, F, G, D gefunden."
            )  # Fehlerbehandlung, wenn nicht genug Punkte vorhanden sind

    def analysiere_verbindungen(
        self,
        bild_pfad,
        objekt_liste,
        start_punkt_buchstabe,
        threshold,
        linien_breite,
    ):
        """
        Analysiert Verbindungen zwischen Punkten auf einem Bild und aktualisiert die real_matrix.

        :param bild_pfad: Pfad zum Bild, das analysiert werden soll.
        :param objekt_liste: Liste von Objekt-Instanzen.
        :param start_punkt_buchstabe: Buchstabe des Startpunkts für die Analyse.
        :param threshold: Mindestanzahl an "farbigen" Pixeln im Balken, um eine Linie zu erkennen.
        :param linien_breite: Breite des Balkens (in Pixeln), der zur Analyse verwendet wird.
        """

        try:
            bild = Image.open(bild_pfad).convert("RGB")  # Öffne das Bild
            zeichner = ImageDraw.Draw(bild)  # Für das Zeichnen von Testbalken (optional)
        except FileNotFoundError:
            print(f"Fehler: Bilddatei nicht gefunden: {bild_pfad}")
            return  # Beende die Methode, wenn das Bild nicht gefunden wird

        # 1. Startpunkt finden
        start_punkt = None
        for obj in objekt_liste:
            if obj.buchstabe == start_punkt_buchstabe:
                start_punkt = obj
                break  # Sobald der Startpunkt gefunden wurde, brich die Schleife ab
        if start_punkt is None:
            print(
                f"Fehler: Startpunkt mit Buchstabe '{start_punkt_buchstabe}' nicht gefunden."
            )
            return

        start_index = self._get_matrix_index(start_punkt.buchstabe)
        if start_index is None:
            print(
                f"Fehler: Startpunkt Buchstabe '{start_punkt_buchstabe}' ist in der"
                " Originalmatrix nicht vorhanden."
            )
            return

        # 2. Iteriere über alle anderen Punkte in der Liste
        for ziel_punkt in objekt_liste:
            if ziel_punkt == start_punkt or ziel_punkt.buchstabe is None:
                continue  # Überspringe den Startpunkt selbst und Punkte ohne Buchstaben

            ziel_index = self._get_matrix_index(ziel_punkt.buchstabe)
            if ziel_index is None:
                print(
                    f"Fehler: Zielpunkt Buchstabe '{ziel_punkt.buchstabe}' ist in der"
                    " Originalmatrix nicht vorhanden."
                )
                continue

            # 3. Balken zwischen den Zentren definieren
            x1, y1 = map(int, start_punkt.zentrum)  # Konvertiere zu Integer
            x2, y2 = map(int, ziel_punkt.zentrum)
            distanz = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5  # Distanz zwischen den Punkten
            if distanz == 0:
                continue  # Vermeide Division durch Null

            # Normalisierter Richtungsvektor
            dx = (x2 - x1) / distanz
            dy = (y2 - y1) / distanz

            # 4. Balkenanalyse
            farbige_pixel_count = 0
            for i in range(int(distanz)):
                # Punkte entlang des Balkens
                aktueller_x = int(x1 + i * dx)
                aktueller_y = int(y1 + i * dy)

                # Untersuche Pixel senkrecht zum Balken
                for j in range(-linien_breite // 2, linien_breite // 2 + 1):
                    # Senkrechte Verschiebung (perpendikulär zur Richtung des Balkens)
                    senkrecht_dx = -dy  # Senkrecht nach links
                    senkrecht_dy = dx

                    untersuchungs_x = aktueller_x + int(j * senkrecht_dx)
                    untersuchungs_y = aktueller_y + int(j * senkrecht_dy)

                    # Stelle sicher, dass wir uns innerhalb der Bildgrenzen befinden
                    if (
                        0 <= untersuchungs_x < bild.width
                        and 0 <= untersuchungs_y < bild.height
                    ):
                        r, g, b = bild.getpixel((untersuchungs_x, untersuchungs_y))
                        if (r, g, b) != (255, 255, 255):  # Nicht perfektes Weiß
                            farbige_pixel_count += 1
                            # Zeichne einen roten Punkt auf dem Bild, wo ein farbiges Pixel gefunden wurde
                            # zeichner.point((untersuchungs_x, untersuchungs_y), fill=(255, 0, 0)) #Optional zum Debuggen

            # 5. Entscheidung treffen und real_matrix aktualisieren
            if farbige_pixel_count > threshold:
                self.real_matrix[start_index, ziel_index] = 1
                self.real_matrix[ziel_index, start_index] = 1  # Annahme: ungerichtete Verbindungen
                print(
                    f"Verbindung gefunden zwischen {start_punkt.buchstabe} und"
                    f" {ziel_punkt.buchstabe}"
                )
            # Optional: Zeichne den analysierten Balken auf das Bild
            # zeichner.line((x1, y1, x2, y2), fill=(0, 255, 0), width=1) #Optional zum Debuggen

        # Optional: Speichere das Bild mit den gezeichneten Balken/Punkten
        # bild.save("verbindungen_analysiert.png")

    def _get_matrix_index(self, buchstabe):
        """
        Hilfsmethode, um den Index in der Matrix für einen gegebenen Buchstaben zu finden.
        """
        spalten_namen = ["A", "B","C","D","E", "F","G","H",]  # Entspricht deiner original_matrix
        try:
            return spalten_namen.index(buchstabe)
        except ValueError:
            return None  # Buchstabe nicht gefunden