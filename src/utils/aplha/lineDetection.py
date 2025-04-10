import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, Scale, Button, Label, Frame, StringVar, colorchooser
from PIL import Image, ImageTk
import os


class FarbfilterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Farbfilter-Anwendung")
        self.root.geometry("1200x800")

        # Variablen
        self.bild_original = None
        self.bild_pfad = None
        self.ausgewaehlte_farben = []
        self.toleranz = 40
        self.helligkeit_schwellenwert = 150
        self.vorschau_groesse = 600

        # GUI-Layout erstellen
        self.erstelle_layout()

    def erstelle_layout(self):
        # Hauptrahmen
        main_frame = Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Linker Bereich (Steuerungselemente)
        control_frame = Frame(main_frame, width=300)
        control_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=10)

        # Bild laden
        Label(control_frame, text="Bildbearbeitung", font=("Arial", 14, "bold")).pack(pady=(0, 10))
        Button(control_frame, text="Bild laden", command=self.bild_laden).pack(fill=tk.X, pady=5)

        # Farben auswählen
        Label(control_frame, text="Farben zum Entfernen", font=("Arial", 12)).pack(pady=(20, 5))

        # Rahmen für Farbauswahltasten
        self.farben_frame = Frame(control_frame)
        self.farben_frame.pack(fill=tk.X, pady=5)

        Button(control_frame, text="+ Farbe hinzufügen", command=self.farbe_auswaehlen).pack(fill=tk.X)

        # Toleranz
        Label(control_frame, text="Farbtoleranz:", font=("Arial", 12)).pack(pady=(20, 5))
        self.toleranz_scale = Scale(control_frame, from_=5, to=100, orient=tk.HORIZONTAL,
                                    command=self.toleranz_aktualisieren)
        self.toleranz_scale.set(self.toleranz)
        self.toleranz_scale.pack(fill=tk.X)

        # Helligkeitsschwelle
        Label(control_frame, text="Helligkeitsschwellenwert:", font=("Arial", 12)).pack(pady=(20, 5))
        self.helligkeit_scale = Scale(control_frame, from_=0, to=255, orient=tk.HORIZONTAL,
                                      command=self.helligkeit_aktualisieren)
        self.helligkeit_scale.set(self.helligkeit_schwellenwert)
        self.helligkeit_scale.pack(fill=tk.X)

        # Bild bearbeiten und speichern
        Button(control_frame, text="Vorschau aktualisieren", command=self.vorschau_aktualisieren).pack(fill=tk.X,
                                                                                                       pady=(20, 5))
        Button(control_frame, text="Bild speichern", command=self.bild_speichern).pack(fill=tk.X, pady=5)

        # Status
        self.status_var = StringVar()
        self.status_var.set("Bereit. Bitte lade ein Bild.")
        Label(control_frame, textvariable=self.status_var, font=("Arial", 10),
              wraplength=280, justify=tk.LEFT).pack(pady=(20, 10), fill=tk.X)

        # Rechter Bereich (Bildvorschau)
        preview_frame = Frame(main_frame)
        preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Original
        Label(preview_frame, text="Original").pack(pady=(0, 5))
        self.original_canvas = tk.Canvas(preview_frame, bg='gray',
                                         width=self.vorschau_groesse, height=self.vorschau_groesse // 2)
        self.original_canvas.pack(pady=(0, 20))

        # Bearbeitet
        Label(preview_frame, text="Bearbeitet").pack(pady=(0, 5))
        self.bearbeitet_canvas = tk.Canvas(preview_frame, bg='gray',
                                           width=self.vorschau_groesse, height=self.vorschau_groesse // 2)
        self.bearbeitet_canvas.pack()

    def bild_laden(self):
        self.bild_pfad = filedialog.askopenfilename(
            filetypes=[("Bildateien", "*.jpg *.jpeg *.png *.bmp")])

        if self.bild_pfad:
            self.bild_original = cv2.imread(self.bild_pfad)
            if self.bild_original is None:
                self.status_var.set("Fehler: Bild konnte nicht geladen werden.")
                return

            self.zeige_original_bild()
            self.status_var.set(f"Bild geladen: {os.path.basename(self.bild_pfad)}")
            self.vorschau_aktualisieren()

    def zeige_original_bild(self):
        if self.bild_original is not None:
            # Bild skalieren für die Anzeige
            bildhoehe, bildbreite = self.bild_original.shape[:2]
            skalierungsfaktor = min(self.vorschau_groesse / bildbreite, (self.vorschau_groesse // 2) / bildhoehe)
            neue_breite = int(bildbreite * skalierungsfaktor)
            neue_hoehe = int(bildhoehe * skalierungsfaktor)

            bild_anzeige = cv2.resize(self.bild_original, (neue_breite, neue_hoehe))
            # BGR zu RGB konvertieren für Tkinter
            bild_anzeige = cv2.cvtColor(bild_anzeige, cv2.COLOR_BGR2RGB)

            # Bild für Tkinter vorbereiten
            self.original_photo = ImageTk.PhotoImage(image=Image.fromarray(bild_anzeige))
            self.original_canvas.config(width=neue_breite, height=neue_hoehe)
            self.original_canvas.create_image(0, 0, anchor=tk.NW, image=self.original_photo)

    def farbe_auswaehlen(self):
        # Farbauswahldialog öffnen
        farbe_hex = colorchooser.askcolor(title="Farbe zum Entfernen auswählen")[1]
        if farbe_hex:
            # Farbe zur Liste hinzufügen
            self.ausgewaehlte_farben.append(farbe_hex)
            # Farbbutton zum Anzeigen erstellen
            self._farb_button_erstellen(farbe_hex)
            # Vorschau aktualisieren
            self.vorschau_aktualisieren()

    def _farb_button_erstellen(self, farbe_hex):
        farb_index = len(self.ausgewaehlte_farben) - 1
        # Farbbutton
        farb_button = Frame(self.farben_frame, bg=farbe_hex, width=30, height=30,
                            borderwidth=1, relief=tk.RAISED)
        farb_button.grid(row=0, column=farb_index % 5, padx=2, pady=2)
        farb_button.pack_propagate(False)

        # Entfernen-Button innerhalb des Farb-Frames
        remove_btn = Button(farb_button, text="X", font=("Arial", 8), bg=farbe_hex,
                            command=lambda idx=farb_index: self.farbe_entfernen(idx))
        remove_btn.pack(side=tk.TOP, anchor=tk.NE, padx=1, pady=1)

    def farbe_entfernen(self, index):
        if 0 <= index < len(self.ausgewaehlte_farben):
            # Farbe aus der Liste entfernen
            self.ausgewaehlte_farben.pop(index)
            # GUI-Elemente für Farben neu aufbauen
            for widget in self.farben_frame.winfo_children():
                widget.destroy()

            for farbe in self.ausgewaehlte_farben:
                self._farb_button_erstellen(farbe)

            # Vorschau aktualisieren
            self.vorschau_aktualisieren()

    def hex_to_bgr(self, hex_farbe):
        # HEX zu BGR konvertieren
        hex_farbe = hex_farbe.lstrip('#')
        return tuple(int(hex_farbe[i:i + 2], 16) for i in (4, 2, 0))

    def toleranz_aktualisieren(self, wert):
        self.toleranz = int(wert)
        # Keine sofortige Aktualisierung für bessere Performance

    def helligkeit_aktualisieren(self, wert):
        self.helligkeit_schwellenwert = int(wert)
        # Keine sofortige Aktualisierung für bessere Performance

    def vorschau_aktualisieren(self):
        if self.bild_original is None:
            self.status_var.set("Kein Bild geladen.")
            return

        if not self.ausgewaehlte_farben:
            # Zeige das Originalbild, wenn keine Farben ausgewählt wurden
            self.zeige_bearbeitetes_bild(self.bild_original.copy())
            self.status_var.set("Keine Farben zum Entfernen ausgewählt.")
            return

        # Kopie des Originalbildes erstellen
        bild_bearbeitet = self.bild_original.copy()

        # Helligkeitsmaske erstellen
        graustufen_bild = cv2.cvtColor(bild_bearbeitet, cv2.COLOR_BGR2GRAY)
        helligkeits_maske = cv2.threshold(graustufen_bild, self.helligkeit_schwellenwert, 255, cv2.THRESH_BINARY)[1]

        # Kombinierte Farbmaske erstellen
        kombinierte_maske_farben = np.zeros_like(graustufen_bild)

        for farbe_hex in self.ausgewaehlte_farben:
            bgr_farbe = self.hex_to_bgr(farbe_hex)

            # Untere und obere Grenzen für die Farbmaske
            untere_grenze = np.array([bgr_farbe[0] - self.toleranz,
                                      bgr_farbe[1] - self.toleranz,
                                      bgr_farbe[2] - self.toleranz])
            obere_grenze = np.array([bgr_farbe[0] + self.toleranz,
                                     bgr_farbe[1] + self.toleranz,
                                     bgr_farbe[2] + self.toleranz])

            # Maske für die aktuelle Farbe
            maske = cv2.inRange(bild_bearbeitet, untere_grenze, obere_grenze)
            kombinierte_maske_farben = cv2.bitwise_or(kombinierte_maske_farben, maske)

        # Kombinierte Maske für Farben und Helligkeit
        kombinierte_maske = cv2.bitwise_or(kombinierte_maske_farben, cv2.bitwise_not(helligkeits_maske))

        # Ausgewählte Farben und dunkle Bereiche durch Weiß ersetzen
        bild_bearbeitet[kombinierte_maske != 0] = (255, 255, 255)

        # Bearbeitetes Bild anzeigen
        self.zeige_bearbeitetes_bild(bild_bearbeitet)
        self.status_var.set(f"{len(self.ausgewaehlte_farben)} Farben entfernt. Toleranz: {self.toleranz}")

    def zeige_bearbeitetes_bild(self, bild):
        # Bild skalieren für die Anzeige
        bildhoehe, bildbreite = bild.shape[:2]
        skalierungsfaktor = min(self.vorschau_groesse / bildbreite, (self.vorschau_groesse // 2) / bildhoehe)
        neue_breite = int(bildbreite * skalierungsfaktor)
        neue_hoehe = int(bildhoehe * skalierungsfaktor)

        bild_anzeige = cv2.resize(bild, (neue_breite, neue_hoehe))
        # BGR zu RGB konvertieren für Tkinter
        bild_anzeige = cv2.cvtColor(bild_anzeige, cv2.COLOR_BGR2RGB)

        # Bild für Tkinter vorbereiten
        self.bearbeitet_photo = ImageTk.PhotoImage(image=Image.fromarray(bild_anzeige))
        self.bearbeitet_canvas.config(width=neue_breite, height=neue_hoehe)
        self.bearbeitet_canvas.create_image(0, 0, anchor=tk.NW, image=self.bearbeitet_photo)

    def bild_speichern(self):
        if self.bild_original is None:
            self.status_var.set("Kein Bild zum Speichern.")
            return

        # Dialog zum Speichern öffnen
        speicherpfad = filedialog.asksaveasfilename(
            defaultextension=".jpg",
            filetypes=[("JPEG-Bild", "*.jpg"), ("PNG-Bild", "*.png"), ("Alle Dateien", "*.*")],
            initialdir=os.path.dirname(self.bild_pfad) if self.bild_pfad else None,
            initialfile=f"bearbeitet_{os.path.basename(self.bild_pfad)}" if self.bild_pfad else "bearbeitet.jpg"
        )

        if not speicherpfad:
            return

        # Aktuelle Bearbeitung anwenden und speichern
        if not self.ausgewaehlte_farben:
            self.status_var.set("Keine Änderungen vorgenommen.")
            return

        # Bild wie in der Vorschaufunktion bearbeiten
        bild_bearbeitet = self.bild_original.copy()

        # Helligkeitsmaske erstellen
        graustufen_bild = cv2.cvtColor(bild_bearbeitet, cv2.COLOR_BGR2GRAY)
        helligkeits_maske = cv2.threshold(graustufen_bild, self.helligkeit_schwellenwert, 255, cv2.THRESH_BINARY)[1]

        # Kombinierte Farbmaske erstellen
        kombinierte_maske_farben = np.zeros_like(graustufen_bild)

        for farbe_hex in self.ausgewaehlte_farben:
            bgr_farbe = self.hex_to_bgr(farbe_hex)

            # Untere und obere Grenzen für die Farbmaske
            untere_grenze = np.array([bgr_farbe[0] - self.toleranz,
                                      bgr_farbe[1] - self.toleranz,
                                      bgr_farbe[2] - self.toleranz])
            obere_grenze = np.array([bgr_farbe[0] + self.toleranz,
                                     bgr_farbe[1] + self.toleranz,
                                     bgr_farbe[2] + self.toleranz])

            # Maske für die aktuelle Farbe
            maske = cv2.inRange(bild_bearbeitet, untere_grenze, obere_grenze)
            kombinierte_maske_farben = cv2.bitwise_or(kombinierte_maske_farben, maske)

        # Kombinierte Maske für Farben und Helligkeit
        kombinierte_maske = cv2.bitwise_or(kombinierte_maske_farben, cv2.bitwise_not(helligkeits_maske))

        # Ausgewählte Farben und dunkle Bereiche durch Weiß ersetzen
        bild_bearbeitet[kombinierte_maske != 0] = (255, 255, 255)

        # Bild speichern
        cv2.imwrite(speicherpfad, bild_bearbeitet)
        self.status_var.set(f"Bild gespeichert unter: {speicherpfad}")


# Programm starten
if __name__ == "__main__":
    root = tk.Tk()
    app = FarbfilterApp(root)
    root.mainloop()