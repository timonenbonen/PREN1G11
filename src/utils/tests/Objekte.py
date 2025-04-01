from sympy.strategies.core import switch


class Objekt:
    def __init__(self, klasse, vertrauen, bounding_box):
        """
        Erstellt ein neues Objekt mit den angegebenen Eigenschaften und berechnet automatisch
        die Fläche und das Zentrum der Bounding Box.

        :param klasse: String - Art des erkannten Objekts (z.B. 'barrier', 'point', 'wall')
        :param vertrauen: float - Vertrauenswert in Prozent (z.B. 99.2)
        :param bounding_box: tuple - Koordinaten (x1, y1, x2, y2)
        """
        self.klasse = klasse
        self.vertrauen = vertrauen
        self.bounding_box = bounding_box

        # Automatische Berechnung von Fläche und Zentrum
        self.flaeche = self._berechne_flaeche()
        self.zentrum = self._berechne_zentrum()

        # Initialisiere Buchstabe mit None
        self.buchstabe = None

        # Wenn die Klasse pointa, pointb oder pointc ist, Buchstabe automatisch setzen
        if self.klasse in ['pointa', 'pointb', 'pointc']:
            self.set_buchstabe_automatisch()

    def __str__(self):
        """Liefert eine lesbare String-Darstellung des Objekts"""
        buchstabe_info = f", Buchstabe: {self.buchstabe}" if self.buchstabe else ""
        return f"Objekt: {self.klasse}, Vertrauen: {self.vertrauen}%, Zentrum: {self.zentrum}, Fläche: {self.flaeche}{buchstabe_info}"

    def __repr__(self):
        """Liefert eine formale String-Darstellung des Objekts"""
        return f"Objekt(klasse='{self.klasse}', vertrauen={self.vertrauen}, bounding_box={self.bounding_box})"

    def _berechne_flaeche(self):
        """Berechnet die Fläche der Bounding Box"""
        x1, y1, x2, y2 = self.bounding_box
        breite = x2 - x1
        hoehe = y2 - y1
        return breite * hoehe

    def _berechne_zentrum(self):
        """Berechnet den Mittelpunkt der Bounding Box"""
        x1, y1, x2, y2 = self.bounding_box
        zentrum_x = (x1 + x2) / 2
        zentrum_y = (y1 + y2) / 2
        return (zentrum_x, zentrum_y)

    def set_buchstabe(self, buchstabe):
        """Setzt den Buchstaben für dieses Objekt"""
        self.buchstabe = buchstabe
        return self

    def ist_vertrauenswuerdig(self, schwellenwert=50.0):
        """Prüft, ob der Vertrauenswert über dem Schwellenwert liegt"""
        return self.vertrauen >= schwellenwert

    def set_buchstabe_automatisch(self):
        buchstaben_mapping = {'pointa': 'A', 'pointb': 'B', 'pointc': 'C'}
        self.buchstabe = buchstaben_mapping.get(self.klasse)
        if self.buchstabe is None:
            print(f"FEHLER: Kein Buchstabe für Klasse {self.klasse} definiert!")