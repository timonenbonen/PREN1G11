import os
import random
import cv2
import tkinter as tk
from tkinter import Scale, Button, Label, Frame, StringVar, filedialog, IntVar
from PIL import Image, ImageTk
from ultralytics import YOLO
import threading
import numpy as np


class YoloDetectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YOLO Objektdetektor")
        self.root.geometry("1200x800")

        # Standardpfade
        self.model_path = r'C:\Users\marin\PycharmProjects\PREN1G11\src\utils\tests\YoloModells\model=yolov8npt epochs=100 imgsz=640\my_model.pt'
        self.image_folder = r'C:\Users\marin\PycharmProjects\PREN1G11\src\utils\tests\Bilder\MusterBoden'
        self.threshold = 10  # In Prozent (10 = 0.1)

        # Variablen
        self.model = None
        self.labels = None
        self.current_image_path = None
        self.current_frame = None
        self.processed_frame = None
        self.is_processing = False
        self.photo_image = None

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
                # Kopie des Frames erstellen
                frame_with_boxes = self.current_frame.copy()

                # Schwellenwert in Dezimalwert umwandeln (von % zu 0-1)
                conf_threshold = self.threshold / 100.0

                # YOLO Inferenz
                results = self.model(frame_with_boxes, verbose=False, conf=conf_threshold)
                detections = results[0].boxes

                # Ergebnisse sammeln für die Anzeige
                results_text = []

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

                    # Zur Ergebnisanzeige hinzufügen
                    results_text.append(f"{classname}: {int(conf * 100)}%")

                # Ergebnistext aktualisieren
                if results_text:
                    self.results_var.set("\n".join(results_text))
                else:
                    self.results_var.set("Keine Objekte erkannt")

                # Verarbeitetes Bild anzeigen
                self.processed_frame = frame_with_boxes
                self.zeige_bild(frame_with_boxes)

                # Status aktualisieren
                self.status_var.set(f"Erkennung abgeschlossen: {len(results_text)} Objekte gefunden")

            except Exception as e:
                self.status_var.set(f"Fehler bei der Erkennung: {str(e)}")
            finally:
                self.is_processing = False

        # In einem separaten Thread ausführen
        threading.Thread(target=detect_thread).start()


# Programm starten
if __name__ == "__main__":
    root = tk.Tk()
    app = YoloDetectorApp(root)
    root.mainloop()