import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog
import os
import time


class ObjectDetector:
    def __init__(self):
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
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Orangene Farbe
        lower_orange = np.array([5, 100, 150])
        upper_orange = np.array([25, 255, 255])

        # Rote Farbe (Rot hat zwei Bereiche im HSV-Farbraum)
        lower_red1 = np.array([0, 120, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 120, 100])
        upper_red2 = np.array([180, 255, 255])

        # Weiße Farbe (Helle Bereiche mit hoher Sättigung vermeiden)
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 50, 255])

        # Masken erstellen
        mask_orange = cv2.inRange(hsv, lower_orange, upper_orange)
        mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask_white = cv2.inRange(hsv, lower_white, upper_white)

        # Masken kombinieren (Orange, Rot, Weiß)
        mask = mask_orange | mask_red1 | mask_red2 | mask_white

        # Rauschreduktion
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.erode(mask, kernel, iterations=1)
        mask = cv2.dilate(mask, kernel, iterations=2)

        # Konturen finden
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            if cv2.contourArea(contour) < 500:
                continue

            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = float(h) / w
            if aspect_ratio > 1.2:
                cv2.rectangle(original, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(original, "Pylon", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        cv2.imshow("Maske", mask)
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