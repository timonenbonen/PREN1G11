import os
import random
import cv2
import tkinter as tk
from tkinter import Scale, Button, Label, Frame, StringVar, filedialog, IntVar
from PIL import Image, ImageTk
from ultralytics import YOLO
import threading
import numpy as np



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

        # Buchstabe wird später zugeordnet
        self.buchstabe = None

    def __str__(self):
        """Liefert eine lesbare String-Darstellung des Objekts"""
        buchstabe_info = f", Buchstabe: {self.buchstabe}" if self.buchstabe else ""
        return f"Objekt: {self.klasse}, Vertrauen: {self.vertrauen:.1f}%, Zentrum: {self.zentrum}, Fläche: {self.flaeche}{buchstabe_info}"

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


class YoloDetectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YOLO Objektdetektor")
        self.root.geometry("1200x800")

        # Standardpfade
        self.model_path = r'/src/utils/tests/YoloModells/model=yolov8npt epochs=100 imgsz=640/my_model.pt'
        self.image_folder = r'C:\Users\marin\PycharmProjects\PREN1G11\src\utils\tests\Bilder\MusterBoden'
        self.output_file = r'/src/utils/tests/Bilder/Bodenlinien/objekte_D.txt'  # Pfad zur Ausgabedatei
        self.threshold = 10  # In Prozent (10 = 0.1)

        # Variablen
        self.model = None
        self.labels = None
        self.current_image_path = None
        self.current_frame = None
        self.processed_frame = None
        self.is_processing = False
        self.photo_image = None
        self.detected_objects = []  # Liste für erkannte Objekte

        # GUI-Layout erstellen
        self.erstelle_layout()

        # Beim Start Modell laden
        self.model_laden()

        # Window resize event binding
        self.root.bind("<Configure>", self.on_window_resize)
        self.last_width = self.root.winfo_width()
        self.last_height = self.root.winfo_height()

    def erstelle_layout(self):
        # Hauptrahmen
        self.main_frame = Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Linker Bereich (Steuerungselemente)
        self.control_frame = Frame(self.main_frame, width=300)
        self.control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # Überschrift
        Label(self.control_frame, text="YOLO Objektdetektor", font=("Arial", 14, "bold")).pack(pady=(0, 10))

        # Modell auswählen
        Label(self.control_frame, text="Modell:", font=("Arial", 12)).pack(anchor=tk.W, pady=(10, 0))
        Button(self.control_frame, text="Modell auswählen", command=self.modell_auswaehlen).pack(fill=tk.X, pady=5)
        self.model_var = StringVar()
        self.model_var.set(os.path.basename(self.model_path))
        Label(self.control_frame, textvariable=self.model_var, font=("Arial", 10), wraplength=280).pack(pady=(0, 10))

        # Bildordner auswählen
        Label(self.control_frame, text="Bildordner:", font=("Arial", 12)).pack(anchor=tk.W, pady=(10, 0))
        Button(self.control_frame, text="Bildordner auswählen", command=self.ordner_auswaehlen).pack(fill=tk.X, pady=5)
        self.folder_var = StringVar()
        self.folder_var.set(os.path.basename(self.image_folder))
        Label(self.control_frame, textvariable=self.folder_var, font=("Arial", 10), wraplength=280).pack(pady=(0, 10))

        # Konfidenz-Schwellenwert
        Label(self.control_frame, text="Konfidenz-Schwellenwert (%):", font=("Arial", 12)).pack(anchor=tk.W,
                                                                                                pady=(10, 0))
        self.threshold_scale = Scale(self.control_frame, from_=1, to=100, orient=tk.HORIZONTAL,
                                     command=self.threshold_aktualisieren)
        self.threshold_scale.set(self.threshold)
        self.threshold_scale.pack(fill=tk.X)

        # Detektieren/Zufallsbild
        Button(self.control_frame, text="Zufallsbild laden & detektieren", command=self.neues_bild_laden).pack(
            fill=tk.X,
            pady=(20, 5))

        # Objekte in Datei speichern Button (statt Konsole)
        Button(self.control_frame, text="Objekte in Datei speichern", command=self.objekte_in_datei_speichern).pack(
            fill=tk.X, pady=5)

        # Checkbox für automatische Erkennung bei Schwellenwertänderung
        self.auto_detect_var = IntVar(value=1)
        auto_detect_checkbox = tk.Checkbutton(self.control_frame,
                                              text="Automatisch bei Schwellenwert-Änderung neu erkennen",
                                              variable=self.auto_detect_var)
        auto_detect_checkbox.pack(anchor=tk.W, pady=(10, 20))

        # Status
        self.status_var = StringVar()
        self.status_var.set("Bereit. Modell wird geladen...")
        Label(self.control_frame, textvariable=self.status_var, font=("Arial", 10),
              wraplength=280, justify=tk.LEFT).pack(pady=(10, 10), fill=tk.X)

        # Ergebnisanzeige
        self.results_var = StringVar()
        self.results_var.set("Noch keine Ergebnisse")
        Label(self.control_frame, text="Erkennungsergebnisse:", font=("Arial", 12)).pack(anchor=tk.W, pady=(20, 5))
        self.results_label = Label(self.control_frame, textvariable=self.results_var, font=("Arial", 10),
                                   wraplength=280, justify=tk.LEFT, anchor=tk.NW)
        self.results_label.pack(pady=(0, 10), fill=tk.X)

        # Rechter Bereich (Bildvorschau) - mit Frame für bessere Skalierung
        self.preview_frame = Frame(self.main_frame, bg="gray")
        self.preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Bildanzeige - verwende ein Label statt Canvas für einfachere Handhabung der Skalierung
        self.image_label = Label(self.preview_frame, bg='gray')
        self.image_label.pack(expand=True, fill=tk.BOTH)

    def on_window_resize(self, event=None):
        # Nur reagieren, wenn es eine signifikante Größenänderung gab und wir ein Bild haben
        current_width = self.root.winfo_width()
        current_height = self.root.winfo_height()

        # Prüfen, ob das Fenster tatsächlich resized wurde (nicht nur, wenn ein Widget umgestaltet wird)
        width_changed = abs(current_width - self.last_width) > 10
        height_changed = abs(current_height - self.last_height) > 10

        if (width_changed or height_changed) and self.processed_frame is not None:
            self.last_width = current_width
            self.last_height = current_height
            # Kurze Verzögerung, um mehrfaches Neurendern bei Resize zu vermeiden
            self.root.after(100, self.zeige_bild, self.processed_frame or self.current_frame)

    def modell_auswaehlen(self):
        new_path = filedialog.askopenfilename(
            filetypes=[("PyTorch Modell", "*.pt"), ("Alle Dateien", "*.*")],
            title="YOLO-Modell auswählen")

        if new_path:
            self.model_path = new_path
            self.model_var.set(os.path.basename(self.model_path))
            self.model_laden()

    def ordner_auswaehlen(self):
        new_folder = filedialog.askdirectory(title="Bildordner auswählen")
        if new_folder:
            self.image_folder = new_folder
            self.folder_var.set(os.path.basename(self.image_folder))

    def threshold_aktualisieren(self, wert):
        self.threshold = int(wert)
        if self.auto_detect_var.get() and self.current_frame is not None:
            # Führe die Erkennung noch einmal mit dem neuen Schwellenwert durch
            self.erkennung_durchfuehren()

    def model_laden(self):
        def load_model_thread():
            self.status_var.set(f"Lade Modell {os.path.basename(self.model_path)}...")
            try:
                self.model = YOLO(self.model_path)
                self.labels = self.model.names
                self.status_var.set(f"Modell geladen: {len(self.labels)} Klassen")
            except Exception as e:
                self.status_var.set(f"Fehler beim Laden des Modells: {str(e)}")

        # Modell in einem separaten Thread laden, damit die GUI nicht einfriert
        threading.Thread(target=load_model_thread).start()

    def neues_bild_laden(self):
        if self.is_processing:
            return

        self.is_processing = True
        self.status_var.set("Lade neues Bild...")

        def process_thread():
            try:
                image_path = self.get_random_image()
                if not image_path:
                    self.status_var.set("Keine Bilder im Ordner gefunden")
                    self.is_processing = False
                    return

                self.current_image_path = image_path
                frame = cv2.imread(image_path)

                if frame is None:
                    self.status_var.set(f"Fehler beim Laden des Bildes: {os.path.basename(image_path)}")
                    self.is_processing = False
                    return

                self.current_frame = frame
                self.status_var.set(f"Bild geladen: {os.path.basename(image_path)}")

                # Bild anzeigen und Erkennung durchführen
                self.zeige_bild(frame)
                self.erkennung_durchfuehren()

            except Exception as e:
                self.status_var.set(f"Fehler: {str(e)}")
            finally:
                self.is_processing = False

        # In einem separaten Thread ausführen
        threading.Thread(target=process_thread).start()

    def get_random_image(self):
        try:
            images = [f for f in os.listdir(self.image_folder)
                      if f.lower().endswith(('png', 'jpg', 'jpeg'))]
            if not images:
                return None
            return os.path.join(self.image_folder, random.choice(images))
        except Exception as e:
            self.status_var.set(f"Fehler beim Zugriff auf den Bildordner: {str(e)}")
            return None

    def zeige_bild(self, frame):
        if frame is None:
            return

        # Verfügbaren Platz für das Bild berechnen (Größe des Preview-Frames)
        available_width = self.preview_frame.winfo_width()
        available_height = self.preview_frame.winfo_height()

        # Mindestgröße setzen, falls das Frame noch nicht gerendert wurde
        if available_width < 50:  # Wenn das Frame noch nicht richtig initialisiert ist
            available_width = max(800, self.root.winfo_width() - 350)  # Abzüglich control_frame und Padding
        if available_height < 50:
            available_height = max(600, self.root.winfo_height() - 50)  # Abzüglich Padding

        # Bildgröße bestimmen
        bildhoehe, bildbreite = frame.shape[:2]

        # Skalierungsfaktor berechnen, um das Bild in den verfügbaren Platz zu passen
        skalierungsfaktor = min(available_width / bildbreite, available_height / bildhoehe)
        neue_breite = int(bildbreite * skalierungsfaktor)
        neue_hoehe = int(bildhoehe * skalierungsfaktor)

        # Bild skalieren
        if neue_breite > 0 and neue_hoehe > 0:  # Vermeide leere Bilder
            frame_anzeige = cv2.resize(frame, (neue_breite, neue_hoehe))
            # BGR zu RGB konvertieren für Tkinter
            frame_anzeige = cv2.cvtColor(frame_anzeige, cv2.COLOR_BGR2RGB)

            # Bild für Tkinter vorbereiten
            self.photo_image = ImageTk.PhotoImage(image=Image.fromarray(frame_anzeige))

            # Bild im Label anzeigen
            self.image_label.config(image=self.photo_image)
            self.image_label.image = self.photo_image  # Referenz behalten

    def erkennung_durchfuehren(self):
        if self.current_frame is None or self.model is None or self.is_processing:
            return

        self.is_processing = True
        self.status_var.set("Führe Objekterkennung durch...")

        def detect_thread():
            try:
                frame_with_boxes = self.current_frame.copy()
                conf_threshold = self.threshold / 100.0
                results = self.model(frame_with_boxes, verbose=False, conf=conf_threshold)
                detections = results[0].boxes

                results_text = []
                self.detected_objects = []  # Zurücksetzen der erkannten Objekte

                # Buchstabenliste für Objekte
                buchstaben = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                buchstaben_index = 0

                for det in detections:
                    xmin, ymin, xmax, ymax = map(int, det.xyxy[0])
                    conf = det.conf.item()
                    classidx = int(det.cls.item())
                    classname = self.labels[classidx]

                    # Bounding Box zeichnen
                    cv2.rectangle(frame_with_boxes, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
                    label = f'{classname}: {int(conf * 100)}%'
                    cv2.putText(frame_with_boxes, label, (xmin, ymin - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                    # Objekt erstellen und zur Liste hinzufügen
                    objekt = Objekt(classname, conf * 100, (xmin, ymin, xmax, ymax))

                    self.detected_objects.append(objekt)

                    # Für die GUI-Anzeige
                    results_text.append(f"{classname}: {int(conf * 100)}%")

                if results_text:
                    self.results_var.set("\n".join(results_text))
                else:
                    self.results_var.set("Keine Objekte erkannt")

                self.processed_frame = frame_with_boxes
                self.zeige_bild(frame_with_boxes)

                self.status_var.set(f"Erkennung abgeschlossen: {len(results_text)} Objekte gefunden")

            except Exception as e:
                self.status_var.set(f"Fehler bei der Erkennung: {str(e)}")
            finally:
                self.is_processing = False

        threading.Thread(target=detect_thread).start()

    def objekte_in_datei_speichern(self):
        if not self.detected_objects:
            self.status_var.set("Keine Objekte zum Speichern vorhanden.")
            return

        # Determine the next available filename
        base_name = "objekte"
        extension = ".txt"
        counter = 1
        output_file = f"{base_name}{counter}{extension}"

        # Find the next available filename
        while os.path.exists(output_file):
            counter += 1
            output_file = f"{base_name}{counter}{extension}"

        try:
            with open(output_file, 'w') as f:
                for obj in self.detected_objects:
                    print(f"DEBUG: Objekt {obj.klasse} - Buchstabe: {obj.buchstabe}")  # Debug
                    line = f"{obj.klasse};{obj.vertrauen:.1f}%;{obj.bounding_box};{obj.flaeche};{obj.zentrum};{obj.buchstabe if obj.buchstabe else ''}\n"
                    f.write(line)

            self.status_var.set(
                f"{len(self.detected_objects)} Objekte gespeichert: {os.path.basename(output_file)}")
            self.output_file = output_file  # Update the current output file
        except Exception as e:
            self.status_var.set(f"Fehler beim Speichern: {str(e)}")


# Programm starten
if __name__ == "__main__":
    root = tk.Tk()
    app = YoloDetectorApp(root)
    root.mainloop()