import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog
import os
import tensorflow as tf  # Dein TensorFlow-Modell

class ObjectDetector:
    def __init__(self):
        self.model = tf.keras.models.load_model('pylonen_erkennungs_modell.h5')  # Dein Modell wird hier geladen
        self.cap = None
        self.image_path = None
        self.is_camera_mode = None
        self.running = False

    def select_image(self):
        """Öffnet einen Dialog zur Bildauswahl."""
        print("Dateiauswahldialog wird geöffnet... (kann im Hintergrund sein)")

        # Root-Fenster erstellen und in den Vordergrund bringen
        root = tk.Tk()
        root.attributes('-topmost', True)
        root.withdraw()  # Hauptfenster verstecken aber topmost Eigenschaft behalten

        # Dialog öffnen
        file_path = filedialog.askopenfilename(
            title="Bild auswählen",
            filetypes=[("Bilder", "*.jpg *.jpeg *.png *.bmp")]
        )

        root.destroy()

        if file_path:
            print(f"Ausgewählte Datei: {file_path}")
        else:
            print("Keine Datei ausgewählt.")

        return file_path

    def detect_orange_cones(self, frame):
        """Erkennt Pylonen in verschiedenen Farbkombinationen."""
        if frame is None:
            return frame

        original = frame.copy()

        # Bildvorverarbeitung (Größe anpassen, etc.)
        resized_frame = cv2.resize(frame, (224, 224))
        normalized_frame = resized_frame / 255.0
        expanded_frame = np.expand_dims(normalized_frame, axis=0)  # Hinzufügen der Batch-Dimension

        # Vorhersage des Modells
        predictions = self.model.predict(expanded_frame)
        print("Vorhersagen des Modells:", predictions)

        if predictions[0][1] > 0.5:  # Beispielannahme: Wahrscheinlichkeit für Pylon
            cv2.putText(original, "Pylon erkannt", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.rectangle(original, (10, 10), (frame.shape[1] - 10, frame.shape[0] - 10), (0, 255, 0), 2)

        return original

    def start_camera(self, camera_url="http://192.168.178.21:4747/video"):
        """Startet die Kamera mit der angegebenen URL oder mit der Standard-Webcam."""
        self.cap = cv2.VideoCapture(camera_url if camera_url else 0)

        if not self.cap.isOpened():
            print("Fehler beim Öffnen der Kamera")
            return False

        # Frame-Größe reduzieren, falls nötig
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        return True

    def run(self):
        """Hauptschleife für die Objekterkennung."""
        self.running = True

        # Erste Auswahl: Kamera oder Bild
        while self.is_camera_mode is None:
            choice = input("Möchtest du (1) die Kamera oder (2) ein Bild verwenden? ")
            if choice == "1":
                self.is_camera_mode = True
            elif choice == "2":
                self.is_camera_mode = False
                print("Bild-Modus ausgewählt.")
                # Sofort nach Bild fragen
                self.image_path = self.select_image()
                if not self.image_path:
                    print("Keine Datei ausgewählt. Wechsle zum Kamera-Modus.")
                    self.is_camera_mode = True
            else:
                print("Ungültige Eingabe. Bitte 1 oder 2 eingeben.")

        print("\nTastenbelegung:")
        print("'c' - Zur Kamera wechseln")
        print("'i' - Zu einem Bild wechseln")
        print("'q' - Programm beenden\n")

        while self.running:
            frame = None

            if self.is_camera_mode:
                if self.cap is None:
                    camera_choice = input("Kameratyp wählen - (1) DroidCam, (2) Webcam: ")
                    if camera_choice == "1":
                        camera_url = input("DroidCam URL eingeben (z.B. http://192.168.178.21:4747/video): ")
                        if not self.start_camera(camera_url):
                            continue
                    elif camera_choice == "2":
                        if not self.start_camera():
                            continue
                    else:
                        print("Ungültige Eingabe. Bitte 1 oder 2 eingeben.")
                        continue

                ret, frame = self.cap.read()
                if not ret:
                    print("Fehler beim Lesen des Kamera-Frames")
                    self.cap.release()
                    self.cap = None
                    continue
            else:
                if self.image_path is None or not os.path.exists(self.image_path):
                    print("Dateidialog wird geöffnet...")
                    self.image_path = self.select_image()
                    if not self.image_path:
                        print("Keine Datei ausgewählt.")
                        choice = input("Möchtest du (1) zur Kamera wechseln oder (2) es erneut versuchen? ")
                        if choice == "1":
                            self.is_camera_mode = True
                        continue

                print(f"Versuche Bild zu laden: {self.image_path}")
                frame = cv2.imread(self.image_path)
                if frame is None:
                    print(f"Fehler beim Laden des Bildes: {self.image_path}")
                    self.image_path = None
                    continue
                else:
                    print(f"Bild erfolgreich geladen: {frame.shape}")

            # Objekterkennung durchführen
            processed_frame = self.detect_orange_cones(frame)

            # Modus-Anzeige
            source_text = "Kamera" if self.is_camera_mode else f"Bild: {os.path.basename(self.image_path)}"
            cv2.putText(processed_frame, f"Quelle: {source_text}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            # Ergebnis anzeigen
            cv2.imshow("Objekt-Erkennung", processed_frame)

            # Tastendruck abfragen (nicht blockierend für Kamera, blockierend für Bild)
            key = cv2.waitKey(1 if self.is_camera_mode else 0) & 0xFF

            if key == ord('q'):
                self.running = False
            elif key == ord('c'):
                self.is_camera_mode = True
                if self.cap is None:
                    print("Wechsel zum Kamera-Modus")
            elif key == ord('i'):
                self.is_camera_mode = False
                self.image_path = None
                print("Wechsel zum Bild-Modus")

        # Aufräumen
        if self.cap is not None:
            self.cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    detector = ObjectDetector()
    detector.run()
