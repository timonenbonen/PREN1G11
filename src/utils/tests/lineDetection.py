import cv2
import numpy as np

# Bild laden
original_pfad = r"C:\Users\marin\PycharmProjects\PREN1G11\src\utils\tests\Bilder\MusterBoden\Test1.jpg"
bild = cv2.imread(original_pfad)

# Überprüfen, ob das Bild geladen wurde
if bild is None:
    print("Das Bild konnte nicht geladen werden. Überprüfe den Pfad.")
    exit()

# HEX-Farben in BGR konvertieren
def hex_to_bgr(hex_farbe):
    return tuple(int(hex_farbe[i:i+2], 16) for i in (1, 3, 5))[::-1]  # HEX zu BGR

farbe1 = "#4E6169"  # Erste Farbe
farbe2 = "#939082"  # Zweite Farbe
bgr_farbe1 = hex_to_bgr(farbe1)
bgr_farbe2 = hex_to_bgr(farbe2)

# Toleranz für die Farbauswahl (Anpassen, um ähnliche Farben zu erfassen)
toleranz = 40

# Maske für die erste Farbe erstellen
untere_grenze1 = np.array([bgr_farbe1[0] - toleranz, bgr_farbe1[1] - toleranz, bgr_farbe1[2] - toleranz])
obere_grenze1 = np.array([bgr_farbe1[0] + toleranz, bgr_farbe1[1] + toleranz, bgr_farbe1[2] + toleranz])
maske1 = cv2.inRange(bild, untere_grenze1, obere_grenze1)

# Maske für die zweite Farbe erstellen
untere_grenze2 = np.array([bgr_farbe2[0] - toleranz, bgr_farbe2[1] - toleranz, bgr_farbe2[2] - toleranz])
obere_grenze2 = np.array([bgr_farbe2[0] + toleranz, bgr_farbe2[1] + toleranz, bgr_farbe2[2] + toleranz])
maske2 = cv2.inRange(bild, untere_grenze2, obere_grenze2)

# Kombinierte Maske für die beiden Farben erstellen
kombinierte_maske_farben = cv2.bitwise_or(maske1, maske2)

# Helligkeitsmaske erstellen (entferne alle Farben, die nicht heller als ein Schwellenwert sind)
helligkeit_schwellenwert = 150  # Schwellenwert für Helligkeit (0 = dunkel, 255 = hell)
graustufen_bild = cv2.cvtColor(bild, cv2.COLOR_BGR2GRAY)  # Bild in Graustufen konvertieren
helligkeits_maske = cv2.threshold(graustufen_bild, helligkeit_schwellenwert, 255, cv2.THRESH_BINARY)[1]

# Kombinierte Maske für Farben und Helligkeit erstellen
kombinierte_maske = cv2.bitwise_or(kombinierte_maske_farben, cv2.bitwise_not(helligkeits_maske))

# Farben aus dem Bild entfernen (durch Ersetzen mit Weiß)
bild_ohne_farben = bild.copy()
bild_ohne_farben[kombinierte_maske != 0] = (255, 255, 255)  # Ersetze die Farben mit Weiß

# Vorschau erstellen (optional)
skalierungsfaktor = 0.5
vorschau_bild = cv2.resize(bild_ohne_farben, None, fx=skalierungsfaktor, fy=skalierungsfaktor)

# Ergebnisse anzeigen
cv2.imshow('Original', cv2.resize(bild, None, fx=skalierungsfaktor, fy=skalierungsfaktor))
cv2.imshow('Ohne Farben und dunkle Bereiche', vorschau_bild)
cv2.waitKey(0)
cv2.destroyAllWindows()