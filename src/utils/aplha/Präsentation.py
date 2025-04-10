from ultralytics import YOLO
import cv2
import numpy as np
from ErkannteObjekte import Objekt


class Praesentation:
    def __init__(self, modellpfad):
        self.modell = YOLO(modellpfad)
        self.objekte = []

    def _weise_buchstaben_zu(self, top4):
        """
        Weist Objekten die Buchstaben A, B, C, D zu:
        - D = der unterste Punkt (höchster Y-Zentrum-Wert)
        - A/B/C = eindeutig, basierend auf Klassenname oder Vertrauen
        """
        # Schritt 1: Finde den untersten Punkt → D
        punkt_d = max(top4, key=lambda obj: obj.zentrum[1])
        punkt_d.set_buchstabe('D')

        # Rest = A/B/C-Kandidaten
        rest = [obj for obj in top4 if obj is not punkt_d]

        # Mögliche Wunschbuchstaben aus Klassenname
        klassenzuordnung = {'pointa': 'A', 'pointb': 'B', 'pointc': 'C'}
        belegung = {}
        freie_buchstaben = {'A', 'B', 'C'}

        # Erst Wünsche nach Vertrauen priorisieren
        rest.sort(key=lambda obj: obj.vertrauen, reverse=True)

        for obj in rest:
            wunsch = klassenzuordnung.get(obj.klasse)
            if wunsch and wunsch in freie_buchstaben:
                obj.set_buchstabe(wunsch)
                belegung[wunsch] = obj
                freie_buchstaben.remove(wunsch)

        # Noch nicht vergebene Buchstaben zufällig verteilen
        for obj in rest:
            if obj.buchstabe is None and freie_buchstaben:
                buchstabe = freie_buchstaben.pop()
                obj.set_buchstabe(buchstabe)

    import numpy as np

    def finde_und_zeichne_verbindungen(self, bildpfad, ausgabepfad="verbindungen.jpg", breite=20,
                                       helligkeitsschwelle=200):
        """
        Prüft und zeichnet Verbindungen von Punkt D zu A/B/C, wenn sie visuell vorhanden sind (weißer Balken).
        """
        bild = cv2.imread(bildpfad)
        bild_grau = cv2.cvtColor(bild, cv2.COLOR_BGR2GRAY)

        # Finde Punkt D
        punkt_d = next((o for o in self.objekte if o.buchstabe == 'D'), None)
        if not punkt_d:
            print("Kein Punkt D gefunden.")
            return

        for ziel_buchstabe in ['A', 'B', 'C']:
            ziel = next((o for o in self.objekte if o.buchstabe == ziel_buchstabe), None)
            if not ziel:
                continue

            p1 = np.array(punkt_d.zentrum, dtype=np.float32)
            p2 = np.array(ziel.zentrum, dtype=np.float32)
            richtung = p2 - p1
            distanz = np.linalg.norm(richtung)

            if distanz < 1:
                continue  # Gleicher Punkt

            richtung_norm = richtung / distanz
            quer = np.array([-richtung_norm[1], richtung_norm[0]])  # 90° gedreht

            # Sammle alle Punkte entlang der Linie (alle 1 px)
            samples = []
            for i in range(int(distanz)):
                punkt_mitte = p1 + richtung_norm * i
                for j in range(-breite // 2, breite // 2):
                    querpunkt = punkt_mitte + quer * j
                    x, y = map(int, querpunkt)
                    if 0 <= x < bild.shape[1] and 0 <= y < bild.shape[0]:
                        samples.append(bild_grau[y, x])

            if not samples:
                continue

            durchschnitt = np.mean(samples)

            if durchschnitt >= helligkeitsschwelle:
                # Verbindung zeichnen
                p1_int = tuple(map(int, p1))
                p2_int = tuple(map(int, p2))
                cv2.line(bild, p1_int, p2_int, (255, 0, 0), 3)  # Blau

        cv2.imwrite(ausgabepfad, bild)
        print(f"[INFO] Verbindungen gezeichnet und gespeichert unter: {ausgabepfad}")

    def verarbeite_bild(self, bildpfad):
        bild = cv2.imread(bildpfad)
        ergebnisse = self.modell(bild, conf=0.01)[0]

        alle_objekte = []

        for box in ergebnisse.boxes:
            klasse_id = int(box.cls[0])
            klasse_name = self.modell.names[klasse_id]
            vertrauen = float(box.conf[0]) * 100
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            erk_obj = Objekt(klasse=klasse_name, vertrauen=vertrauen, bounding_box=(x1, y1, x2, y2))
            alle_objekte.append(erk_obj)

        alle_objekte.sort(key=lambda obj: obj.vertrauen, reverse=True)
        top4 = alle_objekte[:4]

        self._weise_buchstaben_zu(top4)  # <- Buchstaben zuweisen
        self.objekte = top4

    def zeichne_objekte_auf_bild(self, originalbild_pfad, ausgabepfad="annotiert.jpg"):
        """
        Zeichnet alle erkannten Objekte (nur Top 4) ins Bild mit zugewiesenem Buchstaben ein.
        """
        bild = cv2.imread(originalbild_pfad)

        for obj in self.objekte:
            x1, y1, x2, y2 = obj.bounding_box
            farbe = (0, 255, 0)  # Grün
            cv2.rectangle(bild, (x1, y1), (x2, y2), farbe, 2)

            # Beschriftung: Buchstabe falls vorhanden, sonst Fallback auf Klassennamen
            if obj.buchstabe:
                beschriftung = f"{obj.buchstabe}"
            else:
                beschriftung = f"{obj.klasse} ({obj.vertrauen:.1f}%)"

            cv2.putText(bild, beschriftung, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, farbe, 2)

        cv2.imwrite(ausgabepfad, bild)
        print(f"[INFO] Annotiertes Bild gespeichert unter: {ausgabepfad}")


    def run(self, bildpfad, ziel_buchstabe: str, ausgabepfad="final.jpg", breite=20, helligkeitsschwelle=200,
                richtungstoleranz=30):
            """
            Führt das gesamte Pipeline durch und gibt zurück, ob man das Ziel von links, rechts, mittig erreicht,
            oder ob keine Verbindung existiert.
            """
            self.verarbeite_bild(bildpfad)
            self.zeichne_objekte_auf_bild(bildpfad, "annotiert.jpg")

            bild = cv2.imread(bildpfad)
            bild_grau = cv2.cvtColor(bild, cv2.COLOR_BGR2GRAY)

            punkt_d = next((o for o in self.objekte if o.buchstabe == 'D'), None)
            ziel = next((o for o in self.objekte if o.buchstabe == ziel_buchstabe.upper()), None)

            if not punkt_d or not ziel:
                print("Punkt D oder Zielpunkt fehlt.")
                return "keine verbindung"

            # Verbindung prüfen
            p1 = np.array(punkt_d.zentrum, dtype=np.float32)
            p2 = np.array(ziel.zentrum, dtype=np.float32)
            richtung = p2 - p1
            distanz = np.linalg.norm(richtung)

            if distanz < 1:
                return "keine verbindung"

            richtung_norm = richtung / distanz
            quer = np.array([-richtung_norm[1], richtung_norm[0]])

            samples = []
            for i in range(int(distanz)):
                punkt_mitte = p1 + richtung_norm * i
                for j in range(-breite // 2, breite // 2):
                    querpunkt = punkt_mitte + quer * j
                    x, y = map(int, querpunkt)
                    if 0 <= x < bild.shape[1] and 0 <= y < bild.shape[0]:
                        samples.append(bild_grau[y, x])

            if not samples or np.mean(samples) < helligkeitsschwelle:
                return "keine verbindung"

            # Verbindung vorhanden → einzeichnen
            cv2.line(bild, tuple(map(int, p1)), tuple(map(int, p2)), (255, 0, 0), 3)
            cv2.imwrite(ausgabepfad, bild)
            print(f"[INFO] Finales Bild gespeichert unter: {ausgabepfad}")

            # Richtung bestimmen
            delta_x = ziel.zentrum[0] - punkt_d.zentrum[0]
            if delta_x > richtungstoleranz:
                return "rechts"
            elif delta_x < -richtungstoleranz:
                return "links"
            else:
                return "mittig"


def main():
    # Modellpfad und Eingabebild
    modellpfad = "YoloModell/my_model.pt"
    bildpfad = "YoloModell/Presentation.jpg"
    ziel = "A"  # oder "B", "C"

    # Präsentationsobjekt erzeugen
    praes = Praesentation(modellpfad)

    # Run aufrufen
    richtung = praes.run(bildpfad, ziel_buchstabe=ziel)

    # Ergebnis ausgeben
    print(f"[ERGEBNIS] Ziel {ziel} ist: {richtung.upper()}")

if __name__ == "__main__":
    main()