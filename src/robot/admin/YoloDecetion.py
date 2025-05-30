import os
import cv2
from ultralytics import YOLO


# Ihre existierende Objekt-Klasse wird hier importiert
# from your_module import Objekt

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
        """
        Berechnet den Mittelpunkt der Bounding Box.
        - Für 'barrier':
          - x = normaler horizontaler Mittelpunkt
          - y = unterer Rand + halbe Breite von unten nach oben
        - Für alle anderen Objekte: normales Zentrum
        """
        x1, y1, x2, y2 = self.bounding_box
        breite = x2 - x1
        hoehe = y2 - y1

        if self.klasse == 'barrier':
            zentrum_x = (x1 + x2) / 2
            zentrum_y = y2 - (breite / 2)  # von unten nach oben
        else:
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


class YoloDetector:
    def __init__(self, model_path):
        """
        Initialisiert den YOLO Detector ohne GUI

        :param model_path: Pfad zum YOLO-Modell (.pt Datei)
        """
        self.model_path = model_path
        self.model = None
        self.labels = None
        self.load_model()

    def load_model(self):
        """Lädt das YOLO-Modell"""
        try:
            print(f"Lade Modell: {os.path.basename(self.model_path)}")
            self.model = YOLO(self.model_path)
            self.labels = self.model.names
            print(f"Modell erfolgreich geladen: {len(self.labels)} Klassen erkannt")
        except Exception as e:
            print(f"Fehler beim Laden des Modells: {str(e)}")
            raise

    def detect_and_save(self, image_path, confidence_threshold=0.3, output_txt_path=None):
        """
        Führt Objekterkennung durch und speichert Ergebnisse in TXT-Datei

        :param image_path: Pfad zum Eingabebild
        :param confidence_threshold: Mindest-Zuverlässigkeit (0.3 = 30%)
        :param output_txt_path: Pfad zur Ausgabe-TXT (optional, wird automatisch generiert wenn None)
        :return: Liste der erkannten Objekte
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Bilddatei nicht gefunden: {image_path}")

        # Bild laden
        print(f"Lade Bild: {os.path.basename(image_path)}")
        frame = cv2.imread(image_path)
        if frame is None:
            raise ValueError(f"Fehler beim Laden des Bildes: {image_path}")

        # Objekterkennung durchführen
        print(f"Führe Objekterkennung durch (Mindest-Zuverlässigkeit: {confidence_threshold * 100}%)")
        results = self.model(frame, verbose=False, conf=confidence_threshold)
        detections = results[0].boxes

        detected_objects = []

        # Erkannte Objekte verarbeiten
        for det in detections:
            xmin, ymin, xmax, ymax = map(int, det.xyxy[0])
            conf = det.conf.item()
            classidx = int(det.cls.item())
            classname = self.labels[classidx]

            # Objekt erstellen
            objekt = Objekt(classname, conf * 100, (xmin, ymin, xmax, ymax))
            detected_objects.append(objekt)

        print(f"Erkennung abgeschlossen: {len(detected_objects)} Objekte gefunden")

        # Ausgabedatei bestimmen
        if output_txt_path is None:
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            output_txt_path = os.path.join(os.path.dirname(image_path), base_name + ".txt")

        # Objekte in TXT-Datei speichern
        self.save_objects_to_file(detected_objects, output_txt_path)

        return detected_objects

    def save_objects_to_file(self, objects, output_file):
        """
        Speichert erkannte Objekte in eine TXT-Datei

        :param objects: Liste der Objekt-Instanzen
        :param output_file: Pfad zur Ausgabedatei
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                for obj in objects:
                    line = f"{obj.klasse};{obj.vertrauen:.1f}%;{obj.bounding_box};{obj.flaeche};{obj.zentrum};{obj.buchstabe if obj.buchstabe else ''}\n"
                    f.write(line)

            print(f"Ergebnisse gespeichert: {output_file}")
            print(f"Anzahl gespeicherter Objekte: {len(objects)}")

            # Zusammenfassung der erkannten Objekte anzeigen
            if objects:
                print("\nErkannte Objekte:")
                for i, obj in enumerate(objects, 1):
                    print(f"{i:2d}. {obj}")

        except Exception as e:
            print(f"Fehler beim Speichern der Datei: {str(e)}")
            raise


def main():
    """
    Hauptfunktion - Beispiel für die Verwendung
    """
    # Pfade anpassen (diese müssen an Ihre Umgebung angepasst werden)
    model_path = r'/src/utils/tests/YoloModells/model=yolov8npt epochs=100 imgsz=640/my_model.pt'
    image_path = r'C:\Users\marin\PycharmProjects\PREN1G11\src\utils\tests\Bilder\MusterBoden\test_image.jpg'

    try:
        # Detector initialisieren
        detector = YoloDetector(model_path)

        # Objekterkennung durchführen und speichern (30% Mindest-Zuverlässigkeit)
        detected_objects = detector.detect_and_save(
            image_path=image_path,
            confidence_threshold=0.3  # 30%
        )

        print(f"\nFertig! {len(detected_objects)} Objekte wurden erkannt und gespeichert.")

    except Exception as e:
        print(f"Fehler: {str(e)}")


if __name__ == "__main__":
    main()