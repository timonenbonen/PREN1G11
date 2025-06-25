from sympy.strategies.core import switch
import os
import re
import cv2

class Objekt:
    def __init__(self, klasse, vertrauen, bounding_box):
        self.klasse = klasse
        self.vertrauen = vertrauen
        self.bounding_box = bounding_box
        self.flaeche = self._area()
        self.zentrum = self._center()
        self.buchstabe = None

        if self.klasse in ['pointa', 'pointb', 'pointc']:
            self._assign_letter()

    def _area(self):
        x1, y1, x2, y2 = self.bounding_box
        return (x2 - x1) * (y2 - y1)

    def _center(self):
        x1, y1, x2, y2 = self.bounding_box
        if self.klasse == 'barrier':
            return ((x1 + x2) / 2, y2 - ((x2 - x1) / 2))
        return ((x1 + x2) / 2, (y1 + y2) / 2)

    def _assign_letter(self):
        mapping = {'pointa': 'A', 'pointb': 'B', 'pointc': 'C'}
        self.buchstabe = mapping.get(self.klasse)

    @staticmethod
    def parse_text_to_objects(txt_content: str) -> list:
        objects = []
        lines = txt_content.strip().splitlines()
        for line in lines:
            parts = line.split(";")
            if len(parts) < 5:
                continue
            klasse = parts[0]
            vertrauen = float(parts[1].replace("%", ""))
            bbox = eval(parts[2])
            obj = Objekt(klasse, vertrauen, bbox)
            obj.flaeche = float(parts[3])
            obj.zentrum = eval(parts[4])
            if len(parts) > 5 and parts[5]:
                obj.buchstabe = parts[5]
            objects.append(obj)
        return objects

    @staticmethod
    def assignment_A(objects: list):
        letter = ord("A")
        for obj in sorted(objects, key=lambda o: o.zentrum[0]):
            obj.buchstabe = chr(letter)
            letter += 1

    @staticmethod
    def create_adjacency_matrix(objects: list, image_path: str):
        matrix = {}
        obj_letters = [obj.buchstabe for obj in objects if obj.buchstabe]
        for i in range(len(obj_letters) - 1):
            a, b = obj_letters[i], obj_letters[i + 1]
            matrix.setdefault(a, []).append(b)
            matrix.setdefault(b, []).append(a)
        return matrix, obj_letters

    @staticmethod
    def find_wall(objects: list, matrix: dict, obj_letters: list):
        print("🚧 Wall-Erkennung übersprungen (Dummy-Modus).")

    @staticmethod
    def assignment_E(objekte_liste):
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

    @staticmethod
    def assignment_D(objekte_liste):
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

    @staticmethod
    def assignment_F(objekte_liste, image_width, image_height):
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

    @staticmethod
    def assignment_G(objekte_liste, image_width, image_height):  # <-- NEUE PARAMETER
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

    @staticmethod
    def assignment_C(objekte_liste):
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

    @staticmethod
    def assignment_H(objekte_liste):
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

    @staticmethod
    def assignment_A(objekte_liste):
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

    @staticmethod
    def assignment_B(objekte_liste):
        """
        Zuordnungslogik für B (Roboter befindet sich auf Punkt B):
        1. Finde die 3 untersten Punkte
        2. Sortiere sie nach X-Position und weise zu:
           - C (links)
           - H (mitte)
           - A (rechts)
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

        if len(relevante_objekte) < 3:
            print(
                f"Warnung: Nur {len(relevante_objekte)} relevante Objekte gefunden, benötige mindestens 3 für assignment_B")
            # Verarbeite trotzdem die vorhandenen Objekte
            verfuegbare_objekte = relevante_objekte
        else:
            # Nach Y-Position sortieren (absteigend, unterster zuerst)
            sortierte_objekte = sorted(relevante_objekte,
                                       key=lambda obj: obj.zentrum[1],
                                       reverse=True)

            # Die 3 untersten Punkte nehmen
            verfuegbare_objekte = sortierte_objekte[:3]

        # Nach X-Position sortieren (aufsteigend, von links nach rechts)
        verfuegbare_objekte.sort(key=lambda obj: obj.zentrum[0])

        # Zuweisungen basierend auf verfügbaren Objekten
        zuweisungen = ['C', 'H', 'A']  # Links, Mitte, Rechts

        for i, obj in enumerate(verfuegbare_objekte):
            if i < len(zuweisungen):
                obj.set_buchstabe(zuweisungen[i])
                erkannte_punkte.append(obj)
                print(f"Info [assignment_B]: {zuweisungen[i]} zugewiesen an Position {i + 1} von links")

        # Konsistenzprüfung
        buchstaben = [getattr(obj, 'buchstabe', None) for obj in erkannte_punkte]
        if len([b for b in buchstaben if b]) != len(set(b for b in buchstaben if b)):
            print("Warnung: Doppelte Buchstaben in assignment_B erkannt!")

        return erkannte_punkte

    @staticmethod
    def set_current_image_context(objekte_liste, image_path):
        """
        Setzt den aktuellen Bildkontext für alle Objekte (für besseres Logging)

        Args:
            objekte_liste: Liste der Objekte
            image_path: Pfad zum aktuellen Bild
        """
        for obj in objekte_liste:
            obj._current_image_path = image_path

    # Beispiel für erweiterte Assignment-Methode (für assignment_B)


